#!/usr/bin/env python3
"""Validate the bounded evidence and project-context contract.

The contract is deliberately a normalizer, not a completeness gate.  Scratch
projects and work still in discovery may use explicit ``unknown`` and
``in_progress`` values; those values produce warnings and remain usable by the
workflow.  This module never authorizes an action or claims that an observation
is true.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any, Iterable


SCHEMA_VERSION = 1
IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,119}$")
SHA = re.compile(r"^[A-Fa-f0-9]{7,64}$")
TOKEN = re.compile(r"^[a-z][a-z0-9_:-]{0,79}$")
UNKNOWN = "unknown"
IN_PROGRESS = "in_progress"

STAGES = {"discovery", "audit", "implementation", "release"}
EVIDENCE_STRENGTHS = {"E0", "E1", "E2", "E3", "E4"}
EVIDENCE_STATUSES = {
    "observed", "inferred", "proposed", "unknown", "in_progress",
    "superseded", "contradicted",
}
SOURCE_KINDS = {
    "user_statement", "code", "spec", "config", "test", "browser",
    "simulator", "device", "provider", "server", "review", "artifact",
    "telemetry", "docs", "unknown",
}
DOC_STATUSES = {"complete", "partial", "scratch", "unknown", "in_progress"}
MAX_TEXT = 4_000
MAX_OBSERVATION = 10_000
MAX_LIST = 64
MAX_METADATA_KEYS = 32


class EvidenceContractError(ValueError):
    """Raised only for malformed input, never for an explicit unknown value."""


def _text(value: Any, *, name: str, limit: int = MAX_TEXT, allow_unknown: bool = True) -> str:
    if not isinstance(value, str):
        raise EvidenceContractError(f"{name}_must_be_text")
    value = " ".join(value.strip().split())
    if not value or len(value) > limit:
        raise EvidenceContractError(f"{name}_invalid_length")
    if not allow_unknown and value == UNKNOWN:
        raise EvidenceContractError(f"{name}_cannot_be_unknown")
    if re.search(r"(?:sk-|ghp_|github_pat_|sb_secret_|Bearer\s+)[A-Za-z0-9._-]{8,}", value, re.I):
        raise EvidenceContractError(f"{name}_looks_sensitive")
    return value


def _token(value: Any, *, name: str, allowed: set[str]) -> str:
    value = _text(value, name=name).lower().replace(" ", "_")
    if value not in allowed:
        raise EvidenceContractError(f"invalid_{name}")
    return value


def _identifier(value: Any, *, name: str, allow_unknown: bool = True) -> str:
    value = _text(value, name=name)
    if allow_unknown and value == UNKNOWN:
        return value
    if not IDENTIFIER.fullmatch(value):
        raise EvidenceContractError(f"invalid_{name}")
    return value


def _list_of_text(value: Any, *, name: str, limit: int = MAX_LIST) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list) or len(value) > limit:
        raise EvidenceContractError(f"{name}_must_be_bounded_list")
    result = [_text(item, name=name) for item in value]
    return result


def _timestamp(value: Any) -> str:
    value = _text(value, name="observed_at", limit=80)
    if value == UNKNOWN:
        return value
    candidate = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        stamp = dt.datetime.fromisoformat(candidate)
    except ValueError as exc:
        raise EvidenceContractError("observed_at_must_be_iso8601") from exc
    if stamp.tzinfo is None:
        raise EvidenceContractError("observed_at_timezone_required")
    return stamp.astimezone(dt.timezone.utc).isoformat().replace("+00:00", "Z")


def _metadata(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, dict) or len(value) > MAX_METADATA_KEYS:
        raise EvidenceContractError("metadata_must_be_bounded_object")
    # Metadata remains machine-readable but cannot become a transcript sink.
    try:
        encoded = json.dumps(value, ensure_ascii=True, allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise EvidenceContractError("metadata_must_be_json") from exc
    if len(encoded) > 8_000:
        raise EvidenceContractError("metadata_too_large")
    if re.search(r"(?:sk-|ghp_|github_pat_|sb_secret_|Bearer\s+)[A-Za-z0-9._-]{8,}", encoded, re.I):
        raise EvidenceContractError("metadata_looks_sensitive")
    return value


def normalize_evidence(record: dict[str, Any]) -> dict[str, Any]:
    """Return a canonical, bounded evidence record or raise a reason-coded error."""
    if not isinstance(record, dict):
        raise EvidenceContractError("evidence_must_be_object")
    required = {
        "objective_id", "project_id", "stage", "source_kind", "source_ref",
        "observed_at", "observation", "status", "strength",
    }
    missing = sorted(required - set(record))
    if "evidence_id" not in record and "id" not in record:
        missing.append("evidence_id")
    if missing:
        raise EvidenceContractError("missing_evidence_fields:" + ",".join(missing))
    if "evidence_id" in record and "id" in record and record["evidence_id"] != record["id"]:
        raise EvidenceContractError("evidence_id_alias_mismatch")
    evidence_id = record.get("evidence_id", record.get("id"))
    normalized: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "evidence_id": _identifier(evidence_id, name="evidence_id", allow_unknown=False),
        "objective_id": _identifier(record["objective_id"], name="objective_id", allow_unknown=False),
        "project_id": _identifier(record["project_id"], name="project_id", allow_unknown=False),
        "stage": _token(record["stage"], name="stage", allowed=STAGES),
        "source_kind": _token(record["source_kind"], name="source_kind", allowed=SOURCE_KINDS),
        "source_ref": _text(record["source_ref"], name="source_ref"),
        "observed_at": _timestamp(record["observed_at"]),
        "observation": _text(record["observation"], name="observation", limit=MAX_OBSERVATION),
        "status": _token(record["status"], name="status", allowed=EVIDENCE_STATUSES),
        "strength": _text(record["strength"], name="strength", limit=7),
        "supports": _list_of_text(record.get("supports"), name="supports"),
        "contradicts": _list_of_text(record.get("contradicts"), name="contradicts"),
        "metadata": _metadata(record.get("metadata")),
    }
    if normalized["strength"].lower() == UNKNOWN:
        normalized["strength"] = UNKNOWN
    else:
        normalized["strength"] = normalized["strength"].upper()
    if normalized["strength"] not in EVIDENCE_STRENGTHS and normalized["strength"] != UNKNOWN:
        raise EvidenceContractError("invalid_strength")
    if "candidate_sha" in record and record["candidate_sha"] is not None:
        candidate_sha = _text(record["candidate_sha"], name="candidate_sha", limit=64)
        if candidate_sha != UNKNOWN and not SHA.fullmatch(candidate_sha):
            raise EvidenceContractError("invalid_candidate_sha")
        normalized["candidate_sha"] = candidate_sha
    if "acceptance_hash" in record and record["acceptance_hash"] is not None:
        acceptance_hash = _text(record["acceptance_hash"], name="acceptance_hash", limit=64)
        if acceptance_hash != UNKNOWN and not SHA.fullmatch(acceptance_hash):
            raise EvidenceContractError("invalid_acceptance_hash")
        normalized["acceptance_hash"] = acceptance_hash
    return normalized


def validate_evidence(record: dict[str, Any]) -> dict[str, Any]:
    """Validate an evidence record and return machine-readable findings.

    ``unknown`` and ``in_progress`` are valid states.  They yield warnings so a
    caller can keep a scratch objective moving while retaining the missing
    boundary for a later gate.
    """
    try:
        normalized = normalize_evidence(record)
    except EvidenceContractError as exc:
        return {"valid": False, "errors": [str(exc)], "warnings": [], "record": None}
    warnings: list[str] = []
    if normalized["status"] in {UNKNOWN, IN_PROGRESS}:
        warnings.append("evidence_state_incomplete")
    if normalized["source_kind"] == UNKNOWN or normalized["source_ref"] == UNKNOWN:
        warnings.append("evidence_source_incomplete")
    if normalized["observed_at"] == UNKNOWN:
        warnings.append("evidence_time_unknown")
    if normalized["strength"] == UNKNOWN:
        warnings.append("evidence_strength_unknown")
    return {"valid": True, "errors": [], "warnings": warnings, "record": normalized}


def _context_entry(value: Any, *, name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise EvidenceContractError(f"{name}_entry_must_be_object")
    item: dict[str, Any] = {}
    for key, raw in value.items():
        if not isinstance(key, str) or not TOKEN.fullmatch(key):
            raise EvidenceContractError(f"{name}_invalid_key")
        if isinstance(raw, str):
            item[key] = _text(raw, name=f"{name}_{key}")
        elif isinstance(raw, list):
            item[key] = _list_of_text(raw, name=f"{name}_{key}")
        elif isinstance(raw, (bool, int)) and not isinstance(raw, float):
            item[key] = raw
        elif raw is None:
            item[key] = None
        else:
            raise EvidenceContractError(f"{name}_{key}_unsupported")
    return item


def normalize_project_context(context: dict[str, Any]) -> dict[str, Any]:
    """Normalize a project manifest without requiring documentation completeness."""
    if not isinstance(context, dict):
        raise EvidenceContractError("project_context_must_be_object")
    if "project_id" not in context:
        raise EvidenceContractError("project_id_required")
    normalized: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "project_id": _identifier(context["project_id"], name="project_id", allow_unknown=False),
        "documentation_status": _token(
            context.get("documentation_status", UNKNOWN),
            name="documentation_status", allowed=DOC_STATUSES,
        ),
    }
    for field in ("repositories", "components", "environments", "providers"):
        values = context.get(field, [])
        if not isinstance(values, list) or len(values) > MAX_LIST:
            raise EvidenceContractError(f"{field}_must_be_bounded_list")
        normalized[field] = [_context_entry(item, name=field) for item in values]
    canonical_sources = context.get("canonical_sources", {})
    if not isinstance(canonical_sources, dict) or len(canonical_sources) > MAX_METADATA_KEYS:
        raise EvidenceContractError("canonical_sources_must_be_bounded_object")
    normalized["canonical_sources"] = {
        _text(key, name="canonical_source_key"): _text(value, name="canonical_source_value")
        for key, value in canonical_sources.items()
    }
    if "notes" in context:
        normalized["notes"] = _text(context["notes"], name="notes", limit=MAX_OBSERVATION)
    return normalized


def validate_project_context(context: dict[str, Any]) -> dict[str, Any]:
    try:
        normalized = normalize_project_context(context)
    except EvidenceContractError as exc:
        return {"valid": False, "errors": [str(exc)], "warnings": [], "context": None}
    warnings: list[str] = []
    status = normalized["documentation_status"]
    if status in {"scratch", "partial", UNKNOWN, IN_PROGRESS}:
        warnings.append("context_incomplete")
    for field in ("repositories", "components", "environments"):
        if not normalized[field]:
            warnings.append(f"context_{field}_missing")
    if not normalized["canonical_sources"]:
        warnings.append("canonical_sources_missing")
    return {"valid": True, "errors": [], "warnings": sorted(set(warnings)), "context": normalized}


def _load_json(path: str) -> Any:
    raw = sys.stdin.read() if path == "-" else Path(path).read_text(encoding="utf-8")
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise EvidenceContractError("invalid_json") from exc


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("kind", choices=("evidence", "project-context"))
    parser.add_argument("path", help="JSON path, or - for stdin")
    args = parser.parse_args(list(argv) if argv is not None else None)
    value = _load_json(args.path)
    result = validate_evidence(value) if args.kind == "evidence" else validate_project_context(value)
    print(json.dumps(result, ensure_ascii=True, sort_keys=True, indent=2))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
