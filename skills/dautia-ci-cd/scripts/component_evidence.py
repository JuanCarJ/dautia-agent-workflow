#!/usr/bin/env python3
"""Validate bounded multi-repository/component evidence."""
from __future__ import annotations
import re
from typing import Any
from workflow_core import ContractError

def validate_component_evidence(evidence: Any, required_components: list[str] | None = None,
                                shared_contracts: list[str] | None = None) -> dict:
    if not isinstance(evidence, list): raise ContractError('component_evidence_must_be_list')
    required, shared, seen, normalized = set(required_components or []), set(shared_contracts or []), set(), []
    for item in evidence:
        if not isinstance(item, dict) or not isinstance(item.get('component'), str) or not item['component']:
            raise ContractError('invalid_component_evidence')
        name = item['component']
        if name in seen: raise ContractError('duplicate_component_evidence')
        seen.add(name)
        if not isinstance(item.get('repository'), str) or not item.get('repository') or not re.fullmatch(r'[0-9a-fA-F]{7,64}', str(item.get('candidate_sha', ''))):
            raise ContractError('component_candidate_sha_required')
        if item.get('status') not in ('independent', 'dependent', 'blocked'):
            raise ContractError('invalid_component_status')
        if not isinstance(item.get('checks', []), list) or not all(isinstance(x, str) and x for x in item.get('checks', [])):
            raise ContractError('invalid_component_checks')
        depends = item.get('depends_on', [])
        if not isinstance(depends, list) or not all(isinstance(x, str) and x for x in depends):
            raise ContractError('invalid_component_dependencies')
        if 'contract_changed' in shared and not depends: raise ContractError('shared_contract_dependency_missing')
        normalized.append({'component': name, 'repository': item['repository'], 'candidate_sha': item['candidate_sha'].lower(),
                           'status': item['status'], 'checks': item.get('checks', []), 'depends_on': depends})
    missing = sorted(required - seen)
    if missing: raise ContractError('required_component_evidence_missing:' + ','.join(missing))
    return {'valid': True, 'components': normalized, 'required': sorted(required), 'shared_contracts': sorted(shared)}
