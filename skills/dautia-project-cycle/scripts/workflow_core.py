#!/usr/bin/env python3
"""R3 packet-consistency checks. No model, tool execution or permission granting.

The principal extracts requirements and supplies evidence. This module detects
structural conflicts, stale identities and incomplete closure; it cannot prove
semantic understanding or authenticate user statements from a JSON field.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
from pathlib import Path
from typing import Any

from evidence_contract import validate_evidence, validate_project_context

IDENTIFIER = re.compile(r"^[A-Za-z0-9_.:-]{1,120}$")
OPERATIONS = {"read", "capture_docs", "write_artifact", "write_product", "write_tests", "git_write", "external_mutation"}
MODES = {"DISCOVERY", "AUDIT", "IMPLEMENTATION", "RELEASE"}
READ_ROLES = {"code_explorer", "documental", "product_discovery", "systems_analyst", "ux_auditor", "independent_reviewer", "decision_gate", "data_security", "qa_web", "qa_ios", "qa_android", "qa_e2e"}
WRITE_ROLES = {"implementer", "implementer_complex", "systems_implementer", "release_operator", "principal"}
ROOT = Path(__file__).resolve().parents[1]


class ContractError(ValueError):
    """Public reason codes only; never include payloads or private paths."""


def canonical(value: Any) -> bytes:
    try:
        return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    except (TypeError, ValueError, RecursionError) as exc:
        raise ContractError("non_canonical_data") from exc


def fingerprint(value: Any) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def load_json(data: bytes | str) -> Any:
    def unique(pairs: list[tuple[str, Any]]) -> dict:
        out: dict = {}
        for key, val in pairs:
            if key in out:
                raise ContractError("duplicate_json_key")
            out[key] = val
        return out
    try:
        return json.loads(data, object_pairs_hook=unique,
                          parse_constant=lambda _: (_ for _ in ()).throw(ContractError("nonfinite_json")))
    except (ValueError, UnicodeError, RecursionError) as exc:
        if isinstance(exc, ContractError):
            raise
        raise ContractError("invalid_json") from exc


def nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def records(obj: dict, field: str) -> list[dict]:
    value = obj.get(field, [])
    if not isinstance(value, list) or any(not isinstance(v, dict) for v in value):
        raise ContractError("invalid_list_" + field)
    ids = [v.get("evidence_id", v.get("id")) if field == "evidence" else v.get("id") for v in value]
    if any(not isinstance(v, str) or not IDENTIFIER.fullmatch(v) for v in ids) or len(set(ids)) != len(ids):
        raise ContractError("invalid_ids_" + field)
    return value


def refs(value: Any) -> bool:
    return isinstance(value, list) and bool(value) and all(nonempty(x) for x in value)


def policy() -> dict:
    return load_json((ROOT / "config/routing-policy.json").read_bytes())


def role_default(role: str, rules: dict | None = None) -> str:
    rules = rules or policy()
    return rules.get("role_defaults", {}).get(role, rules["default_profile"])


def role_profiles(role: str, rules: dict | None = None) -> list[str]:
    """Finite renderable profiles. The effect gate still owns operation permission."""
    rules = rules or policy()
    if role not in READ_ROLES | WRITE_ROLES:
        raise ContractError("unknown_role")
    for key, entry in rules["profiles"].items():
        if (not re.fullmatch(r"[a-z][a-z0-9_]{0,63}", key) or not isinstance(entry, dict)
                or entry.get("family") not in ("sol", "astra")
                or not nonempty(entry.get("model")) or not nonempty(entry.get("effort"))):
            raise ContractError("invalid_profile_definition")
    return [key for key, profile in rules["profiles"].items()
            if profile["family"] == "sol" or
            (profile["family"] == "astra" and role in READ_ROLES and role in rules["analysis_roles"])]


def routing_arguments(packet: dict) -> dict:
    """Shared inputs for local selection and dispatch; do not drop host limits."""
    w, rt = packet["work"], packet.get("runtime", {})
    return dict(role=w["role"], operation=w["operation"], analysis=w.get("analysis", False),
                available=rt.get("available_profiles"), denied=rt.get("denied_profiles"),
                explicit=rt.get("explicit_override"), principal_choice=rt.get("principal_choice"),
                required_capabilities=w.get("required_capabilities"),
                available_capabilities=packet.get("available_capabilities"),
                within_budget=packet.get("control", {}).get("budget_remaining", True) is not False,
                decisions_resolved=w.get("decisions_resolved"),
                execution_difficulty=w.get("execution_difficulty", "unknown"))


def profile_selection(role: str, operation: str, *, analysis: bool,
                      recommendation: str | None = None, available: list[str] | None = None,
                      required_capabilities: list[str] | None = None,
                      available_capabilities: list[str] | None = None,
                      explicit: dict | None = None, denied: list[str] | None = None,
                      principal_choice: dict | None = None,
                      shadow: bool = False, within_budget: bool = True,
                      decisions_resolved: bool | None = None, execution_difficulty: str = "unknown",
                      rules: dict | None = None) -> dict:
    """Choose an eligible profile, never grant authority or claim a worker ran.

    Prepared implementation can use medium/high. Missing or open decisions need
    preparation, not extra model effort. Difficulty unknown uses high as fallback
    but requires the principal to choose among eligible profiles with evidence. Explicit overrides do not bypass this.
    """
    rules = rules or policy()
    if role not in READ_ROLES | WRITE_ROLES or operation not in OPERATIONS:
        raise ContractError("unknown_role_or_operation")
    if type(analysis) is not bool or decisions_resolved is not None and type(decisions_resolved) is not bool:
        raise ContractError("invalid_routing_boolean")
    if execution_difficulty not in ("routine", "demanding", "unknown"):
        raise ContractError("invalid_execution_difficulty")
    for value in (available, denied, required_capabilities, available_capabilities):
        if value is not None and (not isinstance(value, list) or any(not nonempty(x) for x in value)):
            raise ContractError("invalid_routing_filter")
    if explicit is not None and not isinstance(explicit, dict) or principal_choice is not None and not isinstance(principal_choice, dict):
        raise ContractError("invalid_profile_choice")
    base = role_default(role, rules)
    analytic = analysis and role in rules["analysis_roles"] and operation in rules["analysis_operations"]
    implementing = role in rules.get("implementation_roles", []) and operation in rules.get("implementation_operations", [])
    kind = "implementation" if implementing else "analysis" if analytic else "default"
    candidates = list(rules["ordinary_analysis_profiles"] if analytic else
                      rules.get("ordinary_implementation_profiles", [base]) if implementing else [base])
    requested = (explicit or {}).get("profile")
    reason, status = "default", "selected"
    def blocked(code: str) -> dict:
        return {"status": "blocked", "reason": code, "selected": None, "requested": requested,
                "recommendation": recommendation, "candidates": candidates, "routing_kind": kind,
                "provider_observed": None, "authorizes_action": False, "changes_parent": False}
    if implementing:
        if decisions_resolved is not True:
            return blocked("implementation_decisions_unresolved" if decisions_resolved is False else "implementation_readiness_required")
        if execution_difficulty != "routine":
            base = rules["default_profile"]
        if execution_difficulty == "demanding":
            candidates = [p for p in candidates if p != "sol_medium"]
    if requested is not None:
        if requested not in rules["profiles"]:
            return blocked("unknown_requested_profile")
        if not refs((explicit or {}).get("source_refs")) or (explicit or {}).get("source_kind") != "user":
            return blocked("override_source_required")
        if rules["profiles"][requested]["family"] == "astra" and not analytic:
            return blocked("astra_not_execution_candidate")
        if (rules["profiles"][requested]["family"] == "astra"
                and rules["profiles"][requested].get("effort") not in ("low", "medium")):
            return blocked("profile_above_astra_ceiling")
        candidates.append(requested)
    candidates = [p for p in dict.fromkeys(candidates) if p not in (denied or [])]
    if available is not None:
        candidates = [p for p in candidates if p in available]
    if required_capabilities and not set(required_capabilities).issubset(set(available_capabilities or [])):
        return blocked("capability_unverified")
    if not within_budget:
        return blocked("budget_unavailable")
    if requested:
        if requested not in candidates or available is None:
            return blocked("requested_profile_unavailable_or_unverified")
        selected, reason = requested, "explicit_scoped_override"
    elif principal_choice is not None:
        chosen = principal_choice.get("profile")
        if not refs(principal_choice.get("evidence_refs")):
            return blocked("principal_choice_evidence_required")
        if chosen not in candidates or rules["profiles"].get(chosen, {}).get("explicit_only"):
            return blocked("principal_choice_not_eligible")
        selected, reason = chosen, "principal_evidence_selection"
    elif recommendation in candidates and not shadow:
        selected, reason = recommendation, "advisory_applied"
    else:
        selected = base if base in candidates else None
        reason = "shadow_default" if shadow and recommendation else "default"
        if recommendation and recommendation not in candidates:
            reason = "excluded_recommendation"
    if selected is None:
        return blocked("default_unavailable_no_silent_escalation")
    if available is None:
        status = "availability_unverified"
    return {"status": status, "selected": selected, "requested": requested,
            "recommendation": recommendation, "candidates": candidates, "reason": reason,
            "routing_kind": kind, "profile": rules["profiles"].get(selected), "provider_observed": None,
            "authorizes_action": False, "changes_parent": False}


def validate_packet(packet: Any) -> dict:
    if not isinstance(packet, dict) or packet.get("schema_version") != 3:
        raise ContractError("packet_schema_must_be_3")
    for key in ("objective_id", "project_id"):
        if not isinstance(packet.get(key), str) or not IDENTIFIER.fullmatch(packet[key]):
            raise ContractError("invalid_" + key)
    work = packet.get("work")
    if not isinstance(work, dict) or work.get("mode") not in MODES or work.get("operation") not in OPERATIONS:
        raise ContractError("invalid_work")
    if work.get("role") not in READ_ROLES | WRITE_ROLES:
        raise ContractError("invalid_role")
    for flag in ("material", "analysis", "bugfix", "security_opt_in", "prior_effect_unknown", "product_change", "external_required", "target_verified", "host_key_verified", "decisions_resolved"):
        if flag in work and type(work[flag]) is not bool:
            raise ContractError("invalid_boolean_" + flag)
    for field in ("requirements", "test_expectations", "impacts", "sources", "skills", "checks", "evidence", "pending", "delegations", "spec_changes", "findings", "workspaces"):
        records(packet, field)
    for field in ("authority", "control", "review", "candidate", "diagnostic", "external", "release", "runtime", "data_sharing", "project_context"):
        if field in packet and not isinstance(packet[field], dict):
            raise ContractError("invalid_object_" + field)
    if "required_capabilities" in work and (not isinstance(work["required_capabilities"], list) or any(not nonempty(x) for x in work["required_capabilities"])):
        raise ContractError("invalid_required_capabilities")
    for field in ("available_capabilities",):
        if field in packet and (not isinstance(packet[field], list) or any(not nonempty(x) for x in packet[field])):
            raise ContractError("invalid_" + field)
    boolean_keys = {"required", "blocking", "resolved", "authorized", "available", "monitor_confirmed", "provider_required", "physical_required", "oracle_required", "provider_live", "physical_device", "fail_before", "prior_failed", "foreign_preserved", "integration_required", "integration_observed", "independently_reviewed", "unresolved_disagreement", "budget_remaining"}
    def check_nested(obj: Any, depth: int = 0) -> None:
        if depth > 30:
            raise ContractError("packet_depth_exceeded")
        if isinstance(obj, dict):
            for key, val in obj.items():
                if key in boolean_keys and val is not None and type(val) is not bool:
                    raise ContractError("invalid_boolean_" + key)
                if key in ("approval", "oracle_exception") and not isinstance(val, dict):
                    raise ContractError("invalid_object_" + key)
                check_nested(val, depth + 1)
        elif isinstance(obj, list):
            for val in obj:
                check_nested(val, depth + 1)
    check_nested(packet)
    for item in packet.get("requirements", []):
        if not nonempty(item.get("text")) or "expected" not in item:
            raise ContractError("requirement_text_and_expected_required")
        allowed = item.get("allowed_evidence", [])
        if not isinstance(allowed, list) or any(not nonempty(v) for v in allowed):
            raise ContractError("invalid_evidence_kinds")
    for key in ("operations", "source_refs"):
        value = packet.get("authority", {}).get(key, [])
        if not isinstance(value, list) or any(not nonempty(v) for v in value):
            raise ContractError("invalid_authority_" + key)
    optional = packet.get("optional_context", [])
    if not isinstance(optional, list) or any(not isinstance(c,dict) or not nonempty(c.get("id")) for c in optional):
        raise ContractError("invalid_optional_context")
    if len({c["id"] for c in optional}) != len(optional):
        raise ContractError("duplicate_optional_context")
    for context in optional:
        for key in ("recoverable", "negative_evidence", "pinned"):
            if key in context and type(context[key]) is not bool:
                raise ContractError("invalid_context_flag")
    canonical(packet)
    return packet


def next_action(packet: dict) -> dict:
    control = packet.get("control", {})
    if control.get("state") in ("paused", "cancelled", "interrupted"):
        return {"action": "stop", "reason": control["state"]}
    if control.get("budget_remaining") is False:
        return {"action": "stop", "reason": "budget_exhausted"}
    if packet["work"].get("prior_effect_unknown") is True:
        return {"action": "reconcile", "reason": "external_effect_unknown"}
    if any(x.get("kind") in ("regression", "contradiction", "refuted_hypothesis") and x.get("resolved") is not True for x in packet.get("findings", [])):
        return {"action": "diagnose", "reason": "reframe_before_patch"}
    if control.get("progress") == "stalled":
        return {"action": "diagnose", "reason": "no_progress_new_hypothesis_required"}
    required = [p for p in packet.get("pending", []) if p.get("required", True) and p.get("status") != "complete"]
    for item in required:
        if item.get("authorized") is True and item.get("available") is True:
            if item.get("status") in ("needs_preparation", "needs_team_handoff"):
                return {"action": "team_handoff", "pending_id": item["id"], "reason": item["status"]}
            if item.get("status") == "executable_now":
                return {"action": "continue", "pending_id": item["id"], "reason": "required_work_available"}
    if required:
        item = required[0]
        return {"action": "wait_or_request_minimum", "pending_id": item["id"], "reason": item.get("status", "unknown"), "monitor_confirmed": item.get("monitor_confirmed") is True}
    return {"action": "check_closeout", "reason": "no_known_required_pending"}


def dispatch_receipt_issues(packet: dict, stage: str) -> list[str]:
    """Check the terminal evidence for a required native delegation.

    Dispatch preparation and execution are separate from closeout.  This gate
    is opt-in through ``runtime.dispatch_required``/``required_agent_type`` so
    trivial reads and packets that never delegated remain unchanged.
    """
    if stage not in ("closeout", "release"):
        return []
    runtime = packet.get("runtime", {})
    required = runtime.get("dispatch_required") is True or nonempty(runtime.get("required_agent_type"))
    if not required:
        return []
    issues: list[str] = []
    target = runtime.get("required_agent_type")
    if not nonempty(target):
        issues.append("required_agent_type_missing")
        return issues
    receipt = runtime.get("dispatch_receipt")
    if not isinstance(receipt, dict):
        return ["dispatch_receipt_required"]
    if receipt.get("agent_type") != target:
        issues.append("dispatch_agent_type_mismatch")
    if receipt.get("fork_turns") != "none":
        issues.append("dispatch_fork_turns_must_be_none")
    if receipt.get("status") != "completed":
        issues.append("child_incomplete")
    if not nonempty(receipt.get("child_reference")):
        issues.append("dispatch_child_reference_required")
    if not refs(receipt.get("evidence")):
        issues.append("dispatch_terminal_evidence_required")
    target_role, target_profile = target.rsplit("__", 1) if "__" in target else ("", "")
    if target_role != packet.get("work", {}).get("role"):
        issues.append("dispatch_target_role_mismatch")
    expected_profile = runtime.get("required_profile")
    if expected_profile != target_profile:
        issues.append("dispatch_required_profile_mismatch")
    expected_profile = target_profile
    if expected_profile not in policy().get("profiles", {}):
        issues.append("dispatch_profile_definition_missing")
        return issues
    expected = policy()["profiles"][expected_profile]
    if (expected.get("family") == "astra"
            and expected.get("effort") not in ("low", "medium")):
        issues.append("dispatch_astra_effort_above_ceiling")
    if (expected.get("family") == "astra"
            and target_role not in policy().get("analysis_roles", [])):
        issues.append("dispatch_astra_role_not_analytic")
    if (expected.get("family") == "astra"
            and not (packet.get("work", {}).get("analysis") is True
                     and packet.get("work", {}).get("operation") in policy().get("analysis_operations", []))):
        issues.append("dispatch_astra_requires_analysis")
    if expected.get("explicit_only"):
        override = runtime.get("explicit_override")
        if (not isinstance(override, dict) or override.get("profile") != expected_profile
                or override.get("source_kind") != "user" or not refs(override.get("source_refs"))):
            issues.append("dispatch_explicit_override_required")
    if receipt.get("model_observed") != expected.get("model"):
        issues.append("dispatch_reported_model_mismatch")
    if receipt.get("effort_observed") != expected.get("effort"):
        issues.append("dispatch_reported_effort_mismatch")
    return issues


def visual_surface_issues(packet: dict, stage: str) -> list[str]:
    """Require design and UX evidence for an explicitly broad visual change."""
    if stage not in ("closeout", "release"):
        return []
    work = packet.get("work", {})
    if work.get("visual_scope") not in ("broad", "redesign"):
        return []
    runtime = packet.get("runtime", {})
    issues: list[str] = []
    if not refs(runtime.get("design_baseline_evidence")):
        issues.append("visual_design_baseline_required")
    validation = runtime.get("visual_validation")
    if not isinstance(validation, dict):
        return issues + ["visual_validation_required"]
    if not nonempty(validation.get("viewport")):
        issues.append("visual_viewport_required")
    if not refs(validation.get("screenshots")):
        issues.append("visual_screenshot_evidence_required")
    if not refs(validation.get("content_checks")):
        issues.append("visual_content_acceptance_required")
    if validation.get("responsive_checked") is not True:
        issues.append("visual_responsive_check_required")
    if validation.get("accessibility_checked") is not True:
        issues.append("visual_accessibility_check_required")
    candidate_hash = fingerprint(packet.get("candidate", {}))
    valid_ux = []
    for child in packet.get("delegations", []):
        if not isinstance(child, dict) or not str(child.get("required_agent_type", "")).startswith("ux_auditor__"):
            continue
        target = child.get("required_agent_type")
        profile_id = target.rsplit("__", 1)[1] if "__" in target else ""
        expected = policy().get("profiles", {}).get(profile_id)
        if (child.get("required") is True and child.get("state") == "received"
                and child.get("agent_type") == target and child.get("fork_turns") == "none"
                and refs(child.get("evidence")) and child.get("candidate_hash") == candidate_hash
                and expected and child.get("model_observed") == expected.get("model")
                and child.get("effort_observed") == expected.get("effort")):
            valid_ux.append(child)
    if not valid_ux:
        issues.append("ux_auditor_delegation_required")
    return issues


def gate(packet: dict, stage: str = "preflight") -> dict:
    validate_packet(packet)
    if stage not in ("preflight", "dispatch", "closeout", "release"):
        raise ContractError("invalid_gate_stage")
    w = packet["work"]
    operation, mode, role = w["operation"], w["mode"], w["role"]
    issues: list[str] = []
    warns: list[str] = []
    component_evidence = packet.get("component_evidence")
    required_components = packet.get("required_components", [])
    if "evidence" in packet:
        for record in packet.get("evidence", []):
            checked = validate_evidence(record)
            if not checked["valid"]:
                issues.extend("invalid_evidence:" + x for x in checked["errors"])
            else:
                warns.extend(checked["warnings"])
                normalized = checked["record"]
                if normalized["objective_id"] != packet["objective_id"] or normalized["project_id"] != packet["project_id"]:
                    issues.append("evidence_project_or_objective_mismatch:" + normalized["evidence_id"])
    if "project_context" in packet:
        context = validate_project_context(packet["project_context"])
        if not context["valid"]:
            issues.extend("invalid_project_context:" + x for x in context["errors"])
        else:
            warns.extend(context["warnings"])
            if context["context"]["project_id"] != packet["project_id"]:
                issues.append("project_context_project_mismatch")
    if stage in ("closeout", "release") and required_components and component_evidence is None:
        issues.extend("required_component_evidence_missing:" + str(x) for x in required_components)
    if component_evidence is not None:
        if not isinstance(component_evidence, list):
            issues.append("component_evidence_must_be_list")
        else:
            seen_components = set()
            for component in component_evidence:
                if not isinstance(component, dict) or not isinstance(component.get("component"), str) or not component["component"]:
                    issues.append("invalid_component_evidence"); continue
                name = component["component"]
                if name in seen_components: issues.append("duplicate_component_evidence:" + name)
                seen_components.add(name)
                if not isinstance(component.get("repository"), str) or not component.get("repository") or not re.fullmatch(r"[0-9a-fA-F]{7,64}", str(component.get("candidate_sha", ""))):
                    issues.append("component_candidate_sha_required:" + name)
                if component.get("status") not in ("independent", "dependent", "blocked"):
                    issues.append("invalid_component_status:" + name)
                if not isinstance(component.get("checks", []), list) or not all(isinstance(x, str) and x for x in component.get("checks", [])):
                    issues.append("invalid_component_checks:" + name)
                if not isinstance(component.get("depends_on", []), list) or not all(isinstance(x, str) and x for x in component.get("depends_on", [])):
                    issues.append("invalid_component_dependencies:" + name)
            missing_components = sorted(set(required_components) - seen_components) if isinstance(required_components, list) else []
            issues.extend("required_component_evidence_missing:" + x for x in missing_components)
            if "contract_changed" in packet.get("shared_contracts", []):
                for component in component_evidence:
                    if isinstance(component, dict) and component.get("status") == "dependent" and not component.get("depends_on"):
                        issues.append("shared_contract_dependency_missing:" + component["component"])
            if stage in ("closeout", "release"):
                for component in component_evidence:
                    if not isinstance(component, dict) or component.get("component") not in required_components:
                        continue
                    if component.get("status") == "blocked":
                        issues.append("required_component_blocked:" + component["component"])
                    if not component.get("checks"):
                        issues.append("required_component_checks_missing:" + component["component"])
    material = w.get("material", True) or operation in ("write_product", "write_tests", "git_write", "external_mutation")
    mutating = operation not in ("read",)
    authority = packet.get("authority", {})
    if mutating:
        if not nonempty(w.get("target")):
            issues.append("mutation_target_required")
        if authority.get("source_kind") not in ("user", "project_policy") or not refs(authority.get("source_refs")):
            issues.append("authority_source_required")
        if operation not in authority.get("operations", []):
            issues.append("operation_outside_authority")
        if authority.get("project_id") != packet["project_id"] or authority.get("target") != w.get("target"):
            issues.append("authority_scope_mismatch")
    if mode in ("DISCOVERY", "AUDIT") and operation not in ("read", "capture_docs", "write_artifact"):
        issues.append("read_mode_cannot_mutate_product")
    if role in READ_ROLES and operation in ("write_product", "write_tests", "git_write", "external_mutation"):
        issues.append("authorized_writer_required")
    if operation == "capture_docs" and not authority.get("document_scope"):
        issues.append("document_scope_required")
    if role == "release_operator" and operation in ("write_product", "write_tests"):
        issues.append("release_operator_cannot_author")
    if role == "data_security" and w.get("security_opt_in") is not True:
        issues.append("security_opt_in_required")
    if operation == "write_artifact" and not authority.get("artifact_scope"):
        issues.append("artifact_scope_required")
    if w.get("prior_effect_unknown") is True and operation == "external_mutation":
        issues.append("reconcile_before_retry")
    if w.get("interface") == "ssh" and (w.get("target_verified") is not True or w.get("host_key_verified") is not True):
        issues.append("ssh_identity_unverified")
    if operation == "external_mutation":
        for key in ("target", "procedure", "recovery"):
            if not nonempty(w.get(key)):
                issues.append("external_missing_" + key)
        if w.get("target_verified") is not True:
            issues.append("external_target_unverified")
    if not set(w.get("required_capabilities", [])).issubset(set(packet.get("available_capabilities", []))):
        issues.append("capability_unverified")
    action = next_action(packet)
    if action["action"] == "stop":
        issues.append(action["reason"])
    if material:
        if not nonempty(packet.get("outcome")):
            issues.append("outcome_required")
        if not packet.get("requirements"):
            issues.append("acceptance_required")
        if not refs(packet.get("coherence_evidence")):
            issues.append("coherence_review_required")
        if packet.get("context_complete") is not True:
            (warns if operation == "read" else issues).append("context_incomplete")
        if (stage in ("closeout", "release") and operation in ("write_product", "write_tests", "git_write", "external_mutation")
                and ({"context_incomplete", "context_active_workstream_missing"} & set(warns))):
            issues.append("project_context_incomplete")
        for source in packet.get("sources", []):
            if source.get("expected_hash") != source.get("observed_hash") or not nonempty(source.get("observed_hash")):
                issues.append("stale_source:" + source["id"])
        for skill in packet.get("skills", []):
            if skill.get("required", True) and (skill.get("loaded_hash") != skill.get("expected_hash") or not nonempty(skill.get("loaded_hash"))):
                issues.append("required_skill_not_loaded:" + skill["id"])
        if w.get("bugfix") and not any(s.get("kind") == "diagnosis" and s.get("loaded_hash") == s.get("expected_hash") and nonempty(s.get("loaded_hash")) for s in packet.get("skills", [])):
            issues.append("diagnosis_skill_required")
    reqs = {r["id"]: r for r in packet.get("requirements", [])}
    for expectation in packet.get("test_expectations", []):
        req = reqs.get(expectation.get("requirement_id"))
        if req is None:
            issues.append("orphan_test_expectation:" + expectation["id"])
        elif "expected" in expectation and "expected" in req and canonical(expectation["expected"]) != canonical(req["expected"]):
            issues.append("contract_test_conflict:" + expectation["id"])
    known_checks = {c["id"] for c in packet.get("checks", [])} | {c["id"] for c in packet.get("test_expectations", [])}
    for impact in packet.get("impacts", []):
        treatment = impact.get("treatment")
        if treatment not in ("direct_change", "indirect_validation", "no_change_justified", "unknown"):
            issues.append("invalid_impact:" + impact["id"])
        elif treatment == "unknown" and impact.get("blocking", True) and operation in ("write_product", "write_tests", "external_mutation"):
            issues.append("unresolved_impact:" + impact["id"])
        elif treatment == "no_change_justified" and (not refs(impact.get("evidence")) or not nonempty(impact.get("rationale"))):
            issues.append("unjustified_no_change:" + impact["id"])
        elif treatment in ("direct_change", "indirect_validation") and (not refs(impact.get("check_ids")) or not set(impact["check_ids"]).issubset(known_checks)):
            issues.append("impact_check_missing:" + impact["id"])
    for change in packet.get("spec_changes", []):
        if change.get("classification") == "normative":
            expected = fingerprint({"base": change.get("base_hash"), "delta": change.get("delta")})
            approval = change.get("approval", {})
            if (approval.get("source_kind") != "user" or not refs(approval.get("source_refs")) or approval.get("delta_hash") != expected):
                if mutating or stage in ("closeout", "release"):
                    issues.append("spec_delta_unapproved:" + change["id"])
    if action["action"] == "diagnose" and (operation in ("write_product", "write_tests", "external_mutation") or stage in ("closeout", "release")):
        issues.append(action["reason"])
    if w.get("bugfix") and operation in ("write_product", "write_tests"):
        diagnostic = packet.get("diagnostic", {})
        if not refs(diagnostic.get("evidence")) or diagnostic.get("hypothesis_state") not in ("supported", "reproduced"):
            issues.append("diagnostic_evidence_required")
        if not nonempty(diagnostic.get("discriminating_check")):
            issues.append("discriminating_check_required")
    if stage in ("closeout", "release"):
        issues.extend(dispatch_receipt_issues(packet, stage))
        issues.extend(visual_surface_issues(packet, stage))
        candidate = packet.get("candidate", {})
        if material and not candidate:
            issues.append("candidate_identity_required")
        candidate_hash = fingerprint(candidate)
        acceptance_hash = fingerprint(packet.get("requirements", []))
        checks = packet.get("checks", [])
        for requirement in reqs.values():
            if not requirement.get("required", True):
                continue
            matching = [c for c in checks if c.get("requirement_id") == requirement["id"]]
            valid = []
            for check in matching:
                if (check.get("status") != "passed" or not refs(check.get("evidence")) or check.get("candidate_hash") != candidate_hash or check.get("acceptance_hash") != acceptance_hash):
                    continue
                if check.get("evidence_kind") not in requirement.get("allowed_evidence", ["tool_result", "external_observation", "human_observation"]):
                    continue
                if requirement.get("provider_required") and check.get("provider_live") is not True:
                    continue
                if requirement.get("physical_required") and check.get("physical_device") is not True:
                    continue
                if requirement.get("oracle_required") and check.get("fail_before") is not True:
                    exception = check.get("oracle_exception", {})
                    if not refs(exception.get("evidence")) or exception.get("independently_reviewed") is not True:
                        continue
                if check.get("prior_failed") and not refs(check.get("failure_resolution")):
                    continue
                valid.append(check)
            if not valid:
                issues.append("criterion_unverified:" + requirement["id"])
        for impact in packet.get("impacts", []):
            if impact.get("treatment") in ("direct_change", "indirect_validation"):
                for cid in impact.get("check_ids", []):
                    if not any(c["id"] == cid and c.get("status") == "passed" and refs(c.get("evidence")) and c.get("candidate_hash") == candidate_hash and c.get("acceptance_hash") == acceptance_hash for c in checks):
                        issues.append("impact_unverified:" + impact["id"])
        for child in packet.get("delegations", []):
            if child.get("required", True) and (child.get("state") != "received" or not refs(child.get("evidence")) or child.get("candidate_hash") != candidate_hash):
                issues.append("handoff_missing_or_stale:" + child["id"])
            required_target = child.get("required_agent_type")
            if required_target:
                if required_target in ("worker", "code_explorer") or "__" not in str(required_target):
                    issues.append("delegation_agent_type_role_qualified_required:" + child["id"])
                if child.get("agent_type") != required_target:
                    issues.append("delegation_agent_type_mismatch:" + child["id"])
                if child.get("fork_turns") != "none":
                    issues.append("delegation_fork_turns_must_be_none:" + child["id"])
                if "__" in str(required_target):
                    target_role, profile_id = str(required_target).rsplit("__", 1)
                    if target_role not in READ_ROLES | WRITE_ROLES:
                        issues.append("delegation_agent_role_unknown:" + child["id"])
                    expected_profile = policy().get("profiles", {}).get(profile_id)
                    if not expected_profile:
                        issues.append("delegation_profile_definition_missing:" + child["id"])
                    else:
                        if (expected_profile.get("family") == "astra"
                                and expected_profile.get("effort") not in ("low", "medium")):
                            issues.append("delegation_astra_effort_above_ceiling:" + child["id"])
                        if (expected_profile.get("family") == "astra"
                                and str(required_target).rsplit("__", 1)[0] not in policy().get("analysis_roles", [])):
                            issues.append("delegation_astra_role_not_analytic:" + child["id"])
                        if expected_profile.get("explicit_only"):
                            override = child.get("explicit_override")
                            if (not isinstance(override, dict) or override.get("profile") != profile_id
                                    or override.get("source_kind") != "user" or not refs(override.get("source_refs"))):
                                issues.append("delegation_explicit_override_required:" + child["id"])
                        if child.get("model_observed") != expected_profile.get("model"):
                            issues.append("delegation_model_mismatch:" + child["id"])
                        if child.get("effort_observed") != expected_profile.get("effort"):
                            issues.append("delegation_effort_mismatch:" + child["id"])
        review = packet.get("review", {})
        if review.get("required", False) or operation in ("write_product", "write_tests") or w.get("product_change") is True:
            if (review.get("status") != "approved" or not refs(review.get("evidence")) or
                review.get("candidate_hash") != candidate_hash or review.get("acceptance_hash") != acceptance_hash or
                not nonempty(review.get("author_run")) or not nonempty(review.get("reviewer_run")) or review.get("reviewer_run") == review.get("author_run") or
                review.get("unresolved_disagreement") is True):
                issues.append("independent_review_incomplete")
        for workspace in packet.get("workspaces", []):
            if workspace.get("foreign_preserved") is not True:
                issues.append("foreign_changes_not_preserved:" + workspace["id"])
            if workspace.get("own_residuals_unresolved", 0):
                issues.append("own_workspace_residuals:" + workspace["id"])
            if workspace.get("integration_required") and workspace.get("integration_observed") is not True:
                issues.append("integration_unverified:" + workspace["id"])
        if action["action"] != "check_closeout":
            issues.append("required_work_remaining:" + action["action"])
        if w.get("external_required") and packet.get("external", {}).get("outcome") != "verified":
            issues.append("external_outcome_unverified")
    if stage == "release" and (packet.get("candidate", {}).get("artifact_digest") is None or packet.get("release", {}).get("authorized_candidate_hash") != fingerprint(packet.get("candidate", {}))):
        issues.append("release_candidate_binding_required")
    warns.append("checks_validate_supplied_evidence_not_semantic_truth_or_user_identity")
    return {"schema_version": 1, "stage": stage, "passed": not issues,
            "issues": sorted(set(issues)), "warnings": warns, "next": action,
            "candidate_hash": fingerprint(packet.get("candidate", {})),
            "acceptance_hash": fingerprint(packet.get("requirements", [])),
            "packet_hash": fingerprint(packet), "authorizes_action": False,
            "validation_layer": "packet_consistency"}


def invalidated_nodes(nodes: list[dict], changed_sources: set[str]) -> list[str]:
    """Transitive dependency invalidation, including graphs with bounded cycles."""
    by_id = {n["id"]: n for n in nodes}
    if len(by_id) != len(nodes):
        raise ContractError("duplicate_node")
    if any(dep not in by_id for n in nodes for dep in n.get("depends_on", [])):
        raise ContractError("unknown_dependency")
    invalid = {n["id"] for n in nodes if set(n.get("sources", [])) & changed_sources}
    while True:
        added = {n["id"] for n in nodes if set(n.get("depends_on", [])) & invalid}
        if added <= invalid:
            return sorted(invalid)
        invalid |= added
