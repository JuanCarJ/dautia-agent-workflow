#!/usr/bin/env python3
"""Extract privacy-safe DautIA cycle telemetry from local Codex rollouts."""

from __future__ import annotations

import argparse
import collections
import datetime as dt
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys
import tempfile
from typing import Any


SCHEMA_VERSION = 6
SUPPORTED_SCHEMA_VERSIONS = {1, 2, 3, 4, 5, SCHEMA_VERSION}
SAFE_ID = re.compile(r"^[A-Za-z0-9._-]{1,80}$")
UUID_LIKE = re.compile(r"^[A-Fa-f0-9-]{16,80}$")
SKILL_PATH = re.compile(r"/([A-Za-z0-9._-]{1,80})/SKILL\.md(?:[\"'\\\s]|$)")
NESTED_TOOL_CALL = re.compile(r"\btools\.([A-Za-z][A-Za-z0-9_]*)\s*\(")
LARGE_TOOL_OUTPUT_CHARS = 10_000
VISUAL_TOOL_METHODS = {
    "generatedImage",
    "image",
    "image_gen__imagegen",
    "imagegen",
    "screenshot",
    "view_image",
}
CLASSIFICATIONS = ("direct", "standard", "critical")
WORKFLOW_MODES = ("discovery", "audit", "implementation", "release")
PENDING_INTEGRATION_CLOSEOUTS = (
    "pending_pr",
    "pending_review",
    "pending_authority",
)
INTEGRATION_CLOSEOUTS = (
    "verified",
    *PENDING_INTEGRATION_CLOSEOUTS,
    "local_only",
    "missing",
    "not_applicable",
)
OUTCOMES = (
    "accepted",
    "accepted_with_residuals",
    "rejected",
    "blocked",
    "reopened",
    "released_verified",
    "waiting_external",
    "verifying",
    "failed",
    "unknown",
)
SEMANTIC_COUNTERS = (
    "retries",
    "reused_artifacts",
    "gate_rejections",
    "qa_failures",
    "escaped_defects",
)
SNAPSHOT_KINDS = ("checkpoint", "final")
REPLACEMENT_REASONS = (
    "delta",
    "rejection_fix",
    "independent_verification",
    "closeout",
)
DOC_SYNC_STATES = ("yes", "no", "n-a")
EXTERNAL_STATES = ("verified", "pending", "n-a")
COMMIT_SHA = re.compile(r"^[A-Fa-f0-9]{7,64}$")
GIT_BRANCH = re.compile(r"^(?!/)(?!.*(?:\.\.|//))[A-Za-z0-9._/-]{1,200}(?<!/)$")
TOKEN_KEYS = (
    "input_tokens",
    "cached_input_tokens",
    "cache_write_input_tokens",
    "output_tokens",
    "reasoning_output_tokens",
    "total_tokens",
)


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")


def safe_identifier(value: str, label: str) -> str:
    if not SAFE_ID.fullmatch(value):
        raise ValueError(f"{label} must match {SAFE_ID.pattern}")
    return value


def positive(value: str) -> int:
    parsed = int(value)
    if parsed < 1:
        raise argparse.ArgumentTypeError("must be positive")
    return parsed


def ratio(value: str) -> float:
    parsed = float(value)
    if not 0 <= parsed <= 1:
        raise argparse.ArgumentTypeError("must be between 0 and 1")
    return parsed


def iso_timestamp(value: str) -> str:
    candidate = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = dt.datetime.fromisoformat(candidate)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None:
        raise argparse.ArgumentTypeError("must include a timezone")
    return parsed.astimezone(dt.timezone.utc).isoformat().replace("+00:00", "Z")


def snapshot_reference(kind: str, sequence: int) -> str:
    return f"{kind}:{sequence}"


def parse_snapshot_reference(value: str) -> tuple[str, int]:
    kind, separator, raw_sequence = value.partition(":")
    if not separator or kind not in SNAPSHOT_KINDS:
        raise ValueError("supersedes must be checkpoint:N or final:N")
    try:
        sequence = int(raw_sequence)
    except ValueError as exc:
        raise ValueError("supersedes must be checkpoint:N or final:N") from exc
    if sequence < 1:
        raise ValueError("supersedes sequence must be positive")
    return kind, sequence


def task_fingerprint(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]


def output_fingerprint(payload: dict[str, Any]) -> str | None:
    """Hash a tool result for equality checks without retaining its contents."""
    output = payload.get("output")
    if output is None:
        return None
    if not isinstance(output, str):
        try:
            output = json.dumps(output, sort_keys=True, separators=(",", ":"))
        except (TypeError, ValueError):
            return None
    return hashlib.sha256(output.encode("utf-8")).hexdigest()[:16]


def visual_output(payload: dict[str, Any], methods: set[str]) -> bool:
    """Classify visual/binary payloads without retaining their contents."""
    if methods & VISUAL_TOOL_METHODS:
        return True
    output = payload.get("output")
    if not isinstance(output, str):
        return False
    prefix = output[:2_000].lower()
    return (
        "data:image/" in prefix
        or '"type":"image"' in prefix
        or '"type": "image"' in prefix
        or '"image_url"' in prefix
    )


def output_length(payload: dict[str, Any]) -> int:
    """Measure a tool result without retaining or emitting its contents."""
    output = payload.get("output")
    if output is None:
        return 0
    if not isinstance(output, str):
        try:
            output = json.dumps(output, sort_keys=True, separators=(",", ":"))
        except (TypeError, ValueError):
            return 0
    return len(output)


def repo_closeout(value: str) -> tuple[str, str, str]:
    project, separator, branch_and_sha = value.partition("=")
    branch, branch_separator, sha = branch_and_sha.rpartition("@")
    if not separator or not branch_separator:
        raise argparse.ArgumentTypeError("must be PROJECT=INTEGRATION_BRANCH@SHA")
    try:
        project = safe_identifier(project, "repository closeout project")
    except ValueError as exc:
        raise argparse.ArgumentTypeError(str(exc)) from exc
    if not GIT_BRANCH.fullmatch(branch):
        raise argparse.ArgumentTypeError("INTEGRATION_BRANCH is not a safe Git branch name")
    if not COMMIT_SHA.fullmatch(sha):
        raise argparse.ArgumentTypeError("SHA must be a 7-64 character hexadecimal commit")
    return project, branch, sha.lower()


