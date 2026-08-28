#!/usr/bin/env python3
"""Read-only readiness and identity checks for the canonical windows-wsl host."""

from __future__ import annotations

import argparse
import ipaddress
import json
import re
import shlex
import subprocess
import sys
from typing import Any

CANONICAL_ALIAS = "windows-wsl"
EXIT_PRECONDITION = 4
GIB = 1024**3

REMOTE_PROGRAM = r'''
import hashlib, json, os, pathlib, shutil, socket, subprocess, sys

config = json.loads(sys.argv[1])
project = pathlib.Path(config["project"])

def run(argv):
    try:
        result = subprocess.run(argv, text=True, stdout=subprocess.PIPE,
                                stderr=subprocess.DEVNULL, timeout=20, check=False)
        return result.returncode, result.stdout
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return 127, ""

def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()

def dirty_manifest(root):
    rc, raw = run(["git", "-C", str(root), "status", "--porcelain=v1",
                   "-z", "--untracked-files=all"])
    if rc != 0:
        return []
    entries, fields, index = [], raw.split("\0") if raw else [], 0
    while index < len(fields):
        field = fields[index]
        index += 1
        if not field:
            continue
        status, rel = field[:2], field[3:]
        if status[0] in "RC" and index < len(fields):
            rel = fields[index]
            index += 1
        path = root / rel
        value = sha256(path) if path.is_file() and not path.is_symlink() else None
        entries.append({"path": rel, "status": status, "sha256": value})
    return sorted(entries, key=lambda item: item["path"])

def listeners():
    rc, output = run(["ss", "-H", "-ltn"])
    ports, bindings = set(), {}
    if rc == 0:
        for line in output.splitlines():
            fields = line.split()
            local = fields[3] if len(fields) > 3 else ""
            address, _, tail = local.rpartition(":")
            if tail.isdigit():
                port = int(tail)
                address = address.strip("[]")
                ports.add(port)
                bindings.setdefault(str(port), []).append(address)
    return {"ports": sorted(ports),
            "bindings": {key: sorted(set(value)) for key, value in bindings.items()}}

def tailscale_ipv4s():
    rc, output = run(["tailscale", "ip", "-4"])
    return sorted(set(value.strip() for value in output.splitlines() if value.strip())) \
        if rc == 0 else []

def relay_manifest(path_text):
    result = {"path": path_text, "exists": False, "valid_json": False,
              "root_owned": False, "safe_mode": False, "project_id": None,
              "unit": None, "pid": None, "bind_ipv4": None, "ports": []}
    if not path_text:
        return result
    path = pathlib.Path(path_text)
    if not path.is_file() or path.is_symlink() or path.stat().st_size > 65536:
        return result
    stat = path.stat()
    result.update({"exists": True, "root_owned": stat.st_uid == 0,
                   "safe_mode": stat.st_mode & 0o022 == 0})
    try:
        parsed = json.loads(path.read_text())
    except (OSError, UnicodeError, json.JSONDecodeError):
        return result
    if not isinstance(parsed, dict):
        return result
    result["valid_json"] = True
    for key in ("project_id", "unit", "bind_ipv4"):
        value = parsed.get(key)
        result[key] = value if isinstance(value, str) else None
    result["pid"] = parsed.get("pid") if isinstance(parsed.get("pid"), int) else None
    ports = parsed.get("ports")
    result["ports"] = sorted(set(value for value in ports if isinstance(value, int))) \
        if isinstance(ports, list) else []
    return result

def relay_unit(unit):
    result = {"unit": unit, "load_state": None, "active_state": None,
              "sub_state": None, "main_pid": None}
    if not unit:
        return result
    rc, output = run(["systemctl", "show", unit, "--property=LoadState",
                      "--property=ActiveState", "--property=SubState",
                      "--property=MainPID"])
    if rc != 0:
        return result
    values = dict(line.split("=", 1) for line in output.splitlines() if "=" in line)
    result.update({"load_state": values.get("LoadState"),
                   "active_state": values.get("ActiveState"),
                   "sub_state": values.get("SubState"),
                   "main_pid": int(values.get("MainPID", "0"))
                   if values.get("MainPID", "0").isdigit() else None})
    return result

def docker_ownership(compose_project):
    ownership = {"containers": [], "networks": [], "ports": {},
                 "non_loopback_ports": []}
    if not compose_project:
        return ownership
    label = "com.docker.compose.project=" + compose_project
    rc, ids = run(["docker", "ps", "-a", "--filter", "label=" + label,
                   "--format", "{{.ID}}"])
    container_ids = [value for value in ids.splitlines() if value] if rc == 0 else []
    if container_ids:
        rc, raw = run(["docker", "inspect", *container_ids])
        if rc == 0:
            try:
                inspected = json.loads(raw)
            except json.JSONDecodeError:
                inspected = []
            for item in inspected:
                name = str(item.get("Name", "")).lstrip("/")
                ownership["containers"].append(name)
                bindings = item.get("NetworkSettings", {}).get("Ports", {}) or {}
                for values in bindings.values():
                    for binding in values or []:
                        port = str(binding.get("HostPort", ""))
                        host_ip = str(binding.get("HostIp", ""))
                        if port.isdigit():
                            ownership["ports"].setdefault(port, []).append(host_ip)
                            if host_ip not in {"127.0.0.1", "::1"}:
                                ownership["non_loopback_ports"].append(int(port))
    rc, networks = run(["docker", "network", "ls", "--filter", "label=" + label,
                        "--format", "{{.Name}}"])
    if rc == 0:
        ownership["networks"] = sorted(value for value in networks.splitlines() if value)
    ownership["containers"] = sorted(ownership["containers"])
    ownership["non_loopback_ports"] = sorted(set(ownership["non_loopback_ports"]))
    return ownership

def identity(path_text):
    result = {"path": path_text, "exists": False, "sha256": None,
              "valid_json": False, "project_id": None,
              "compose_project": None, "source_manifest_path": None,
              "source_manifest_sha256": None}
    if not path_text:
        return result
    path = pathlib.Path(path_text)
    if not path.is_file() or path.is_symlink() or path.stat().st_size > 1024 * 1024:
        return result
    result["exists"] = True
    result["sha256"] = sha256(path)
    try:
        parsed = json.loads(path.read_text())
    except (OSError, UnicodeError, json.JSONDecodeError):
        return result
    if not isinstance(parsed, dict):
        return result
    result["valid_json"] = True
    for key in ("project_id", "compose_project", "source_manifest_path",
                "source_manifest_sha256"):
        value = parsed.get(key)
        result[key] = value if isinstance(value, str) else None
    return result

def deployment_source_manifest(path_text):
    result = {"path": path_text, "exists": False, "sha256": None,
              "valid_json": False, "git_head": None, "git_branch": None,
              "content_digest": None, "dirty_digest": None}
    if not path_text:
        return result
    path = pathlib.Path(path_text)
    if (not path.is_absolute() or not path.is_file() or path.is_symlink()
            or path.stat().st_size > 1024 * 1024):
        return result
    result["exists"] = True
    result["sha256"] = sha256(path)
    try:
        parsed = json.loads(path.read_text())
    except (OSError, UnicodeError, json.JSONDecodeError):
        return result
    if not isinstance(parsed, dict):
        return result
    result["valid_json"] = True
    for key in ("git_head", "git_branch", "content_digest", "dirty_digest"):
        value = parsed.get(key)
        result[key] = value if isinstance(value, str) else None
    return result

exists = project.is_dir()
disk_root = project if exists else project.parent
while not disk_root.exists() and disk_root != disk_root.parent:
    disk_root = disk_root.parent
disk = shutil.disk_usage(disk_root)
mem = {}
try:
    for line in pathlib.Path("/proc/meminfo").read_text().splitlines():
        key, value = line.split(":", 1)
        if key in {"MemTotal", "MemAvailable", "SwapTotal", "SwapFree"}:
            mem[key] = int(value.strip().split()[0]) * 1024
except OSError:
    pass

head_rc, head = run(["git", "-C", str(project), "rev-parse", "HEAD"])
branch_rc, branch = run(["git", "-C", str(project), "branch", "--show-current"])
docker_rc, docker_version = run(["docker", "version", "--format",
                                 "client={{.Client.Version}} server={{.Server.Version}}"])
compose_rc, compose_version = run(["docker", "compose", "version", "--short"])
bound = listeners()
manifest = {
    "schema_version": 1,
    "source_root": str(project),
    "git_head": head.strip() if head_rc == 0 else None,
    "git_branch": branch.strip() if branch_rc == 0 else None,
    "dirty": dirty_manifest(project) if head_rc == 0 else [],
}
canonical = json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode()
deployment_identity = identity(config.get("expected_manifest"))
print(json.dumps({
    "schema_version": 2,
    "mode": config["mode"],
    "host": {"hostname": socket.gethostname(), "kernel": os.uname().release},
    "project": {"path": str(project), "exists": exists, "is_git": head_rc == 0},
    "capacity": {"disk_total_bytes": disk.total, "disk_free_bytes": disk.free,
                 "memory": mem},
    "ports": {"requested": config["ports"], "listening": bound["ports"],
              "bindings": bound["bindings"]},
    "tailscale": {"ipv4": tailscale_ipv4s()},
    "docker": {"daemon_available": docker_rc == 0,
               "version": docker_version.strip() if docker_rc == 0 else None,
               "compose_available": compose_rc == 0,
               "compose_version": compose_version.strip() if compose_rc == 0 else None},
    "ownership": docker_ownership(config.get("compose_project")),
    "relays": [{"port": item["port"],
                "manifest": relay_manifest(item["manifest"]),
                "unit": relay_unit(item["unit"])}
               for item in config.get("relays", [])],
    "identity": deployment_identity,
    "deployment_source_manifest": deployment_source_manifest(
        deployment_identity.get("source_manifest_path")
    ),
    "source_manifest": manifest,
    "source_manifest_sha256": hashlib.sha256(canonical).hexdigest(),
}, sort_keys=True))
'''


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--mode", choices=("prepare-new", "verify-existing"))
    parser.add_argument("--stack-kind", choices=("ci", "dev"), default="ci")
    parser.add_argument("--project", help="Explicit absolute Linux path in WSL")
    parser.add_argument("--project-id", help="Explicit stable project identity")
    parser.add_argument("--compose-project", help="Expected Docker Compose project")
    parser.add_argument("--expected-manifest", help="Absolute WSL identity-manifest path")
    parser.add_argument("--expected-digest", help="Expected SHA-256 of identity manifest")
    parser.add_argument("--port", action="append", type=int, default=[])
    parser.add_argument("--relay-port", action="append", type=int, default=[])
    parser.add_argument("--tailscale-ip")
    parser.add_argument("--relay-unit", action="append", default=[])
    parser.add_argument("--relay-manifest", action="append", default=[])
    parser.add_argument("--min-free-gib", type=float, default=10.0)
    parser.add_argument("--min-memory-gib", type=float, default=4.0)
    execution = parser.add_mutually_exclusive_group()
    execution.add_argument("--execute", action="store_true")
    execution.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def normalize_digest(value: object) -> str | None:
    if not isinstance(value, str) or not value:
        return None
    if value.startswith("sha256:"):
        value = value[7:]
    return value.lower()


