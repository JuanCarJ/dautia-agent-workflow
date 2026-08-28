#!/usr/bin/env python3
"""Validate a Markdown traceability table."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


ALIASES = {
    "requirement": {"requirement", "requisito"},
    "status": {"status", "estado"},
    "repos": {"repos", "repositorios"},
    "commits": {"pr/commits", "pr/commit", "pr", "commits"},
    "tests": {"tests", "pruebas", "test"},
    "environment": {"environment", "ambiente", "entorno"},
    "release": {"release", "versión", "version"},
}
CLOSED = {"closed", "cerrado", "implemented", "implementado", "production", "released", "publicado"}
ID_PATTERN = re.compile(r"^(?:BO|BR|RF|RNF|ADR|INC|BUG|PF|MEJ|TEST|REL|RY-RF|RY-BR|RY-RNF)-[A-Z0-9-]+$")


def clean_cell(value: str) -> str:
    return value.strip().strip("`").strip()


def parse_tables(text: str) -> list[tuple[list[str], list[list[str]]]]:
    lines = text.splitlines()
    tables: list[tuple[list[str], list[list[str]]]] = []
    i = 0
    while i + 1 < len(lines):
        if "|" not in lines[i] or "|" not in lines[i + 1]:
            i += 1
            continue
        separator = [part.strip() for part in lines[i + 1].strip().strip("|").split("|")]
        if not separator or any(not re.fullmatch(r":?-{3,}:?", part) for part in separator):
            i += 1
            continue
        header = [clean_cell(part).lower() for part in lines[i].strip().strip("|").split("|")]
        rows: list[list[str]] = []
        i += 2
        while i < len(lines) and "|" in lines[i] and lines[i].strip():
            row = [clean_cell(part) for part in lines[i].strip().strip("|").split("|")]
            if len(row) == len(header):
                rows.append(row)
            i += 1
        tables.append((header, rows))
    return tables


def resolve_columns(header: list[str]) -> dict[str, int]:
    resolved: dict[str, int] = {}
    for canonical, aliases in ALIASES.items():
        for index, name in enumerate(header):
            if name in aliases:
                resolved[canonical] = index
                break
    return resolved


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("traceability", type=Path)
    args = parser.parse_args()
    try:
        text = args.traceability.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"ERROR {args.traceability}: {exc}", file=sys.stderr)
        return 2

    candidate = None
    for header, rows in parse_tables(text):
        columns = resolve_columns(header)
        if "requirement" in columns and "status" in columns:
            candidate = (header, rows, columns)
            break
    if candidate is None:
        print("ERROR no traceability table with requirement and status columns", file=sys.stderr)
        return 1

    _, rows, columns = candidate
    missing = [name for name in ALIASES if name not in columns]
    errors: list[str] = []
    if missing:
        errors.append(f"missing required columns: {', '.join(missing)}")
    seen: set[str] = set()
    for row_number, row in enumerate(rows, start=1):
        requirement = row[columns["requirement"]]
        status = row[columns["status"]].lower()
        if requirement in {"", "—", "-"}:
            errors.append(f"row {row_number}: requirement is empty")
        elif requirement in seen:
            errors.append(f"row {row_number}: duplicate requirement {requirement}")
        else:
            seen.add(requirement)
        if requirement and requirement not in {"—", "-"} and not ID_PATTERN.fullmatch(requirement):
            errors.append(f"row {row_number}: invalid requirement id {requirement!r}")
        if status in CLOSED and not missing:
            for field in ("repos", "commits", "tests", "environment", "release"):
                value = row[columns[field]]
                if value in {"", "—", "-", "N/A", "n/a"}:
                    errors.append(f"row {row_number}: closed item missing {field}")
    if not rows:
        errors.append("traceability table has no data rows")
    if errors:
        for error in errors:
            print(f"ERROR {args.traceability}: {error}", file=sys.stderr)
        return 1
    print(f"OK rows={len(rows)} traceability={args.traceability}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
