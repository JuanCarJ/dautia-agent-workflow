#!/usr/bin/env python3
"""Bounded skill metadata inventory. Discovery never means loaded or understood."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import re
from workflow_core import ContractError


def frontmatter(text: str) -> tuple[dict, str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise ContractError("missing_frontmatter")
    try:
        end = next(i for i in range(1, len(lines)) if lines[i].strip() == "---")
    except StopIteration as exc:
        raise ContractError("unterminated_frontmatter") from exc
    fields, i = {}, 1
    while i < end:
        line = lines[i]
        match = re.match(r"^([A-Za-z_][\w-]*):\s*(.*?)\s*$", line)
        if not match:
            i += 1
            continue
        key, val = match.groups()
        if key in fields:
            raise ContractError("duplicate_frontmatter_key")
        if val in (">", ">-", "|", "|-"):
            fragments = []
            i += 1
            while i < end and (not lines[i].strip() or lines[i][0].isspace()):
                fragments.append(lines[i].strip())
                i += 1
            fields[key] = (" " if val.startswith(">") else "\n").join(fragments).strip()
            continue
        if val.startswith('"'):
            try:
                value = json.loads(val)
            except ValueError as exc:
                raise ContractError("unsupported_quoted_frontmatter") from exc
        elif val.startswith("'") and val.endswith("'"):
            value = val[1:-1].replace("''", "'")
        elif val.startswith(("[", "{")):
            try:
                value = json.loads(val)
            except ValueError:
                # Nested metadata is left to its actual YAML consumer. Never eval it.
                value = None
        elif val.startswith(("!", "&", "*")):
            value = None
        else:
            value = val
        fields[key] = value
        i += 1
    return fields, "\n".join(lines[end + 1:]).strip() + "\n"


def inventory(roots: list[Path], max_skills: int = 500) -> dict:
    entries, warnings = [], []
    for root_index, root in enumerate(roots):
        if not root.is_dir() or root.is_symlink():
            warnings.append("unavailable_root")
            continue
        for skill in sorted(root.iterdir()):
            if len(entries) >= max_skills:
                warnings.append("inventory_truncated")
                break
            file = skill / "SKILL.md"
            if skill.is_symlink() or file.is_symlink() or not file.is_file():
                continue
            if file.stat().st_size > 256_000:
                warnings.append("skill_too_large")
                continue
            data = file.read_bytes()
            try:
                fields, _ = frontmatter(data.decode("utf-8"))
                name = fields.get("name")
                description = fields.get("description")
                if not isinstance(name, str) or not isinstance(description, str) or not description or description == "---":
                    raise ContractError("skill_metadata_incomplete")
                entry = {"name": name, "description": description,
                         "source_root": root_index, "relative_path": skill.name + "/SKILL.md",
                         "sha256": hashlib.sha256(data).hexdigest(), "state": "discoverable",
                         "loaded": None, "used": None}
                for key in ('origin', 'version', 'triggers', 'exclusions', 'tools', 'permissions', 'outputs'):
                    if key in fields and fields[key] is not None:
                        entry[key] = fields[key]
                entries.append(entry)
            except (ContractError, UnicodeError):
                warnings.append("invalid_skill_metadata")
    names = [x["name"] for x in entries]
    collisions = sorted({name for name in names if names.count(name) > 1})
    return {"schema_version": 1, "skills": entries, "collisions": collisions,
            "warnings": sorted(set(warnings)), "automatic_deletion": False}
