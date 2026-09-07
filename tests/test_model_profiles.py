import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

EXPECTED_AGENTS = {
    "code_explorer": ["gpt-5.6-sol", "medium"],
    "data_security": ["gpt-5.6-sol", "high"],
    "decision_gate": ["gpt-5.6-sol", "high"],
    "documental": ["gpt-5.6-sol", "medium"],
    "implementer": ["gpt-5.6-sol", "medium"],
    "implementer_complex": ["gpt-5.6-sol", "high"],
    "independent_reviewer": ["gpt-5.6-sol", "high"],
    "product_discovery": ["gpt-6-astra", "low"],
    "qa_android": ["gpt-5.6-sol", "high"],
    "qa_e2e": ["gpt-5.6-sol", "high"],
    "qa_ios": ["gpt-5.6-sol", "high"],
    "qa_web": ["gpt-5.6-sol", "high"],
    "release_operator": ["gpt-5.6-sol", "medium"],
    "systems_analyst": ["gpt-6-astra", "medium"],
    "systems_implementer": ["gpt-6-astra", "medium"],
    "ux_auditor": ["gpt-6-astra", "low"],
}


class ModelProfileTests(unittest.TestCase):
    def load_profile(self, name: str) -> dict:
        return json.loads((ROOT / "profiles" / name).read_text(encoding="utf-8"))

    def test_codex_profiles_match_approved_routing(self) -> None:
        for name in ("codex-macos.yaml", "wsl-shared.yaml"):
            with self.subTest(profile=name):
                profile = self.load_profile(name)
                self.assertEqual(
                    profile["codex_root"],
                    {"model": "gpt-5.6-sol", "reasoning_effort": "high"},
                )
                self.assertEqual(profile["codex_agents"], EXPECTED_AGENTS)

    def test_cursor_declares_runtime_inheritance_without_enforcement_claim(self) -> None:
        cursor = self.load_profile("wsl-shared.yaml")["cursor_agents"]
        self.assertEqual(cursor["model"], "inherit")
        self.assertIn("inherits", cursor["policy"])
        self.assertIn("not claimed", cursor["policy"])

    def test_rendered_adapters_are_current(self) -> None:
        result = subprocess.run(
            [sys.executable, "scripts/render_agents.py", "--check"],
            cwd=ROOT,
            text=True,
            capture_output=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
