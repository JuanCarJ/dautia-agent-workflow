from __future__ import annotations

import sys
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
import workflow_core  # noqa: E402


def packet(*, operation="write_product", mode="IMPLEMENTATION", material=True, runtime=None, role="implementer"):
    return {
        "work": {"operation": operation, "mode": mode, "material": material, "role": role},
        "runtime": runtime or {},
    }


def receipt(agent_type="implementer__sol_medium", model="gpt-6-sol", effort="medium"):
    return {
        "agent_type": agent_type,
        "fork_turns": "none",
        "status": "completed",
        "child_reference": "child-001",
        "evidence": ["terminal-001"],
        "model_observed": model,
        "effort_observed": effort,
    }


class MandatoryOrchestrationTests(unittest.TestCase):
    def test_material_implementation_requires_qualified_target(self):
        issues = workflow_core.dispatch_receipt_issues(packet(), "closeout")
        self.assertIn("mandatory_dispatch_target_missing", issues)
        self.assertEqual(
            workflow_core.mandatory_dispatch_plan_issues(packet(), "preflight"),
            ["mandatory_dispatch_target_missing"],
        )

    def test_material_implementation_requires_terminal_receipt(self):
        issues = workflow_core.dispatch_receipt_issues(
            packet(runtime={"required_agent_type": "implementer__sol_medium", "required_profile": "sol_medium"}),
            "closeout",
        )
        self.assertIn("dispatch_receipt_required", issues)

    def test_material_implementation_rejects_non_writer_target(self):
        target = "code_explorer__luna_high"
        issues = workflow_core.dispatch_receipt_issues(
            packet(
                role="code_explorer",
                runtime={
                    "required_agent_type": target,
                    "required_profile": "luna_high",
                    "dispatch_receipt": receipt(target, "gpt-6-luna", "high"),
                },
            ),
            "closeout",
        )
        self.assertIn("mandatory_implementation_agent_required", issues)

    def test_completed_qualified_implementation_receipt_passes_dispatch_gate(self):
        issues = workflow_core.dispatch_receipt_issues(
            packet(
                runtime={
                    "required_agent_type": "implementer__sol_medium",
                    "required_profile": "sol_medium",
                    "dispatch_receipt": receipt(),
                }
            ),
            "closeout",
        )
        self.assertEqual(issues, [])

    def test_preflight_rejects_analysis_role_for_material_write(self):
        target = "systems_analyst__astra_low"
        issues = workflow_core.mandatory_dispatch_plan_issues(
            packet(
                role="systems_analyst",
                runtime={"required_agent_type": target},
            ),
            "preflight",
        )
        self.assertEqual(issues, ["mandatory_implementation_agent_required"])

    def test_preflight_accepts_qualified_implementation_target(self):
        issues = workflow_core.mandatory_dispatch_plan_issues(
            packet(runtime={"required_agent_type": "implementer__sol_medium", "required_profile": "sol_medium"}),
            "preflight",
        )
        self.assertEqual(issues, [])

    def test_preflight_rejects_unknown_or_mismatched_profile(self):
        self.assertEqual(
            workflow_core.mandatory_dispatch_plan_issues(
                packet(runtime={"required_agent_type": "implementer__made_up", "required_profile": "made_up"}),
                "preflight",
            ),
            ["mandatory_dispatch_profile_invalid"],
        )
        self.assertEqual(
            workflow_core.mandatory_dispatch_plan_issues(
                packet(runtime={"required_agent_type": "implementer__sol_medium", "required_profile": "sol_high"}),
                "preflight",
            ),
            ["mandatory_dispatch_profile_mismatch"],
        )

    def test_trivial_user_exception_remains_direct(self):
        issues = workflow_core.dispatch_receipt_issues(
            packet(
                runtime={
                    "direct_execution_exception": {
                        "scope": "trivial",
                        "source_kind": "user",
                        "source_refs": ["user-request-1"],
                        "reason": "one-line copy correction",
                    }
                }
            ),
            "closeout",
        )
        self.assertEqual(issues, [])

    def test_reads_do_not_require_implementation_delegation(self):
        issues = workflow_core.dispatch_receipt_issues(
            packet(operation="read", mode="AUDIT", material=True), "closeout"
        )
        self.assertEqual(issues, [])


if __name__ == "__main__":
    unittest.main()