def is_sha256(value: object) -> bool:
    return isinstance(value, str) and bool(
        re.fullmatch(r"(?:sha256:)?[0-9a-fA-F]{64}", value)
    )


def build_config(args: argparse.Namespace) -> dict[str, Any]:
    if not args.mode:
        raise ValueError("--mode is required")
    if not args.project or not args.project.startswith("/") or any(
        char in args.project for char in "\n\r\0"
    ):
        raise ValueError("--project must be an absolute single-line Linux path")
    if not args.port or any(port < 1 or port > 65535 for port in args.port):
        raise ValueError("at least one --port between 1 and 65535 is required")
    if args.min_free_gib < 0 or args.min_memory_gib < 0:
        raise ValueError("capacity thresholds cannot be negative")
    config: dict[str, Any] = {
        "mode": args.mode,
        "stack_kind": args.stack_kind,
        "project": args.project,
        "ports": sorted(set(args.port)),
        "min_free_bytes": int(args.min_free_gib * GIB),
        "min_memory_bytes": int(args.min_memory_gib * GIB),
        "project_id": None,
        "compose_project": None,
        "expected_manifest": None,
        "expected_digest": None,
        "reset_allowed": False,
        "relay_ports": [],
        "tailscale_ip": None,
        "relays": [],
    }
    if args.stack_kind == "dev":
        if len(set(args.relay_port)) != 2 or any(
            port < 1 or port > 65535 for port in args.relay_port
        ):
            raise ValueError("dev requires exactly two distinct API/DB --relay-port values")
        try:
            address = ipaddress.ip_address(args.tailscale_ip or "")
        except ValueError as error:
            raise ValueError("dev requires a valid --tailscale-ip IPv4") from error
        if address.version != 4 or not address in ipaddress.ip_network("100.64.0.0/10"):
            raise ValueError("--tailscale-ip must be an IPv4 in Tailscale CGNAT space")
        if len(args.relay_unit or []) != 2 or any(
            not re.fullmatch(r"[A-Za-z0-9@_.-]+\.service", unit)
            for unit in (args.relay_unit or [])
        ):
            raise ValueError("dev requires two safe --relay-unit values")
        if len(args.relay_manifest or []) != 2 or any(
            not value.startswith("/") or any(char in value for char in "\n\r\0")
            for value in (args.relay_manifest or [])
        ):
            raise ValueError("dev requires two absolute --relay-manifest values")
        relays = [
            {"port": port, "unit": unit, "manifest": manifest}
            for port, unit, manifest in zip(
                args.relay_port, args.relay_unit, args.relay_manifest, strict=True
            )
        ]
        config.update({"relay_ports": sorted(set(args.relay_port)),
                       "tailscale_ip": str(address),
                       "relays": relays})
    elif args.relay_port or args.tailscale_ip or args.relay_unit or args.relay_manifest:
        raise ValueError("relay arguments are valid only for --stack-kind dev")
    if args.mode == "verify-existing":
        if not args.project_id or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", args.project_id):
            raise ValueError("verify-existing requires a safe --project-id")
        if not args.compose_project or not re.fullmatch(
            r"[A-Za-z0-9][A-Za-z0-9_.-]*", args.compose_project
        ):
            raise ValueError("verify-existing requires a safe --compose-project")
        if (not args.expected_manifest or not args.expected_manifest.startswith("/")
                or any(char in args.expected_manifest for char in "\n\r\0")):
            raise ValueError("verify-existing requires an absolute --expected-manifest")
        digest = normalize_digest(args.expected_digest)
        if not digest or not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise ValueError("verify-existing requires a SHA-256 --expected-digest")
        config.update({
            "project_id": args.project_id,
            "compose_project": args.compose_project,
            "expected_manifest": args.expected_manifest,
            "expected_digest": digest,
        })
    return config


