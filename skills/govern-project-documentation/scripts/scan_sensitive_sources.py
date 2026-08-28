#!/usr/bin/env python3
"""Report sensitive-looking files that are not ignored. Never reads file content."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


SKIP_DIRS = {".git", "node_modules", "dist", "build", ".next", ".vercel", "coverage"}
SENSITIVE_NAMES = {".env", "storage-state.json", "secrets.json", "credentials.json"}
SENSITIVE_SUFFIXES = {".pem", ".key", ".p12", ".dump", ".sql.gz"}


def looks_sensitive(path: Path, root: Path) -> bool:
    relative = path.relative_to(root)
    name = path.name.lower()
    if name in SENSITIVE_NAMES or any(name.endswith(suffix) for suffix in SENSITIVE_SUFFIXES):
        return True
    parts = {part.lower() for part in relative.parts}
    return "docs" in parts and "in" in parts and path.suffix.lower() in {".pdf", ".xlsx", ".xls", ".csv"}


def ignored(root: Path, path: Path) -> bool:
    result = subprocess.run(["git", "-C", str(root), "check-ignore", "-q", str(path)], check=False)
    return result.returncode == 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    args = parser.parse_args()
    root = args.root.expanduser().resolve()
    if not (root / ".git").exists():
        print(f"ERROR not a Git repository: {root}", file=sys.stderr)
        return 2
    findings: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_file() or any(part in SKIP_DIRS for part in path.relative_to(root).parts):
            continue
        if looks_sensitive(path, root) and not ignored(root, path):
            findings.append(path.relative_to(root))
    if findings:
        for finding in sorted(findings):
            print(f"ERROR sensitive-unignored {finding}", file=sys.stderr)
        return 1
    print("OK sensitive-unignored=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