def positive_float(value: str) -> float:
    parsed = float(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be positive")
    return parsed


def nonnegative_float(value: str) -> float:
    parsed = float(value)
    if parsed < 0:
        raise argparse.ArgumentTypeError("must be non-negative")
    return parsed


def load_sessions(sessions_dir: Path) -> tuple[dict[str, dict[str, Any]], list[str]]:
    sessions: dict[str, dict[str, Any]] = {}
    warnings: set[str] = set()
    for path in sessions_dir.rglob("*.jsonl"):
        metadata = None
        events: list[tuple[str, int, str, dict[str, Any]]] = []
        malformed = 0
        try:
            with path.open("r", encoding="utf-8") as handle:
                previous_timestamp = ""
                for line_number, raw in enumerate(handle, 1):
                    try:
                        item = json.loads(raw)
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        malformed += 1
                        continue
                    kind = item.get("type")
                    payload = item.get("payload")
                    if not isinstance(payload, dict):
                        payload = {}
                    timestamp = item.get("timestamp")
                    if not isinstance(timestamp, str):
                        timestamp = ""
                    if timestamp and previous_timestamp and timestamp < previous_timestamp:
                        warnings.add("out_of_order_events_sorted")
                    if timestamp:
                        previous_timestamp = timestamp
                    if kind not in {
                        "session_meta",
                        "turn_context",
                        "event_msg",
                        "response_item",
                        "world_state",
                        "inter_agent_communication_metadata",
                    }:
                        warnings.add("unknown_event_type_ignored")
                    if kind == "session_meta" and metadata is None:
                        metadata = payload
                    events.append((timestamp, line_number, str(kind or ""), payload))
        except OSError:
            warnings.add("session_read_error")
            continue
        if not isinstance(metadata, dict) or not isinstance(metadata.get("id"), str):
            warnings.add("missing_session_meta")
            continue
        if malformed:
            warnings.add("malformed_lines_skipped")
        events.sort(key=lambda event: (event[0], event[1]))
        sessions[metadata["id"]] = {
            "meta": metadata,
            "events": events,
            "malformed": malformed,
        }
    return sessions, sorted(warnings)


def direct_parent(meta: dict[str, Any]) -> str | None:
    parent = meta.get("parent_thread_id")
    if isinstance(parent, str):
        return parent
    source = meta.get("source")
    if not isinstance(source, dict):
        return None
    subagent = source.get("subagent")
    if not isinstance(subagent, dict):
        return None
    spawn = subagent.get("thread_spawn")
    if not isinstance(spawn, dict):
        return None
    value = spawn.get("parent_thread_id")
    return value if isinstance(value, str) else None


def descendant_tree(
    sessions: dict[str, dict[str, Any]], root_thread_id: str
) -> tuple[list[tuple[dict[str, Any], int]], bool]:
    by_parent: dict[str, list[dict[str, Any]]] = collections.defaultdict(list)
    for session in sessions.values():
        parent = direct_parent(session["meta"])
        if parent is not None:
            by_parent[parent].append(session)
    for children in by_parent.values():
        children.sort(key=lambda session: str(session["meta"].get("id", "")))

    result: list[tuple[dict[str, Any], int]] = []
    queue = collections.deque([(root_thread_id, 0)])
    seen = {root_thread_id}
    cycle_skipped = False
    while queue:
        parent_id, parent_depth = queue.popleft()
        for child in by_parent.get(parent_id, []):
            child_id = child["meta"].get("id")
            if not isinstance(child_id, str) or child_id in seen:
                cycle_skipped = True
                continue
            seen.add(child_id)
            depth = parent_depth + 1
            result.append((child, depth))
            queue.append((child_id, depth))
    return result, cycle_skipped


def session_start(session: dict[str, Any]) -> str | None:
    return next(
        (
            timestamp
            for timestamp, _, kind, _ in session["events"]
            if kind == "session_meta" and timestamp
        ),
        None,
    )


def parsed_arguments(payload: dict[str, Any]) -> dict[str, Any]:
    arguments = payload.get("arguments")
    if isinstance(arguments, dict):
        return arguments
    if not isinstance(arguments, str):
        return {}
    try:
        value = json.loads(arguments)
    except json.JSONDecodeError:
        return {}
    return value if isinstance(value, dict) else {}


def argument_text(payload: dict[str, Any]) -> str:
    """Return argument text for structural signals only; callers must not persist it."""
    for key in ("arguments", "input"):
        arguments = payload.get(key)
        if isinstance(arguments, str):
            return arguments
        if isinstance(arguments, dict):
            return json.dumps(arguments, sort_keys=True)
    return ""


def skill_names_in_arguments(payload: dict[str, Any]) -> set[str]:
    return set(SKILL_PATH.findall(argument_text(payload)))


def is_plan_update(name: Any, payload: dict[str, Any]) -> bool:
    normalized = str(name or "").rsplit(".", 1)[-1]
    return normalized == "update_plan" or "tools.update_plan(" in argument_text(payload)


def output_timed_out(payload: dict[str, Any]) -> bool | None:
    output = payload.get("output")
    if isinstance(output, dict):
        value = output
    elif isinstance(output, str):
        try:
            value = json.loads(output)
        except json.JSONDecodeError:
            return None
    else:
        return None
    result = value.get("timed_out") if isinstance(value, dict) else None
    return result if isinstance(result, bool) else None


def token_value(payload: dict[str, Any]) -> dict[str, int] | None:
    info = payload.get("info")
    total = info.get("total_token_usage") if isinstance(info, dict) else None
    if not isinstance(total, dict):
        return None
    return {key: int(total.get(key, 0) or 0) for key in TOKEN_KEYS}


def add_token_values(target: collections.Counter[str], values: dict[str, int]) -> None:
    for key in TOKEN_KEYS:
        target[key] += values.get(key, 0)


def analyze_turn_lifecycle(
    session: dict[str, Any], window_end: str | None = None
) -> dict[str, str | None]:
    """Return the latest identifiable runtime turn state at the boundary.

    Turn identifiers keep a late terminal event for an older turn from closing a
    newer open turn. Events without identifiers remain compatible with older
    rollouts by applying their terminal state to the latest observed turn.
    """
    turns: dict[str, dict[str, str | None]] = {}
    latest_turn: str | None = None
    anonymous_turn = 0

    for timestamp, _, kind, payload in session["events"]:
        if window_end is not None and (not timestamp or timestamp > window_end):
            continue
        if kind != "event_msg":
            continue
        event_type = str(payload.get("type") or "").lower()
        if event_type not in {
            "task_started", "task_start", "task_complete", "turn_complete",
            "turn_aborted", "task_aborted",
        }:
            continue
        raw_turn_id = payload.get("turn_id")
        turn_id = raw_turn_id if isinstance(raw_turn_id, str) and raw_turn_id else None

        if event_type in ("task_started", "task_start"):
            if turn_id is None:
                anonymous_turn += 1
                key = f"anonymous:{anonymous_turn}"
            else:
                key = f"identified:{turn_id}"
            turns[key] = {"state": "open", "terminal_timestamp": None}
            latest_turn = key
            continue

        terminal_state = (
            "completed"
            if event_type in ("task_complete", "turn_complete")
            else "aborted"
        )
        if turn_id is not None:
            key = f"identified:{turn_id}"
            if key not in turns:
                turns[key] = {
                    "state": terminal_state,
                    "terminal_timestamp": timestamp or None,
                }
                if (
                    latest_turn is None
                    or turns[latest_turn]["state"] != "open"
                ):
                    latest_turn = key
                continue
            turns[key] = {
                "state": terminal_state,
                "terminal_timestamp": timestamp or None,
            }
            continue

        if latest_turn is None:
            anonymous_turn += 1
            latest_turn = f"anonymous:{anonymous_turn}"
        turns[latest_turn] = {
            "state": terminal_state,
            "terminal_timestamp": timestamp or None,
        }

    if latest_turn is None:
        return {"state": "unknown", "terminal_timestamp": None}
    return turns[latest_turn]


def analyze_token_profiles(
    session: dict[str, Any],
    window_start: str | None,
    window_end: str | None,
) -> dict[str, Any]:
    """Attribute observable cumulative-counter deltas to effective turn profiles.

    Counter decreases start a new observable epoch. The post-reset snapshot is a
    lower bound for that epoch; consumption between the prior snapshot and reset
    remains unknown. A window boundary between counter snapshots is also kept as
    an explicit gap instead of assigning the whole interval to the latest profile.
    """
    profiles: list[dict[str, Any]] = []
    token_segments: list[dict[str, Any]] = []
    segment_by_key: dict[tuple[int, int], dict[str, Any]] = {}
    totals: collections.Counter[str] = collections.Counter()
    current_model: str | None = None
    current_effort: str | None = None
    turn_index = 0
    active_profile_index: int | None = None
    counter_epoch = 0
    previous_tokens: dict[str, int] | None = None
    previous_token_timestamp: str | None = None
    token_snapshots = 0
    reset_count = 0
    unknown_gaps = 0
    missing_start_boundary = False
    exact_start_boundary = window_start is None
    token_at_window_end = window_end is None
    latest_turn = analyze_turn_lifecycle(session, window_end)
    latest_turn_completed_in_window = bool(
        latest_turn["state"] == "completed"
        and latest_turn["terminal_timestamp"]
        and (
            window_start is None
            or str(latest_turn["terminal_timestamp"]) >= window_start
        )
    )
    started_at = session_start(session)
    if window_start is not None and started_at is not None and started_at >= window_start:
        exact_start_boundary = True

    def in_window(timestamp: str) -> bool:
        return bool(
            timestamp
            and (window_start is None or timestamp >= window_start)
            and (window_end is None or timestamp <= window_end)
        )

    def ensure_profile(started_in_window: bool) -> int:
        nonlocal active_profile_index
        if active_profile_index is not None:
            return active_profile_index
        profiles.append(
            {
                "turn": max(turn_index, 1),
                "model": current_model or "unknown",
                "reasoning_effort": current_effort or "unknown",
                "started_in_window": started_in_window,
            }
        )
        active_profile_index = len(profiles) - 1
        return active_profile_index

    def add_delta(
        delta: dict[str, int], reset_counters: list[str] | None = None
    ) -> None:
        profile_index = ensure_profile(False)
        key = (profile_index, counter_epoch)
        segment = segment_by_key.get(key)
        if segment is None:
            profile = profiles[profile_index]
            segment = {
                "turn": profile["turn"],
                "model": profile["model"],
                "reasoning_effort": profile["reasoning_effort"],
                "counter_epoch": counter_epoch,
                "coverage": "lower_bound_after_reset" if reset_counters else "observed_delta",
                "token_snapshots": 0,
                **{token_key: 0 for token_key in TOKEN_KEYS},
            }
            if reset_counters:
                segment["reset_counters"] = reset_counters
            segment_by_key[key] = segment
            token_segments.append(segment)
        segment["token_snapshots"] += 1
        for token_key in TOKEN_KEYS:
            segment[token_key] += delta[token_key]
        add_token_values(totals, delta)

    for timestamp, _, kind, payload in session["events"]:
        before_window = bool(window_start is not None and timestamp and timestamp < window_start)
        after_window = bool(window_end is not None and timestamp and timestamp > window_end)
        if after_window:
            continue

        if kind == "turn_context":
            turn_index += 1
            if isinstance(payload.get("model"), str):
                current_model = payload["model"]
            if isinstance(payload.get("effort"), str):
                current_effort = payload["effort"]
            if before_window:
                active_profile_index = None
                continue
            if in_window(timestamp):
                active_profile_index = None
                ensure_profile(True)
            continue

        if before_window:
            if kind == "event_msg" and payload.get("type") == "token_count":
                value = token_value(payload)
                if value is not None:
                    previous_tokens = value
                    previous_token_timestamp = timestamp
            continue
        if not in_window(timestamp):
            continue

        if current_model is not None or current_effort is not None:
            ensure_profile(False)
        if kind != "event_msg":
            continue
        event_type = payload.get("type")
        if event_type != "token_count":
            continue
        current_tokens = token_value(payload)
        if current_tokens is None:
            continue
        token_snapshots += 1
        if window_end is not None and timestamp == window_end:
            token_at_window_end = True
        if window_start is not None and timestamp == window_start:
            previous_tokens = current_tokens
            previous_token_timestamp = timestamp
            exact_start_boundary = True
            continue
        if previous_tokens is None:
            if exact_start_boundary:
                add_delta(current_tokens)
            else:
                missing_start_boundary = True
                unknown_gaps += 1
            previous_tokens = current_tokens
            previous_token_timestamp = timestamp
            continue
        if (
            window_start is not None
            and previous_token_timestamp is not None
            and previous_token_timestamp < window_start
            and not exact_start_boundary
        ):
            missing_start_boundary = True
            unknown_gaps += 1
            previous_tokens = current_tokens
            previous_token_timestamp = timestamp
            continue
        reset_counters = [
            key for key in TOKEN_KEYS if current_tokens[key] < previous_tokens[key]
        ]
        if reset_counters:
            counter_epoch += 1
            reset_count += 1
            unknown_gaps += 1
        delta = {
            key: (
                current_tokens[key]
                if key in reset_counters
                else current_tokens[key] - previous_tokens[key]
            )
            for key in TOKEN_KEYS
        }
        add_delta(delta, reset_counters or None)
        previous_tokens = current_tokens
        previous_token_timestamp = timestamp

    end_boundary_partial = bool(
        window_end is not None
        and not token_at_window_end
        and not latest_turn_completed_in_window
    )
    if end_boundary_partial:
        unknown_gaps += 1
    known_tokens = bool(token_segments) or (token_snapshots > 0 and exact_start_boundary)
    partial = bool(reset_count or missing_start_boundary or end_boundary_partial)
    if not known_tokens and (token_snapshots == 0 or partial):
        coverage = "unavailable"
    elif partial:
        coverage = "partial_segmented"
    elif window_start is not None or window_end is not None:
        coverage = "exact_segmented"
    else:
        coverage = "segmented_cumulative"
    return {
        "profiles": profiles,
        "token_segments": token_segments,
        "token_usage": {key: totals[key] for key in TOKEN_KEYS},
        "token_snapshots": token_snapshots,
        "counter_resets": reset_count,
        "unknown_gaps": unknown_gaps,
        "values_known": known_tokens,
        "coverage": coverage,
        "start_boundary": (
            "session_start_or_counter_snapshot"
            if exact_start_boundary
            else "between_counter_snapshots"
        ),
        "end_boundary": (
            "counter_snapshot_or_completion"
            if not end_boundary_partial
            else "between_counter_snapshots"
        ),
    }


def analyze_session(
    session: dict[str, Any], include_coordination: bool,
    window_start: str | None = None, window_end: str | None = None,
) -> dict[str, Any]:
    events = session["events"]
    token_profiles = analyze_token_profiles(session, window_start, window_end)
    latest_turn = analyze_turn_lifecycle(session, window_end)
    calls: set[str] = set()
    call_methods: dict[str, set[str]] = {}
    agent_wait_calls: set[str] = set()
    agent_wait_order: list[str] = []
    execution_wait_calls: set[str] = set()
    wait_results: dict[str, bool | None] = {}
    wait_output_fingerprints: dict[str, str] = {}
    output_calls: set[str] = set()
    spawns: list[dict[str, str | None]] = []
    spawn_call_keys: set[str] = set()
    followup_call_keys: set[str] = set()
    timestamps: list[str] = []
    polling_streak = 0
    max_polling_streak = 0
    repeated_polling = 0
    polling_sequence: list[str] = []
    task_starts = 0
    task_completions = 0
    context_compactions = 0
    turn_aborts = 0
    plan_updates = 0
    current_turn = -1
    skills_seen_by_turn: dict[int, set[str]] = collections.defaultdict(set)
    skill_turns: dict[str, set[int]] = collections.defaultdict(set)
    skill_references: collections.Counter[str] = collections.Counter()
    repeated_skill_references: collections.Counter[str] = collections.Counter()
    user_turns = 0
    tool_input_chars = 0
    tool_output_chars = 0
    largest_tool_output_chars = 0
    large_text_tool_outputs = 0
    large_visual_tool_outputs = 0
    tool_methods: collections.Counter[str] = collections.Counter()

    for timestamp, line_number, kind, payload in events:
        in_window = bool(
            timestamp
            and (window_start is None or timestamp >= window_start)
            and (window_end is None or timestamp <= window_end)
        )
        if timestamp and in_window:
            timestamps.append(timestamp)
        if window_start is not None and timestamp and timestamp < window_start:
            continue
        if not in_window:
            continue
        if kind == "turn_context":
            current_turn += 1
        elif kind == "event_msg":
            event_type = payload.get("type")
            normalized_event = str(event_type or "").lower()
            if normalized_event in ("task_started", "task_start"):
                task_starts += 1
            if "compact" in normalized_event and "context" in normalized_event:
                context_compactions += 1
            if normalized_event in ("turn_aborted", "task_aborted"):
                turn_aborts += 1
            if event_type != "token_count":
                polling_streak = 0
                polling_sequence = []
            if event_type in ("task_complete", "turn_complete"):
                task_completions += 1
        elif kind == "response_item":
            item_type = payload.get("type")
            if item_type in ("function_call", "custom_tool_call"):
                call_id = payload.get("call_id")
                call_key = call_id if isinstance(call_id, str) else f"line:{line_number}"
                if call_key in calls:
                    continue
                calls.add(call_key)
                name = payload.get("name")
                normalized_name = str(name or "").rsplit(".", 1)[-1]
                arguments = argument_text(payload)
                tool_input_chars += len(arguments)
                nested_methods = NESTED_TOOL_CALL.findall(arguments)
                methods = set(nested_methods) if nested_methods else {normalized_name or "unknown"}
                call_methods[call_key] = methods
                if nested_methods:
                    tool_methods.update(nested_methods)
                else:
                    tool_methods[normalized_name or "unknown"] += 1
                if normalized_name == "wait":
                    execution_wait_calls.add(call_key)
                if is_plan_update(name, payload):
                    plan_updates += 1
                referenced_skills = skill_names_in_arguments(payload)
                for skill_name in referenced_skills:
                    skill_references[skill_name] += 1
                    skill_turns[skill_name].add(current_turn)
                    if skill_name in skills_seen_by_turn[current_turn]:
                        repeated_skill_references[skill_name] += 1
                    skills_seen_by_turn[current_turn].add(skill_name)
                if name in (
                    "wait_agent", "agents.wait_agent",
                    "list_agents", "agents.list_agents",
                ):
                    poll_kind = "wait" if "wait_agent" in str(name) else "list"
                    if poll_kind == "wait":
                        agent_wait_calls.add(call_key)
                        agent_wait_order.append(call_key)
                    polling_streak += 1
                    allowed = not polling_sequence or (
                        polling_sequence == ["wait"] and poll_kind == "list"
                    )
                    if not allowed:
                        repeated_polling += 1
                    polling_sequence.append(poll_kind)
                    max_polling_streak = max(max_polling_streak, polling_streak)
                else:
                    polling_streak = 0
                    polling_sequence = []
                if include_coordination and name in ("followup_task", "agents.followup_task"):
                    followup_call_keys.add(call_key)
                if include_coordination and name in ("spawn_agent", "agents.spawn_agent"):
                    spawn_call_keys.add(call_key)
                    args = parsed_arguments(payload)
                    task_name = args.get("task_name")
                    agent_type = args.get("agent_type")
                    if not isinstance(task_name, str) or not SAFE_ID.fullmatch(task_name):
                        task_fingerprint_value = None
                    else:
                        task_fingerprint_value = task_fingerprint(task_name)
                    if not isinstance(agent_type, str) or not SAFE_ID.fullmatch(agent_type):
                        delegation_fingerprint = None
                    elif task_fingerprint_value is None:
                        delegation_fingerprint = None
                    else:
                        delegation_fingerprint = task_fingerprint(f"{agent_type}:{task_name}")
                    spawns.append(
                        {
                            "task_fingerprint": task_fingerprint_value,
                            "delegation_fingerprint": delegation_fingerprint,
                            "agent_type": agent_type if isinstance(agent_type, str) else None,
                            "model": args.get("model") if isinstance(args.get("model"), str) else None,
                            "reasoning_effort": args.get("reasoning_effort") if isinstance(args.get("reasoning_effort"), str) else None,
                            "fork_turns": str(args.get("fork_turns", "default")),
                        }
                    )
            elif item_type in ("function_call_output", "custom_tool_call_output"):
                call_id = payload.get("call_id")
                size = output_length(payload)
                tool_output_chars += size
                largest_tool_output_chars = max(largest_tool_output_chars, size)
                if size > LARGE_TOOL_OUTPUT_CHARS:
                    methods = call_methods.get(str(call_id), set())
                    if visual_output(payload, methods):
                        large_visual_tool_outputs += 1
                    else:
                        large_text_tool_outputs += 1
                if isinstance(call_id, str):
                    output_calls.add(call_id)
                    wait_results[call_id] = output_timed_out(payload)
                    fingerprint = output_fingerprint(payload)
                    if fingerprint is not None:
                        wait_output_fingerprints[call_id] = fingerprint
            elif item_type == "message" and payload.get("role") == "user":
                user_turns += 1
        elif kind == "inter_agent_communication_metadata":
            polling_streak = 0
            polling_sequence = []

    agent_waits = {"completed": 0, "timed_out": 0, "pending": 0}
    for call_id in agent_wait_calls:
        if call_id not in wait_results or wait_results[call_id] is None:
            agent_waits["pending"] += 1
        elif wait_results[call_id]:
            agent_waits["timed_out"] += 1
        else:
            agent_waits["completed"] += 1

    execution_waits = {
        "calls": len(execution_wait_calls),
        "returned": len(execution_wait_calls & output_calls),
        "pending_result": len(execution_wait_calls - output_calls),
    }
    unchanged_wait_results = 0
    previous_wait_fingerprint = None
    for call_id in agent_wait_order:
        fingerprint = wait_output_fingerprints.get(call_id)
        if fingerprint is not None and fingerprint == previous_wait_fingerprint:
            unchanged_wait_results += 1
        if fingerprint is not None:
            previous_wait_fingerprint = fingerprint

    return {
        "profiles": token_profiles["profiles"],
        "token_segments": token_profiles["token_segments"],
        "segmented_token_usage": token_profiles["token_usage"],
        "token_snapshots": token_profiles["token_snapshots"],
        "token_counter_resets": token_profiles["counter_resets"],
        "token_unknown_gaps": token_profiles["unknown_gaps"],
        "token_values_known": token_profiles["values_known"],
        "token_coverage": token_profiles["coverage"],
        "token_start_boundary": token_profiles["start_boundary"],
        "token_end_boundary": token_profiles["end_boundary"],
        "completed": latest_turn["state"] == "completed",
        "latest_turn_state": latest_turn["state"],
        "tool_calls": len(calls),
        "tool_input_chars": tool_input_chars,
        "tool_output_chars": tool_output_chars,
        "largest_tool_output_chars": largest_tool_output_chars,
        "large_text_tool_outputs": large_text_tool_outputs,
        "large_visual_tool_outputs": large_visual_tool_outputs,
        "tool_methods": dict(tool_methods),
        "agent_waits": agent_waits,
        "execution_waits": execution_waits,
        "spawns": spawns,
        "followup_turns": len(followup_call_keys),
        "polling": {
            "repeated_calls": repeated_polling,
            "max_streak": max_polling_streak,
            "unchanged_wait_results": unchanged_wait_results,
        },
        "user_turns": user_turns,
        "task_starts": task_starts,
        "task_completions": task_completions,
        "context_compactions": context_compactions,
        "turn_aborts": turn_aborts,
        "plan_updates": plan_updates,
        "skill_references": dict(skill_references),
        "skill_reference_turns": {
            skill_name: len(turns) for skill_name, turns in skill_turns.items()
        },
        "repeated_skill_references": dict(repeated_skill_references),
        "repeated_skill_reference_turns": {
            skill_name: len(turns) - 1
            for skill_name, turns in skill_turns.items()
            if len(turns) > 1
        },
        "start": min(timestamps) if timestamps else None,
        "end": max(timestamps) if timestamps else None,
        "malformed": session["malformed"],
    }


def add_counter(counter: collections.Counter[str], value: str | None) -> None:
    counter[value or "unknown"] += 1


def clip_session(
    session: dict[str, Any], window_start: str | None, window_end: str | None
) -> dict[str, Any]:
    if window_start is None and window_end is None:
        return session
    events = [
        event
        for event in session["events"]
        if event[0]
        and (window_start is None or event[0] >= window_start)
        and (window_end is None or event[0] <= window_end)
    ]
    return {**session, "events": events}


def build_record(
    args: argparse.Namespace,
    sessions: dict[str, dict[str, Any]] | None = None,
    load_warnings: list[str] | None = None,
) -> dict[str, Any]:
    if sessions is None:
        sessions, warnings = load_sessions(args.sessions_dir)
    else:
        warnings = list(load_warnings or [])
    include_unbounded_tokens = bool(getattr(args, "include_unbounded_tokens", False))
    root = sessions.get(args.root_thread_id)
    if root is None:
        raise ValueError("root thread not found")
    descendants, cycle_skipped = descendant_tree(sessions, args.root_thread_id)
    if cycle_skipped:
        warnings.append("session_parent_cycle_skipped")
    bounded = args.window_start is not None or args.window_end is not None
    def meta_started_in_window(session: dict[str, Any]) -> bool:
        metas = [timestamp for timestamp, _, kind, _ in session["events"] if kind == "session_meta" and timestamp]
        return bool(metas and (args.window_start is None or metas[0] >= args.window_start)
                    and (args.window_end is None or metas[0] <= args.window_end))

    selected_descendants = [
        (session, depth)
        for session, depth in descendants
        if not bounded or any(
            timestamp
            and (args.window_start is None or timestamp >= args.window_start)
            and (args.window_end is None or timestamp <= args.window_end)
            for timestamp, _, _, _ in session["events"]
        )
    ]
    selected = [root, *(session for session, _ in selected_descendants)]
    children = selected[1:]
    child_depths = [depth for _, depth in selected_descendants]
    analyses = [
        analyze_session(session, True, args.window_start, args.window_end)
        for session in selected
    ]

    role_counts: collections.Counter[str] = collections.Counter()
    model_counts: collections.Counter[str] = collections.Counter()
    effort_counts: collections.Counter[str] = collections.Counter()
    model_effort_counts: collections.Counter[str] = collections.Counter()
    execution_profiles: list[dict[str, Any]] = []
    token_segments: list[dict[str, Any]] = []
    for index, (session, analysis) in enumerate(zip(selected, analyses)):
        role = "root" if index == 0 else session["meta"].get("agent_role")
        add_counter(role_counts, role if isinstance(role, str) else None)
        session_kind = "root" if index == 0 else "child"
        for profile in analysis["profiles"]:
            model_counts[profile["model"]] += 1
            effort_counts[profile["reasoning_effort"]] += 1
            model_effort_counts[
                f'{profile["model"]}|{profile["reasoning_effort"]}'
            ] += 1
            execution_profiles.append(
                {
                    "session_kind": session_kind,
                    "session_ordinal": index,
                    **profile,
                }
            )
        for segment in analysis["token_segments"]:
            token_segments.append(
                {
                    "session_kind": session_kind,
                    "session_ordinal": index,
                    **segment,
                }
            )

    token_totals: collections.Counter[str] = collections.Counter()
    missing_tokens = sum(analysis["token_snapshots"] == 0 for analysis in analyses)
    counter_resets = sum(analysis["token_counter_resets"] for analysis in analyses)
    token_unknown_gaps = sum(analysis["token_unknown_gaps"] for analysis in analyses)
    for analysis in analyses:
        add_token_values(token_totals, analysis["segmented_token_usage"])
    if missing_tokens:
        warnings.append("missing_token_count")
    if counter_resets:
        warnings.append("token_counter_reset_segmented")
    if any(
        analysis["token_start_boundary"] == "between_counter_snapshots"
        for analysis in analyses
    ):
        warnings.append("window_start_between_token_snapshots")
    if any(
        analysis["token_end_boundary"] == "between_counter_snapshots"
        for analysis in analyses
    ):
        warnings.append("window_end_between_token_snapshots")

    root_spawns = analyses[0]["spawns"]
    spawns = [spawn for analysis in analyses for spawn in analysis["spawns"]]
    spawn_calls = len(spawns)
    successful_child_sessions = sum(1 for session in children if meta_started_in_window(session)) if bounded else len(children)
    followup_turns = sum(analysis["followup_turns"] for analysis in analyses)
    fork_counts: collections.Counter[str] = collections.Counter(spawn["fork_turns"] for spawn in spawns)
    task_counts: collections.Counter[str] = collections.Counter(
        spawn["task_fingerprint"] for spawn in spawns if spawn["task_fingerprint"] is not None
    )
    delegation_counts: collections.Counter[str] = collections.Counter(
        spawn["delegation_fingerprint"]
        for spawn in spawns
        if spawn["delegation_fingerprint"] is not None
    )
    if any(spawn["task_fingerprint"] is None for spawn in spawns):
        warnings.append("invalid_task_name_redacted")
    if spawns:
        warnings.append("task_name_fingerprint_is_proxy")

    agent_waits = collections.Counter()
    execution_waits = collections.Counter()
    polling = collections.Counter()
    skill_references: collections.Counter[str] = collections.Counter()
    skill_reference_turns: collections.Counter[str] = collections.Counter()
    repeated_skill_references: collections.Counter[str] = collections.Counter()
    repeated_skill_reference_turns: collections.Counter[str] = collections.Counter()
    tool_methods: collections.Counter[str] = collections.Counter()
    for analysis in analyses:
        agent_waits.update(analysis["agent_waits"])
        execution_waits.update(analysis["execution_waits"])
        polling.update(analysis["polling"])
        skill_references.update(analysis["skill_references"])
        skill_reference_turns.update(analysis["skill_reference_turns"])
        repeated_skill_references.update(analysis["repeated_skill_references"])
        repeated_skill_reference_turns.update(analysis["repeated_skill_reference_turns"])
        tool_methods.update(analysis["tool_methods"])
    wait_observed = agent_waits["completed"] + agent_waits["timed_out"]
    wait_timeout_ratio = agent_waits["timed_out"] / wait_observed if wait_observed else None
    wait_timeout_alert = bool(
        wait_timeout_ratio is not None
        and agent_waits["timed_out"] > 0
        and wait_timeout_ratio >= args.wait_timeout_alert_ratio
        and polling["unchanged_wait_results"] > 0
    )
    starts = [analysis["start"] for analysis in analyses if analysis["start"]]
    ends = [analysis["end"] for analysis in analyses if analysis["end"]]
    user_turns = sum(analysis["user_turns"] for analysis in analyses)
    plan_updates = sum(analysis["plan_updates"] for analysis in analyses)
    plan_milestones = getattr(args, "plan_milestones", None)
    plan_update_alert_ratio = getattr(args, "plan_update_alert_ratio", 2.0)
    plan_updates_per_milestone = (
        plan_updates / plan_milestones if plan_milestones else None
    )
    plan_update_alert = bool(
        bounded
        and plan_updates_per_milestone is not None
        and plan_updates_per_milestone > plan_update_alert_ratio
    )
    integration_closeout = getattr(args, "integration_closeout", None)
    default_integration_branch = getattr(args, "integration_branch", None)
    repo_closeouts = []
    missing_repo_branches = 0
    for closeout in getattr(args, "repo_closeout", []):
        if len(closeout) == 3:
            project, branch, sha = closeout
        else:
            project, sha = closeout
            branch = default_integration_branch
        evidence = {"project": project, "integration_sha": sha}
        if branch is not None:
            evidence["integration_branch"] = branch
        else:
            missing_repo_branches += 1
        repo_closeouts.append(evidence)
    release_operator_sessions = role_counts["release_operator"]
    release_tuple_complete = bool(
        bounded and args.project_slug and args.baseline and args.release_target
    )
    release_operator_reuse_alert = bool(
        release_tuple_complete and release_operator_sessions > 1
    )
    roles_by_session = {
        str(session["meta"].get("id")): session["meta"].get("agent_role")
        for session in sessions.values()
    }
    nested_release_operator_sessions = sum(
        1
        for session in children
        if session["meta"].get("agent_role") == "release_operator"
        and roles_by_session.get(str(direct_parent(session["meta"]))) == "release_operator"
    )
    tool_output_chars = sum(analysis["tool_output_chars"] for analysis in analyses)
    large_text_tool_outputs = sum(
        analysis["large_text_tool_outputs"] for analysis in analyses
    )
    large_visual_tool_outputs = sum(
        analysis["large_visual_tool_outputs"] for analysis in analyses
    )
    tool_output_volume_alert = large_text_tool_outputs > 0
    xhigh_evidence = bool(getattr(args, "xhigh_evidence", False))

    semantic = {
        "source": "operator_supplied",
        "objective_id": args.objective_id,
        "workflow_mode": args.workflow_mode,
        "project_slug": args.project_slug,
        "host_id": getattr(args, "host_id", None),
        "classification": args.classification,
        "outcome": args.outcome,
        "integration_closeout": integration_closeout,
        "integration_branch": default_integration_branch,
        "release_target": args.release_target,
        "docs_sync": getattr(args, "docs_sync", None),
        "external_state": getattr(args, "external_state", None),
        "contract_version": getattr(args, "contract_version", None),
        "xhigh_evidence": xhigh_evidence,
        "repository_closeouts": repo_closeouts,
    }
    for field in SEMANTIC_COUNTERS:
        semantic[field] = getattr(args, field)
    outcome_metrics: dict[str, Any] = {}
    acceptance_at_first_pass = getattr(args, "acceptance_at_first_pass", None)
    if acceptance_at_first_pass is not None:
        outcome_metrics["acceptance_at_first_pass"] = acceptance_at_first_pass == "yes"
    human_corrections = getattr(args, "human_corrections", None)
    if human_corrections is not None:
        outcome_metrics["human_corrections"] = human_corrections
    human_intervention_minutes = getattr(args, "human_intervention_minutes", None)
    if human_intervention_minutes is not None:
        outcome_metrics["human_intervention_minutes"] = human_intervention_minutes
    if outcome_metrics:
        semantic["outcome_metrics"] = {
            "source": "operator_supplied",
            **outcome_metrics,
        }

    snapshot_end = max(ends) if ends else None
    contract_changed_at = getattr(args, "contract_changed_at", None)
    root_started_at = session_start(root)
    if contract_changed_at is None:
        contract_state = "unknown"
    elif (
        root_started_at is not None
        and root_started_at < contract_changed_at
        and snapshot_end is not None
        and snapshot_end >= contract_changed_at
    ):
        contract_state = "stale_contract"
    elif root_started_at is not None and root_started_at >= contract_changed_at:
        contract_state = "current"
    else:
        contract_state = "unknown"
    snapshot_ref = snapshot_reference(args.snapshot_kind, args.sequence)
    coverage_values = {analysis["token_coverage"] for analysis in analyses}
    known_segmented_tokens = any(analysis["token_values_known"] for analysis in analyses)
    if not bounded and not include_unbounded_tokens:
        token_coverage = "cumulative_totals_suppressed"
        warnings.append("unbounded_token_totals_suppressed")
    elif "unavailable" in coverage_values:
        token_coverage = "partial_segmented" if known_segmented_tokens else "unavailable"
    elif "partial_segmented" in coverage_values:
        token_coverage = "partial_segmented"
    elif bounded:
        token_coverage = "exact_segmented"
    elif include_unbounded_tokens:
        token_coverage = "segmented_cumulative"
    else:
        token_coverage = "segmented_cumulative"
    tokens = {
        "semantics": "processed_session_telemetry_not_billing_or_cost",
        "mode": "bounded" if bounded else "full_session",
        "coverage": token_coverage,
        "attribution_basis": "turn_context_model_effort_and_counter_epoch",
        "counter_resets": counter_resets,
        "unknown_gaps": token_unknown_gaps,
    }
    if (bounded or include_unbounded_tokens) and known_segmented_tokens:
        profile_totals: dict[tuple[str, str], collections.Counter[str]] = {}
        profile_turns: dict[tuple[str, str], set[tuple[int, int]]] = collections.defaultdict(set)
        for profile in execution_profiles:
            key = (profile["model"], profile["reasoning_effort"])
            profile_turns[key].add((profile["session_ordinal"], profile["turn"]))
        for segment in token_segments:
            key = (segment["model"], segment["reasoning_effort"])
            profile_totals.setdefault(key, collections.Counter())
            add_token_values(profile_totals[key], segment)
        by_model_effort = [
            {
                "model": model,
                "reasoning_effort": effort,
                "turns": len(profile_turns[(model, effort)]),
                **{
                    key: profile_totals.get((model, effort), collections.Counter())[key]
                    for key in TOKEN_KEYS
                },
            }
            for model, effort in sorted(profile_turns)
        ]
        tokens = {
            **{key: token_totals[key] for key in TOKEN_KEYS},
            **tokens,
            "segments": token_segments,
            "by_model_effort": by_model_effort,
        }
    if args.workflow_mode is None or args.objective_id is None:
        warnings.append("objective_or_workflow_mode_missing")
    if args.workflow_mode == "implementation" and integration_closeout in (None, "missing"):
        warnings.append("implementation_integration_closeout_missing")
    if (
        args.workflow_mode == "implementation"
        and integration_closeout in PENDING_INTEGRATION_CLOSEOUTS
    ):
        warnings.append("implementation_candidate_pending")
        if args.snapshot_kind == "final" and args.outcome in {"accepted", "released_verified"}:
            warnings.append("pending_candidate_with_terminal_outcome")
    if (
        args.workflow_mode == "implementation"
        and integration_closeout == "verified"
        and not repo_closeouts
    ):
        warnings.append("verified_integration_closeout_without_repository_evidence")
    if missing_repo_branches:
        warnings.append("repository_closeout_integration_branch_missing")
    if args.workflow_mode == "release" and args.release_target is None:
        warnings.append("release_target_missing")
    if release_operator_reuse_alert:
        warnings.append("multiple_release_operators_for_same_bounded_tuple")
    if nested_release_operator_sessions:
        warnings.append("release_operator_nested")
    if tool_output_volume_alert:
        warnings.append("large_text_tool_output_in_context")
    if contract_state == "stale_contract":
        warnings.append("stale_workflow_contract")
    if any(
        profile["reasoning_effort"] == "xhigh" for profile in execution_profiles
    ) and not xhigh_evidence:
        warnings.append("xhigh_without_evaluation_evidence")
    if not bounded and user_turns > 1:
        warnings.append("unbounded_multi_turn_scope")
    if plan_update_alert:
        warnings.append("plan_updates_exceed_milestone_budget")
    unique_skill_loads = {
        skill_name: 1 for skill_name in sorted(skill_references)
    }
    latest_turn_states = collections.Counter(
        analysis["latest_turn_state"] for analysis in analyses
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": snapshot_end or utc_now(),
        "cycle_id": args.cycle_id,
        "root_thread_id": args.root_thread_id,
        "cycle_root": args.root_thread_id,
        "snapshot_kind": args.snapshot_kind,
        "sequence": args.sequence,
        "snapshot_id": snapshot_ref,
        "baseline": args.baseline,
        "supersedes": args.supersedes,
        "snapshot_start": min(starts) if starts else None,
        "snapshot_end": snapshot_end,
        "window": {
            "start": args.window_start, "end": args.window_end,
            "mode": "bounded" if bounded else "full_session",
            "coverage": token_coverage,
        },
        "scope": {
            "user_turns": user_turns,
            "bounded": bounded,
            "comparison_reliability": (
                "explicit_window"
                if bounded
                else "single_turn"
                if user_turns <= 1
                else "multi_turn_unbounded"
            ),
        },
        "semantic_summary": semantic,
        "execution_profiles": {
            "basis": "effective_turn_contexts_with_carried_window_context",
            "segments": execution_profiles,
        },
        "contract": {
            "version": getattr(args, "contract_version", None),
            "changed_at": contract_changed_at,
            "root_started_at": root_started_at,
            "state": contract_state,
        },
        "sessions": {
            "root": 1,
            "children": len(children),
            "direct_children": sum(1 for depth in child_depths if depth == 1),
            "max_depth": max(child_depths, default=0),
            "complete": sum(1 for analysis in analyses if analysis["completed"]),
            "incomplete": sum(1 for analysis in analyses if not analysis["completed"]),
            "completion_basis": "latest_identified_runtime_turn",
            "latest_turn_states": dict(sorted(latest_turn_states.items())),
            "malformed_lines_skipped": sum(analysis["malformed"] for analysis in analyses),
        },
        "distributions": {
            "profile_basis": "turn_segments",
            "roles": dict(sorted(role_counts.items())),
            "models": dict(sorted(model_counts.items())),
            "reasoning_efforts": dict(sorted(effort_counts.items())),
            "model_effort": dict(sorted(model_effort_counts.items())),
            "fork_turns": dict(sorted(fork_counts.items())),
        },
        "spawns": {
            "total": len(spawns),
            "root_total": len(root_spawns),
            "task_name_fingerprints": sorted(task_counts),
            "duplicate_task_name_fingerprints": sorted(name for name, count in task_counts.items() if count > 1),
            "fingerprint_basis": "task_name_proxy",
            "delegation_fingerprints": sorted(delegation_counts),
            "duplicate_delegation_fingerprints": sorted(
                name for name, count in delegation_counts.items() if count > 1
            ),
            "delegation_fingerprint_basis": "agent_type_and_task_name_proxy",
            "semantic_fingerprint_available": False,
            "retry_count": args.retries if args.retries is not None else "unknown",
        },
        "runtime": {
            "tool_calls": sum(analysis["tool_calls"] for analysis in analyses),
            "tool_input_chars": sum(analysis["tool_input_chars"] for analysis in analyses),
            "tool_output_chars": tool_output_chars,
            "largest_tool_output_chars": max(
                (analysis["largest_tool_output_chars"] for analysis in analyses),
                default=0,
            ),
            "text_tool_outputs_over_10000_chars": large_text_tool_outputs,
            "visual_tool_outputs_over_10000_chars": large_visual_tool_outputs,
            "tool_output_volume_alert": tool_output_volume_alert,
            "tool_methods": dict(sorted(tool_methods.items())),
            "task_starts": sum(analysis["task_starts"] for analysis in analyses),
            "task_completions": sum(analysis["task_completions"] for analysis in analyses),
            "context_compactions": sum(analysis["context_compactions"] for analysis in analyses),
            "turn_aborts": sum(analysis["turn_aborts"] for analysis in analyses),
            "plan_updates": plan_updates,
            "plan": {
                "updates": plan_updates,
                "milestones": plan_milestones,
                "updates_per_milestone": plan_updates_per_milestone,
                "alert_ratio": plan_update_alert_ratio,
                "alert": plan_update_alert,
            },
            "agent_waits": {
                **dict(sorted(agent_waits.items())),
                "timeout_ratio": wait_timeout_ratio,
                "timeout_alert": wait_timeout_alert,
                "alert_threshold": args.wait_timeout_alert_ratio,
            },
            "execution_waits": dict(sorted(execution_waits.items())),
            "skill_file_read_calls": dict(sorted(skill_references.items())),
            "skill_objective_loads": unique_skill_loads,
            "skill_read_turns": dict(sorted(skill_reference_turns.items())),
            "skill_extra_reads_same_turn": dict(sorted(repeated_skill_references.items())),
            "skill_reload_turns": dict(sorted(repeated_skill_reference_turns.items())),
            "skill_reload_alert": bool(repeated_skill_reference_turns),
        },
        "coordination": {
            "spawn_calls": spawn_calls,
            "successful_child_sessions": successful_child_sessions,
            "followup_turns": followup_turns,
            "delegated_invocations": spawn_calls + followup_turns,
            "duplicate_prevented": args.duplicate_prevented,
            "reuse": args.reuse,
            "replacement_reason": args.replacement_reason,
            "release_operator_sessions": release_operator_sessions,
            "release_operator_reuse_alert": release_operator_reuse_alert,
            "release_tuple_complete": release_tuple_complete,
            "nested_release_operator_sessions": nested_release_operator_sessions,
        },
        "polling": {
            "repeated_calls": polling["repeated_calls"],
            "max_streak": max((analysis["polling"]["max_streak"] for analysis in analyses), default=0),
            "unchanged_wait_results": polling["unchanged_wait_results"],
            "alert": (
                polling["unchanged_wait_results"] > 0
                or (
                    polling["repeated_calls"] >= 2
                    and max(
                        (analysis["polling"]["max_streak"] for analysis in analyses),
                        default=0,
                    ) >= 4
                )
            ),
        },
        "tokens": tokens,
        "warnings": sorted(set(warnings)),
    }


def reject_symlink(path: Path, label: str) -> None:
    try:
        mode = path.lstat().st_mode
    except FileNotFoundError:
        return
    if stat.S_ISLNK(mode):
        raise ValueError(f"{label} must not be a symlink")


def record_identity(record: dict[str, Any]) -> tuple[Any, ...]:
    if record.get("snapshot_kind") in SNAPSHOT_KINDS and isinstance(record.get("sequence"), int):
        return (
            "snapshot",
            record.get("cycle_id"),
            record.get("cycle_root", record.get("root_thread_id")),
            record.get("snapshot_kind"),
            record.get("sequence"),
        )
    return (
        "legacy",
        record.get("cycle_id"),
        record.get("root_thread_id"),
        record.get("snapshot_end"),
    )


def read_registry(path: Path) -> tuple[list[str], dict[tuple[Any, ...], dict[str, Any]]]:
    lines: list[str] = []
    records: dict[tuple[Any, ...], dict[str, Any]] = {}
    if not path.exists():
        return lines, records
    with path.open("r", encoding="utf-8") as handle:
        for number, line in enumerate(handle, 1):
            if not line.strip():
                raise ValueError(f"registry contains blank line {number}")
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"registry contains corrupt JSON at line {number}") from exc
            if not isinstance(record, dict):
                raise ValueError(f"registry line {number} is not an object")
            if record.get("schema_version") not in SUPPORTED_SCHEMA_VERSIONS:
                raise ValueError(f"registry line {number} has unsupported schema version")
            key = record_identity(record)
            if key in records and records[key] != record:
                raise ValueError(f"registry has conflicting duplicate key at line {number}")
            records[key] = record
            lines.append(json.dumps(record, sort_keys=True, separators=(",", ":")))
    return lines, records


