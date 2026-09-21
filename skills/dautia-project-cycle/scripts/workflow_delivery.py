#!/usr/bin/env python3
"""Local dispatch ledger for delivery reconciliation.

The ledger records opaque hashes and state transitions only.  It never retries a
native child and never treats a late or stale response as a valid delivery.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from workflow_core import ContractError, IDENTIFIER, canonical
from workflow_store import atomic_write, private_dir, read_private, safe_path


def _check(value: Any, label: str) -> str:
    if not isinstance(value, str) or not IDENTIFIER.fullmatch(value):
        raise ContractError("invalid_" + label)
    return value


def _hash(value: Any, label: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or any(c not in "0123456789abcdef" for c in value.lower()):
        raise ContractError("invalid_" + label)
    return value.lower()


def _path(root: Path) -> Path:
    if not root.is_absolute():
        raise ContractError("ledger_root_must_be_absolute")
    private_dir(root)
    path = root / "dispatch-ledger.json"
    safe_path(path)
    return path


def _load(root: Path) -> dict:
    path = _path(root)
    if not path.exists():
        return {"schema_version": 1, "dispatches": []}
    return json.loads(read_private(path, 2_000_000))


def _save(root: Path, value: dict) -> None:
    atomic_write(_path(root), canonical(value))


def reserve_dispatch(root: Path, *, objective_id: str, project_id: str, block_id: str,
                     attempt: str, profile: str, candidate_hash: str, packet_hash: str,
                     dispatch_key: str) -> dict:
    for value, label in ((objective_id, "objective_id"), (project_id, "project_id"),
                         (block_id, "block_id"), (attempt, "attempt"), (profile, "profile")):
        _check(value, label)
    candidate_hash, packet_hash, dispatch_key = (_hash(candidate_hash, "candidate_hash"),
                                                _hash(packet_hash, "packet_hash"),
                                                _hash(dispatch_key, "dispatch_key"))
    data = _load(root)
    for item in data["dispatches"]:
        if item.get("dispatch_key") != dispatch_key:
            continue
        if item.get("candidate_hash") != candidate_hash or item.get("packet_hash") != packet_hash:
            return {"status": "reconcile_required", "reason": "dispatch_key_payload_changed", "dispatch": item}
        if item.get("state") in ("reserved", "started", "delivered"):
            return {"status": "reused", "reason": "identical_dispatch", "dispatch": item}
        return {"status": "reconcile_required", "reason": "dispatch_state_unknown", "dispatch": item}
    dispatch_id = "d-" + hashlib.sha256((dispatch_key + objective_id).encode()).hexdigest()[:24]
    item = {"dispatch_id": dispatch_id, "objective_id": objective_id, "project_id": project_id,
            "block_id": block_id, "attempt": attempt, "profile": profile,
            "candidate_hash": candidate_hash, "packet_hash": packet_hash,
            "dispatch_key": dispatch_key, "state": "reserved", "child_reference_hash": None,
            "delivery_hash": None, "delivery": None}
    data["dispatches"].append(item)
    _save(root, data)
    return {"status": "reserved", "dispatch": item}


def _find(data: dict, dispatch_id: str) -> dict:
    _check(dispatch_id, "dispatch_id")
    for item in data["dispatches"]:
        if item.get("dispatch_id") == dispatch_id:
            return item
    raise ContractError("dispatch_not_found")


def mark_started(root: Path, dispatch_id: str, child_reference: str) -> dict:
    data = _load(root); item = _find(data, dispatch_id); _check(child_reference, "child_reference")
    if item["state"] not in ("reserved", "started"):
        raise ContractError("dispatch_not_startable")
    item["state"] = "started"
    item["child_reference_hash"] = hashlib.sha256(child_reference.encode()).hexdigest()
    _save(root, data)
    return {"status": "started", "dispatch": item}


def record_delivery(root: Path, dispatch_id: str, *, candidate_hash: str, packet_hash: str,
                    delivery: dict, objective_state: str = "RUNNING") -> dict:
    data = _load(root); item = _find(data, dispatch_id)
    candidate_hash, packet_hash = _hash(candidate_hash, "candidate_hash"), _hash(packet_hash, "packet_hash")
    if candidate_hash != item["candidate_hash"] or packet_hash != item["packet_hash"]:
        item["state"] = "stale"; _save(root, data)
        return {"status": "stale", "reason": "candidate_or_packet_changed", "dispatch": item}
    if objective_state in ("PAUSED", "CANCELLED", "FAILED"):
        return {"status": "late_ignored", "reason": "objective_not_running", "dispatch": item}
    if not isinstance(delivery, dict):
        raise ContractError("delivery_must_be_object")
    item["state"] = "delivered"; item["delivery_hash"] = hashlib.sha256(canonical(delivery)).hexdigest()
    item["delivery"] = {k: delivery[k] for k in ("status", "evidence", "summary", "candidate_hash") if k in delivery}
    _save(root, data)
    return {"status": "delivered", "dispatch": item}


def continuation(root: Path, dispatch_id: str, *, objective_state: str = "RUNNING",
                 budget_remaining: bool = True) -> dict:
    data = _load(root); item = _find(data, dispatch_id)
    if objective_state in ("PAUSED", "CANCELLED") or not budget_remaining:
        return {"action": "stop", "reason": "objective_control_or_budget", "dispatch": item}
    if item["state"] in ("stale",):
        return {"action": "reconcile", "reason": "stale_delivery", "dispatch": item}
    if item["state"] in ("reserved",):
        return {"action": "wait", "reason": "dispatch_not_started", "dispatch": item}
    if item["state"] in ("started",):
        return {"action": "reconcile", "reason": "delivery_not_observed", "dispatch": item}
    return {"action": "continue", "reason": "delivery_recorded", "dispatch": item}
