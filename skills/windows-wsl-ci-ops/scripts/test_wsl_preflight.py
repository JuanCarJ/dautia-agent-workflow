#!/usr/bin/env python3
"""Deterministic tests for WSL preflight failure and ownership semantics."""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import pathlib
import subprocess
import sys
import unittest
from unittest import mock

SCRIPT = pathlib.Path(__file__).with_name("wsl_preflight.py")
SPEC = importlib.util.spec_from_file_location("wsl_preflight", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class PreflightTests(unittest.TestCase):
    def config(self, mode: str) -> dict[str, object]:
        return {
            "mode": mode,
            "stack_kind": "ci",
            "project": "/srv/codex/example",
            "ports": [15432],
            "min_free_bytes": 10 * MODULE.GIB,
            "min_memory_bytes": 4 * MODULE.GIB,
            "project_id": "example-ci" if mode == "verify-existing" else None,
            "compose_project": "example-ci" if mode == "verify-existing" else None,
            "expected_manifest": "/srv/codex/example/identity.json"
            if mode == "verify-existing" else None,
            "expected_digest": "a" * 64 if mode == "verify-existing" else None,
            "reset_allowed": False,
            "relay_ports": [],
            "tailscale_ip": None,
            "relays": [],
        }

    def test_prepare_new_failure_is_machine_readable_and_nonzero(self) -> None:
        report = MODULE.mock_report(existing=False)
        report["project"] = {"exists": False, "is_git": False}
        report["ports"]["listening"] = [15432]
        report["docker"] = {"daemon_available": False, "compose_available": False}
        report["capacity"] = {"disk_free_bytes": 1,
                              "memory": {"MemAvailable": 1}}
        argv = ["wsl_preflight.py", "--mode", "prepare-new", "--project",
                "/srv/codex/example", "--port", "15432", "--execute"]
        calls = [
            subprocess.CompletedProcess([], 0, "", ""),
            subprocess.CompletedProcess([], 0, json.dumps(report), ""),
        ]
        output = io.StringIO()
        with mock.patch.object(sys, "argv", argv), \
                mock.patch.object(MODULE.subprocess, "run", side_effect=calls), \
                contextlib.redirect_stdout(output):
            code = MODULE.main()
        result = json.loads(output.getvalue())
        self.assertEqual(code, MODULE.EXIT_PRECONDITION)
        self.assertFalse(result["ok"])
        self.assertIn("project_missing", result["fail_reasons"])
        self.assertIn("requested_port_occupied", result["fail_reasons"])
        self.assertIn("docker_unavailable", result["fail_reasons"])

    def test_verify_existing_accepts_project_owned_stack(self) -> None:
        failures = MODULE.evaluate_report(
            self.config("verify-existing"), MODULE.mock_report(existing=True)
        )
        self.assertEqual(failures, [])

    def test_verify_existing_rejects_foreign_port_and_identity(self) -> None:
        report = MODULE.mock_report(existing=True)
        report["identity"]["project_id"] = "another-project"
        report["identity"]["source_manifest_sha256"] = "c" * 64
        report["ownership"]["ports"] = {}
        failures = MODULE.evaluate_report(self.config("verify-existing"), report)
        self.assertIn("project_identity_mismatch", failures)
        self.assertIn("requested_port_not_owned", failures)
        self.assertIn("source_baseline_unverified", failures)

    def test_verify_existing_accepts_immutable_package_manifest(self) -> None:
        report = MODULE.mock_report(existing=True)
        report["project"]["is_git"] = False
        report["identity"]["source_manifest_path"] = \
            "/srv/codex/example/releases/abc/source-manifest.json"
        report["identity"]["source_manifest_sha256"] = "c" * 64
        report["deployment_source_manifest"] = {
            "exists": True,
            "valid_json": True,
            "sha256": "c" * 64,
            "git_head": "1" * 40,
            "git_branch": "dev",
            "content_digest": "sha256:" + "d" * 64,
            "dirty_digest": None,
        }
        self.assertEqual(
            MODULE.evaluate_report(self.config("verify-existing"), report), []
        )

    def test_verify_existing_rejects_missing_or_null_source_identity(self) -> None:
        report = MODULE.mock_report(existing=True)
        report["project"]["is_git"] = False
        report["identity"]["project_id"] = None
        report["identity"]["source_manifest_sha256"] = None
        report["deployment_source_manifest"] = {
            "exists": False, "valid_json": False, "sha256": None,
            "git_head": None, "git_branch": None,
            "content_digest": None, "dirty_digest": None,
        }
        failures = MODULE.evaluate_report(self.config("verify-existing"), report)
        self.assertIn("identity_fields_missing", failures)
        self.assertIn("source_baseline_unverified", failures)

    def test_dev_accepts_exact_controller_owned_tailscale_relay(self) -> None:
        config = self.config("verify-existing")
        config.update({
            "stack_kind": "dev",
            "project_id": "example-dev",
            "relay_ports": [55321, 55322],
            "tailscale_ip": "100.80.1.2",
            "relays": [
                {"port": 55321, "unit": "example-dev-api-relay.service",
                 "manifest": "/run/dautia-local-stacks/example-dev-api-relay.json"},
                {"port": 55322, "unit": "example-dev-db-relay.service",
                 "manifest": "/run/dautia-local-stacks/example-dev-db-relay.json"},
            ],
        })
        report = MODULE.mock_report(existing=True)
        report["identity"]["project_id"] = "example-dev"
        report["tailscale"] = {"ipv4": ["100.80.1.2"]}
        report["ports"]["listening"].extend([55321, 55322])
        report["ports"]["bindings"] = {
            "15432": ["127.0.0.1"],
            "55321": ["100.80.1.2", "127.0.0.1"],
            "55322": ["100.80.1.2", "127.0.0.1"],
        }
        report["relays"] = [{
            "port": port,
            "manifest": {
                "exists": True, "valid_json": True, "root_owned": True,
                "safe_mode": True, "project_id": "example-dev",
                "unit": f"example-dev-{kind}-relay.service",
                "pid": pid, "bind_ipv4": "100.80.1.2", "ports": [port],
            },
            "unit": {
                "unit": f"example-dev-{kind}-relay.service",
                "load_state": "loaded", "active_state": "active",
                "sub_state": "running", "main_pid": pid,
            },
        } for port, kind, pid in ((55321, "api", 412), (55322, "db", 413))]
        self.assertEqual(MODULE.evaluate_report(config, report), [])

    def test_dev_rejects_wildcard_or_docker_owned_relay(self) -> None:
        config = self.config("verify-existing")
        config.update({
            "stack_kind": "dev", "project_id": "example-dev",
            "relay_ports": [55321, 55322], "tailscale_ip": "100.80.1.2",
            "relays": [
                {"port": 55321, "unit": "example-dev-api-relay.service",
                 "manifest": "/run/dautia-local-stacks/example-dev-api-relay.json"},
                {"port": 55322, "unit": "example-dev-db-relay.service",
                 "manifest": "/run/dautia-local-stacks/example-dev-db-relay.json"},
            ],
        })
        report = MODULE.mock_report(existing=True)
        report["identity"]["project_id"] = "example-dev"
        report["tailscale"] = {"ipv4": ["100.80.1.2"]}
        report["ports"]["bindings"] = {
            "15432": ["127.0.0.1"], "55321": ["0.0.0.0"],
            "55322": ["100.80.1.2"],
        }
        report["ownership"]["non_loopback_ports"] = [55322]
        failures = MODULE.evaluate_report(config, report)
        self.assertIn("relay_binding_mismatch", failures)
        self.assertIn("non_loopback_binding", failures)
        self.assertIn("relay_manifest_invalid", failures)

    def test_reset_allowed_defaults_false(self) -> None:
        report = MODULE.mock_report(existing=False)
        config = self.config("prepare-new")
        self.assertEqual(MODULE.evaluate_report(config, report), [])
        config["reset_allowed"] = True
        self.assertIn("reset_allowed_must_initialize_false",
                      MODULE.evaluate_report(config, report))


if __name__ == "__main__":
    unittest.main()
