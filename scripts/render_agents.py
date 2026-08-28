#!/usr/bin/env python3
"""Render Codex and Cursor agent adapters from model-neutral role files."""

from __future__ import annotations

import argparse
import json
import tempfile
import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ROLE_DIR = ROOT / "roles"
CODEX_DIR = ROOT / "adapters" / "codex" / "agents"
CURSOR_DIR = ROOT / "adapters" / "cursor" / "agents"
PROFILE = ROOT / "profiles" / "codex-macos.yaml"

READ_ONLY = {
    "code_explorer",
    "decision_gate",
    "documental",
    "independent_reviewer",
    "product_discovery",
    "qa_android",
    "qa_e2e",
    "qa_ios",
    "qa_web",
    "ux_auditor",
}


def neutralize(body: str) -> str:
    return (
        body.strip()
        .replace("Return to root", "Return to the parent orchestrator")
        .replace("Never spawn agents or delegate", "Never delegate")
    )


def bootstrap_roles() -> None:
    ROLE_DIR.mkdir(parents=True, exist_ok=True)
    for source in sorted(CODEX_DIR.glob("*.toml")):
        target = ROLE_DIR / f"{source.stem}.md"
        if target.exists():
            continue
        data = tomllib.loads(source.read_text(encoding="utf-8"))
        metadata = {
            "id": data["name"],
            "description": data["description"],
            "mutability": "read_only" if data["name"] in READ_ONLY else "bounded_write",
        }
        frontmatter = "\n".join(f"{key}: {json.dumps(value)}" for key, value in metadata.items())
        target.write_text(
            f"---\n{frontmatter}\n---\n{neutralize(data['developer_instructions'])}\n",
            encoding="utf-8",
        )


def read_role(path: Path) -> tuple[dict[str, str], str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    if len(lines) < 5 or lines[0] != "---":
        raise ValueError(f"Frontmatter invalido: {path}")
    end = lines.index("---", 1)
    metadata: dict[str, str] = {}
    for line in lines[1:end]:
        key, raw = line.split(":", 1)
        metadata[key.strip()] = json.loads(raw.strip())
    required = {"id", "description", "mutability"}
    if required - metadata.keys():
        raise ValueError(f"Faltan campos en {path}: {sorted(required - metadata.keys())}")
    body = "\n".join(lines[end + 1 :]).strip() + "\n"
    return metadata, body


def render_to(base: Path) -> None:
    profile = json.loads(PROFILE.read_text(encoding="utf-8"))
    model_map = profile["codex_agents"]
    codex_out = base / "codex"
    cursor_out = base / "cursor"
    codex_out.mkdir(parents=True, exist_ok=True)
    cursor_out.mkdir(parents=True, exist_ok=True)

    role_ids: set[str] = set()
    for role_path in sorted(ROLE_DIR.glob("*.md")):
        metadata, body = read_role(role_path)
        role_id = metadata["id"]
        role_ids.add(role_id)
        if role_id not in model_map:
            raise ValueError(f"El perfil no mapea el rol {role_id}")
        if '"""' in body:
            raise ValueError(f"El rol {role_id} contiene triple comilla no portable")
        model, effort = model_map[role_id]
        codex_text = (
            f"name = {json.dumps(role_id)}\n"
            f"description = {json.dumps(metadata['description'])}\n"
            f"model = {json.dumps(model)}\n"
            f"model_reasoning_effort = {json.dumps(effort)}\n"
            f"developer_instructions = \"\"\"\n{body}\"\"\"\n"
        )
        (codex_out / f"{role_id}.toml").write_text(codex_text, encoding="utf-8")

        cursor_id = role_id.replace("_", "-")
        readonly = metadata["mutability"] == "read_only"
        cursor_text = (
            "---\n"
            f"name: {cursor_id}\n"
            f"description: {json.dumps(metadata['description'])}\n"
            "model: inherit\n"
            f"readonly: {'true' if readonly else 'false'}\n"
            "---\n"
            f"{body}"
        )
        (cursor_out / f"{cursor_id}.md").write_text(cursor_text, encoding="utf-8")

    extra = set(model_map) - role_ids
    if extra:
        raise ValueError(f"El perfil contiene roles sin definicion: {sorted(extra)}")


def compare_dirs(expected: Path, actual: Path) -> list[str]:
    differences: list[str] = []
    expected_files = {p.name: p.read_bytes() for p in expected.iterdir() if p.is_file()}
    actual_files = {p.name: p.read_bytes() for p in actual.iterdir() if p.is_file()}
    for name in sorted(set(expected_files) | set(actual_files)):
        if expected_files.get(name) != actual_files.get(name):
            differences.append(name)
    return differences


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bootstrap", action="store_true")
    parser.add_argument("--render", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if not any((args.bootstrap, args.render, args.check)):
        parser.error("usa --bootstrap, --render o --check")
    if args.bootstrap:
        bootstrap_roles()
    if args.render:
        with tempfile.TemporaryDirectory() as raw:
            temp = Path(raw)
            render_to(temp)
            CODEX_DIR.mkdir(parents=True, exist_ok=True)
            CURSOR_DIR.mkdir(parents=True, exist_ok=True)
            for target_dir, source_dir in ((CODEX_DIR, temp / "codex"), (CURSOR_DIR, temp / "cursor")):
                for old in target_dir.iterdir():
                    if old.is_file():
                        old.unlink()
                for source in source_dir.iterdir():
                    (target_dir / source.name).write_bytes(source.read_bytes())
    if args.check:
        with tempfile.TemporaryDirectory() as raw:
            temp = Path(raw)
            render_to(temp)
            differences = compare_dirs(temp / "codex", CODEX_DIR) + compare_dirs(temp / "cursor", CURSOR_DIR)
        if differences:
            print("Adapters desactualizados: " + ", ".join(sorted(differences)))
            return 2
        print(f"OK: {len(list(ROLE_DIR.glob('*.md')))} roles y ambos adapters sincronizados")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
