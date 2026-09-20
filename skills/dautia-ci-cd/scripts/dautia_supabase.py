#!/usr/bin/env python3
"""Version-dispatch wrapper preserving legacy Supabase execution and credentials.

Only v3 target resolution changes. No new commands, fallbacks, credentials or
permission bypasses are added. --component/--target-id disambiguate v3 bindings.
"""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import dautia_supabase_legacy as legacy
from delivery_v3 import select_provider

_old_resolve = legacy.resolve_target
_component = None
_target_id = None


def resolve_target(start: Path, environment: str, require_link_match: bool = True):
    root=legacy.find_root(start); contract=legacy.load_json(root/'delivery.yaml')
    if contract.get('schema_version') != 3:
        if _component or _target_id: raise legacy.SetupError('Component selectors require delivery schema 3.')
        return _old_resolve(start,environment,require_link_match)
    try: entry=select_provider(contract,'supabase',environment,_component,_target_id)
    except ValueError as exc: raise legacy.SetupError(str(exc)) from exc
    comp=next(c for c in contract['codebases'] if c['id']==entry['component'])
    repo=next(r for r in contract['repositories'] if r['id']==comp['repository'])
    workdir=(root/repo['path']/entry['workdir']).resolve()
    if root.resolve() not in workdir.parents and workdir!=root.resolve(): raise legacy.SetupError('Workdir leaves product root.')
    if not workdir.is_dir(): raise legacy.SetupError('Declared Supabase workdir is unavailable.')
    linked=legacy.current_linked_ref(workdir)
    if require_link_match and linked and linked!=entry['project_ref']: raise legacy.SetupError('Linked project does not match declared target.')
    return legacy.Target(root,environment,entry['project_ref'],workdir,'delivery-v3')


legacy.resolve_target=resolve_target


def __getattr__(name): return getattr(legacy,name)


def main():
    global _component,_target_id
    args=list(sys.argv[1:]); i=0
    while i<len(args) and args[i]!='--':
        if args[i] in ('--component','--target-id'):
            if i+1>=len(args): raise legacy.SetupError('Missing target selector value.')
            if args[i]=='--component': _component=args[i+1]
            else: _target_id=args[i+1]
            del args[i:i+2]
        else: i+=1
    sys.argv[1:]=args
    return legacy.main()


if __name__=='__main__':
    try: raise SystemExit(main())
    except legacy.SetupError as exc:
        print(str(exc),file=sys.stderr); raise SystemExit(2)
