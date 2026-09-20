#!/usr/bin/env python3
"""Private operational bindings, cooperative resource leases and minimal events.

No cleanup, remote calls, raw transcripts, commands, tool payloads or credentials
are collected. This complements the existing cycle telemetry collector.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import hmac
import json
import os
from pathlib import Path
import sqlite3
import stat
import tempfile
import uuid
from contextlib import contextmanager
from typing import Any

from workflow_core import ContractError, IDENTIFIER, canonical, load_json


def state_root() -> Path:
    root = Path(os.environ.get("XDG_STATE_HOME", str(Path.home() / ".local/state"))).expanduser()
    if not root.is_absolute():
        raise ContractError("state_root_must_be_absolute")
    return root / "dautia"


def safe_path(path: Path) -> None:
    # macOS exposes its private temporary tree through the stable `/var`
    # alias. Rejecting that system alias makes every tempfile-backed fixture
    # fail before the private directory itself can be checked. Explicit
    # symlinks in the requested path remain rejected.
    system_aliases = {Path('/var'): Path('/private/var'), Path('/tmp'): Path('/private/tmp')}
    for candidate in [path, *path.parents]:
        if candidate.is_symlink() and system_aliases.get(candidate) != candidate.resolve():
            raise ContractError("symlinked_private_path")


def private_dir(path: Path) -> None:
    safe_path(path)
    path.mkdir(mode=0o700, parents=True, exist_ok=True)
    info = path.stat()
    if not stat.S_ISDIR(info.st_mode) or (os.name == "posix" and info.st_uid != os.getuid()):
        raise ContractError("private_directory_owner_mismatch")
    path.chmod(0o700)


def read_private(path: Path, limit: int = 1_000_000) -> bytes:
    safe_path(path)
    fd = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    with os.fdopen(fd, "rb") as stream:
        st = os.fstat(stream.fileno())
        if not stat.S_ISREG(st.st_mode) or st.st_size > limit:
            raise ContractError("invalid_private_file")
        if os.name == "posix" and (st.st_uid != os.getuid() or st.st_mode & 0o077):
            raise ContractError("unsafe_private_file_permissions")
        return stream.read(limit + 1)


def atomic_write(path: Path, data: bytes, mode: int = 0o600) -> None:
    private_dir(path.parent)
    safe_path(path)
    fd, name = tempfile.mkstemp(prefix=".pending-", dir=path.parent)
    try:
        os.fchmod(fd, mode)
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


@contextmanager
def database(root: Path, name: str):
    if name not in ("leases.sqlite3", "bindings.sqlite3"):
        raise ContractError("invalid_store_name")
    private_dir(root)
    path = root / name
    safe_path(path)
    try:
        fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY | getattr(os, "O_NOFOLLOW", 0), 0o600)
        os.close(fd)
    except FileExistsError:
        read_private(path, 64_000_000)
    db = sqlite3.connect(path, timeout=3)
    try:
        db.execute("PRAGMA journal_mode=DELETE")
        db.execute("PRAGMA synchronous=FULL")
        yield db
    finally:
        db.close()


def resource_lease(root: Path, resource: str, owner: str, generation: str, release: bool = False) -> dict:
    for value in (resource, owner, generation):
        if not isinstance(value, str) or not IDENTIFIER.fullmatch(value):
            raise ContractError("invalid_lease_identity")
    with database(root, "leases.sqlite3") as db:
        db.execute("CREATE TABLE IF NOT EXISTS leases (resource TEXT PRIMARY KEY, owner TEXT NOT NULL, generation TEXT NOT NULL)")
        with db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT owner, generation FROM leases WHERE resource=?", (resource,)).fetchone()
            if release:
                if row != (owner, generation):
                    return {"released": False, "reason": "lease_owner_or_generation_mismatch"}
                db.execute("DELETE FROM leases WHERE resource=?", (resource,))
                return {"released": True}
            if row and row != (owner, generation):
                return {"acquired": False, "reason": "resource_in_use"}
            db.execute("INSERT OR IGNORE INTO leases VALUES (?,?,?)", (resource, owner, generation))
            return {"acquired": True, "generation": generation, "scope": "cooperative_local_host_only"}


def bind(root: Path, session: str, cwd: Path, packet: dict, generation: str) -> dict:
    from workflow_core import validate_packet, fingerprint
    validate_packet(packet)
    if not IDENTIFIER.fullmatch(session) or not IDENTIFIER.fullmatch(generation):
        raise ContractError("invalid_binding_identity")
    with database(root, "bindings.sqlite3") as db:
        db.execute("CREATE TABLE IF NOT EXISTS bindings (session TEXT PRIMARY KEY, cwd TEXT, generation TEXT, packet BLOB, state TEXT, stop_count INTEGER)")
        with db:
            db.execute("BEGIN IMMEDIATE")
            old = db.execute("SELECT generation, stop_count FROM bindings WHERE session=?", (session,)).fetchone()
            count = old[1] if old and old[0] == generation else 0
            db.execute("INSERT OR REPLACE INTO bindings VALUES (?,?,?,?,?,?)", (session, str(cwd.resolve()), generation, canonical(packet), "active", count))
    return {"bound": True, "packet_hash": fingerprint(packet), "generation": generation, "authority_verified_by_store": False}


def binding(root: Path, session: str, cwd: Path, *, interrupt: bool = False, reserve_stop: bool = False) -> dict | None:
    if not (root / "bindings.sqlite3").exists():
        return None
    if not isinstance(session, str) or not IDENTIFIER.fullmatch(session):
        raise ContractError("invalid_binding_identity")
    with database(root, "bindings.sqlite3") as db:
        with db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT cwd,generation,packet,state,stop_count FROM bindings WHERE session=?", (session,)).fetchone()
            if not row:
                return None
            if row[0] != str(cwd.resolve()):
                raise ContractError("binding_workspace_mismatch")
            state, count = row[3], row[4]
            if interrupt:
                state = "interrupted"
                db.execute("UPDATE bindings SET state=? WHERE session=?", (state, session))
            if reserve_stop:
                if state != "active" or count >= 2:
                    return None
                db.execute("UPDATE bindings SET stop_count=stop_count+1 WHERE session=?", (session,))
            return {"generation": row[1], "packet": load_json(row[2]), "state": state, "stop_count": count}


EVENT_TYPES = {
    "objective.opened", "objective.closed", "objective.reopened", "context.bound", "context.invalidated",
    "skill.selected", "skill.load_observed", "route.evaluated", "dispatch.requested", "agent.started",
    "agent.ended", "handoff.received", "validation.completed", "review.completed", "spec_change.proposed",
    "spec_change.authorized", "scope.changed", "continuation.decided", "work.blocked", "usage.observed",
    "telemetry.degraded", "workspace.reconciled", "hook.observed",
}
EVENT_FIELDS = {"event_id", "event_type", "objective_id", "project_id", "work_item_id", "run_id", "parent_run_id", "generation", "repo_id", "workspace_id", "candidate_hash", "context_hash", "policy_hash", "question_hash", "skill_hash", "profile_requested", "profile_configured", "profile_reported", "effort_reported", "recommended_profile", "selected_profile", "mode", "stage", "status", "reason_code", "observation_kind", "input_tokens", "output_tokens", "cached_input_tokens", "reasoning_output_tokens", "duration_ms", "network_called", "own_residual_count", "authorizes_action", "probabilities", "confidence", "model_reported", "occurred_at", "retry_of", "included_by", "usage_scope", "question_id", "question_revision", "choice"}
NUMBER_FIELDS = {"input_tokens", "output_tokens", "cached_input_tokens", "reasoning_output_tokens", "duration_ms", "own_residual_count"}


def validate_event(event: Any) -> dict:
    if not isinstance(event, dict) or set(event) - EVENT_FIELDS:
        raise ContractError("unknown_telemetry_fields")
    if event.get("event_type") not in EVENT_TYPES:
        raise ContractError("invalid_event_type")
    if not nonempty_alias(event.get("objective_id")):
        raise ContractError("objective_alias_required")
    for key, value in event.items():
        if value is None:
            continue
        if key in NUMBER_FIELDS:
            if type(value) not in (int, float) or not 0 <= value < 10**18:
                raise ContractError("invalid_numeric_telemetry")
        elif key in ("network_called", "authorizes_action"):
            if type(value) is not bool or (key == "authorizes_action" and value):
                raise ContractError("invalid_telemetry_boolean")
        elif key == "probabilities":
            if not isinstance(value, dict) or len(value) > 64:
                raise ContractError("invalid_probabilities")
            for label, probability in value.items():
                if not nonempty_alias(label) or type(probability) not in (int, float) or not 0 <= probability <= 1:
                    raise ContractError("invalid_probability")
        elif key == "confidence":
            if type(value) not in (int, float) or not 0 <= value <= 1:
                raise ContractError("invalid_confidence")
        elif key == "occurred_at":
            if not isinstance(value, str) or len(value) > 40:
                raise ContractError("invalid_event_time")
            try:
                stamp = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
                if stamp.tzinfo is None:
                    raise ValueError()
            except ValueError as exc:
                raise ContractError("invalid_event_time") from exc
        elif not nonempty_alias(value):
            raise ContractError("unsafe_telemetry_text")
    canonical(event)
    return event


def nonempty_alias(value: Any) -> bool:
    return isinstance(value, str) and bool(IDENTIFIER.fullmatch(value)) and not any(value.lower().startswith(t) for t in ("bearer", "ghp_", "github_pat_", "sk-", "sb_secret_"))


def emit(root: Path, event: dict, emitter: str = "workflow") -> dict:
    """Best-effort diagnostics; a failed exporter cannot authorize or block work."""
    if os.environ.get("DAUTIA_TELEMETRY") == "off":
        return {"recorded": False, "disabled": True}
    try:
        validate_event(event)
        if not nonempty_alias(emitter):
            raise ContractError("invalid_emitter")
        import fcntl
        directory = root / "events" / event["objective_id"]
        private_dir(directory)
        path = directory / (emitter + ".jsonl")
        safe_path(path)
        fd = os.open(path, os.O_WRONLY | os.O_APPEND | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0), 0o600)
        with os.fdopen(fd, "ab") as stream:
            st = os.fstat(stream.fileno())
            if st.st_mode & 0o077 or st.st_uid != os.getuid():
                raise ContractError("unsafe_event_store")
            fcntl.flock(stream, fcntl.LOCK_EX)
            try:
                if os.fstat(stream.fileno()).st_size > 8_000_000:
                    raise ContractError("event_stream_budget_exceeded")
                stored = dict(event)
                stored.setdefault("event_id", uuid.uuid4().hex)
                stored.setdefault("occurred_at", dt.datetime.now(dt.timezone.utc).isoformat())
                stored["observed_at"] = dt.datetime.now(dt.timezone.utc).isoformat()
                stored["schema_version"] = 1
                stored["emitter_id"] = emitter
                stream.write(canonical(stored) + b"\n")
                stream.flush()
            finally:
                fcntl.flock(stream, fcntl.LOCK_UN)
        return {"recorded": True, "event_id": stored["event_id"]}
    except (ContractError, OSError, ImportError):
        return {"recorded": False, "warning": "telemetry_degraded"}


def export_events(root: Path, objective: str, legacy_snapshot: dict | None = None) -> dict:
    if not nonempty_alias(objective):
        raise ContractError("invalid_objective_alias")
    events, seen, warnings = [], {}, []
    for path in sorted((root / "events" / objective).glob("*.jsonl")):
        raw = read_private(path, 16_000_000)
        for index, line in enumerate(raw.splitlines()):
            try:
                event = load_json(line)
                validate_event({k: v for k, v in event.items() if k not in ("observed_at", "schema_version", "emitter_id")})
                if event.get("objective_id") != objective:
                    raise ContractError("cross_objective_event")
                eid = event.get("event_id")
                if not nonempty_alias(eid):
                    raise ContractError("event_id_required")
                if eid in seen:
                    if canonical({k:v for k,v in seen[eid].items() if k != "observed_at"}) != canonical({k:v for k,v in event.items() if k != "observed_at"}):
                        warnings.append("conflicting_duplicate_event")
                    continue
                seen[eid] = event
                events.append(event)
            except (ContractError, AttributeError):
                warnings.append("unreadable_or_unsupported_event")
    # Preserve the existing collector's result, never re-sum cumulative counters.
    # The caller must supply only its already-sanitized snapshot, not raw logs.
    return {"schema_version": 1, "objective_id": objective, "events": events,
            "event_count": len(events), "warnings": sorted(set(warnings)),
            "legacy_snapshot_hash": hashlib.sha256(canonical(legacy_snapshot)).hexdigest() if legacy_snapshot is not None else None, "usage_aggregation": "legacy_collector_owns_session_counters",
            "evidence_completeness": "partial" if warnings else "events_only_not_semantic_acceptance"}