def evaluate_report(config: dict[str, Any], report: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    project = report.get("project", {})
    capacity = report.get("capacity", {})
    docker = report.get("docker", {})
    ports = report.get("ports", {})
    if config.get("reset_allowed") is not False:
        failures.append("reset_allowed_must_initialize_false")
    if not project.get("exists"):
        failures.append("project_missing")
    if config["mode"] == "prepare-new" and not project.get("is_git"):
        failures.append("project_not_git")
    if not docker.get("daemon_available"):
        failures.append("docker_unavailable")
    if not docker.get("compose_available"):
        failures.append("compose_unavailable")
    if capacity.get("disk_free_bytes", 0) < config["min_free_bytes"]:
        failures.append("disk_capacity_insufficient")
    available_memory = capacity.get("memory", {}).get("MemAvailable", 0)
    if available_memory < config["min_memory_bytes"]:
        failures.append("memory_capacity_insufficient")

    requested = set(config["ports"])
    listening = set(ports.get("listening", []))
    if config["mode"] == "prepare-new":
        if (requested | set(config.get("relay_ports", []))) & listening:
            failures.append("requested_port_occupied")
    else:
        identity = report.get("identity", {})
        package_manifest = report.get("deployment_source_manifest", {})
        ownership = report.get("ownership", {})
        owned_ports = {int(port) for port in ownership.get("ports", {})}
        if not identity.get("exists"):
            failures.append("identity_manifest_missing")
        elif not identity.get("valid_json"):
            failures.append("identity_manifest_invalid")
        if identity.get("sha256") != config["expected_digest"]:
            failures.append("identity_digest_mismatch")
        if identity.get("project_id") != config["project_id"]:
            failures.append("project_identity_mismatch")
        if identity.get("compose_project") != config["compose_project"]:
            failures.append("compose_identity_mismatch")
        identity_source_digest = normalize_digest(identity.get("source_manifest_sha256"))
        if not identity.get("project_id") or not identity.get("compose_project") \
                or not identity_source_digest:
            failures.append("identity_fields_missing")
        git_baseline_valid = bool(
            project.get("is_git")
            and identity_source_digest == normalize_digest(report.get("source_manifest_sha256"))
        )
        package_baseline_valid = bool(
            package_manifest.get("exists")
            and package_manifest.get("valid_json")
            and identity_source_digest == normalize_digest(package_manifest.get("sha256"))
            and isinstance(package_manifest.get("git_head"), str)
            and bool(package_manifest.get("git_head"))
            and isinstance(package_manifest.get("git_branch"), str)
            and bool(package_manifest.get("git_branch"))
            and (is_sha256(package_manifest.get("content_digest"))
                 or is_sha256(package_manifest.get("dirty_digest")))
        )
        if not (git_baseline_valid or package_baseline_valid):
            failures.append("source_baseline_unverified")
        if not ownership.get("containers"):
            failures.append("owned_containers_missing")
        if not ownership.get("networks"):
            failures.append("owned_network_missing")
        if requested - listening:
            failures.append("requested_port_not_listening")
        if requested - owned_ports:
            failures.append("requested_port_not_owned")
        if ownership.get("non_loopback_ports"):
            failures.append("non_loopback_binding")
        if config.get("stack_kind") == "ci":
            if report.get("relay", {}).get("manifest", {}).get("exists"):
                failures.append("ci_relay_forbidden")
        else:
            expected_ip = config.get("tailscale_ip")
            relay_ports = set(config.get("relay_ports", []))
            active_ips = set(report.get("tailscale", {}).get("ipv4", []))
            bindings = ports.get("bindings", {})
            relays = report.get("relays", [])
            if active_ips != {expected_ip}:
                failures.append("tailscale_ipv4_mismatch")
            for port in relay_ports:
                observed_bindings = set(bindings.get(str(port), []))
                if expected_ip not in observed_bindings or not observed_bindings.issubset(
                    {expected_ip, "127.0.0.1", "::1"}
                ):
                    failures.append("relay_binding_mismatch")
            expected_relays = {item["port"]: item for item in config.get("relays", [])}
            observed_relays = {item.get("port"): item for item in relays}
            if set(observed_relays) != set(expected_relays):
                failures.append("relay_descriptor_mismatch")
            for port, expected in expected_relays.items():
                observed = observed_relays.get(port, {})
                relay_identity = observed.get("manifest", {})
                relay_unit = observed.get("unit", {})
                if not relay_identity.get("exists") or not relay_identity.get("valid_json") \
                        or not relay_identity.get("root_owned") or not relay_identity.get("safe_mode"):
                    failures.append("relay_manifest_invalid")
                if relay_identity.get("project_id") != config.get("project_id") \
                        or relay_identity.get("unit") != expected["unit"] \
                        or relay_identity.get("bind_ipv4") != expected_ip \
                        or set(relay_identity.get("ports", [])) != {port}:
                    failures.append("relay_identity_mismatch")
                if relay_unit.get("unit") != expected["unit"] \
                        or relay_unit.get("load_state") != "loaded" \
                        or relay_unit.get("active_state") != "active" \
                        or not relay_unit.get("main_pid") \
                        or relay_unit.get("main_pid") != relay_identity.get("pid"):
                    failures.append("relay_unit_not_owner")
    return sorted(set(failures))


def build_command(config: dict[str, Any]) -> list[str]:
    payload = json.dumps(config, sort_keys=True, separators=(",", ":"))
    remote_command = shlex.join(["python3", "-", payload])
    return ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10",
            CANONICAL_ALIAS, remote_command]


