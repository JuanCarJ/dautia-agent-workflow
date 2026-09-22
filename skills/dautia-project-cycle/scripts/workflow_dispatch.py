#!/usr/bin/env python3
"""Bind a routing decision to a generated native worker definition.

The CLI prepares only. A host integration may pass its supported spawn callable
into dispatch_prepared; no sockets, shell proxy, model API or hidden retry is used.
A returned model is a runtime report, not independent provider attestation.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tomllib
from typing import Callable

from workflow_core import (ContractError, READ_ROLES, canonical, fingerprint, gate,
                           policy, profile_selection, routing_arguments)
from workflow_store import emit, safe_path
from workflow_delivery import mark_started, reserve_dispatch


def validate_spawn_report(prepared: dict, returned: dict) -> list[str]:
    """Validate the host's observed native spawn contract.

    A prepared plan is only a request.  The host must echo the role-qualified
    target, the bounded delegation depth and the effective profile.  Missing
    observations are failures of the dispatch contract, not implicit passes.
    """
    if not isinstance(returned, dict):
        return ['native_response_not_object']
    issues: list[str] = []
    if returned.get('agent_type') != prepared.get('agent_type'):
        issues.append('agent_type_mismatch')
    if returned.get('fork_turns') != 'none':
        issues.append('fork_turns_must_be_none')
    if returned.get('model') != prepared.get('model_requested'):
        issues.append('reported_model_mismatch')
    if returned.get('model_reasoning_effort') != prepared.get('effort_requested'):
        issues.append('reported_effort_mismatch')
    return issues


def prepare_dispatch(packet: dict, decision: dict, agents_dir: Path) -> dict:
    checked = gate(packet, 'dispatch')
    if not checked['passed']:
        raise ContractError('dispatch_packet_not_ready')
    if packet['work']['role'] == 'principal':
        raise ContractError('choose_a_worker_role_not_principal')
    if (decision.get('stage') != 'route' or decision.get('context_hash') != fingerprint(packet)
            or decision.get('policy_hash') != fingerprint(policy())):
        raise ContractError('stale_or_unbound_routing_decision')
    if decision.get('dispatch_blocked_reason'):
        raise ContractError('resolve_analysis_before_dispatch')
    selection = decision.get('selection', {})
    selected = selection.get('selected')
    if not selected or selection.get('status') != 'selected':
        raise ContractError('profile_availability_unverified')
    # Recheck eligibility independently of the name supplied by a caller.
    expected = profile_selection(**routing_arguments(packet), recommendation=selected)
    if expected.get('selected') != selected or expected['status'] != 'selected':
        raise ContractError('ineligible_dispatch_profile')
    target = packet['work']['role'] + '__' + selected
    if decision.get('dispatch_target') != target:
        raise ContractError('dispatch_target_mismatch')
    runtime = packet.get('runtime', {})
    if (runtime.get('dispatch_required') is not True
            or runtime.get('required_agent_type') != target
            or runtime.get('required_profile') != selected):
        raise ContractError('dispatch_requirement_not_bound')
    if runtime.get('harness') != 'codex' or target not in runtime.get('available_targets', []):
        raise ContractError('native_target_not_observed')
    path = agents_dir / (target + '.toml')
    safe_path(path)
    if not path.is_file() or path.stat().st_size > 256_000:
        raise ContractError('native_target_definition_missing')
    raw = path.read_bytes()
    manifest_path = agents_dir / 'dautia-r3-definitions.json'
    if not manifest_path.is_file() or manifest_path.stat().st_size > 256_000:
        raise ContractError('native_target_manifest_missing')
    try:
        manifest = json.loads(manifest_path.read_bytes())
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ContractError('invalid_native_target_manifest') from exc
    definitions = manifest.get('definitions') if isinstance(manifest, dict) else None
    expected_hash = definitions.get(target + '.toml') if isinstance(definitions, dict) else None
    if (not isinstance(manifest, dict) or manifest.get('schema_version') != 1
            or not isinstance(expected_hash, str)
            or expected_hash != hashlib.sha256(raw).hexdigest()):
        raise ContractError('native_target_definition_drift')
    try:
        config = tomllib.loads(raw.decode('utf-8'))
    except (UnicodeError, tomllib.TOMLDecodeError) as exc:
        raise ContractError('invalid_native_target_definition') from exc
    profile = policy()['profiles'][selected]
    sandbox = 'read-only' if packet['work']['role'] in READ_ROLES else 'workspace-write'
    if (config.get('name') != target or config.get('model') != profile['model']
            or config.get('model_reasoning_effort') != profile['effort']
            or config.get('sandbox_mode') != sandbox or not config.get('developer_instructions')):
        raise ContractError('native_target_configuration_mismatch')
    result = {'schema_version': 1, 'status': 'prepared', 'agent_type': target,
              'profile_id': selected, 'model_requested': profile['model'], 'effort_requested': profile['effort'],
              'definition_hash': hashlib.sha256(raw).hexdigest(), 'context_hash': fingerprint(packet),
              'policy_hash': fingerprint(policy()), 'decision_hash': fingerprint(decision),
              'dispatch_performed': False, 'model_reported': None, 'effort_reported': None,
              'native_enforcement_verified': False, 'authorizes_action': False,
              'fork_turns_requested': 'none', 'required_agent_type': target,
              'required_profile': selected}
    result['model_provenance'] = {
        'profile_id': selected,
        'policy_hash': result['policy_hash'],
        'definition_hash': result['definition_hash'],
        'configured_source': 'routing_policy_and_generated_definition',
        'model_configured': profile['model'],
        'effort_configured': profile['effort'],
        'reported_source': None,
        'model_reported': None,
        'effort_reported': None,
        'callback_metadata_matched': None,
        'provider_verified': False,
    }
    # Runtime timings and external metadata can vary between identical
    # evaluations. They belong in the audit plan, not the idempotency key.
    result['dispatch_key'] = fingerprint({
        'objective_id': packet['objective_id'], 'project_id': packet['project_id'],
        'block_id': str(packet.get('work', {}).get('block_id', 'root-block')),
        'attempt': str(packet.get('work', {}).get('attempt', 'attempt-1')),
        'profile_id': selected, 'context_hash': result['context_hash'],
        'policy_hash': result['policy_hash'], 'definition_hash': result['definition_hash']})
    result['plan_hash'] = fingerprint(result)
    return result


def dispatch_prepared(packet: dict, decision: dict, prepared: dict, agents_dir: Path,
                      spawn: Callable[[dict], dict], *, events_root: Path | None = None,
                      ledger_root: Path | None = None) -> dict:
    """Consumer for an existing, authorized host's native spawn callable.

    The host maps agent_type/message to its actual tool schema. A failure after
    calling spawn is unknown outcome: reconcile; this function NEVER retries.
    A CLI process cannot call the parent Codex tool, so it must not claim a spawn.
    """
    if packet.get('fixture_only') is True:
        raise ContractError('synthetic_fixture_cannot_dispatch_real_worker')
    current = prepare_dispatch(packet, decision, agents_dir)
    if current['plan_hash'] != prepared.get('plan_hash'):
        raise ContractError('dispatch_plan_changed')
    reservation = None
    if ledger_root is not None:
        reservation = reserve_dispatch(
            ledger_root, objective_id=packet['objective_id'], project_id=packet['project_id'],
            block_id=str(packet.get('work', {}).get('block_id', 'root-block')),
            attempt=str(packet.get('work', {}).get('attempt', 'attempt-1')),
            profile=current['profile_id'], candidate_hash=fingerprint(packet.get('candidate', {})),
            packet_hash=current['context_hash'], dispatch_key=current['dispatch_key'])
        if reservation['status'] == 'reconcile_required':
            return dict(current, status='dispatch_outcome_unknown', dispatch_performed=None,
                        reason='reconcile_before_retry', dispatch_id=reservation['dispatch']['dispatch_id'], reservation=reservation)
        if reservation['status'] == 'reused':
            return dict(current, status='dispatch_already_reserved', dispatch_performed=False,
                        reason='identical_dispatch_reused', dispatch_id=reservation['dispatch']['dispatch_id'], reservation=reservation)
    dispatch_id = reservation['dispatch']['dispatch_id'] if reservation is not None else None
    event = {'objective_id': packet['objective_id'], 'project_id': packet['project_id'],
             'profile_requested': current['profile_id'], 'profile_configured': current['profile_id'],
             'context_hash': current['context_hash'], 'policy_hash': current['policy_hash'],
             'observation_kind': 'host_adapter', 'authorizes_action': False}
    if events_root is not None:
        try:
            emit(events_root, dict(event, event_type='dispatch.requested', status='requested'), 'dispatch')
        except Exception:
            # Telemetry is optional; it must not turn a prepared dispatch into a retry gate.
            pass
    # Context goes to the worker, never into the statistical event stream.
    message = 'Execute only this delegated packet within its authority; return evidence to the principal.\n' + canonical(packet).decode()
    try:
        returned = spawn({'agent_type': current['agent_type'], 'fork_turns': 'none', 'message': message})
    except Exception:
        return dict(current, status='dispatch_outcome_unknown', dispatch_performed=None,
                    reason='reconcile_before_retry', dispatch_id=dispatch_id)
    if not isinstance(returned, dict):
        return dict(current, status='dispatch_outcome_unknown', dispatch_performed=None,
                    reason='unrecognized_native_response', dispatch_id=dispatch_id)
    child = returned.get('agent_id') or returned.get('thread_id') or returned.get('id')
    if not isinstance(child, str) or not child:
        return dict(current, status='dispatch_outcome_unknown', dispatch_performed=None,
                        reason='native_child_identity_missing', dispatch_id=dispatch_id)
    if ledger_root is not None:
        try:
            started = mark_started(ledger_root, reservation['dispatch']['dispatch_id'], child)
            if started.get('status') == 'reconcile_required':
                return dict(current, status='dispatch_outcome_unknown', dispatch_performed=True,
                            child_reference=child, reason='dispatch_child_identity_conflict',
                            delivery_received=False, dispatch_id=dispatch_id)
        except Exception:
            return dict(current, status='dispatch_outcome_unknown', dispatch_performed=True,
                        child_reference=child, reason='dispatch_ledger_write_unknown',
                        delivery_received=False, dispatch_id=dispatch_id)
    model, effort = returned.get('model'), returned.get('model_reasoning_effort')
    contract_issues = validate_spawn_report(current, returned)
    mismatch = bool(contract_issues)
    provenance = dict(current['model_provenance'], reported_source='native_callback_metadata',
                      model_reported=model, effort_reported=effort,
                      callback_metadata_matched=not mismatch)
    result = dict(current, status='dispatch_contract_violation' if mismatch else 'started',
                  dispatch_performed=True, child_reference=child, model_reported=model,
                  effort_reported=effort, delivery_received=False, dispatch_id=dispatch_id,
                  native_enforcement_verified=False,
                  native_callback_metadata_matched=not mismatch,
                  model_provenance=provenance,
                  dispatch_contract_issues=contract_issues)
    if events_root is not None:
        # Only opaque correlation escapes into telemetry; no prompts or native IDs.
        run = 'child-' + hashlib.sha256(child.encode()).hexdigest()[:24]
        try:
            emit(events_root, dict(event, event_type='agent.started', status=result['status'], run_id=run,
                                   model_reported=model, effort_reported=effort), 'dispatch')
        except Exception:
            return dict(result, status='dispatch_outcome_unknown', reason='post_spawn_telemetry_unknown',
                        delivery_received=False)
    return result
