from pathlib import Path
import unittest


ROOT = Path(__file__).parents[1]


class MandatoryOrchestrationContractTests(unittest.TestCase):
    def test_skill_requires_material_delegation_and_review(self):
        text = (ROOT / "skills/dautia-project-cycle/SKILL.md").read_text()
        self.assertIn("Delegate material work by default", text)
        self.assertIn("independent reviewer", text)
        self.assertIn("dispatch-plan", text)

    def test_agents_contract_requires_qualified_implementation_child(self):
        text = (ROOT / "AGENTS.md").read_text()
        self.assertIn("implementer__PROFILE", text)
        self.assertIn("revisor independiente", text)

    def test_reference_preserves_read_exception_and_visual_gate(self):
        text = (ROOT / "skills/dautia-project-cycle/references/mandatory-orchestration.md").read_text()
        self.assertIn("Read-only discovery and audit remain direct", text)
        self.assertIn("ux_auditor__PROFILE", text)


if __name__ == "__main__":
    unittest.main()
