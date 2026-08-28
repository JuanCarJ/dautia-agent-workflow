#!/usr/bin/env python3
"""Read-only host diagnosis for a DautIA workflow profile."""

from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import stat
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def is_wsl() -> bool:
    try:
        release = Path("/proc/sys/kernel/osrelease").read_text(encoding="utf-8").lower()
    except OSError:
        return False
    return "microsoft" in release or "wsl" in release


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", choices=("codex-macos", "wsl-shared"), required=True)
    args = parser.parse_args()
    profile = json.loads((ROOT / "profiles" / f"{args.profile}.yaml").read_text(encoding="utf-8"))
    failures: list[str] = []
    warnings: list[str] = []

    actual_platform = "darwin" if platform.system() == "Darwin" else "linux-wsl" if is_wsl() else platform.system().lower()
    if actual_platform != profile["platform"]:
        failures.append(f"platform expected={profile['platform']} actual={actual_platform}")

    for command in ("git", "python3", "ssh"):
        if not shutil.which(command):
            failures.append(f"missing command: {command}")
    for command in ("gh", "node", "npm", "supabase"):
        if not shutil.which(command):
            warnings.append(f"optional until a project needs it: {command}")

    credential = Path.home() / ".config" / "dautia" / "supabase-db-credentials.json"
    if credential.exists():
        mode = stat.S_IMODE(credential.stat().st_mode)
        if mode != 0o600:
            failures.append(f"credential registry permissions={oct(mode)} expected=0o600")
    else:
        warnings.append("Supabase DB registry not bootstrapped on this host")

    install = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "install.py"), "--profile", args.profile, "--check"],
        text=True,
        capture_output=True,
        check=False,
    )
    if install.returncode:
        failures.append(install.stdout.strip() or "workflow installation differs")

    print(f"profile={args.profile}")
    print(f"platform={actual_platform}")
    print(f"workflow={'ok' if install.returncode == 0 else 'drift'}")
    for warning in warnings:
        print(f"WARN: {warning}")
    for failure in failures:
        print(f"FAIL: {failure}")
    return 2 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
