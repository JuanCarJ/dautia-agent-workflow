from pathlib import Path
import importlib.util
import json
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("workflow_sim", ROOT / "scripts/run_workflow_simulations.py")
sim = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sim)


class RoleGradingTests(unittest.TestCase):
    def setUp(self):
        self.root = {"model":"gpt-5.6-sol","effort":"high","completed":True,"spawn_calls":[{"role":"implementer","fork_turns":"none"}]}
        self.child = {"role":"implementer","model":"gpt-5.6-sol","effort":"medium","completed":True,"mutation_observed":True}
        self.expected = {"implementer":["gpt-5.6-sol","medium"]}

    def test_valid_observed_context_passes(self):
        self.assertEqual(sim.grade_roles(self.expected, self.root, [self.child]), [])

    def test_wrong_profile_fails(self):
        self.child["effort"] = "high"
        self.assertIn("wrong_profile:implementer", sim.grade_roles(self.expected, self.root, [self.child]))

    def test_missing_child_fails(self):
        self.assertIn("missing_child:implementer", sim.grade_roles(self.expected, self.root, []))

    def test_incomplete_or_unattributed_child_fails(self):
        self.child["completed"] = False; self.child["mutation_observed"] = False
        errors = sim.grade_roles(self.expected, self.root, [self.child])
        self.assertIn("child_not_complete:implementer", errors)
        self.assertIn("no_child_mutation:implementer", errors)

    def test_copy_control_rejects_any_child(self):
        self.assertIn("unexpected_child", sim.grade_roles({}, self.root, [self.child]))

    def test_copy_control_rejects_failed_spawn_attempt(self):
        root={"model":"gpt-5.6-sol","effort":"high","completed":True,"spawn_calls":[{"role":"implementer","fork_turns":"none"}]}
        errors=sim.grade_roles({},root,[])
        self.assertIn("spawn_call_count",errors)
        self.assertIn("unexpected_spawn_call",errors)

    def test_duplicate_spawn_attempt_fails(self):
        self.root["spawn_calls"].append({"role":"implementer","fork_turns":"none"})
        errors=sim.grade_roles(self.expected,self.root,[self.child])
        self.assertIn("spawn_call_count",errors)
        self.assertIn("spawn_contract:implementer",errors)

    def test_duplicate_role_fails_exact_count(self):
        duplicate = dict(self.child)
        errors = sim.grade_roles(self.expected, self.root, [self.child, duplicate])
        self.assertIn("child_count:implementer:2", errors)

    def test_extra_incomplete_child_fails(self):
        extra = {"role":"unexpected","completed":False,"parent_thread_id":None}
        errors = sim.grade_roles(self.expected, self.root, [self.child, extra])
        self.assertIn("incomplete_observed_child", errors)
        self.assertIn("unexpected_child", errors)

    def test_root_edit_rejected_for_delegated_case(self):
        with tempfile.TemporaryDirectory() as raw:
            case_dir = Path(raw)
            self.root["mutations"] = [{"files":[str(case_dir / "owned.py")]}]
            errors = sim.grade_roles(self.expected, self.root, [self.child], ["owned.py"], case_dir)
            self.assertIn("root_mutated_delegated_files", errors)

    def test_child_patch_outside_allowed_files_fails(self):
        with tempfile.TemporaryDirectory() as raw:
            case_dir=Path(raw); self.child["mutations"]=[{"files":[str(case_dir/"other.py")]}]
            errors=sim.grade_roles(self.expected,self.root,[self.child],["owned.py"],case_dir)
            self.assertIn("child_mutated_outside_allowed_files",errors)

    def test_readonly_role_mutation_fails(self):
        readonly={"role":"ux_auditor","model":"gpt-6-astra","effort":"low","completed":True,"mutations":[{"files":[]}],"mutation_observed":True}
        root={"model":"gpt-5.6-sol","effort":"high","completed":True,"spawn_calls":[{"role":"ux_auditor","fork_turns":"none"}]}
        errors=sim.grade_roles({"ux_auditor":["gpt-6-astra","low"]},root,[readonly])
        self.assertIn("readonly_role_mutated:ux_auditor",errors)


class MutationAttributionTests(unittest.TestCase):
    def events(self, output="{}"):
        call = {"type":"response_item","payload":{"type":"custom_tool_call","call_id":"c1","input":'text(await tools.apply_patch("*** Begin Patch\\n*** Update File: owned.py\\n@@\\n-old\\n+new\\n*** End Patch"));'}}
        result = {"type":"response_item","payload":{"type":"custom_tool_call_output","call_id":"c1","output":[{"text":output}]}}
        return [call, result]

    def test_successful_relative_patch_is_attributed(self):
        with tempfile.TemporaryDirectory() as raw:
            rows = sim._successful_mutations(self.events(), Path(raw), "child", "implementer")
            self.assertEqual(rows[0]["files"], [str((Path(raw)/"owned.py").resolve())])
            self.assertEqual(rows[0]["mutator_role"], "implementer")

    def test_failed_patch_is_not_attributed(self):
        with tempfile.TemporaryDirectory() as raw:
            self.assertEqual(sim._successful_mutations(self.events("Error: invalid patch"), Path(raw), "child", "implementer"), [])


