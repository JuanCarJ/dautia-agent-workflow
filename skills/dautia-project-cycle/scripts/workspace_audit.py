#!/usr/bin/env python3
"""Bounded, read-only workspace observations. Never stage, stash, delete or fetch."""
from __future__ import annotations
import hashlib
import os
import stat
import subprocess
from pathlib import Path
from workflow_core import ContractError, fingerprint

MAX_OUTPUT = 2_000_000
MAX_FILE = 8_000_000


def git(repo: Path, *args: str, optional: bool = False) -> bytes:
    env = dict(os.environ, GIT_OPTIONAL_LOCKS='0', GIT_PAGER='cat', GIT_TERMINAL_PROMPT='0')
    try:
        p = subprocess.run(['git', '--no-optional-locks', '-c', 'core.fsmonitor=false', '-C', str(repo), *args],
                           env=env, capture_output=True, timeout=15, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ContractError('git_unavailable_or_timeout') from exc
    if len(p.stdout) > MAX_OUTPUT or len(p.stderr) > MAX_OUTPUT:
        raise ContractError('git_output_budget_exceeded')
    if p.returncode and not optional:
        raise ContractError('git_read_failed')
    return p.stdout if not p.returncode else b''


def digest_path(root: Path, relative: str) -> str | None:
    path = Path(relative)
    if path.is_absolute() or '..' in path.parts:
        raise ContractError('path_outside_workspace')
    target = root / path
    # Do not follow a symlink directory, even for metadata collection.
    if any(p.is_symlink() for p in list(target.parents) if p != root and root in p.parents):
        return None
    try:
        st = target.lstat()
        if stat.S_ISLNK(st.st_mode):
            return hashlib.sha256(os.fsencode(os.readlink(target))).hexdigest()
        if not stat.S_ISREG(st.st_mode) or st.st_size > MAX_FILE:
            return None
        with target.open('rb') as f:
            data = f.read(MAX_FILE + 1)
        if len(data) > MAX_FILE or target.stat().st_mtime_ns != st.st_mtime_ns:
            return None
        return hashlib.sha256(data).hexdigest()
    except FileNotFoundError:
        return 'absent'
    except OSError:
        return None


def parse_status(data: bytes) -> list[dict]:
    items = data.split(b'\0'); out = []; i = 0
    while i < len(items):
        raw = items[i]; i += 1
        if not raw or raw.startswith(b'# '):
            continue
        kind = raw[:1]
        if kind in (b'?', b'!'):
            path = raw[2:]; xy = kind.decode(); original = None
        elif kind in (b'1', b'2', b'u'):
            fields = raw.split(b' ', {b'1': 8, b'2': 9, b'u': 10}[kind])
            if len(fields) != {b'1': 9, b'2': 10, b'u': 11}[kind]:
                raise ContractError('unsupported_porcelain_record')
            xy, path, original = fields[1].decode('ascii'), fields[-1], None
            if kind == b'2':
                if i >= len(items) or not items[i]:
                    raise ContractError('truncated_rename_record')
                original = os.fsdecode(items[i]); i += 1
        else:
            raise ContractError('unsupported_porcelain_record')
        out.append({'path': os.fsdecode(path), 'status': xy, 'original_path': original})
    return out


def snapshot(repo: Path, repo_id: str, checkout_id: str) -> dict:
    root = Path(os.fsdecode(git(repo, 'rev-parse', '--show-toplevel')).strip()).resolve()
    head = git(root, 'rev-parse', 'HEAD', optional=True).decode().strip() or None
    branch = git(root, 'symbolic-ref', '--short', '-q', 'HEAD', optional=True).decode().strip() or None
    upstream = git(root, 'rev-parse', '--symbolic-full-name', '@{upstream}', optional=True).decode().strip() or None
    # A configured clean/process filter may run on content comparison. Do not run it.
    filters = git(root, 'config', '--get-regexp', r'^filter\..*\.(clean|process)$', optional=True)
    if filters:
        return {'schema_version': 1, 'repo_id': repo_id, 'checkout_id': checkout_id, 'head': head,
                'branch': branch, 'upstream_local': upstream, 'coverage': 'partial',
                'reason': 'external_filter_present_comparison_not_executed', 'entries': [], 'remote_verified': False}
    index_before = git(root, 'ls-files', '--stage', '-z')
    raw = git(root, 'status', '--porcelain=v2', '-z', '--untracked-files=all')
    entries = parse_status(raw)
    if len(entries) > 4000:
        raise ContractError('workspace_entry_budget_exceeded')
    for entry in entries:
        entry['content_hash'] = digest_path(root, entry['path'])
        entry['owner'] = 'unknown'
    head_after = git(root, 'rev-parse', 'HEAD', optional=True).decode().strip() or None
    index_after = git(root, 'ls-files', '--stage', '-z')
    raw_after = git(root, 'status', '--porcelain=v2', '-z', '--untracked-files=all')
    changed = head != head_after or index_before != index_after or raw != raw_after
    changed = changed or any(digest_path(root, e['path']) != e['content_hash'] for e in entries)
    return {'schema_version': 1, 'repo_id': repo_id, 'checkout_id': checkout_id, 'head': head,
            'branch': branch, 'upstream_local': upstream, 'index_hash': hashlib.sha256(index_after).hexdigest(),
            'entries': entries, 'concurrent_change_detected': changed,
            'coverage': 'partial' if changed or any(e['content_hash'] is None for e in entries) else 'complete_for_status_entries',
            'ignored_content_inspected': False, 'remote_verified': False,
            'disposable': False, 'observation': 'local_only_no_authority_or_authorship_inferred'}


def reconcile(before: dict, after: dict, owned_paths: list[str]) -> dict:
    if any(before.get(k) != after.get(k) for k in ('repo_id', 'checkout_id')):
        raise ContractError('workspace_identity_mismatch')
    owned = set(owned_paths)
    b = {e['path']: e for e in before.get('entries', [])}
    a = {e['path']: e for e in after.get('entries', [])}
    uncertain = before.get('coverage') != 'complete_for_status_entries' or after.get('coverage') != 'complete_for_status_entries'
    changed_foreign = [p for p in b if p not in owned and (p not in a or a[p]['content_hash'] != b[p]['content_hash'] or a[p]['status'] != b[p]['status'])]
    mixed = sorted(set(b) & owned)
    own_remaining = sorted(owned & set(a))
    unknown_new = sorted(set(a) - set(b) - owned)
    return {'foreign_preserved': None if uncertain or mixed else not changed_foreign,
            'foreign_changed': sorted(changed_foreign), 'mixed_preexisting_paths': mixed,
            'own_residual_paths': own_remaining, 'new_unattributed_paths': unknown_new,
            'reconciled': not (uncertain or changed_foreign or mixed or own_remaining or unknown_new),
            'disposable': False, 'mutations_performed': False,
            'note': 'Mixed hunks need independent preservation evidence; no file-wide ownership inference.'}