def append_record(path: Path, record: dict[str, Any]) -> str:
    path = path.expanduser()
    directory = path.parent
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    os.chmod(directory, 0o700)
    lock_path = directory / f".{path.name}.lock"
    reject_symlink(path, "telemetry file")
    reject_symlink(lock_path, "lock file")
    lock_fd = os.open(lock_path, os.O_CREAT | os.O_RDWR, 0o600)
    os.fchmod(lock_fd, 0o600)
    try:
        with os.fdopen(lock_fd, "r+") as lock_handle:
            fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX)
            reject_symlink(path, "telemetry file")
            lines, records = read_registry(path)
            key = record_identity(record)
            existing = records.get(key)
            if existing is not None:
                if existing == record:
                    return "no-op"
                raise ValueError("registry key conflict: existing payload differs")
            root = record.get("cycle_root", record.get("root_thread_id"))
            sequence = record.get("sequence")
            prior_sequences = [
                prior.get("sequence")
                for prior in records.values()
                if prior.get("cycle_id") == record.get("cycle_id")
                and prior.get("cycle_root", prior.get("root_thread_id")) == root
                and isinstance(prior.get("sequence"), int)
            ]
            if isinstance(sequence, int) and prior_sequences and sequence <= max(prior_sequences):
                raise ValueError("snapshot sequence must increase within the cycle root")
            supersedes = record.get("supersedes")
            if supersedes is not None:
                if record.get("replacement_reason") is None and record.get("coordination", {}).get("replacement_reason") is None:
                    raise ValueError("supersedes requires replacement_reason")
                target_kind, target_sequence = parse_snapshot_reference(supersedes)
                target_key = (
                    "snapshot",
                    record.get("cycle_id"),
                    root,
                    target_kind,
                    target_sequence,
                )
                if target_key == key:
                    raise ValueError("snapshot cannot supersede itself")
                if target_key not in records:
                    raise ValueError("superseded snapshot does not exist in this cycle root")
                for prior in records.values():
                    if (
                        prior.get("cycle_id") == record.get("cycle_id")
                        and prior.get("cycle_root", prior.get("root_thread_id")) == root
                        and prior.get("supersedes") == supersedes
                    ):
                        raise ValueError("superseded snapshot already has a replacement")
            lines.append(json.dumps(record, sort_keys=True, separators=(",", ":")))
            fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=directory)
            try:
                os.fchmod(fd, 0o600)
                with os.fdopen(fd, "w", encoding="utf-8") as handle:
                    handle.write("\n".join(lines) + "\n")
                    handle.flush()
                    os.fsync(handle.fileno())
                os.replace(temporary, path)
                os.chmod(path, 0o600)
                dir_fd = os.open(directory, os.O_RDONLY)
                try:
                    os.fsync(dir_fd)
                finally:
                    os.close(dir_fd)
            finally:
                if os.path.exists(temporary):
                    os.unlink(temporary)
            return "appended"
    except Exception:
        if not os.path.exists(lock_path):
            pass
        raise


