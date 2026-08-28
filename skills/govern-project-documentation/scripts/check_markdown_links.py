#!/usr/bin/env python3
"""Check local Markdown links without fetching network resources."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from urllib.parse import unquote


SKIP_DIRS = {".git", "node_modules", "dist", "build", ".next", ".vercel", "coverage"}
LINK_RE = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")


def markdown_files(root: Path) -> list[Path]:
    return sorted(
        path for path in root.rglob("*.md")
        if not any(part in SKIP_DIRS for part in path.relative_to(root).parts)
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("--allow-absolute", action="store_true")
    args = parser.parse_args()
    root = args.root.expanduser().resolve()
    if not root.exists():
        print(f"ERROR root does not exist: {root}", file=sys.stderr)
        return 2

    errors: list[str] = []
    checked = 0
    for document in markdown_files(root):
        text = document.read_text(encoding="utf-8", errors="replace")
        for raw in LINK_RE.findall(text):
            link = raw.strip().strip("<>").split(maxsplit=1)[0]
            if not link or link.startswith(("http://", "https://", "mailto:", "#", "data:")):
                continue
            path_part = unquote(link.split("#", 1)[0])
            if not path_part:
                continue
            target = Path(path_part)
            if target.is_absolute():
                if not args.allow_absolute:
                    errors.append(f"{document}: machine-local absolute link: {link}")
                    continue
            else:
                target = (document.parent / target).resolve()
            checked += 1
            if not target.exists():
                errors.append(f"{document}: missing target: {link}")
    if errors:
        for error in errors:
            print(f"ERROR {error}", file=sys.stderr)
        return 1
    print(f"OK markdown_files={len(markdown_files(root))} local_links={checked}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