class SessionCompletionTests(unittest.TestCase):
    def observed(self, followup_complete):
        events=[
            {"type":"session_meta","payload":{"id":"child","source":{"subagent":{"thread_spawn":{"agent_role":"implementer","parent_thread_id":"root","depth":1}}}}},
            {"type":"turn_context","payload":{"turn_id":"t2","model":"gpt-5.6-sol","effort":"medium","cwd":"/tmp"}},
            {"timestamp":"2026-09-06T15:00:00Z","type":"event_msg","payload":{"type":"task_started","turn_id":"t1"}},
            {"timestamp":"2026-09-06T15:01:00Z","type":"event_msg","payload":{"type":"task_complete","turn_id":"t1"}},
            {"timestamp":"2026-09-06T15:02:00Z","type":"event_msg","payload":{"type":"task_started","turn_id":"t2"}},
        ]
        if followup_complete:
            events.append({"timestamp":"2026-09-06T15:03:00Z","type":"event_msg","payload":{"type":"task_complete","turn_id":"t2"}})
        with tempfile.TemporaryDirectory() as raw:
            path=Path(raw)/"rollout.jsonl"
            path.write_text("\n".join(json.dumps(x) for x in events)+"\n")
            return sim.observed_session(path,"child",Path(raw))

    def test_unfinished_followup_is_not_complete(self):
        observed=self.observed(False)
        self.assertFalse(observed["completed"])
        self.assertEqual(observed["started_at"],"2026-09-06T15:00:00Z")

    def test_completed_followup_is_complete(self):
        observed=self.observed(True)
        self.assertTrue(observed["completed"])
        self.assertEqual(observed["completed_at"],"2026-09-06T15:03:00Z")


class DependencyTests(unittest.TestCase):
    receipt="CONTRACT_RECEIPT TR-FACETS-V1 same-variant-stock-positive url-roundtrip removable-stale no-modal"

    def rows(self, downstream_start="2026-09-06T15:03:00Z", marker="2026-09-06T15:02:30Z", receipt=None, mutation_time="2026-09-06T15:04:00Z"):
        handoff="handoff: stock > 0 in same variante; preserve URL"
        root={"session_id":"root","handoff_markers":[{"timestamp":marker,"text":handoff}],"spawn_calls":[{"role":"implementer_complex","fork_turns":"none","message_observable":True,"message_text":handoff}]}
        children=[
            {"role":"product_discovery","parent_thread_id":"root","completed_at":"2026-09-06T15:02:00Z"},
            {"role":"ux_auditor","parent_thread_id":"root","completed_at":"2026-09-06T15:02:10Z"},
            {"role":"implementer_complex","parent_thread_id":"root","started_at":downstream_start,"assistant_messages":[] if receipt is None else [{"timestamp":"2026-09-06T15:03:30Z","text":receipt}],"mutations":[{"timestamp":mutation_time}]},
        ]
        return root,children

    def test_ordered_handoff_passes(self):
        root,children=self.rows(); self.assertEqual(sim.grade_dependencies("templorojo-filters",root,children),[])

    def test_concurrent_downstream_fails(self):
        root,children=self.rows(downstream_start="2026-09-06T15:01:00Z")
        self.assertIn("downstream_started_before_upstream_complete",sim.grade_dependencies("templorojo-filters",root,children))

    def test_missing_handoff_marker_fails(self):
        root,children=self.rows(marker="2026-09-06T15:01:00Z")
        self.assertIn("semantic_handoff_marker_missing_before_downstream",sim.grade_dependencies("templorojo-filters",root,children))

    def test_encrypted_payload_with_child_receipt_passes(self):
        root,children=self.rows(receipt=self.receipt); root["spawn_calls"][0].update(message_observable=False,message_text=None); root["handoff_markers"]=[]
        self.assertEqual(sim.grade_dependencies("templorojo-filters",root,children),[])

    def test_missing_child_receipt_fails(self):
        root,children=self.rows(); root["spawn_calls"][0].update(message_observable=False,message_text=None)
        self.assertIn("downstream_contract_receipt_missing_or_wrong",sim.grade_dependencies("templorojo-filters",root,children))

    def test_wrong_child_receipt_fails(self):
        root,children=self.rows(receipt=self.receipt.replace("same-variant-stock-positive","any-variant")); root["spawn_calls"][0].update(message_observable=False,message_text=None)
        self.assertIn("downstream_contract_receipt_missing_or_wrong",sim.grade_dependencies("templorojo-filters",root,children))

    def test_late_child_receipt_fails(self):
        root,children=self.rows(receipt=self.receipt,mutation_time="2026-09-06T15:03:20Z"); root["spawn_calls"][0].update(message_observable=False,message_text=None)
        self.assertIn("downstream_contract_receipt_after_edit",sim.grade_dependencies("templorojo-filters",root,children))


class ArtifactGradingTests(unittest.TestCase):
    def test_omitted_requirement_fails(self):
        with tempfile.TemporaryDirectory() as raw:
            case_dir = Path(raw)
            for name, text in sim.FIXTURES["templorojo-filters"].items():
                (case_dir / name).write_text(text)
            errors = sim.grade_artifacts("templorojo-filters", case_dir)
            self.assertTrue(errors)
            self.assertTrue(any(x.startswith("artifact_exception") for x in errors))

    def test_exact_copy_acceptance_is_independent(self):
        with tempfile.TemporaryDirectory() as raw:
            case_dir = Path(raw)
            (case_dir / "button.html").write_text('<button class="save" aria-label="Guardar"><span>Guardar cambios</span></button>\n<script>window.formMode="safe";</script>\n')
            self.assertEqual(sim.grade_artifacts("copy-no-delegation", case_dir), [])
            (case_dir / "button.html").write_text("Guardar cambios\n")
            self.assertEqual(sim.grade_artifacts("copy-no-delegation", case_dir), ["exact_copy_only"])


if __name__ == "__main__":
    unittest.main()
