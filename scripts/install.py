#!/usr/bin/env python3
"""Install the versioned DautIA workflow without copying secrets."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def digest(path: Path) -> str:
    hasher = hashlib.sha256()
    if path.is_file():
        hasher.update(path.read_bytes())
        return hasher.hexdigest()
    if not path.exists():
        return "missing"
    for item in sorted(p for p in path.rglob("*") if p.is_file()):
        hasher.update(str(item.relative_to(path)).encode())
        hasher.update(item.read_bytes())
    return hasher.hexdigest()


def copy_with_backup(source: Path, target: Path, backup_root: Path) -> bool:
    if digest(source) == digest(target):
        return False
    if target.exists() or target.is_symlink():
        relative = target.as_posix().lstrip("/").replace(":", "_")
        backup = backup_root / relative
        backup.parent.mkdir(parents=True, exist_ok=True)
        if target.is_dir() and not target.is_symlink():
            shutil.copytree(target, backup)
            shutil.rmtree(target)
        else:
            shutil.copy2(target, backup, follow_symlinks=False)
            target.unlink()
    target.parent.mkdir(parents=True, exist_ok=True)
    if source.is_dir():
        shutil.copytree(source, target)
    else:
        shutil.copy2(source, target)
    return True


def managed_pairs(profile: dict) -> list[tuple[Path, Path]]:
    home = Path.home()
    codex_home = Path(os.environ.get("CODEX_HOME", home / ".codex")).expanduser()
    pairs: list[tuple[Path, Path]] = [(ROOT / "AGENTS.md", codex_home / "AGENTS.md")]
    for skill in sorted((ROOT / "skills").iterdir()):
        if (skill / "SKILL.md").is_file():
            pairs.append((skill, codex_home / "skills" / skill.name))
    if "codex" in profile["harnesses"]:
        for agent in sorted((ROOT / "adapters" / "codex" / "agents").glob("*.toml")):
            pairs.append((agent, codex_home / "agents" / agent.name))
    if "cursor" in profile["harnesses"]:
        for agent in sorted((ROOT / "adapters" / "cursor" / "agents").glob("*.md")):
            pairs.append((agent, home / ".cursor" / "agents" / agent.name))
    return pairs


def launcher_text() -> str:
    return """#!/bin/sh
set -eu
codex_root=${CODEX_HOME:-$HOME/.codex}
exec ${PYTHON:-python3} "$codex_root/skills/dautia-ci-cd/scripts/dautia_supabase.py" "$@"
"""


def git_revision() -> str:
    result = subprocess.run(
        ["git", "-C", str(ROOT), "rev-parse", "HEAD"],
        text=True,
        capture_output=True,
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else "uncommitted"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", choices=("codex-macos", "wsl-shared"), required=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    profile = json.loads((ROOT / "profiles" / f"{args.profile}.yaml").read_text(encoding="utf-8"))
    pairs = managed_pairs(profile)
    differences = [(source, target) for source, target in pairs if digest(source) != digest(target)]
    launcher = Path.home() / ".local" / "bin" / "dautia-supabase"
    launcher_differs = not launcher.is_file() or launcher.read_text(encoding="utf-8", errors="replace") != launcher_text()

    if args.check:
        if differences or launcher_differs:
            print(f"PENDING: {len(differences)} assets y launcher={launcher_differs}")
            for source, target in differences[:12]:
                print(f"  {source.relative_to(ROOT)} -> {target}")
            return 2
        print(f"OK: perfil {args.profile} instalado y sincronizado")
        return 0

    timestamp = dt.datetime.now().strftime("%Y%m%dT%H%M%S")
    backup_root = Path.home() / ".config" / "dautia" / "workflow-backups" / timestamp
    changed = 0
    for source, target in pairs:
        changed += int(copy_with_backup(source, target, backup_root))
    launcher.parent.mkdir(parents=True, exist_ok=True)
    if launcher_differs:
        if launcher.exists():
            backup_root.mkdir(parents=True, exist_ok=True)
            shutil.copy2(launcher, backup_root / "dautia-supabase")
        launcher.write_text(launcher_text(), encoding="utf-8")
        launcher.chmod(0o755)
        changed += 1

    state_path = Path.home() / ".config" / "dautia" / "workflow-install.json"
    state_path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    state_path.write_text(
        json.dumps(
            {
                "profile": args.profile,
                "revision": git_revision(),
                "installed_at": dt.datetime.now(dt.timezone.utc).isoformat(),
                "source": str(ROOT),
            },
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )
    state_path.chmod(0o600)
    print(f"OK: perfil {args.profile}; assets actualizados={changed}; backup={backup_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
