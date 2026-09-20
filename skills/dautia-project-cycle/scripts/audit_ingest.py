#!/usr/bin/env python3
"""Validate a Git audit archive without extracting it or executing its contents."""
from __future__ import annotations
import hashlib
import zipfile
from pathlib import Path, PurePosixPath
from workflow_core import ContractError, load_json

REQUIRED = {'informe-git.md', 'inventario-workspaces.json', 'cambios-locales.json',
            'ramas-pr.json', 'artefactos.json', 'plan-reconciliacion.md', 'manifest.json'}


def inspect_archive(path: Path) -> dict:
    if path.stat().st_size > 40_000_000:
        raise ContractError('audit_archive_too_large')
    try:
        with zipfile.ZipFile(path) as z:
            info = z.infolist()
            if len(info) > 200 or sum(i.file_size for i in info) > 80_000_000:
                raise ContractError('audit_archive_budget_exceeded')
            files: dict[str, bytes] = {}
            for entry in info:
                p = PurePosixPath(entry.filename)
                mode = (entry.external_attr >> 16) & 0o170000
                if (p.is_absolute() or '..' in p.parts or '\\' in entry.filename or ':' in entry.filename or mode == 0o120000 or entry.flag_bits & 1):
                    raise ContractError('unsafe_audit_archive_entry')
                if entry.is_dir():
                    continue
                if p.name in files:
                    raise ContractError('duplicate_audit_basename')
                if entry.file_size > 12_000_000:
                    raise ContractError('audit_entry_too_large')
                files[p.name] = z.read(entry)
    except (zipfile.BadZipFile, RuntimeError, OSError) as exc:
        raise ContractError('invalid_audit_archive') from exc
    missing = sorted(REQUIRED - files.keys())
    if missing:
        return {'accepted': False, 'issues': ['missing_required_files'], 'missing': missing, 'actions_executed': False}
    manifest = load_json(files['manifest.json'])
    if not isinstance(manifest, dict):
        raise ContractError('invalid_audit_manifest')
    # Canonical format emitted by this workflow; alternate historic manifests
    # are retained for inspection but not falsely declared hash-verified.
    items = manifest.get('files', manifest.get('source_files', []))
    if not isinstance(items, list):
        raise ContractError('invalid_manifest_files')
    checked = set(); issues = []
    for item in items:
        if not isinstance(item, dict):
            raise ContractError('invalid_manifest_entry')
        name = item.get('file', item.get('path'))
        if not isinstance(name, str) or PurePosixPath(name).name != name or name not in files or name in checked:
            issues.append('manifest_reference_invalid'); continue
        checked.add(name)
        if hashlib.sha256(files[name]).hexdigest() != item.get('sha256') or len(files[name]) != item.get('bytes'):
            issues.append('manifest_integrity_mismatch')
    if (REQUIRED - {'manifest.json'}) - checked:
        issues.append('manifest_coverage_incomplete')
    for name in REQUIRED:
        if name.endswith('.json'):
            load_json(files[name])
    return {'accepted': not issues, 'issues': sorted(set(issues)), 'files_checked': len(checked),
            'archive_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
            'semantic_privacy_review': 'required_before_export_or_action',
            'recovery_backlog': 'requires_source_review_and_current_workspace_revalidation',
            'prevention_backlog': 'map_supported_findings_to_r3_tests',
            'authorizes_cleanup': False, 'actions_executed': False, 'archive_extracted': False}
