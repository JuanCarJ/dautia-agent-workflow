#!/usr/bin/env python3
"""Generate adapters at install time from canonical roles, not stale checked-in copies."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import re
import sys
import tomllib

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'skills/dautia-project-cycle/scripts'))
from skill_catalog import frontmatter
from workflow_core import ContractError, policy


def render(repo: Path, profile: dict) -> dict[str,bytes]:
    rules=json.loads((repo/'skills/dautia-project-cycle/config/routing-policy.json').read_text())
    boundary=(repo/'roles/_boundary.md').read_text()
    result={}; seen=set()
    for path in sorted((repo/'roles').glob('*.md')):
        if path.name.startswith('_'):continue
        meta,body=frontmatter(path.read_text());role=meta.get('id')
        if role!=path.stem or not re.fullmatch(r'[a-z][a-z0-9_]*',str(role)) or role in seen:
            raise ContractError('invalid_role_identity')
        if meta.get('mutability') not in ('read_only','bounded_write') or not meta.get('description'):
            raise ContractError('invalid_role_metadata')
        if re.search(r'\b(?:Astra|Sol)\b',body):
            raise ContractError('model_specific_role_body:'+role)
        seen.add(role)
        if profile['codex_agents'].get(role)!=['gpt-5.6-sol','high']:
            raise ContractError('default_role_profile_must_be_sol_high:'+role)
        profiles=['sol_high']
        if role in rules['analysis_roles'] and meta['mutability']=='read_only':
            profiles+=['astra_low','astra_medium','astra_high']
        for key in profiles:
            selected=rules['profiles'][key];name=role if key=='sol_high' else role+'__'+key
            # Read-only is the conservative sandbox. Artifact-writing QA needs a
            # separately verified artifact workspace/permission profile on the host.
            values={'name':name,'description':meta['description']+(' Analysis-only; high requires explicit request.' if key!='sol_high' else ''),
                    'model':selected['model'],'model_reasoning_effort':selected['effort'],
                    'sandbox_mode':'read-only' if meta['mutability']=='read_only' else 'workspace-write',
                    'developer_instructions':body+'\n'+boundary}
            text='\n'.join(k+' = '+json.dumps(v,ensure_ascii=False) for k,v in values.items())+'\n'
            tomllib.loads(text)
            result['codex/'+name+'.toml']=text.encode()
        cursor=role.replace('_','-')
        text='---\nname: '+cursor+'\ndescription: '+json.dumps(meta['description'])+'\nmodel: inherit\nreadonly: '+str(meta['mutability']=='read_only').lower()+'\n---\n'+body+'\n'+boundary
        result['cursor/'+cursor+'.md']=text.encode()
    if set(profile['codex_agents'])!=seen:raise ContractError('profile_role_catalog_mismatch')
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check',action='store_true');p.add_argument('--output',type=Path);p.add_argument('--profile',default='codex-macos');p.add_argument('--render',action='store_true');a=p.parse_args()
    if a.profile not in ('codex-macos','wsl-shared'):p.error('unknown profile')
    profile=json.loads((ROOT/'profiles'/(a.profile+'.yaml')).read_text())
    files=render(ROOT,profile)
    if a.render and not a.output:p.error('--render requires --output outside the canonical adapter sources')
    if a.output:
        a.output.mkdir(parents=True,exist_ok=True)
        for name,data in files.items():
            dest=a.output/name
            if dest.is_symlink():raise ContractError('adapter_symlink_refused')
            dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
    print(json.dumps({'generated':len(files),'role_defaults':len(profile['codex_agents']),'source_validation':'passed','runtime_validated':False}))
    return 0


if __name__=='__main__':raise SystemExit(main())
