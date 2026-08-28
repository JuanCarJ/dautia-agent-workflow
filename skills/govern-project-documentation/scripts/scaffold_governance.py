#!/usr/bin/env python3
"""Dry-run-first scaffolder for governance, repository, and initiative contracts."""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parent.parent
TEMPLATES = SKILL_ROOT / "assets" / "templates"


def git_root(path: Path) -> Path | None:
    result = subprocess.run(
        ["git", "-C", str(path), "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
        check=False,
    )
    return Path(result.stdout.strip()).resolve() if result.returncode == 0 else None


def render(text: str, replacements: dict[str, str]) -> str:
    for source, target in replacements.items():
        text = text.replace(source, target)
    return text


def collect(source: Path, destination: Path, replacements: dict[str, str]) -> list[tuple[Path, Path]]:
    files: list[tuple[Path, Path]] = []
    for item in source.rglob("*"):
        if item.is_symlink():
            raise ValueError(f"template symlink is not allowed: {item}")
        if not item.is_file():
            continue
        relative = Path(render(item.relative_to(source).as_posix(), replacements))
        files.append((item, destination / relative))
    return files


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("governance", "repository", "initiative"))
    parser.add_argument("destination", type=Path)
    parser.add_argument("--project", default="Project Name")
    parser.add_argument("--repo", default="Repository Name")
    parser.add_argument("--role", default="repository-role")
    parser.add_argument("--initiative-id", default="INIT-ID")
    parser.add_argument("--initiative-name", default="Initiative Name")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--allow-non-git", action="store_true")
    args = parser.parse_args()

    raw_destination = args.destination.expanduser().absolute()
    if raw_destination.is_symlink():
        print("ERROR destination cannot be a symlink", file=sys.stderr)
        return 2
    if args.mode == "initiative" and not re.fullmatch(r"[A-Z0-9][A-Z0-9-]{1,63}", args.initiative_id):
        print("ERROR initiative id must use uppercase letters, digits, and hyphens", file=sys.stderr)
        return 2
    destination = raw_destination.resolve()
    destination.mkdir(parents=True, exist_ok=True) if args.write else None
    existing_parent = destination if destination.exists() else destination.parent
    if not args.allow_non_git and git_root(existing_parent) is None:
        print("ERROR destination is not inside a Git repository; use --allow-non-git explicitly", file=sys.stderr)
        return 2
    replacements = {
        "[PROJECT_NAME]": args.project,
        "[REPO_NAME]": args.repo,
        "[ROLE]": args.role,
        "INIT-ID": args.initiative_id,
        "Initiative Name": args.initiative_name,
    }
    if args.mode == "initiative":
        source = TEMPLATES / "governance" / "docs" / "initiatives" / "INIT-ID"
        target = destination / "docs" / "initiatives" / args.initiative_id
    else:
        source = TEMPLATES / args.mode
        target = destination
    try:
        files = collect(source, target, replacements)
    except ValueError as exc:
        print(f"ERROR {exc}", file=sys.stderr)
        return 2
    conflicts = [target_file for _, target_file in files if target_file.exists()]
    if conflicts and not args.force:
        for conflict in conflicts:
            print(f"CONFLICT {conflict}", file=sys.stderr)
        return 1
    for source_file, target_file in files:
        action = "OVERWRITE" if target_file.exists() else "CREATE"
        print(f"{action} {target_file}")
        if not args.write:
            continue
        target_file.parent.mkdir(parents=True, exist_ok=True)
        content = render(source_file.read_text(encoding="utf-8"), replacements)
        target_file.write_text(content, encoding="utf-8")
        shutil.copymode(source_file, target_file)
    print("mode=write" if args.write else "mode=dry-run")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
