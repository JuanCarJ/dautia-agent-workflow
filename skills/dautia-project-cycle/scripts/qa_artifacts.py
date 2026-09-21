#!/usr/bin/env python3
"""Opt-in evidence workspace with a narrow, observable write boundary."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from workflow_core import ContractError
from workflow_store import atomic_write, private_dir, safe_path

MARKER = '.dautia-qa-workspace.json'


def _resolve_root(path: Path) -> Path:
    if not path.is_absolute():
        raise ContractError('evidence_root_must_be_absolute')
    safe_path(path)
    return path.resolve()


def _root(path: Path) -> Path:
    resolved = _resolve_root(path)
    private_dir(path)
    return resolved


def _overlaps(first: Path, second: Path) -> bool:
    return first == second or first in second.parents or second in first.parents


def prepare_workspace(state_root: Path, evidence_root: Path, product_root: Path | None = None) -> dict[str, Any]:
    evidence = _resolve_root(evidence_root)
    product = product_root.resolve() if product_root is not None else None
    state = _resolve_root(state_root)
    if product is not None and (_overlaps(product, evidence) or _overlaps(product, state)):
        raise ContractError('qa_workspace_overlaps_product_root')
    if _overlaps(state, evidence):
        raise ContractError('qa_state_overlaps_evidence_root')
    _root(evidence_root)
    descriptor = {'schema_version': 1, 'evidence_root': str(evidence),
                  'product_root': str(product) if product is not None else None,
                  'write_scope': 'evidence_only', 'native_enforcement_observed': False,
                  'product_write_granted': False}
    atomic_write(evidence / MARKER, (json.dumps(descriptor, sort_keys=True) + '\n').encode())
    private_dir(state_root)
    atomic_write(state_root / 'qa-evidence-workspace.json', (json.dumps(descriptor, sort_keys=True) + '\n').encode())
    return descriptor


def _contained(root: Path, relative: str) -> Path:
    if not isinstance(relative, str) or not relative or Path(relative).is_absolute() or '..' in Path(relative).parts:
        raise ContractError('evidence_path_not_contained')
    target = root / relative
    safe_path(target)
    resolved = target.resolve()
    if resolved != root and root not in resolved.parents:
        raise ContractError('evidence_path_not_contained')
    return target


def write_evidence(evidence_root: Path, relative: str, data: bytes, *, max_bytes: int = 10_000_000) -> dict[str, Any]:
    root = _resolve_root(evidence_root)
    marker = root / MARKER
    safe_path(marker)
    if not marker.is_file():
        raise ContractError('qa_workspace_not_prepared')
    try:
        descriptor = json.loads(marker.read_text())
    except (OSError, ValueError) as exc:
        raise ContractError('invalid_qa_workspace_descriptor') from exc
    product = Path(descriptor['product_root']).resolve() if descriptor.get('product_root') else None
    if descriptor.get('evidence_root') != str(root) or (product is not None and _overlaps(root, product)):
        raise ContractError('invalid_qa_workspace_descriptor')
    if relative == MARKER:
        raise ContractError('qa_workspace_descriptor_reserved')
    if not isinstance(data, bytes) or len(data) > max_bytes:
        raise ContractError('evidence_size_exceeded')
    target = _contained(root, relative)
    if product is not None and (target.resolve() == product or product in target.resolve().parents):
        raise ContractError('product_write_not_granted')
    target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    atomic_write(target, data)
    return {'written': True, 'path': str(target), 'sha256': hashlib.sha256(data).hexdigest(),
            'bytes': len(data), 'product_write_granted': False}


def inspect_write_boundary(evidence_root: Path, product_root: Path, candidate: Path) -> dict[str, Any]:
    evidence = _resolve_root(evidence_root)
    product = product_root.resolve()
    resolved = candidate.resolve()
    return {'inside_evidence': resolved == evidence or evidence in resolved.parents,
            'inside_product': resolved == product or product in resolved.parents,
            'native_enforcement_observed': False,
            'write_allowed_by_helper': (resolved == evidence or evidence in resolved.parents)
                                       and not (resolved == product or product in resolved.parents)}
