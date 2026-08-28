#!/usr/bin/env python3
"""Validate DautIA objective terminality independently from Codex runtime state."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any


OBJECTIVE_STATES = {"RUNNING", "WAITING_EXTERNAL", "VERIFYING", "COMPLETE", "BLOCKED", "FAILED"}
RUNTIME_STATES = {"running", "task_complete", "interrupted"}
DEPENDENCY_STATES = {"pending", "running", "success", "failed", "unknown"}
ACTIVE_STATES = {"pending", "running"}


def nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def validate(ledger: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    objective = ledger.get("objective_state")
    runtime = ledger.get("runtime_state")
    if objective not in OBJECTIVE_STATES:
        errors.append("invalid_objective_state")
    if runtime not in RUNTIME_STATES:
        errors.append("invalid_runtime_state")

    target = ledger.get("target")
    if not isinstance(target, dict):
        target = {}
    target_sha = target.get("sha")
    target_environment = target.get("environment")
    dependencies = ledger.get("dependencies")
    if not isinstance(dependencies, list):
        errors.append("dependencies_must_be_list")
        dependencies = []

    required: list[dict[str, Any]] = []
    for index, dependency in enumerate(dependencies):
        if not isinstance(dependency, dict):
            errors.append(f"dependency_{index}_invalid")
            continue
        if not dependency.get("required", True):
            continue
        required.append(dependency)
        for field in ("provider", "run_id", "sha", "environment", "state", "success_condition", "failure_condition", "next_action"):
            if not nonempty(dependency.get(field)):
                errors.append(f"dependency_{index}_missing_{field}")
        if dependency.get("state") not in DEPENDENCY_STATES:
            errors.append(f"dependency_{index}_invalid_state")
        if nonempty(target_sha) and dependency.get("sha") != target_sha:
            errors.append(f"dependency_{index}_sha_mismatch")
        if nonempty(target_environment) and dependency.get("environment") != target_environment:
            errors.append(f"dependency_{index}_environment_mismatch")

    active = [dependency for dependency in required if dependency.get("state") in ACTIVE_STATES]
    failed_or_unknown = [dependency for dependency in required if dependency.get("state") in {"failed", "unknown"}]
    successful = [dependency for dependency in required if dependency.get("state") == "success"]

    if required and objective in {"WAITING_EXTERNAL", "VERIFYING", "COMPLETE"}:
        if not nonempty(target_sha):
            errors.append("missing_target_sha")
        if not nonempty(target_environment):
            errors.append("missing_target_environment")

    if objective == "WAITING_EXTERNAL":
        if not active:
            errors.append("waiting_external_requires_active_dependency")
        if failed_or_unknown:
            errors.append("waiting_external_has_failed_or_unknown_dependency")
        for index, dependency in enumerate(required):
            if dependency.get("state") in ACTIVE_STATES:
                if not nonempty(dependency.get("monitor_id")):
                    errors.append(f"active_dependency_{index}_missing_monitor_id")
                if not nonempty(dependency.get("next_check_at")):
                    errors.append(f"active_dependency_{index}_missing_next_check_at")
                if dependency.get("monitor_confirmed") is not True:
                    errors.append(f"active_dependency_{index}_monitor_not_confirmed")
                if dependency.get("monitor_kind") != "heartbeat":
                    errors.append(f"active_dependency_{index}_monitor_not_heartbeat")
                if not nonempty(ledger.get("root_thread_id")):
                    errors.append("waiting_external_missing_root_thread_id")
                elif dependency.get("monitor_target_thread_id") != ledger.get("root_thread_id"):
                    errors.append(f"active_dependency_{index}_monitor_thread_mismatch")

    if objective == "VERIFYING":
        if active or failed_or_unknown:
            errors.append("verifying_requires_all_dependencies_successful")
        if len(successful) != len(required):
            errors.append("verifying_requires_all_dependencies_successful")

    if objective == "COMPLETE":
        if active:
            errors.append("complete_has_active_dependency")
        if failed_or_unknown:
            errors.append("complete_has_failed_or_unknown_dependency")
        if len(successful) != len(required):
            errors.append("complete_requires_all_dependencies_successful")
        if ledger.get("verification_complete") is not True:
            errors.append("complete_requires_final_verification")

    if objective == "FAILED" and not nonempty(ledger.get("reason_code")):
        errors.append("failed_requires_reason_code")

    if objective == "BLOCKED":
        if not nonempty(ledger.get("reason_code")):
            errors.append("blocked_requires_reason_code")
        if not isinstance(ledger.get("goal_runtime_active"), bool):
            errors.append("blocked_requires_explicit_goal_runtime_state")
        elif ledger.get("goal_runtime_active") is True and ledger.get("goal_blocked_threshold_satisfied") is not True:
            errors.append("blocked_goal_threshold_not_satisfied")

    return sorted(set(errors))


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ledger", nargs="?", type=Path, help="JSON ledger path; stdin when omitted")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        raw = args.ledger.read_text(encoding="utf-8") if args.ledger else sys.stdin.read()
        ledger = json.loads(raw)
    except (OSError, json.JSONDecodeError) as exc:
        print(json.dumps({"valid": False, "errors": ["invalid_json"], "detail": str(exc)}))
        return 2
    if not isinstance(ledger, dict):
        print(json.dumps({"valid": False, "errors": ["ledger_must_be_object"]}))
        return 2
    errors = validate(ledger)
    print(json.dumps({"valid": not errors, "objective_state": ledger.get("objective_state"), "runtime_state": ledger.get("runtime_state"), "errors": errors}, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
