#!/usr/bin/env python3
"""Per-repository integration and per-component delivery. No live provider claims."""
from __future__ import annotations
import json
import re
import subprocess
from pathlib import Path, PurePosixPath
from typing import Any

IDENT = re.compile(r'^[A-Za-z0-9_.-]{1,100}$')
SECRET_KEY = re.compile(r'(?i)(password|passwd|secret|token|api[_-]?key|private[_-]?key|credential|connection[_-]?string)')
SECRET_VALUE = re.compile(r'(?i)(-----BEGIN .*PRIVATE KEY-----|Bearer\s+[\w.-]+|\b(?:sk-|ghp_|github_pat_|sb_secret_)[\w-]{8,}|://[^\s/:]+:[^\s/@]+@)')


def nonempty(v: Any) -> bool:
    return isinstance(v,str) and bool(v.strip())


def relative(v: Any) -> bool:
    return nonempty(v) and not any(ord(c) < 32 for c in v) and not PurePosixPath(v).is_absolute() and '..' not in PurePosixPath(v).parts and '\\' not in v and ':' not in v


def branch(v: Any) -> bool:
    return nonempty(v) and not any(ord(c) < 32 or ord(c) == 127 for c in v) and not any(c in v for c in ' ~^:?*[\\') and not any(x in v for x in ('..','@{','//')) and not v.startswith(('-', '/','.')) and not v.endswith(('/','.','.lock'))


