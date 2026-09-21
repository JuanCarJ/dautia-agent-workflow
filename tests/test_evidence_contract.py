import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills/dautia-project-cycle/scripts/evidence_contract.py"
SPEC = importlib.util.spec_from_file_location("evidence_contract", SCRIPT)
assert SPEC and SPEC.loader
evidence_contract = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(evidence_contract)


def evidence(**overrides):
    value = {
        "evidence_id": "obs-001",
        "objective_id": "obj-001",
        "project_id": "scratch-app",
        "stage": "audit",
        "source_kind": "simulator",
        "source_ref": "sim-run-001",
        "observed_at": "2026-09-21T15:00:00Z",
        "observation": "La pantalla conserva el estado al volver de background.",
        "status": "observed",
        "strength": "E3",
    }
    value.update(overrides)
    return value


class EvidenceContractTests(unittest.TestCase):
    def test_normalizes_and_keeps_hashes(self):
        result = evidence_contract.validate_evidence(
            evidence(stage=" AUDIT ", status=" observed ", candidate_sha="a" * 40)
        )
        self.assertTrue(result["valid"], result)
        self.assertEqual(result["record"]["stage"], "audit")
        self.assertEqual(result["record"]["strength"], "E3")
        self.assertEqual(result["record"]["candidate_sha"], "a" * 40)

    def test_accepts_legacy_id_alias(self):
        value = evidence()
        value.pop("evidence_id")
        value["id"] = "obs-legacy"
        result = evidence_contract.validate_evidence(value)
        self.assertTrue(result["valid"], result)
        self.assertEqual(result["record"]["evidence_id"], "obs-legacy")

    def test_unknown_and_in_progress_are_valid_warnings(self):
        result = evidence_contract.validate_evidence(
            evidence(
                source_kind="unknown",
                source_ref="unknown",
                observed_at="unknown",
                observation="unknown",
                status="in progress",
                strength="unknown",
            )
        )
        self.assertTrue(result["valid"], result)
        self.assertIn("evidence_state_incomplete", result["warnings"])
        self.assertIn("evidence_source_incomplete", result["warnings"])
        self.assertIn("evidence_strength_unknown", result["warnings"])

    def test_missing_field_and_secret_are_rejected(self):
        missing = evidence_contract.validate_evidence({"project_id": "p"})
        self.assertFalse(missing["valid"])
        secret = evidence_contract.validate_evidence(evidence(observation="Bearer sk-secret-value"))
        self.assertFalse(secret["valid"])

    def test_scratch_context_is_valid_but_warns(self):
        result = evidence_contract.validate_project_context({
            "project_id": "scratch-app",
            "documentation_status": "scratch",
            "repositories": [{"name": "app", "path": "unknown", "integration_branch": "unknown"}],
        })
        self.assertTrue(result["valid"], result)
        self.assertIn("context_incomplete", result["warnings"])
        self.assertIn("context_components_missing", result["warnings"])
        self.assertEqual(result["context"]["documentation_status"], "scratch")

    def test_context_requires_project_id_but_not_all_sections(self):
        result = evidence_contract.validate_project_context({"documentation_status": "in_progress"})
        self.assertFalse(result["valid"])
        self.assertIn("project_id_required", result["errors"])

    def test_cli_accepts_stdin_and_reports_json(self):
        process = subprocess.run(
            [sys.executable, str(SCRIPT), "evidence", "-"],
            input=json.dumps(evidence(status="in_progress")),
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(process.returncode, 0, process.stderr)
        parsed = json.loads(process.stdout)
        self.assertTrue(parsed["valid"])
        self.assertIn("evidence_state_incomplete", parsed["warnings"])


if __name__ == "__main__":
    unittest.main()
