#!/usr/bin/env python3
"""Validate portable workflow structure without accessing credentials."""

from __future__ import annotations

import json
import py_compile
import re
import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEXT_SUFFIXES = {".md", ".py", ".sh", ".toml", ".yaml", ".yml", ".json"}
ABSOLUTE_HOME = re.compile(r"/(?:Users|home)/[^/\s]+|[A-Za-z]:\\\\Users\\\\[^\\\s]+")


def skill_metadata(path: Path) -> tuple[str, str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0] != "---":
        raise ValueError(f"sin frontmatter: {path}")
    end = lines.index("---", 1)
    values: dict[str, str] = {}
    for line in lines[1:end]:
        if ":" in line:
            key, value = line.split(":", 1)
            values[key.strip()] = value.strip().strip('"')
    return values.get("name", ""), values.get("description", "")


def main() -> int:
    errors: list[str] = []
    skills = sorted((ROOT / "skills").glob("*/SKILL.md"))
    for path in skills:
        try:
            name, description = skill_metadata(path)
        except (ValueError, UnicodeError) as exc:
            errors.append(str(exc))
            continue
        if name != path.parent.name:
            errors.append(f"skill name mismatch: {path.parent.name} != {name}")
        if not description:
            errors.append(f"skill without description: {name}")

    for path in ROOT.rglob("*"):
        if (
            not path.is_file()
            or ".git" in path.parts
            or "tests" in path.parts
            or path.suffix.lower() not in TEXT_SUFFIXES
        ):
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeError:
            continue
        match = ABSOLUTE_HOME.search(content)
        if match:
            errors.append(f"absolute user path in {path.relative_to(ROOT)}: {match.group(0)}")

    for profile_path in (ROOT / "profiles").glob("*.yaml"):
        try:
            profile = json.loads(profile_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeError) as exc:
            errors.append(f"invalid profile {profile_path.name}: {exc}")
            continue
        if "pstack" in json.dumps(profile).lower():
            errors.append(f"stable profile depends on pstack: {profile_path.name}")

    role_count = len(list((ROOT / "roles").glob("*.md")))
    codex_agents = list((ROOT / "adapters" / "codex" / "agents").glob("*.toml"))
    cursor_agents = list((ROOT / "adapters" / "cursor" / "agents").glob("*.md"))
    if not role_count or role_count != len(codex_agents) or role_count != len(cursor_agents):
        errors.append(
            f"agent counts roles={role_count} codex={len(codex_agents)} cursor={len(cursor_agents)}"
        )
    for path in codex_agents:
        try:
            tomllib.loads(path.read_text(encoding="utf-8"))
        except (tomllib.TOMLDecodeError, UnicodeError) as exc:
            errors.append(f"invalid TOML {path.name}: {exc}")

    if "Contrato v8" not in (ROOT / "AGENTS.md").read_text(encoding="utf-8"):
        errors.append("AGENTS.md is not contract v8")

    for script in (ROOT / "scripts").glob("*.py"):
        try:
            py_compile.compile(str(script), doraise=True)
        except py_compile.PyCompileError as exc:
            errors.append(str(exc))

    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        return 2
    print(f"OK: portable workflow; skills={len(skills)} roles={role_count} profiles=2")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