def validate_v3(c: Any, repo: Path | None = None, require_active: bool = False) -> list[str]:
    errors: list[str] = []
    def bad(code: str): errors.append(code)
    if not isinstance(c,dict) or type(c.get('schema_version')) is not int or c['schema_version'] != 3:
        return ['schema_version_must_be_3']
    def secrets(v: Any, depth: int = 0):
        if depth > 20: bad('contract_too_deep'); return
        if isinstance(v,dict):
            for key,value in v.items():
                if SECRET_KEY.search(str(key)): bad('credential_key_forbidden')
                secrets(value,depth+1)
        elif isinstance(v,list):
            for value in v: secrets(value,depth+1)
        elif isinstance(v,str) and SECRET_VALUE.search(v): bad('secret_value_forbidden')
    secrets(c)
    base={'schema_version','project','product_topology','repository_layout','configuration_status','production_enabled'}
    optional={'activation_blocked_reason','repositories','codebases','targets','provider_projects'}
    if set(c)-base-optional: bad('unknown_top_level_field')
    if base-set(c): bad('missing_base_field')
    if not isinstance(c.get('project'),str) or not IDENT.fullmatch(c['project']): bad('invalid_project')
    state=c.get('configuration_status')
    if state not in ('active','draft'): bad('invalid_configuration_status')
    if type(c.get('production_enabled')) is not bool: bad('production_enabled_must_be_boolean')
    if c.get('repository_layout') not in ('single-repo','monorepo','multi-repo'): bad('invalid_repository_layout')
    if c.get('product_topology') not in ('single-codebase','multi-codebase'): bad('invalid_product_topology')
    if state=='draft':
        if c.get('production_enabled') is not False or not nonempty(c.get('activation_blocked_reason')): bad('draft_requires_disabled_production_and_reason')
        if require_active: bad('active_configuration_required')
        if set(c)&{'repositories','codebases','targets','provider_projects'}: bad('draft_cannot_claim_active_sections')
        return sorted(set(errors))
    if 'activation_blocked_reason' in c: bad('active_cannot_have_blocked_reason')
    def entries(key: str, required: bool = True) -> list[dict]:
        value=c.get(key,[])
        if not isinstance(value,list) or any(not isinstance(x,dict) for x in value) or (required and not value):
            bad('invalid_'+key); return []
        ids=[x.get('id') for x in value]
        if any(not isinstance(x,str) or not IDENT.fullmatch(x) for x in ids) or len(set(str(x) for x in ids)) != len(ids): bad('invalid_ids_'+key)
        return value
    repos=entries('repositories'); components=entries('codebases'); targets=entries('targets'); providers=entries('provider_projects',False)
    rb={x.get('id'):x for x in repos if isinstance(x.get('id'),str)}
    cb={x.get('id'):x for x in components if isinstance(x.get('id'),str)}
    paths=[]
    for r in repos:
        if set(r) != {'id','path','integration_branch'}: bad('invalid_repository_fields')
        if not relative(r.get('path')): bad('repository_path_not_contained')
        if not branch(r.get('integration_branch')): bad('invalid_integration_branch')
        paths.append(r.get('path'))
    if len(set(str(p) for p in paths))!=len(paths): bad('duplicate_repository_path')
    if c.get('repository_layout') in ('single-repo','monorepo') and len(repos)!=1: bad('layout_requires_one_repository')
    if c.get('repository_layout')=='multi-repo' and len(repos)<2: bad('layout_requires_multiple_repositories')
    if c.get('product_topology')=='single-codebase' and len(components)!=1: bad('topology_requires_one_codebase')
    if c.get('product_topology')=='multi-codebase' and len(components)<2: bad('topology_requires_multiple_codebases')
    component_paths=[]
    for x in components:
        if set(x)-{'id','repository','path','kind','status','required_capabilities'} or {'id','repository','path','kind','status'}-set(x): bad('invalid_codebase_fields')
        if not isinstance(x.get('repository'),str) or x['repository'] not in rb: bad('unknown_codebase_repository')
        if not relative(x.get('path')) or not nonempty(x.get('kind')) or x.get('status') not in ('active','planned'): bad('invalid_codebase')
        caps=x.get('required_capabilities',[])
        if not isinstance(caps,list) or any(not nonempty(v) for v in caps): bad('invalid_codebase_capabilities')
        component_paths.append((str(x.get('repository')),str(x.get('path'))))
    if len(set(component_paths))!=len(component_paths): bad('duplicate_codebase_path')
    target_keys=[]
    for t in targets:
        required={'id','component','environment','state','deploy_enabled','target','checks','rollback_ref'}
        if required-set(t) or set(t)-required-{'branch','provider'}: bad('invalid_target_fields')
        if not isinstance(t.get('component'),str) or t['component'] not in cb: bad('unknown_target_component')
        if t.get('state') not in ('observed','planned') or type(t.get('deploy_enabled')) is not bool: bad('invalid_target_state')
        if t.get('state')=='planned' and t.get('deploy_enabled') is not False: bad('planned_target_cannot_deploy')
        if t.get('environment')=='production' and t.get('deploy_enabled') is True and c.get('production_enabled') is not True: bad('production_disabled')
        if any(not nonempty(t.get(k)) for k in ('environment','target','rollback_ref')): bad('target_identity_and_recovery_required')
        checks=t.get('checks')
        if not isinstance(checks,list) or any(not nonempty(v) for v in checks) or (t.get('state')=='observed' and not checks): bad('observed_target_requires_checks')
        if 'branch' in t and not branch(t['branch']): bad('invalid_target_branch')
        if t.get('environment')=='integration' and isinstance(t.get('component'),str) and t['component'] in cb:
            r=rb.get(str(cb[t['component']].get('repository')), {})
            if t.get('branch')!=r.get('integration_branch'): bad('integration_target_mismatches_own_repository')
        target_keys.append((str(t.get('component')),str(t.get('environment')),str(t.get('target'))))
    if len(set(target_keys))!=len(target_keys): bad('duplicate_target_binding')
    for component in components:
        if component.get('status')=='active' and not any(t.get('component')==component.get('id') and t.get('environment')=='integration' for t in targets): bad('active_component_requires_integration_target')
    provider_keys=[]
    for p in providers:
        required={'id','provider','component','environment','target_id','workdir'}
        if required-set(p) or set(p)-required-{'project_ref'}: bad('invalid_provider_fields')
        if not isinstance(p.get('component'),str) or p['component'] not in cb or not relative(p.get('workdir')): bad('invalid_provider_component_or_path')
        matches=[t for t in targets if t.get('id')==p.get('target_id') and t.get('component')==p.get('component') and t.get('environment')==p.get('environment')]
        if len(matches)!=1: bad('provider_target_binding_missing')
        if not isinstance(p.get('provider'),str) or not IDENT.fullmatch(p['provider']): bad('invalid_provider')
        if p.get('provider')=='supabase':
            if not re.fullmatch(r'[a-z]{20}',str(p.get('project_ref',''))) or p.get('environment') not in ('staging','production'): bad('invalid_supabase_target')
        provider_keys.append(tuple(str(p.get(k)) for k in ('provider','component','environment','target_id')))
    if len(set(provider_keys))!=len(provider_keys): bad('duplicate_provider_binding')
    if repo is not None and not errors:
        root=repo.resolve()
        for r in repos:
            path=(root/r['path']).resolve()
            if path!=root and root not in path.parents: bad('repository_escapes_root'); continue
            names={r['integration_branch']}
            owned={x['id'] for x in components if x['repository']==r['id']}
            names|={t['branch'] for t in targets if t['component'] in owned and t['state']=='observed' and 'branch' in t}
            for name in names:
                try:
                    args=['git','--no-optional-locks','-c','core.fsmonitor=false','-C',str(path),'show-ref','--verify','--quiet']
                    local=subprocess.run(args+['refs/heads/'+name],capture_output=True,timeout=5)
                    remote=subprocess.run(args+['refs/remotes/origin/'+name],capture_output=True,timeout=5) if local.returncode else local
                    if local.returncode and remote.returncode: bad('declared_branch_not_observed_locally')
                except (OSError,subprocess.TimeoutExpired): bad('repository_unavailable')
    return sorted(set(errors))


def select_provider(contract: dict, provider: str, environment: str, component: str | None = None, target_id: str | None = None) -> dict:
    errors=validate_v3(contract,require_active=True)
    if errors: raise ValueError('invalid_delivery_v3:'+','.join(errors))
    matches=[p for p in contract.get('provider_projects',[]) if p['provider']==provider and p['environment']==environment and (component is None or p['component']==component) and (target_id is None or p['target_id']==target_id)]
    if len(matches)!=1: raise ValueError('target_missing_or_ambiguous_select_component_and_target')
    return matches[0]
