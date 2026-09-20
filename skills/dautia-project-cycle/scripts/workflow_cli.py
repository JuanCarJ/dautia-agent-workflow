#!/usr/bin/env python3
"""DautIA r3 boundaries and audit helpers. No product or remote mutations."""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import shlex
import sqlite3
import sys
from typing import Any
from workflow_core import ContractError, gate, load_json, validate_packet, profile_selection, canonical, fingerprint, routing_arguments
from workflow_store import state_root, atomic_write, read_private, bind, binding, resource_lease, emit, export_events
from workspace_audit import snapshot, reconcile
from skill_catalog import inventory
from audit_ingest import inspect_archive


def read_input(path: Path, limit: int = 256_000) -> dict:
    if path.stat().st_size > limit:
        raise ContractError('input_budget_exceeded')
    return load_json(path.read_bytes())


def refresh_sources(packet: dict, cwd: Path) -> dict:
    p = copy.deepcopy(packet)
    base = cwd.resolve()
    for source in p.get('sources', []):
        relative = source.get('path')
        if relative is None:
            continue  # References outside this checkout need their own verified packet.
        path = Path(relative)
        if path.is_absolute() or '..' in path.parts:
            raise ContractError('source_path_not_contained')
        target = base / path
        if not target.is_file() or target.is_symlink() or base not in target.resolve().parents or target.stat().st_size > 2_000_000:
            source['observed_hash'] = None
        else:
            source['observed_hash'] = hashlib.sha256(target.read_bytes()).hexdigest()
    return p


def safe_read_command(raw: Any) -> bool:
    if not isinstance(raw, str) or any(c in raw for c in ';|&><`$\n\r'):
        return False
    try:
        tokens = shlex.split(raw)
    except ValueError:
        return False
    if not tokens:
        return False
    # Deliberately tiny convenience path, not a shell authorization parser.
    # Git log/show/diff can run pagers, filters or --output; let the bound gate
    # and native permissions handle them rather than assume "git means read".
    if tokens[0] in ('pwd', 'ls', 'cat', 'head', 'wc', 'stat'):
        return True
    if tokens[0] == 'tail':
        return not any(t in ('-f', '-F', '--follow') or t.startswith('--follow=') for t in tokens)
    if tokens[0] in ('grep', 'rg'):
        return not any(t in ('--pre', '--pre-glob', '--hostname-bin') or t.startswith(('--pre=', '--pre-glob=', '--hostname-bin=')) for t in tokens)
    return False


def packet_event(root: Path, packet: dict, event_type: str, stage: str, status: str, **extra) -> dict:
    return emit(root, {'event_type':event_type,'objective_id':packet['objective_id'],
                      'project_id':packet['project_id'],'context_hash':fingerprint(packet),
                      'stage':stage,'status':status,'observation_kind':'local_validator', **extra}, 'workflow')


