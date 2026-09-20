#!/usr/bin/env python3
"""Read-only checkout observation. Integration and workspace cleanup are separate.

No fetch, checkout, reset, stage or cleanup. Remote freshness is never inferred
from a local tracking ref. An objective packet is required for closeout checks.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import subprocess
import sys
HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(HERE),str(HERE.parents[1]/'dautia-project-cycle/scripts')]
from workflow_core import ContractError, load_json, gate
from workspace_audit import snapshot
from delivery_v3 import relative, branch as valid_branch

class CheckoutError(ValueError): pass

def declared_repositories(c):
    if c.get('configuration_status')!='active':raise CheckoutError('delivery_not_active')
    if c.get('schema_version') in (2,3):
        entries=c.get('repositories')
        if not isinstance(entries,list) or not entries:raise CheckoutError('repositories_missing')
        result=[]
        for r in entries:
            if not isinstance(r,dict) or not isinstance(r.get('id'),str) or not relative(r.get('path')) or not valid_branch(r.get('integration_branch')):raise CheckoutError('invalid_repository_binding')
            result.append((r['id'],r['path'],r['integration_branch']))
        if len({x[0] for x in result})!=len(result):raise CheckoutError('duplicate_repository_identity')
        return result
    if c.get('schema_version')==1:
        name=c.get('branches',{}).get('integration',{}).get('name')
        if not valid_branch(name):raise CheckoutError('integration_branch_missing')
        return [(c.get('project','product'),'.',name)]
    raise CheckoutError('unsupported_delivery_version')

def require_integration_bindings(packet, observations):
    entries=packet.get('workspaces',[])
    if not isinstance(entries,list):raise CheckoutError('integration_requirement_missing')
    for observed in observations:
        ident=observed['repository']
        matches=[w for w in entries if isinstance(w,dict) and w.get('repo_id')==ident]
        if len(matches)!=1 or matches[0].get('integration_required') is not True:
            raise CheckoutError('integration_requirement_missing')
        if matches[0].get('integration_branch')!=observed['integration_branch']:
            raise CheckoutError('integration_branch_binding_mismatch')
    return True

def run(repo,*args):
    return subprocess.run(['git','--no-optional-locks','-c','core.fsmonitor=false','-C',str(repo),*args],text=True,capture_output=True,timeout=8)

def inspect(repo_id,repo,integration,mode):
    observed=snapshot(repo,repo_id,'checkout-'+repo_id)
    target=None
    for ref in ('refs/remotes/origin/'+integration,'refs/heads/'+integration):
        if run(repo,'show-ref','--verify','--quiet',ref).returncode==0:target=ref;break
    notes=['local observation only; remote freshness unverified']
    return {'repository':repo_id,'integration_branch':integration,'target_ref':target,
            'workspace':observed,'verdict':'REVIEW','notes':notes,
            'integration_verified':False,'disposable':False,'mode':mode}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('contract',type=Path);p.add_argument('--repo',type=Path);p.add_argument('--repository',action='append',default=[])
    p.add_argument('--mode',choices=('start','candidate','closeout'),default='start');p.add_argument('--closure-packet',type=Path);p.add_argument('--json',action='store_true')
    a=p.parse_args()
    try:
        root=(a.repo or a.contract.parent).resolve();declared=declared_repositories(load_json(a.contract.read_bytes()))
        if set(a.repository)-{x[0] for x in declared}:raise CheckoutError('unknown_repository')
        results=[]
        for ident,path,integration in declared:
            if a.repository and ident not in a.repository:continue
            cwd=(root/path).resolve()
            if cwd!=root and root not in cwd.parents:raise CheckoutError('repository_path_escapes_root')
            results.append(inspect(ident,cwd,integration,a.mode))
        closure=None
        if a.mode=='closeout':
            if not a.closure_packet:raise CheckoutError('closeout_requires_objective_packet_and_independent_integration_evidence')
            packet=load_json(a.closure_packet.read_bytes())
            require_integration_bindings(packet,results)
            closure=gate(packet,'closeout')
        print(json.dumps({'observations':results,'closeout':closure,'remote_verified_by_this_command':False},ensure_ascii=True))
        return 3 if closure and not closure['passed'] else 0
    except (OSError,ValueError,TypeError,KeyError,subprocess.TimeoutExpired) as e:
        reason=str(e) if isinstance(e,(CheckoutError,ContractError)) else 'checkout_observation_failed'
        print(json.dumps({'verdict':'BLOCKED','reason':reason}),file=sys.stderr);return 2

if __name__=='__main__':raise SystemExit(main())
