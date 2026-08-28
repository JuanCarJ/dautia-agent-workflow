#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("check_checkout.py")


def git(repo: Path, *args: str) -> str:
    result = subprocess.run(["git", *args], cwd=repo, text=True, capture_output=True, check=True)
    return result.stdout.strip()


def fixture() -> tuple[tempfile.TemporaryDirectory[str], Path, Path]:
    temp = tempfile.TemporaryDirectory()
    root = Path(temp.name)
    bare = root / "remote.git"
    repo = root / "product"
    subprocess.run(["git", "init", "--bare", str(bare)], check=True, capture_output=True)
    subprocess.run(["git", "clone", str(bare), str(repo)], check=True, capture_output=True)
    git(repo, "config", "user.email", "test@example.com")
    git(repo, "config", "user.name", "Test")
    git(repo, "switch", "-c", "dev")
    (repo / "README.md").write_text("ok\n", encoding="utf-8")
    git(repo, "add", "README.md")
    git(repo, "commit", "-m", "initial")
    git(repo, "push", "-u", "origin", "dev")
    contract = {
        "schema_version": 2,
        "project": "test",
        "product_topology": "single-codebase",
        "repository_layout": "single-repo",
        "configuration_status": "active",
        "production_enabled": False,
        "repositories": [{"id": "product", "path": "product", "integration_branch": "dev"}],
    }
    contract_path = root / "delivery.yaml"
    contract_path.write_text(json.dumps(contract), encoding="utf-8")
    return temp, root, contract_path


def check(root: Path, contract: Path, mode: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["python3", str(SCRIPT), str(contract), "--repo", str(root), "--mode", mode, "--json"],
        text=True,
        capture_output=True,
        check=False,
    )


class CheckoutTests(unittest.TestCase):
    def test_clean_integration_closeout_is_ready(self) -> None:
        temp, root, contract = fixture()
        with temp:
            result = check(root, contract, "closeout")
            self.assertEqual(0, result.returncode)
            self.assertEqual("READY", json.loads(result.stdout)[0]["verdict"])

    def test_closeout_rejects_dirty_checkout(self) -> None:
        temp, root, contract = fixture()
        with temp:
            (root / "product" / "README.md").write_text("dirty\n", encoding="utf-8")
            result = check(root, contract, "closeout")
            self.assertEqual(1, result.returncode)
            self.assertIn("entradas sin integrar", result.stdout)

    def test_start_accepts_clean_feature_based_on_integration(self) -> None:
        temp, root, contract = fixture()
        with temp:
            git(root / "product", "switch", "-c", "feature/test")
            result = check(root, contract, "start")
            self.assertEqual(0, result.returncode)
            self.assertIn("rama corta basada", result.stdout)

    def test_closeout_rejects_feature_branch(self) -> None:
        temp, root, contract = fixture()
        with temp:
            git(root / "product", "switch", "-c", "feature/test")
            result = check(root, contract, "closeout")
            self.assertEqual(1, result.returncode)
            self.assertIn("no en dev", result.stdout)


if __name__ == "__main__":
    unittest.main()