def hook(payload: dict, root: Path) -> dict:
    if not isinstance(payload, dict) or not isinstance(payload.get('cwd'), str):
        raise ContractError('invalid_hook_input')
    event, session, cwd = payload.get('hook_event_name'), payload.get('session_id'), Path(payload['cwd'])
    current = binding(root, session, cwd, interrupt=event == 'Interrupt')
    if not current:
        return {}  # No global gate for an unbound objective; coverage is explicit.
    if event in ('SubagentStart', 'SubagentStop') or payload.get('agent_id'):
        # Parent session IDs can be shared. Never apply parent authority to a child.
        return {}
    packet = refresh_sources(current['packet'], cwd)
    if current['state'] != 'active':
        packet.setdefault('control', {})['state'] = current['state']
    if event == 'Interrupt':
        packet_event(root,packet,'hook.observed','Interrupt','interrupted')
        return {}  # Never restart a user-interrupted turn.
    if event == 'PreCompact':
        return {}  # The private binding already preserves the core; no transcript copy.
    if event == 'PreToolUse':
        tool = payload.get('tool_name', '')
        if tool not in ('Bash', 'apply_patch', 'Write', 'Edit', 'MultiEdit'):
            return {}
        inp = payload.get('tool_input', {})
        result = gate(packet, 'preflight')
        reasons = result['issues'][:]
        if packet['work']['operation'] == 'read':
            prepared = packet['work'].get('read_commands', [])
            command = inp.get('command', inp.get('cmd')) if isinstance(inp,dict) else None
            auth = packet.get('authority', {})
            matched_read = (tool == 'Bash' and isinstance(command,str) and isinstance(prepared,list)
                            and command in prepared and auth.get('source_kind') in ('user','project_policy')
                            and bool(auth.get('source_refs')) and 'read' in auth.get('operations', [])
                            and auth.get('project_id') == packet['project_id']
                            and auth.get('target') == packet['work'].get('target'))
            if not matched_read: reasons.append('tool_effect_not_read_verified')
        packet_event(root,packet,'hook.observed','PreToolUse','passed' if not reasons else 'blocked')
        if reasons:
            return {'hookSpecificOutput': {'hookEventName': 'PreToolUse', 'permissionDecision': 'deny',
                    'permissionDecisionReason': 'DautIA: ' + ','.join(sorted(set(reasons)))[:1800] + '. Resolve the bound task; no new authority is granted.'}}
        return {}  # The native sandbox/approvals still own execution permission.
    if event == 'Stop':
        if payload.get('stop_hook_active') is True or current['state'] != 'active':
            return {}
        result = gate(packet, 'closeout')
        action = result['next']['action']
        packet_event(root,packet,'continuation.decided','Stop',action)
        if action == 'stop' or action in ('wait_or_request_minimum',):
            return {}
        # Bounded continuation only for an actionable gap, not a generic missing receipt.
        actionable = action in ('continue', 'team_handoff', 'diagnose', 'reconcile')
        if not result['passed'] and actionable and binding(root, session, cwd, reserve_stop=True):
            return {'decision': 'block', 'reason': 'DautIA: ' + action + '. Complete or diagnose the remaining authorized work; update the bound packet. This continuation is not a user approval. Respect pause, permissions and budget.'}
    return {}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--state-root', type=Path)
    sub = ap.add_subparsers(dest='command', required=True)
    g = sub.add_parser('gate'); g.add_argument('stage', choices=('preflight','dispatch','closeout','release')); g.add_argument('packet', type=Path); g.add_argument('--cwd', type=Path)
    b = sub.add_parser('bind'); b.add_argument('packet', type=Path); b.add_argument('--session', required=True); b.add_argument('--generation', required=True); b.add_argument('--cwd', required=True, type=Path)
    sub.add_parser('hook')
    r = sub.add_parser('route'); r.add_argument('packet', type=Path)
    d = sub.add_parser('dispatch-plan'); d.add_argument('packet', type=Path); d.add_argument('--agents-dir', type=Path, required=True); d.add_argument('--cwd', type=Path, required=True); d.add_argument('--allow-network', action='store_true')
    s = sub.add_parser('snapshot'); s.add_argument('--repo', type=Path, required=True); s.add_argument('--repo-id', required=True); s.add_argument('--checkout-id', required=True)
    rec = sub.add_parser('reconcile'); rec.add_argument('before', type=Path); rec.add_argument('after', type=Path); rec.add_argument('--owned', nargs='*', default=[])
    c = sub.add_parser('catalog'); c.add_argument('roots', nargs='+', type=Path)
    i = sub.add_parser('ingest-audit'); i.add_argument('archive', type=Path)
    l = sub.add_parser('lease'); l.add_argument('resource'); l.add_argument('--owner', required=True); l.add_argument('--generation', required=True); l.add_argument('--release', action='store_true')
    e = sub.add_parser('event'); e.add_argument('file', type=Path); e.add_argument('--emitter', default='workflow')
    ex = sub.add_parser('export'); ex.add_argument('objective'); ex.add_argument('--legacy-snapshot', type=Path)
    sub.add_parser('doctor')
    args = ap.parse_args(argv); root = args.state_root or state_root(); code = 0
    try:
        if not root.is_absolute():
            raise ContractError('state_root_must_be_absolute')
        if args.command == 'gate':
            packet = read_input(args.packet)
            if args.cwd: packet = refresh_sources(packet, args.cwd)
            result = gate(packet, args.stage); code = 0 if result['passed'] else 3
            result['telemetry']=packet_event(root,packet,'validation.completed',args.stage,'passed' if result['passed'] else 'blocked')
        elif args.command == 'bind':
            packet = validate_packet(read_input(args.packet))
            if packet.get('fixture_only') is True: raise ContractError('synthetic_fixture_cannot_bind_real_session')
            result = bind(root, args.session, args.cwd, packet, args.generation)
            result['telemetry']=packet_event(root,packet,'context.bound','bind','bound',generation=args.generation)
        elif args.command == 'route':
            p = validate_packet(read_input(args.packet)); w=p['work']; rt=p.get('runtime',{})
            result = profile_selection(**routing_arguments(p))
            code = 0 if result['status'] == 'selected' else 3
        elif args.command == 'dispatch-plan':
            from jev_support import evaluate, load_config, config_dir
            from workflow_dispatch import prepare_dispatch
            packet = refresh_sources(validate_packet(read_input(args.packet)), args.cwd)
            cfg_root = config_dir()
            decision = evaluate('route', packet, load_config(cfg_root), cfg_root,
                                allow_network=args.allow_network, events_root=root)
            result = prepare_dispatch(packet, decision, args.agents_dir)
        elif args.command == 'hook':
            raw = sys.stdin.buffer.read(256_001)
            if len(raw) > 256_000: raise ContractError('hook_input_budget_exceeded')
            result = hook(load_json(raw), root)
        elif args.command == 'snapshot': result = snapshot(args.repo, args.repo_id, args.checkout_id)
        elif args.command == 'reconcile': result = reconcile(read_input(args.before, 2_000_000), read_input(args.after,2_000_000), args.owned)
        elif args.command == 'catalog': result = inventory(args.roots)
        elif args.command == 'ingest-audit': result = inspect_archive(args.archive); code = 0 if result['accepted'] else 3
        elif args.command == 'lease': result = resource_lease(root,args.resource,args.owner,args.generation,args.release); code = 0 if result.get('released',result.get('acquired')) else 3
        elif args.command == 'event': result = emit(root,read_input(args.file),args.emitter)
        elif args.command == 'export':
            result = export_events(root,args.objective)
            if args.legacy_snapshot:
                # Keep old collector output separate. Never copy arbitrary free-form content into statistical events.
                data = args.legacy_snapshot.read_bytes()
                load_json(data)
                result['legacy_snapshot_sha256'] = hashlib.sha256(data).hexdigest()
                result['legacy_snapshot_included'] = False
        else:
            result = {'contract_version':15,'storage_exists':root.exists(),'network_called':False,
                      'hook_coverage':'bound_root_objectives_supported_tools_only','native_runtime_tested':False,
                      'model_availability_verified':False,'telemetry_content':'allowlisted_metadata_only'}
        print(json.dumps(result, ensure_ascii=True, allow_nan=False)); return code
    except (ContractError, OSError, sqlite3.Error, ValueError, TypeError) as exc:
        reason = str(exc) if isinstance(exc,ContractError) else 'local_io_schema_or_store_error'
        # For a synchronous pre-tool hook, exit 2 is a blocking error in the supported harness.
        print('DautIA: '+reason, file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