def mock_report(*, existing: bool) -> dict[str, Any]:
    digest = "a" * 64
    return {
        "project": {"exists": True, "is_git": True},
        "capacity": {"disk_free_bytes": 20 * GIB,
                     "memory": {"MemAvailable": 8 * GIB}},
        "docker": {"daemon_available": True, "compose_available": True},
        "ports": {"listening": [15432] if existing else [],
                  "bindings": {"15432": ["127.0.0.1"]} if existing else {}},
        "tailscale": {"ipv4": []},
        "relays": [],
        "identity": {"exists": existing, "valid_json": existing,
                     "sha256": digest if existing else None,
                     "project_id": "example-ci" if existing else None,
                     "compose_project": "example-ci" if existing else None,
                     "source_manifest_path": None,
                     "source_manifest_sha256": "b" * 64 if existing else None},
        "deployment_source_manifest": {"exists": False, "valid_json": False,
                                       "sha256": None, "git_head": None,
                                       "git_branch": None, "content_digest": None,
                                       "dirty_digest": None},
        "source_manifest_sha256": "b" * 64,
        "ownership": {"containers": ["example-db"] if existing else [],
                      "networks": ["example-ci_default"] if existing else [],
                      "ports": {"15432": ["127.0.0.1"]} if existing else {},
                      "non_loopback_ports": []},
    }


