#!/usr/bin/env python3
"""Privacy-safe report for recent observable workflow objectives."""
from __future__ import annotations
from pathlib import Path
from workflow_store import export_events

def report(root: Path, limit: int = 30) -> dict:
    if not root.is_absolute() or limit < 1 or limit > 30:
        raise ValueError('invalid_report_arguments')
    rows = []
    events_root = root / 'events'
    if events_root.exists():
        for directory in events_root.iterdir():
            if not directory.is_dir():
                continue
            exported = export_events(root, directory.name)
            events = sorted(exported.get('events', []), key=lambda e: e.get('occurred_at', ''))
            if not events:
                continue
            rows.append({'objective_id': directory.name,
                         'project_id': next((e.get('project_id') for e in events if e.get('project_id')), None),
                         'event_count': len(events), 'first_observed': events[0].get('occurred_at'),
                         'last_observed': events[-1].get('occurred_at'),
                         'profiles': sorted({x for e in events for x in (e.get('profile_requested'), e.get('selected_profile'), e.get('profile_configured')) if x}),
                         'stages': sorted({e.get('stage') for e in events if e.get('stage')}),
                         'statuses': sorted({e.get('status') for e in events if e.get('status')}),
                         'dispatch_count': sum(e.get('event_type') == 'dispatch.requested' for e in events),
                         'child_start_count': sum(e.get('event_type') == 'agent.started' for e in events),
                         'unknown_count': sum(e.get('status') in ('unknown', 'dispatch_outcome_unknown') for e in events),
                         'telemetry_warnings': exported.get('warnings', [])})
    rows.sort(key=lambda x: x.get('last_observed') or '', reverse=True)
    return {'schema_version': 1, 'limit': limit, 'objectives': rows[:limit],
            'observable_objectives': len(rows), 'coverage': 'event_stream_only',
            'usage_aggregation': 'delegated_to_cycle_collector; no token re-sum',
            'unknowns_preserved': True, 'raw_prompts_included': False}
