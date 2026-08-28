#!/usr/bin/env python3
"""Build a sanitized multi-repo workspace lock from workspace.yaml."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    raise SystemExit("PyYAML is required: python3 -m pip install PyYAML") from exc


def git(repo: Path, *args: str) -> tuple[int, str]:
    result = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, check=False)
    return result.returncode, result.stdout.strip()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--status", choices=("draft", "approved"), default="draft")
    args = parser.parse_args()

    try:
        data = yaml.safe_load(args.manifest.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        print(f"ERROR {exc}", file=sys.stderr)
        return 2
    repos = data.get("repositories") if isinstance(data, dict) else None
    if not isinstance(repos, list) or not repos:
        print("ERROR repositories list is required", file=sys.stderr)
        return 2

    locked: dict[str, dict[str, object]] = {}
    any_dirty = False
    for entry in repos:
        if not isinstance(entry, dict) or not entry.get("id") or not entry.get("path"):
            print("ERROR every repository needs id and path", file=sys.stderr)
            return 2
        repo = (args.manifest.parent / str(entry["path"])).resolve()
        if not (repo / ".git").exists():
            print(f"ERROR not a Git repository: {repo}", file=sys.stderr)
            return 2
        _, sha = git(repo, "rev-parse", "HEAD")
        _, branch = git(repo, "branch", "--show-current")
        _, status = git(repo, "status", "--porcelain=v1", "--untracked-files=all")
        dirty = bool(status)
        any_dirty = any_dirty or dirty
        locked[str(entry["id"])] = {
            "path": str(entry["path"]),
            "branch": branch or "DETACHED",
            "sha": sha,
            "dirty": dirty,
        }
    if args.status == "approved" and any_dirty:
        print("ERROR approved lock requires clean repositories", file=sys.stderr)
        return 1
    output = {
        "version": 1,
        "project": data.get("project", {}).get("id", "unknown"),
        "status": args.status,
        "repositories": locked,
    }
    rendered = yaml.safe_dump(output, sort_keys=False, allow_unicode=True)
    if args.output:
        if not args.write:
            print(f"WOULD_WRITE {args.output}")
            print(rendered, end="")
        else:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(rendered, encoding="utf-8")
            print(f"WROTE {args.output}")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