def nonnegative(value: str) -> int:
    parsed = int(value)
    if parsed < 0:
        raise argparse.ArgumentTypeError("must be non-negative")
    return parsed


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root-thread-id",
        dest="root_thread_ids",
        action="append",
        required=True,
        help="root thread to analyze; repeat to reuse one session scan for a batch",
    )
    parser.add_argument("--cycle-id", required=True)
    parser.add_argument("--sessions-dir", type=Path, default=Path.home() / ".codex" / "sessions")
    parser.add_argument("--append", action="store_true")
    parser.add_argument("--telemetry-file", type=Path, default=Path.home() / ".codex" / "telemetry" / "dautia-cycles.jsonl")
    parser.add_argument("--project-slug")
    parser.add_argument("--objective-id")
    parser.add_argument("--workflow-mode", choices=WORKFLOW_MODES)
    parser.add_argument("--classification", choices=CLASSIFICATIONS)
    parser.add_argument("--outcome", choices=OUTCOMES)
    parser.add_argument(
        "--integration-closeout",
        dest="integration_closeout",
        choices=INTEGRATION_CLOSEOUTS,
        help="implementation closeout against the project's effective integration branch",
    )
    parser.add_argument(
        "--integration-branch",
        help="effective integration branch for a single-repository closeout",
    )
    parser.add_argument("--host-id", help="privacy-safe operator label for the host being measured")
    parser.add_argument("--release-target")
    parser.add_argument(
        "--contract-version",
        help="short version or fingerprint of the workflow contract loaded for comparison",
    )
    parser.add_argument(
        "--contract-changed-at",
        type=iso_timestamp,
        help="workflow-contract change time used to flag roots that continued from an older snapshot",
    )
    parser.add_argument(
        "--repo-closeout",
        action="append",
        default=[],
        type=repo_closeout,
        metavar="PROJECT=INTEGRATION_BRANCH@SHA",
        help="repeat for each affected repository integrated and pushed to its effective branch",
    )
    parser.add_argument("--docs-sync", choices=DOC_SYNC_STATES)
    parser.add_argument("--external-state", choices=EXTERNAL_STATES)
    parser.add_argument("--acceptance-at-first-pass", choices=("yes", "no"))
    parser.add_argument("--human-corrections", type=nonnegative)
    parser.add_argument("--human-intervention-minutes", type=nonnegative_float)
    parser.add_argument("--plan-milestones", type=positive)
    parser.add_argument("--plan-update-alert-ratio", type=positive_float, default=2.0)
    parser.add_argument(
        "--xhigh-evidence",
        action="store_true",
        help="confirm representative evaluation evidence justified xhigh reasoning",
    )
    parser.add_argument("--snapshot-kind", choices=SNAPSHOT_KINDS, default="final")
    parser.add_argument("--sequence", type=positive, default=1)
    parser.add_argument("--baseline")
    parser.add_argument("--supersedes")
    parser.add_argument("--window-start", type=iso_timestamp)
    parser.add_argument("--window-end", type=iso_timestamp)
    parser.add_argument(
        "--include-unbounded-tokens", action="store_true",
        help="include segmented cumulative token telemetry for an unbounded session",
    )
    parser.add_argument("--wait-timeout-alert-ratio", type=ratio, default=0.5)
    parser.add_argument("--duplicate-prevented", type=nonnegative)
    parser.add_argument("--reuse", type=nonnegative)
    parser.add_argument("--replacement-reason", choices=REPLACEMENT_REASONS)
    for field in SEMANTIC_COUNTERS:
        parser.add_argument(f"--{field.replace('_', '-')}", dest=field, type=nonnegative)
    args = parser.parse_args(argv)
    try:
        args.cycle_id = safe_identifier(args.cycle_id, "cycle-id")
        for root_thread_id in args.root_thread_ids:
            if not UUID_LIKE.fullmatch(root_thread_id):
                raise ValueError("root-thread-id is not UUID-like")
        args.root_thread_id = args.root_thread_ids[0]
        if args.project_slug is not None:
            args.project_slug = safe_identifier(args.project_slug, "project-slug")
        if args.host_id is not None:
            args.host_id = safe_identifier(args.host_id, "host-id")
        if args.objective_id is not None:
            args.objective_id = safe_identifier(args.objective_id, "objective-id")
        if args.release_target is not None:
            args.release_target = safe_identifier(args.release_target, "release-target")
        if args.integration_branch is not None and not GIT_BRANCH.fullmatch(args.integration_branch):
            raise ValueError("integration-branch is not a safe Git branch name")
        if args.contract_version is not None:
            args.contract_version = safe_identifier(args.contract_version, "contract-version")
        if args.baseline is not None:
            args.baseline = safe_identifier(args.baseline, "baseline")
        if args.supersedes is not None:
            parse_snapshot_reference(args.supersedes)
        if args.window_start and args.window_end and args.window_start > args.window_end:
            raise ValueError("window-start must not be after window-end")
        if args.replacement_reason is not None and args.supersedes is None:
            raise ValueError("replacement-reason requires supersedes")
        if args.supersedes is not None and args.replacement_reason is None:
            raise ValueError("supersedes requires replacement-reason")
    except ValueError as exc:
        parser.error(str(exc))
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        sessions, load_warnings = load_sessions(args.sessions_dir)
        records = []
        statuses = []
        for root_thread_id in args.root_thread_ids:
            current = argparse.Namespace(**vars(args))
            current.root_thread_id = root_thread_id
            record = build_record(current, sessions, load_warnings)
            records.append(record)
            statuses.append(
                append_record(args.telemetry_file, record) if args.append else "stdout-only"
            )
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    payload: dict[str, Any] | list[dict[str, Any]] = records[0] if len(records) == 1 else records
    print(json.dumps(payload, indent=2, sort_keys=True))
    if len(statuses) == 1:
        print(f"telemetry_status={statuses[0]}", file=sys.stderr)
    else:
        counts = collections.Counter(statuses)
        summary = ",".join(f"{status}:{counts[status]}" for status in sorted(counts))
        print(f"telemetry_status=batch({summary})", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
