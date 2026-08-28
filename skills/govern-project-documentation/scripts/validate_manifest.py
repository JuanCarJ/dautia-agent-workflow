#!/usr/bin/env python3
"""Validate workspace or document-first initiative YAML manifests."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:  # pragma: no cover - environment guard
    raise SystemExit("PyYAML is required: python3 -m pip install PyYAML") from exc


LIFECYCLES = {
    "operational",
    "discovery",
    "design",
    "approved",
    "implementation",
    "staging",
    "production",
    "superseded",
    "cancelled",
    "blocked",
}
TOPOLOGIES = {"single-repo", "monorepo", "multi-repo"}


def load_yaml(path: Path) -> dict[str, Any]:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise ValueError(f"cannot read valid YAML: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError("manifest root must be a mapping")
    return data


def validate_workspace(data: dict[str, Any], path: Path, check_paths: bool) -> list[str]:
    errors: list[str] = []
    project = data.get("project")
    if not isinstance(project, dict):
        return ["project: mapping is required"]
    if not project.get("id"):
        errors.append("project.id: value is required")
    if project.get("topology") not in TOPOLOGIES:
        errors.append(f"project.topology: expected one of {sorted(TOPOLOGIES)}")

    repos = data.get("repositories")
    if not isinstance(repos, list) or not repos:
        return errors + ["repositories: non-empty list is required"]

    seen: set[str] = set()
    base = path.parent
    for index, repo in enumerate(repos):
        prefix = f"repositories[{index}]"
        if not isinstance(repo, dict):
            errors.append(f"{prefix}: mapping is required")
            continue
        repo_id = repo.get("id")
        if not isinstance(repo_id, str) or not repo_id.strip():
            errors.append(f"{prefix}.id: non-empty string is required")
        elif repo_id in seen:
            errors.append(f"{prefix}.id: duplicate id {repo_id!r}")
        else:
            seen.add(repo_id)
        for key in ("path", "role", "base_branch"):
            if not isinstance(repo.get(key), str) or not repo[key].strip():
                errors.append(f"{prefix}.{key}: non-empty string is required")
        flows = repo.get("allowed_flows", [])
        if not isinstance(flows, list) or any(not isinstance(v, str) for v in flows):
            errors.append(f"{prefix}.allowed_flows: list of strings is required")
        if check_paths and isinstance(repo.get("path"), str):
            target = (base / repo["path"]).resolve()
            if not target.exists():
                errors.append(f"{prefix}.path: path does not exist: {target}")

    documentation = data.get("documentation", {})
    if documentation and not isinstance(documentation, dict):
        errors.append("documentation: mapping is required")
    return errors


def validate_initiative(data: dict[str, Any], path: Path, check_paths: bool) -> list[str]:
    errors: list[str] = []
    for key in ("id", "name", "authority"):
        if not isinstance(data.get(key), str) or not data[key].strip():
            errors.append(f"{key}: non-empty string is required")
    lifecycle = data.get("lifecycle")
    if lifecycle not in LIFECYCLES:
        errors.append(f"lifecycle: expected one of {sorted(LIFECYCLES)}")
    canonical = data.get("canonical")
    if not isinstance(canonical, dict) or not canonical:
        errors.append("canonical: non-empty mapping is required")
    elif check_paths:
        for key, value in canonical.items():
            if isinstance(value, str) and value:
                target = (path.parent / value).resolve()
                if not target.exists():
                    errors.append(f"canonical.{key}: path does not exist: {target}")
    gate = data.get("implementation_entry_gate")
    if not isinstance(gate, dict):
        errors.append("implementation_entry_gate: mapping is required")
    else:
        if not isinstance(gate.get("approved"), bool):
            errors.append("implementation_entry_gate.approved: boolean is required")
        criteria = gate.get("criteria")
        if not isinstance(criteria, list) or not criteria:
            errors.append("implementation_entry_gate.criteria: non-empty list is required")
    if lifecycle == "design" and isinstance(gate, dict) and gate.get("approved") is True:
        errors.append("lifecycle design cannot have an approved implementation entry gate")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--kind", choices=("auto", "workspace", "initiative"), default="auto")
    parser.add_argument("--check-paths", action="store_true")
    args = parser.parse_args()

    try:
        data = load_yaml(args.manifest)
    except ValueError as exc:
        print(f"ERROR {args.manifest}: {exc}", file=sys.stderr)
        return 2

    kind = args.kind
    if kind == "auto":
        kind = "workspace" if "project" in data or "repositories" in data else "initiative"
    errors = (
        validate_workspace(data, args.manifest, args.check_paths)
        if kind == "workspace"
        else validate_initiative(data, args.manifest, args.check_paths)
    )
    if errors:
        for error in errors:
            print(f"ERROR {args.manifest}: {error}", file=sys.stderr)
        return 1
    print(f"OK kind={kind} manifest={args.manifest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