def self_test() -> int:
    base = {"mode": "prepare-new", "stack_kind": "ci",
            "project": "/srv/codex/example",
            "ports": [15432], "min_free_bytes": 10 * GIB,
            "min_memory_bytes": 4 * GIB, "project_id": None,
            "compose_project": None, "expected_manifest": None,
            "expected_digest": None, "reset_allowed": False,
            "relay_ports": [], "tailscale_ip": None, "relays": []}
    assert evaluate_report(base, mock_report(existing=False)) == []
    negative = mock_report(existing=False)
    negative["project"] = {"exists": False, "is_git": False}
    negative["ports"]["listening"] = [15432]
    negative["docker"]["daemon_available"] = False
    negative["capacity"]["disk_free_bytes"] = 1
    negative["capacity"]["memory"]["MemAvailable"] = 1
    reasons = evaluate_report(base, negative)
    assert {"project_missing", "project_not_git", "requested_port_occupied",
            "docker_unavailable", "disk_capacity_insufficient",
            "memory_capacity_insufficient"}.issubset(reasons)
    existing = dict(base, mode="verify-existing", project_id="example-ci",
                    compose_project="example-ci",
                    expected_manifest="/srv/codex/example/identity.json",
                    expected_digest="a" * 64)
    assert evaluate_report(existing, mock_report(existing=True)) == []
    assert "'" in build_command(dict(base, project="/srv/codex/path with spaces"))[-1]
    print(json.dumps({"self_test": "passed", "cases": 4,
                      "ssh_alias": CANONICAL_ALIAS}, sort_keys=True))
    return 0


