from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest


SCRIPT = Path(__file__).parents[1] / "scripts" / "dautia_terminal_guard.py"
SPEC = importlib.util.spec_from_file_location("terminal_guard", SCRIPT)
guard = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(guard)


def dependency(state="running", monitor=True, sha="abc123", environment="staging"):
    result = {
        "required": True,
        "provider": "github",
        "run_id": "run-123",
        "sha": sha,
        "environment": environment,
        "state": state,
        "success_condition": "workflow_success",
        "failure_condition": "workflow_failed_or_cancelled",
        "next_action": "verify_target",
    }
    if monitor:
        result.update({
            "monitor_id": "heartbeat-123",
            "monitor_confirmed": True,
            "monitor_kind": "heartbeat",
            "monitor_target_thread_id": "root-thread-123",
            "next_check_at": "2026-07-11T16:00:00Z",
        })
    return result


def ledger(objective, state="running", monitor=True):
    return {
        "runtime_state": "running",
        "objective_state": objective,
        "root_thread_id": "root-thread-123",
        "target": {"sha": "abc123", "environment": "staging"},
        "dependencies": [dependency(state, monitor)],
        "verification_complete": False,
    }


class TerminalGuardTests(unittest.TestCase):
    def test_waiting_external_requires_confirmed_monitor(self):
        self.assertEqual(guard.validate(ledger("WAITING_EXTERNAL")), [])
        self.assertIn("active_dependency_0_missing_monitor_id", guard.validate(ledger("WAITING_EXTERNAL", monitor=False)))

    def test_waiting_external_rejects_unconfirmed_or_wrong_thread_monitor(self):
        value = ledger("WAITING_EXTERNAL")
        value["dependencies"][0]["monitor_confirmed"] = False
        self.assertIn("active_dependency_0_monitor_not_confirmed", guard.validate(value))
        value = ledger("WAITING_EXTERNAL")
        value["dependencies"][0]["monitor_target_thread_id"] = "other-thread"
        self.assertIn("active_dependency_0_monitor_thread_mismatch", guard.validate(value))

    def test_templo_runtime_complete_does_not_complete_running_e2e(self):
        value = ledger("COMPLETE")
        value["runtime_state"] = "task_complete"
        errors = guard.validate(value)
        self.assertIn("complete_has_active_dependency", errors)
        self.assertIn("complete_requires_final_verification", errors)

    def test_success_transitions_to_verifying(self):
        self.assertEqual(guard.validate(ledger("VERIFYING", state="success", monitor=False)), [])

    def test_complete_requires_success_and_final_verification(self):
        value = ledger("COMPLETE", state="success", monitor=False)
        value["verification_complete"] = True
        self.assertEqual(guard.validate(value), [])

    def test_failed_external_dependency_rejects_complete(self):
        errors = guard.validate(ledger("COMPLETE", state="failed", monitor=False))
        self.assertIn("complete_has_failed_or_unknown_dependency", errors)

    def test_target_identity_must_match(self):
        value = ledger("VERIFYING", state="success", monitor=False)
        value["dependencies"][0]["sha"] = "stale"
        value["dependencies"][0]["environment"] = "dev"
        errors = guard.validate(value)
        self.assertIn("dependency_0_sha_mismatch", errors)
        self.assertIn("dependency_0_environment_mismatch", errors)

    def test_monitor_transfer_failure_is_failed_reason(self):
        value = ledger("FAILED", monitor=False)
        value["reason_code"] = "monitor_transfer_failed"
        self.assertEqual(guard.validate(value), [])

    def test_goal_blocked_threshold_is_enforced(self):
        value = ledger("BLOCKED", monitor=False)
        value.update({"reason_code": "missing_authority", "goal_runtime_active": True, "goal_blocked_threshold_satisfied": False})
        self.assertIn("blocked_goal_threshold_not_satisfied", guard.validate(value))

    def test_blocked_requires_explicit_goal_runtime_state(self):
        value = ledger("BLOCKED", monitor=False)
        value["reason_code"] = "missing_authority"
        self.assertIn("blocked_requires_explicit_goal_runtime_state", guard.validate(value))
        value["goal_runtime_active"] = False
        self.assertNotIn("blocked_requires_explicit_goal_runtime_state", guard.validate(value))

    def test_required_dependency_needs_operational_conditions(self):
        value = ledger("VERIFYING", state="success", monitor=False)
        del value["dependencies"][0]["success_condition"]
        self.assertIn("dependency_0_missing_success_condition", guard.validate(value))

    def test_local_complete_needs_no_fake_target(self):
        value = {
            "runtime_state": "task_complete",
            "objective_state": "COMPLETE",
            "dependencies": [],
            "verification_complete": True,
        }
        self.assertEqual(guard.validate(value), [])


if __name__ == "__main__":
    unittest.main()
