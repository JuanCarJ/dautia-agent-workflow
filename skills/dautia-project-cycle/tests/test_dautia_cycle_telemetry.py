from __future__ import annotations

import argparse
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


SCRIPT = Path(__file__).parents[1] / "scripts" / "dautia_cycle_telemetry.py"
SPEC = importlib.util.spec_from_file_location("telemetry", SCRIPT)
telemetry = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(telemetry)


ROOT = "019f4947-bb76-7583-9a23-33020d6a5437"
CHILD = "019f519d-c735-7e43-96f0-15f3370f65a4"
GRANDCHILD = "019f519d-f8bc-7e93-a25a-12d01df5fdca"
SECRET = "TOP-SECRET-PROMPT-VALUE"


def event(timestamp, kind, payload):
    return {"timestamp": timestamp, "type": kind, "payload": payload}


class TelemetryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)
        self.sessions = self.base / "sessions"
        self.sessions.mkdir()

    def tearDown(self):
        self.temp.cleanup()

    def write_session(self, name, records):
        path = self.sessions / f"{name}.jsonl"
        path.write_text("\n".join(json.dumps(item) for item in records) + "\n", encoding="utf-8")
        return path

    def args(self):
        return argparse.Namespace(
            root_thread_id=ROOT,
            cycle_id="TEST-01",
            sessions_dir=self.sessions,
            append=False,
            telemetry_file=self.base / "registry.jsonl",
            project_slug="sample",
            objective_id="workflow-review",
            workflow_mode="audit",
            classification="standard",
            outcome="accepted",
            integration_closeout="not_applicable",
            integration_branch=None,
            host_id=None,
            release_target=None,
            repo_closeout=[],
            docs_sync="n-a",
            external_state="n-a",
            acceptance_at_first_pass=None,
            human_corrections=None,
            human_intervention_minutes=None,
            plan_milestones=None,
            plan_update_alert_ratio=2.0,
            xhigh_evidence=False,
            retries=None,
            reused_artifacts=0,
            gate_rejections=None,
            qa_failures=1,
            escaped_defects=None,
            snapshot_kind="final",
            sequence=1,
            baseline="abc123",
            supersedes=None,
            window_start=None,
            window_end=None,
            wait_timeout_alert_ratio=0.5,
            duplicate_prevented=1,
            reuse=2,
            replacement_reason=None,
            include_unbounded_tokens=True,
        )

    def fixtures(self):
        root = [
            event("2026-01-01T00:00:00Z", "session_meta", {"id": ROOT, "cwd": SECRET, "base_instructions": SECRET}),
            event("2026-01-01T00:00:01Z", "turn_context", {"model": "gpt-5.6-sol", "effort": "high", "summary": SECRET}),
            event("2026-01-01T00:00:02Z", "response_item", {"type": "function_call", "name": "spawn_agent", "call_id": "spawn-1", "arguments": json.dumps({"task_name": "audit_docs", "agent_type": "documental", "fork_turns": "none", "message": SECRET})}),
            event("2026-01-01T00:00:03Z", "response_item", {"type": "function_call", "name": "agents.wait_agent", "call_id": "wait-1", "arguments": json.dumps({"timeout_ms": 10, "secret": SECRET})}),
            event("2026-01-01T00:00:04Z", "response_item", {"type": "function_call_output", "call_id": "wait-1", "output": json.dumps({"timed_out": True, "secret": SECRET})}),
            event("2026-01-01T00:00:05Z", "event_msg", {"type": "token_count", "info": {"total_token_usage": {"input_tokens": 10, "cached_input_tokens": 5, "output_tokens": 2, "reasoning_output_tokens": 1, "total_tokens": 12}}}),
            event("2026-01-01T00:00:06Z", "event_msg", {"type": "token_count", "info": {"total_token_usage": {"input_tokens": 20, "cached_input_tokens": 15, "output_tokens": 4, "reasoning_output_tokens": 2, "total_tokens": 24}}}),
            event("2026-01-01T00:00:07Z", "event_msg", {"type": "task_complete"}),
        ]
        child = [
            event("2026-01-01T00:01:00Z", "session_meta", {"id": CHILD, "parent_thread_id": ROOT, "agent_role": "documental", "agent_nickname": SECRET}),
            event("2026-01-01T00:01:01Z", "turn_context", {"model": "gpt-5.6-sol", "effort": "high"}),
            event("2026-01-01T00:01:02Z", "event_msg", {"type": "token_count", "info": {"total_token_usage": {"input_tokens": 3, "cached_input_tokens": 2, "output_tokens": 1, "reasoning_output_tokens": 0, "total_tokens": 4}}}),
        ]
        grandchild = [event("2026-01-01T00:02:00Z", "session_meta", {"id": GRANDCHILD, "parent_thread_id": CHILD, "agent_role": "worker"})]
        self.write_session("root", root)
        self.write_session("child", child)
        self.write_session("grandchild", grandchild)

    def test_privacy_tree_tokens_waits_and_incomplete(self):
        self.fixtures()
        record = telemetry.build_record(self.args())
        encoded = json.dumps(record)
        self.assertNotIn(SECRET, encoded)
        self.assertNotIn(CHILD, encoded)
        self.assertNotIn(GRANDCHILD, encoded)
        self.assertEqual(record["sessions"]["children"], 2)
        self.assertEqual(record["sessions"]["direct_children"], 1)
        self.assertEqual(record["sessions"]["max_depth"], 2)
        self.assertEqual(record["sessions"]["complete"], 1)
        self.assertEqual(record["sessions"]["incomplete"], 2)
        self.assertEqual(record["tokens"]["total_tokens"], 28)
        self.assertEqual(record["runtime"]["agent_waits"]["timed_out"], 1)
        self.assertEqual(record["runtime"]["agent_waits"]["timeout_ratio"], 1.0)
        self.assertFalse(record["runtime"]["agent_waits"]["timeout_alert"])
        self.assertEqual(record["snapshot_kind"], "final")
        self.assertEqual(record["sequence"], 1)
        self.assertEqual(record["cycle_root"], ROOT)
        self.assertEqual(record["coordination"]["duplicate_prevented"], 1)
        self.assertEqual(record["coordination"]["reuse"], 2)
        self.assertEqual(record["spawns"]["task_name_fingerprints"], [telemetry.task_fingerprint("audit_docs")])
        self.assertEqual(record["spawns"]["fingerprint_basis"], "task_name_proxy")
        self.assertEqual(
            record["spawns"]["delegation_fingerprints"],
            [telemetry.task_fingerprint("documental:audit_docs")],
        )
        self.assertFalse(record["spawns"]["semantic_fingerprint_available"])
        self.assertEqual(record["spawns"]["retry_count"], "unknown")
        self.assertIsNone(record["semantic_summary"]["retries"])
        self.assertEqual(record["semantic_summary"]["reused_artifacts"], 0)
        self.assertEqual(record["semantic_summary"]["objective_id"], "workflow-review")
        self.assertEqual(record["semantic_summary"]["workflow_mode"], "audit")

    def test_supplied_retry_count_is_preserved(self):
        self.fixtures()
        args = self.args()
        args.retries = 3
        record = telemetry.build_record(args)
        self.assertEqual(record["spawns"]["retry_count"], 3)
        self.assertEqual(record["semantic_summary"]["retries"], 3)

    def test_malformed_and_invalid_task_name_are_warned(self):
        self.fixtures()
        root = self.sessions / "root.jsonl"
        with root.open("a", encoding="utf-8") as handle:
            handle.write("not-json\n")
            handle.write(json.dumps(event("2026-01-01T00:00:08Z", "response_item", {"type": "function_call", "name": "spawn_agent", "call_id": "spawn-2", "arguments": json.dumps({"task_name": SECRET, "message": SECRET})})) + "\n")
            handle.write(json.dumps(event("2026-01-01T00:00:09Z", "response_item", {"type": "function_call", "name": "spawn_agent", "call_id": "spawn-3", "arguments": json.dumps({"task_name": "invalid secret task", "message": SECRET})})) + "\n")
        record = telemetry.build_record(self.args())
        encoded = json.dumps(record)
        self.assertNotIn(SECRET, encoded)
        self.assertIn("malformed_lines_skipped", record["warnings"])
        self.assertIn("invalid_task_name_redacted", record["warnings"])

    def test_append_is_idempotent_and_conflicts_fail(self):
        self.fixtures()
        record = telemetry.build_record(self.args())
        target = self.base / "telemetry" / "cycles.jsonl"
        self.assertEqual(telemetry.append_record(target, record), "appended")
        self.assertEqual(telemetry.append_record(target, record), "no-op")
        changed = json.loads(json.dumps(record))
        changed["tokens"]["total_tokens"] += 1
        with self.assertRaisesRegex(ValueError, "conflict"):
            telemetry.append_record(target, changed)
        self.assertEqual(target.stat().st_mode & 0o777, 0o600)
        self.assertEqual(target.parent.stat().st_mode & 0o777, 0o700)

    def test_corrupt_registry_and_symlink_are_rejected(self):
        self.fixtures()
        record = telemetry.build_record(self.args())
        corrupt = self.base / "corrupt.jsonl"
        corrupt.write_text("not-json\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "corrupt"):
            telemetry.append_record(corrupt, record)
        real = self.base / "real.jsonl"
        real.write_text("", encoding="utf-8")
        link = self.base / "link.jsonl"
        link.symlink_to(real)
        with self.assertRaisesRegex(ValueError, "symlink"):
            telemetry.append_record(link, record)

    def test_concurrent_cli_append_keeps_one_valid_record(self):
        self.fixtures()
        target = self.base / "telemetry" / "cycles.jsonl"
        command = [
            sys.executable,
            str(SCRIPT),
            "--root-thread-id",
            ROOT,
            "--cycle-id",
            "TEST-01",
            "--sessions-dir",
            str(self.sessions),
            "--telemetry-file",
            str(target),
            "--append",
        ]
        first = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        second = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        first.communicate(timeout=10)
        second.communicate(timeout=10)
        self.assertEqual(first.returncode, 0)
        self.assertEqual(second.returncode, 0)
        lines = target.read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(lines), 1)
        self.assertIsInstance(json.loads(lines[0]), dict)

    def test_cli_batch_reuses_scan_and_returns_one_record_per_root(self):
        self.fixtures()
        second_root = "019f4947-bb76-7583-9a23-33020d6a9999"
        self.write_session("second-root", [
            event("2026-01-02T00:00:00Z", "session_meta", {"id": second_root}),
            event("2026-01-02T00:00:01Z", "event_msg", {"type": "task_complete"}),
        ])
        stdout = io.StringIO()
        stderr = io.StringIO()
        with mock.patch.object(telemetry, "load_sessions", wraps=telemetry.load_sessions) as loader:
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                result = telemetry.main([
                    "--root-thread-id", ROOT,
                    "--root-thread-id", second_root,
                    "--cycle-id", "TEST-BATCH",
                    "--sessions-dir", str(self.sessions),
                ])
        self.assertEqual(loader.call_count, 1)
        self.assertEqual(result, 0)
        records = json.loads(stdout.getvalue())
        self.assertEqual([record["root_thread_id"] for record in records], [ROOT, second_root])
        self.assertIn("telemetry_status=batch(stdout-only:2)", stderr.getvalue())

    def test_out_of_order_unknown_events_and_tool_dedup(self):
        records = [
            event("2026-01-01T00:00:00Z", "session_meta", {"id": ROOT}),
            event("2026-01-01T00:00:03Z", "response_item", {"type": "function_call", "name": "example", "call_id": "same"}),
            event("2026-01-01T00:00:02Z", "response_item", {"type": "function_call", "name": "example", "call_id": "same"}),
            event("2026-01-01T00:00:04Z", "future_event", {"secret": SECRET}),
        ]
        self.write_session("root", records)
        record = telemetry.build_record(self.args())
        self.assertEqual(record["runtime"]["tool_calls"], 1)
        self.assertIn("out_of_order_events_sorted", record["warnings"])
        self.assertIn("unknown_event_type_ignored", record["warnings"])
        self.assertNotIn(SECRET, json.dumps(record))

    def test_window_delimits_cycle_root_and_direct_children(self):
        self.fixtures()
        args = self.args()
        args.snapshot_kind = "checkpoint"
        args.window_start = "2026-01-01T00:00:02Z"
        args.window_end = "2026-01-01T00:00:06Z"
        record = telemetry.build_record(args)
        self.assertEqual(record["sessions"]["children"], 0)
        self.assertEqual(record["runtime"]["tool_calls"], 2)
        self.assertEqual(record["snapshot_start"], args.window_start)
        self.assertEqual(record["snapshot_end"], args.window_end)
        self.assertEqual(record["window"]["start"], args.window_start)
        self.assertEqual(record["window"]["end"], args.window_end)
        self.assertEqual(record["window"]["mode"], "bounded")

    def test_coordination_aggregates_the_complete_descendant_tree(self):
        self.fixtures()
        root = self.sessions / "root.jsonl"
        with root.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event("2026-01-01T00:00:08Z", "response_item", {
                "type": "function_call", "name": "spawn_agent", "call_id": "rejected",
                "arguments": json.dumps({"task_name": "rejected", "message": SECRET}),
            })) + "\n")
            handle.write(json.dumps(event("2026-01-01T00:00:09Z", "response_item", {
                "type": "function_call", "name": "followup_task", "call_id": "follow-1",
                "arguments": json.dumps({"target": CHILD, "message": SECRET}),
            })) + "\n")
            handle.write(json.dumps(event("2026-01-01T00:00:10Z", "response_item", {
                "type": "function_call", "name": "agents.spawn_agent", "call_id": "rejected",
                "arguments": json.dumps({"task_name": "duplicate", "message": SECRET}),
            })) + "\n")
            handle.write(json.dumps(event("2026-01-01T00:00:11Z", "response_item", {
                "type": "function_call", "name": "agents.followup_task", "call_id": "follow-1",
                "arguments": json.dumps({"target": CHILD, "message": SECRET}),
            })) + "\n")
        child = self.sessions / "child.jsonl"
        with child.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event("2026-01-01T00:01:03Z", "response_item", {
                "type": "function_call", "name": "spawn_agent", "call_id": "nested",
                "arguments": json.dumps({"task_name": "nested", "message": SECRET}),
            })) + "\n")
        record = telemetry.build_record(self.args())
        self.assertEqual(record["spawns"]["total"], 3)
        self.assertEqual(record["spawns"]["root_total"], 2)
        self.assertEqual(record["sessions"]["children"], 2)
        self.assertEqual(record["coordination"]["spawn_calls"], 3)
        self.assertEqual(record["coordination"]["successful_child_sessions"], 2)
        self.assertEqual(record["coordination"]["followup_turns"], 1)
        self.assertEqual(record["coordination"]["delegated_invocations"], 4)
        self.assertEqual(record["runtime"]["tool_calls"], 5)
        self.assertNotIn(SECRET, json.dumps(record))
        self.assertNotIn(CHILD, json.dumps(record))

    def test_nested_release_operator_and_large_outputs_are_classified(self):
        release_one = [
            event("2026-01-01T00:01:00Z", "session_meta", {
                "id": CHILD, "parent_thread_id": ROOT, "agent_role": "release_operator",
            }),
            event("2026-01-01T00:01:01Z", "response_item", {
                "type": "custom_tool_call", "name": "exec", "call_id": "exec-1",
                "input": "await tools.exec_command({}); await tools.view_image({});",
            }),
            event("2026-01-01T00:01:02Z", "response_item", {
                "type": "custom_tool_call_output", "call_id": "exec-1", "output": "x" * 10001,
            }),
            event("2026-01-01T00:01:03Z", "response_item", {
                "type": "custom_tool_call", "name": "exec", "call_id": "exec-2",
                "input": "await tools.exec_command({});",
            }),
            event("2026-01-01T00:01:04Z", "response_item", {
                "type": "custom_tool_call_output", "call_id": "exec-2", "output": "y" * 10001,
            }),
        ]
        release_two = [
            event("2026-01-01T00:02:00Z", "session_meta", {
                "id": GRANDCHILD, "parent_thread_id": CHILD, "agent_role": "release_operator",
            }),
        ]
        self.write_session("root", [
            event("2026-01-01T00:00:00Z", "session_meta", {"id": ROOT}),
        ])
        self.write_session("release-one", release_one)
        self.write_session("release-two", release_two)
        record = telemetry.build_record(self.args())
        self.assertEqual(record["sessions"]["children"], 2)
        self.assertEqual(record["coordination"]["nested_release_operator_sessions"], 1)
        self.assertIn("release_operator_nested", record["warnings"])
        self.assertEqual(record["runtime"]["tool_output_chars"], 20002)
        self.assertEqual(record["runtime"]["visual_tool_outputs_over_10000_chars"], 1)
        self.assertEqual(record["runtime"]["text_tool_outputs_over_10000_chars"], 1)
        self.assertTrue(record["runtime"]["tool_output_volume_alert"])
        self.assertEqual(record["runtime"]["tool_methods"], {"exec_command": 2, "view_image": 1})
        self.assertIn("large_text_tool_output_in_context", record["warnings"])
        self.assertNotIn("x" * 100, json.dumps(record))

    def test_large_visual_output_is_volume_not_context_noise(self):
        self.write_session("root", [
            event("2026-01-01T00:00:00Z", "session_meta", {"id": ROOT}),
            event("2026-01-01T00:00:01Z", "response_item", {
                "type": "custom_tool_call", "name": "exec", "call_id": "visual-1",
                "input": "await tools.view_image({});",
            }),
            event("2026-01-01T00:00:02Z", "response_item", {
                "type": "custom_tool_call_output", "call_id": "visual-1",
                "output": "data:image/png;base64," + "x" * 10001,
            }),
        ])
        record = telemetry.build_record(self.args())
        self.assertEqual(record["runtime"]["visual_tool_outputs_over_10000_chars"], 1)
        self.assertEqual(record["runtime"]["text_tool_outputs_over_10000_chars"], 0)
        self.assertFalse(record["runtime"]["tool_output_volume_alert"])
        self.assertNotIn("large_text_tool_output_in_context", record["warnings"])

    def test_contract_change_marks_older_running_root_stale(self):
        self.fixtures()
        args = self.args()
        args.contract_version = "workflow-20260807-token-v2"
        args.contract_changed_at = "2026-01-01T00:00:03Z"
        record = telemetry.build_record(args)
        self.assertEqual(record["contract"]["version"], args.contract_version)
        self.assertEqual(record["contract"]["state"], "stale_contract")
        self.assertIn("stale_workflow_contract", record["warnings"])

    def test_window_exact_delta_model_carry_and_new_child_zero_baseline(self):
        self.fixtures()
        args = self.args()
        args.window_start = "2026-01-01T00:00:06Z"
        args.window_end = "2026-01-01T00:01:02Z"
        record = telemetry.build_record(args)
        self.assertEqual(record["tokens"]["total_tokens"], 4)
        self.assertEqual(record["window"]["coverage"], "exact_segmented")
        self.assertEqual(record["distributions"]["models"], {"gpt-5.6-sol": 2})
        self.assertEqual(record["coordination"]["successful_child_sessions"], 1)

    def test_window_missing_baseline_and_reset_are_explicit(self):
        self.write_session("root", [
            event("2026-01-01T00:00:00Z", "session_meta", {"id": ROOT}),
            event("2026-01-01T00:00:02Z", "event_msg", {"type": "token_count", "info": {"total_token_usage": {"total_tokens": 9}}}),
        ])
        args = self.args()
        args.window_start = "2026-01-01T00:00:01Z"
        record = telemetry.build_record(args)
        self.assertNotIn("total_tokens", record["tokens"])
        self.assertEqual(record["tokens"]["coverage"], "unavailable")
        self.assertIn("window_start_between_token_snapshots", record["warnings"])

        root = self.sessions / "root.jsonl"
        root.write_text("\n".join(json.dumps(item) for item in [
            event("2026-01-01T00:00:00Z", "session_meta", {"id": ROOT}),
            event("2026-01-01T00:00:01Z", "event_msg", {"type": "token_count", "info": {"total_token_usage": {"total_tokens": 10}}}),
            event("2026-01-01T00:00:02Z", "event_msg", {"type": "token_count", "info": {"total_token_usage": {"total_tokens": 2}}}),
        ]) + "\n", encoding="utf-8")
        record = telemetry.build_record(args)
        self.assertEqual(record["tokens"]["total_tokens"], 2)
        self.assertEqual(record["tokens"]["counter_resets"], 1)
        self.assertEqual(record["tokens"]["coverage"], "partial_segmented")
        self.assertIn("token_counter_reset_segmented", record["warnings"])

    def test_historical_image_rollout_profiles_remove_latest_model_bias(self):
        high_end = {
            "input_tokens": 8_534_920,
            "cached_input_tokens": 8_322_816,
            "output_tokens": 17_423,
            "reasoning_output_tokens": 6_833,
            "total_tokens": 8_552_343,
        }
        final = {
            "input_tokens": 12_674_277,
            "cached_input_tokens": 12_262_400,
            "output_tokens": 22_756,
            "reasoning_output_tokens": 7_829,
            "total_tokens": 12_697_033,
        }
        records = [event("2026-09-05T00:00:00Z", "session_meta", {"id": ROOT})]
        for turn in range(1, 7):
            usage = {key: value * turn // 6 for key, value in high_end.items()}
            records.extend([
                event(f"2026-09-05T00:00:{turn * 2 - 1:02d}Z", "turn_context", {
                    "model": "gpt-6-astra", "effort": "high", "summary": SECRET,
                }),
                event(f"2026-09-05T00:00:{turn * 2:02d}Z", "event_msg", {
                    "type": "token_count", "info": {"total_token_usage": usage},
                }),
            ])
        for offset in range(1, 6):
            usage = {
                key: high_end[key] + (final[key] - high_end[key]) * offset // 5
                for key in high_end
            }
            records.extend([
                event(f"2026-09-05T00:00:{offset * 2 + 11:02d}Z", "turn_context", {
                    "model": "gpt-6-astra", "effort": "medium",
                }),
                event(f"2026-09-05T00:00:{offset * 2 + 12:02d}Z", "event_msg", {
                    "type": "token_count", "info": {"total_token_usage": usage},
                }),
            ])
        self.write_session("root", records)

        record = telemetry.build_record(self.args())
        self.assertEqual(record["distributions"]["model_effort"], {
            "gpt-6-astra|high": 6,
            "gpt-6-astra|medium": 5,
        })
        profiles = {
            item["reasoning_effort"]: item
            for item in record["tokens"]["by_model_effort"]
        }
        self.assertEqual(profiles["high"]["total_tokens"], 8_552_343)
        self.assertEqual(profiles["medium"]["total_tokens"], 4_144_690)
        self.assertEqual(record["tokens"]["total_tokens"], 12_697_033)
        self.assertEqual(record["tokens"]["semantics"], "processed_session_telemetry_not_billing_or_cost")
        self.assertNotIn(SECRET, json.dumps(record))

    def test_counter_reset_keeps_observable_lower_bound_by_profile(self):
        self.write_session("root", [
            event("2026-01-01T00:00:00Z", "session_meta", {"id": ROOT}),
            event("2026-01-01T00:00:01Z", "turn_context", {
                "model": "gpt-5.6-sol", "effort": "high",
            }),
            event("2026-01-01T00:00:02Z", "event_msg", {
                "type": "token_count", "info": {"total_token_usage": {"total_tokens": 10}},
            }),
            event("2026-01-01T00:00:03Z", "turn_context", {
                "model": "gpt-5.6-sol", "effort": "medium",
            }),
            event("2026-01-01T00:00:04Z", "event_msg", {
                "type": "token_count", "info": {"total_token_usage": {"total_tokens": 4}},
            }),
            event("2026-01-01T00:00:05Z", "event_msg", {
                "type": "token_count", "info": {"total_token_usage": {"total_tokens": 8}},
            }),
        ])
        args = self.args()
        args.window_start = "2026-01-01T00:00:00Z"
        args.window_end = "2026-01-01T00:00:05Z"
        record = telemetry.build_record(args)
        profiles = {
            item["reasoning_effort"]: item["total_tokens"]
            for item in record["tokens"]["by_model_effort"]
        }
        self.assertEqual(profiles, {"high": 10, "medium": 8})
        self.assertEqual(record["tokens"]["total_tokens"], 18)
        self.assertEqual(record["tokens"]["counter_resets"], 1)
        self.assertEqual(record["tokens"]["unknown_gaps"], 1)
        self.assertEqual(record["tokens"]["coverage"], "partial_segmented")
        self.assertTrue(any(
            segment["coverage"] == "lower_bound_after_reset"
            for segment in record["tokens"]["segments"]
        ))

    def test_partial_window_skips_cross_boundary_delta(self):
        self.write_session("root", [
            event("2026-01-01T00:00:00Z", "session_meta", {"id": ROOT}),
            event("2026-01-01T00:00:01Z", "turn_context", {
                "model": "gpt-5.6-sol", "effort": "high",
            }),
            event("2026-01-01T00:00:02Z", "event_msg", {
                "type": "token_count", "info": {"total_token_usage": {"total_tokens": 10}},
            }),
            event("2026-01-01T00:00:04Z", "turn_context", {
                "model": "gpt-5.6-sol", "effort": "medium",
            }),
            event("2026-01-01T00:00:05Z", "event_msg", {
                "type": "token_count", "info": {"total_token_usage": {"total_tokens": 20}},
            }),
            event("2026-01-01T00:00:06Z", "event_msg", {
                "type": "token_count", "info": {"total_token_usage": {"total_tokens": 30}},
            }),
        ])
        args = self.args()
        args.window_start = "2026-01-01T00:00:03Z"
        args.window_end = "2026-01-01T00:00:06Z"
        record = telemetry.build_record(args)
        self.assertEqual(record["tokens"]["total_tokens"], 10)
        self.assertEqual(record["tokens"]["coverage"], "partial_segmented")
        self.assertEqual(record["distributions"]["model_effort"], {
            "gpt-5.6-sol|medium": 1,
        })
        self.assertIn("window_start_between_token_snapshots", record["warnings"])

    def test_outcome_metrics_and_host_are_emitted_only_when_supplied(self):
        self.fixtures()
        args = self.args()
        record = telemetry.build_record(args)
        self.assertNotIn("outcome_metrics", record["semantic_summary"])

        args.acceptance_at_first_pass = "no"
        args.human_corrections = 2
        args.human_intervention_minutes = 12.5
        args.host_id = "windows-wsl"
        measured = telemetry.build_record(args)
        self.assertEqual(measured["semantic_summary"]["host_id"], "windows-wsl")
        self.assertEqual(measured["semantic_summary"]["outcome_metrics"], {
            "source": "operator_supplied",
            "acceptance_at_first_pass": False,
            "human_corrections": 2,
            "human_intervention_minutes": 12.5,
        })

    def test_polling_alert_and_structural_reset(self):
        self.write_session("root", [
            event("2026-01-01T00:00:00Z", "session_meta", {"id": ROOT}),
            event("2026-01-01T00:00:01Z", "response_item", {"type": "function_call", "name": "wait_agent", "call_id": "w1"}),
            event("2026-01-01T00:00:02Z", "response_item", {"type": "function_call", "name": "list_agents", "call_id": "l1"}),
            event("2026-01-01T00:00:03Z", "response_item", {"type": "function_call", "name": "wait_agent", "call_id": "w2"}),
            event("2026-01-01T00:00:04Z", "event_msg", {"type": "task_complete"}),
            event("2026-01-01T00:00:05Z", "response_item", {"type": "function_call", "name": "wait_agent", "call_id": "w3"}),
            event("2026-01-01T00:00:06Z", "response_item", {"type": "function_call", "name": "list_agents", "call_id": "l2"}),
        ])
        record = telemetry.build_record(self.args())
        self.assertEqual(record["polling"], {
            "repeated_calls": 1,
            "max_streak": 3,
            "unchanged_wait_results": 0,
            "alert": False,
        })

    def test_objective_scope_plan_budget_and_closeout_evidence(self):
        self.write_session("root", [
            event("2026-01-01T00:00:00Z", "session_meta", {"id": ROOT}),
            event("2026-01-01T00:00:01Z", "turn_context", {
                "model": "gpt-5.6-sol", "effort": "xhigh",
            }),
            event("2026-01-01T00:00:02Z", "response_item", {
                "type": "message", "role": "user", "content": [{"type": "input_text", "text": SECRET}],
            }),
            event("2026-01-01T00:00:03Z", "response_item", {
                "type": "message", "role": "user", "content": [{"type": "input_text", "text": SECRET}],
            }),
            *[
                event(f"2026-01-01T00:00:{second:02d}Z", "response_item", {
                    "type": "function_call",
                    "name": "update_plan",
                    "call_id": f"plan-{second}",
                })
                for second in range(4, 9)
            ],
            event("2026-01-01T00:00:09Z", "event_msg", {"type": "task_complete"}),
        ])
        args = self.args()
        args.workflow_mode = "implementation"
        args.integration_closeout = "verified"
        args.plan_milestones = 2
        record = telemetry.build_record(args)
        self.assertEqual(record["scope"]["comparison_reliability"], "multi_turn_unbounded")
        self.assertEqual(record["runtime"]["plan"]["updates"], 5)
        self.assertFalse(record["runtime"]["plan"]["alert"])
        self.assertIn("unbounded_multi_turn_scope", record["warnings"])
        self.assertNotIn("plan_updates_exceed_milestone_budget", record["warnings"])
        self.assertIn("xhigh_without_evaluation_evidence", record["warnings"])
        self.assertIn(
            "verified_integration_closeout_without_repository_evidence",
            record["warnings"],
        )

        args.window_start = "2026-01-01T00:00:01Z"
        args.window_end = "2026-01-01T00:00:09Z"
        bounded = telemetry.build_record(args)
        self.assertTrue(bounded["runtime"]["plan"]["alert"])
        self.assertIn("plan_updates_exceed_milestone_budget", bounded["warnings"])
        self.assertNotIn("unbounded_multi_turn_scope", bounded["warnings"])

    def test_repository_closeouts_support_multi_repo_evidence(self):
        self.fixtures()
        args = self.args()
        args.workflow_mode = "implementation"
        args.integration_closeout = "verified"
        args.repo_closeout = [
            ("frontend", "staging", "abcdef1"),
            ("backend", "integration/api", "1234567"),
        ]
        record = telemetry.build_record(args)
        self.assertEqual(
            record["semantic_summary"]["repository_closeouts"],
            [
                {"project": "frontend", "integration_branch": "staging", "integration_sha": "abcdef1"},
                {"project": "backend", "integration_branch": "integration/api", "integration_sha": "1234567"},
            ],
        )
        self.assertNotIn(
            "verified_integration_closeout_without_repository_evidence",
            record["warnings"],
        )

    def test_unchanged_agent_wait_results_are_counted_without_payload(self):
        result = json.dumps({"timed_out": True, "secret": SECRET})
        self.write_session("root", [
            event("2026-01-01T00:00:00Z", "session_meta", {"id": ROOT}),
            event("2026-01-01T00:00:01Z", "response_item", {
                "type": "function_call", "name": "wait_agent", "call_id": "w1",
            }),
            event("2026-01-01T00:00:02Z", "response_item", {
                "type": "function_call_output", "call_id": "w1", "output": result,
            }),
            event("2026-01-01T00:00:03Z", "response_item", {
                "type": "function_call", "name": "wait_agent", "call_id": "w2",
            }),
            event("2026-01-01T00:00:04Z", "response_item", {
                "type": "function_call_output", "call_id": "w2", "output": result,
            }),
        ])
        record = telemetry.build_record(self.args())
        self.assertEqual(record["polling"]["unchanged_wait_results"], 1)
        self.assertTrue(record["polling"]["alert"])
        self.assertNotIn(SECRET, json.dumps(record))

    def test_workflow_friction_signals_are_separated_and_privacy_safe(self):
        skill_path = "/Users/example/.codex/skills/computer-use/SKILL.md"
        self.write_session("root", [
            event("2026-01-01T00:00:00Z", "session_meta", {"id": ROOT}),
            event("2026-01-01T00:00:01Z", "turn_context", {"model": "gpt-5.6-sol"}),
            event("2026-01-01T00:00:02Z", "event_msg", {"type": "task_started"}),
            event("2026-01-01T00:00:03Z", "response_item", {
                "type": "custom_tool_call", "name": "functions.exec", "call_id": "skill-1",
                "arguments": f"await tools.exec_command({{cmd: 'sed -n 1,100p {skill_path}'}})",
            }),
            event("2026-01-01T00:00:04Z", "response_item", {
                "type": "custom_tool_call", "name": "functions.exec", "call_id": "skill-2",
                "input": f"await tools.exec_command({{cmd: 'sed -n 101,200p {skill_path}'}})",
            }),
            event("2026-01-01T00:00:05Z", "response_item", {
                "type": "custom_tool_call", "name": "functions.exec", "call_id": "plan-1",
                "arguments": "await tools.update_plan({plan: []})",
            }),
            event("2026-01-01T00:00:06Z", "response_item", {
                "type": "custom_tool_call", "name": "functions.wait", "call_id": "exec-wait",
                "arguments": "{}",
            }),
            event("2026-01-01T00:00:07Z", "response_item", {
                "type": "custom_tool_call_output", "call_id": "exec-wait", "output": "done",
            }),
            event("2026-01-01T00:00:07.1Z", "turn_context", {"model": "gpt-5.6-sol"}),
            event("2026-01-01T00:00:07.2Z", "response_item", {
                "type": "custom_tool_call", "name": "functions.exec", "call_id": "skill-3",
                "arguments": f"await tools.exec_command({{cmd: 'sed -n 1,200p {skill_path}'}})",
            }),
            event("2026-01-01T00:00:08Z", "event_msg", {"type": "context_compacted"}),
            event("2026-01-01T00:00:09Z", "event_msg", {"type": "turn_aborted"}),
        ])
        record = telemetry.build_record(self.args())
        runtime = record["runtime"]
        self.assertEqual(runtime["task_starts"], 1)
        self.assertEqual(runtime["task_completions"], 0)
        self.assertEqual(runtime["context_compactions"], 1)
        self.assertEqual(runtime["turn_aborts"], 1)
        self.assertEqual(runtime["plan_updates"], 1)
        self.assertEqual(runtime["execution_waits"], {"calls": 1, "pending_result": 0, "returned": 1})
        self.assertEqual(runtime["agent_waits"]["completed"], 0)
        self.assertEqual(runtime["skill_file_read_calls"], {"computer-use": 3})
        self.assertEqual(runtime["skill_objective_loads"], {"computer-use": 1})
        self.assertEqual(runtime["skill_read_turns"], {"computer-use": 2})
        self.assertEqual(runtime["skill_extra_reads_same_turn"], {"computer-use": 1})
        self.assertEqual(runtime["skill_reload_turns"], {"computer-use": 1})
        self.assertTrue(runtime["skill_reload_alert"])
        self.assertNotIn("/Users/example", json.dumps(record))

    def test_missing_implementation_integration_closeout_is_flagged(self):
        self.fixtures()
        args = self.args()
        args.workflow_mode = "implementation"
        args.integration_closeout = "missing"
        record = telemetry.build_record(args)
        self.assertIn("implementation_integration_closeout_missing", record["warnings"])

    def test_pending_candidates_are_sanitized_and_not_reported_as_integrated(self):
        self.fixtures()
        for state in telemetry.PENDING_INTEGRATION_CLOSEOUTS:
            with self.subTest(state=state):
                args = self.args()
                args.workflow_mode = "implementation"
                args.integration_closeout = state
                args.snapshot_kind = "checkpoint"
                args.outcome = "verifying"
                record = telemetry.build_record(args)
                self.assertEqual(state, record["semantic_summary"]["integration_closeout"])
                self.assertEqual([], record["semantic_summary"]["repository_closeouts"])
                self.assertIn("implementation_candidate_pending", record["warnings"])
                self.assertNotIn("implementation_integration_closeout_missing", record["warnings"])
                self.assertNotIn(
                    "verified_integration_closeout_without_repository_evidence",
                    record["warnings"],
                )
                self.assertNotIn(SECRET, json.dumps(record))

    def test_final_accepted_pending_candidate_is_advisory_inconsistent(self):
        self.fixtures()
        args = self.args()
        args.workflow_mode = "implementation"
        args.integration_closeout = "pending_authority"
        args.snapshot_kind = "final"
        args.outcome = "accepted"
        record = telemetry.build_record(args)
        self.assertIn("implementation_candidate_pending", record["warnings"])
        self.assertIn("pending_candidate_with_terminal_outcome", record["warnings"])

        args.outcome = "accepted_with_residuals"
        residual = telemetry.build_record(args)
        self.assertNotIn("pending_candidate_with_terminal_outcome", residual["warnings"])

    def test_unbounded_tokens_are_suppressed_by_default(self):
        self.fixtures()
        args = self.args()
        args.include_unbounded_tokens = False
        record = telemetry.build_record(args)
        self.assertNotIn("total_tokens", record["tokens"])
        self.assertEqual(record["tokens"]["coverage"], "cumulative_totals_suppressed")
        self.assertIn("unbounded_token_totals_suppressed", record["warnings"])

    def test_bounded_window_with_missing_token_session_omits_aggregate(self):
        self.fixtures()
        child = self.sessions / "child.jsonl"
        with child.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event(
                "2026-01-01T00:01:03Z", "event_msg", {"type": "future_without_tokens"}
            )) + "\n")
        args = self.args()
        args.window_start = "2026-01-01T00:01:03Z"
        args.window_end = "2026-01-01T00:01:03Z"
        record = telemetry.build_record(args)
        self.assertNotIn("total_tokens", record["tokens"])
        self.assertEqual(record["tokens"]["coverage"], "unavailable")
        self.assertIn("missing_token_count", record["warnings"])

    def test_legacy_registries_remain_readable(self):
        legacy_records = [
            {
                "schema_version": version,
                "cycle_id": f"LEGACY-0{version}",
                "root_thread_id": ROOT,
                "snapshot_end": f"2025-12-3{version}T00:00:00Z",
            }
            for version in (1, 2, 3, 4)
        ]
        target = self.base / "legacy.jsonl"
        target.write_text(
            "\n".join(json.dumps(record) for record in legacy_records) + "\n",
            encoding="utf-8",
        )
        lines, records = telemetry.read_registry(target)
        self.assertEqual(len(lines), 4)
        for legacy in legacy_records:
            self.assertIn(
                (
                    "legacy",
                    legacy["cycle_id"],
                    ROOT,
                    legacy["snapshot_end"],
                ),
                records,
            )

    def test_checkpoint_final_supersession_and_idempotence(self):
        self.fixtures()
        target = self.base / "registry.jsonl"
        checkpoint_args = self.args()
        checkpoint_args.snapshot_kind = "checkpoint"
        checkpoint = telemetry.build_record(checkpoint_args)
        self.assertEqual(telemetry.append_record(target, checkpoint), "appended")

        final_args = self.args()
        final_args.sequence = 2
        final_args.supersedes = "checkpoint:1"
        final_args.replacement_reason = "closeout"
        final = telemetry.build_record(final_args)
        self.assertEqual(telemetry.append_record(target, final), "appended")
        self.assertEqual(telemetry.append_record(target, final), "no-op")

        duplicate_replacement = json.loads(json.dumps(final))
        duplicate_replacement["sequence"] = 3
        duplicate_replacement["snapshot_id"] = "final:3"
        with self.assertRaisesRegex(ValueError, "already has a replacement"):
            telemetry.append_record(target, duplicate_replacement)

    def test_missing_superseded_snapshot_and_identity_conflict_fail(self):
        self.fixtures()
        target = self.base / "registry.jsonl"
        args = self.args()
        args.sequence = 2
        args.supersedes = "checkpoint:1"
        args.replacement_reason = "delta"
        record = telemetry.build_record(args)
        with self.assertRaisesRegex(ValueError, "does not exist"):
            telemetry.append_record(target, record)

        args.supersedes = None
        args.replacement_reason = None
        record = telemetry.build_record(args)
        self.assertEqual(telemetry.append_record(target, record), "appended")
        conflict = json.loads(json.dumps(record))
        conflict["baseline"] = "changed"
        with self.assertRaisesRegex(ValueError, "key conflict"):
            telemetry.append_record(target, conflict)

        lower = json.loads(json.dumps(record))
        lower["snapshot_kind"] = "checkpoint"
        lower["sequence"] = 1
        lower["snapshot_id"] = "checkpoint:1"
        with self.assertRaisesRegex(ValueError, "sequence must increase"):
            telemetry.append_record(target, lower)

    def test_cli_rejects_invalid_window_and_replacement_without_supersedes(self):
        parsed = telemetry.parse_args([
            "--root-thread-id", ROOT,
            "--cycle-id", "TEST-01",
            "--integration-closeout", "verified",
            "--repo-closeout", "frontend=staging@abcdef1",
        ])
        self.assertEqual(parsed.repo_closeout, [("frontend", "staging", "abcdef1")])
        for state in telemetry.PENDING_INTEGRATION_CLOSEOUTS:
            with self.subTest(state=state):
                pending = telemetry.parse_args([
                    "--root-thread-id", ROOT,
                    "--cycle-id", "TEST-01",
                    "--integration-closeout", state,
                ])
                self.assertEqual(state, pending.integration_closeout)
        invalid_argv = [
            [
                "--root-thread-id", ROOT,
                "--cycle-id", "TEST-01",
                "--window-start", "2026-01-02T00:00:00Z",
                "--window-end", "2026-01-01T00:00:00Z",
            ],
            [
                "--root-thread-id", ROOT,
                "--cycle-id", "TEST-01",
                "--replacement-reason", "delta",
            ],
            [
                "--root-thread-id", ROOT,
                "--cycle-id", "TEST-01",
                "--supersedes", "checkpoint:1",
            ],
            [
                "--root-thread-id", ROOT,
                "--cycle-id", "TEST-01",
                "--repo-closeout", "frontend=abcdef1",
            ],
            [
                "--root-thread-id", ROOT,
                "--cycle-id", "TEST-01",
                "--integration-closeout", "https://example.invalid/pr/1",
            ],
        ]
        for argv in invalid_argv:
            with self.subTest(argv=argv), contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit):
                    telemetry.parse_args(argv)


if __name__ == "__main__":
    unittest.main()
