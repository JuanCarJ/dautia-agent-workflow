#!/usr/bin/env python3
"""Validate a proposed source -> target branch transition from workspace.yaml."""

from __future__ import annotations

import argparse
import fnmatch
import sys
from pathlib import Path

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    raise SystemExit("PyYAML is required: python3 -m pip install PyYAML") from exc


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("repo_id")
    parser.add_argument("source")
    parser.add_argument("target")
    args = parser.parse_args()
    try:
        data = yaml.safe_load(args.manifest.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        print(f"ERROR {exc}", file=sys.stderr)
        return 2
    repos = data.get("repositories", []) if isinstance(data, dict) else []
    repo = next((item for item in repos if isinstance(item, dict) and item.get("id") == args.repo_id), None)
    if repo is None:
        print(f"ERROR unknown repository id: {args.repo_id}", file=sys.stderr)
        return 2
    flows = repo.get("allowed_flows", [])
    for flow in flows:
        if not isinstance(flow, str) or "->" not in flow:
            continue
        source_pattern, target_pattern = (part.strip() for part in flow.split("->", 1))
        if fnmatch.fnmatchcase(args.source, source_pattern) and fnmatch.fnmatchcase(args.target, target_pattern):
            print(f"OK repo={args.repo_id} flow={args.source}->{args.target}")
            return 0
    print(f"ERROR disallowed flow for {args.repo_id}: {args.source} -> {args.target}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