def main() -> int:
    args = parse_args()
    if args.self_test:
        return self_test()
    try:
        config = build_config(args)
    except ValueError as error:
        print(json.dumps({"ok": False, "fail_reasons": ["invalid_arguments"],
                          "message": str(error)}, sort_keys=True))
        return 2
    command = build_command(config)
    if not args.execute:
        print(json.dumps({"ok": True, "mode": "dry-run",
                          "operation": config["mode"], "ssh_alias": CANONICAL_ALIAS,
                          "project": config["project"], "stack_kind": config["stack_kind"],
                          "ports": config["ports"], "relay_ports": config["relay_ports"],
                          "reset_allowed": config["reset_allowed"],
                          "command": shlex.join(command), "mutation": False},
                         sort_keys=True, indent=2))
        return 0
    ssh_config = subprocess.run(["ssh", "-G", CANONICAL_ALIAS], text=True,
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                check=False)
    if ssh_config.returncode != 0:
        print(json.dumps({"ok": False, "fail_reasons": ["ssh_alias_unavailable"]},
                         sort_keys=True))
        return 3
    result = subprocess.run(command, input=REMOTE_PROGRAM, text=True,
                            capture_output=True, check=False)
    if result.returncode != 0:
        print(json.dumps({"ok": False, "fail_reasons": ["remote_collector_failed"],
                          "collector_exit": result.returncode}, sort_keys=True))
        return result.returncode
    try:
        report = json.loads(result.stdout)
    except json.JSONDecodeError:
        print(json.dumps({"ok": False, "fail_reasons": ["remote_report_invalid"]},
                         sort_keys=True))
        return 5
    failures = evaluate_report(config, report)
    report["ok"] = not failures
    report["fail_reasons"] = failures
    print(json.dumps(report, sort_keys=True, indent=2))
    return 0 if not failures else EXIT_PRECONDITION


if __name__ == "__main__":
    raise SystemExit(main())
