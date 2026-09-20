#!/usr/bin/env python3
"""Validate canonical assets and generated schemas, not literal version slogans."""
import ast
import hashlib
import json
from pathlib import Path
import sys
from render_agents import render
ROOT=Path(__file__).resolve().parents[1]
LEGACY={'skills/dautia-ci-cd/scripts/validate_delivery_legacy.py':'3754ad4dc5cfdad7f622bd831c47f8feb8d81019','skills/dautia-ci-cd/scripts/dautia_supabase_legacy.py':'1f9c244ea1377db15193c10145de88e340d019fa'}

def check(root=ROOT,overlay=False):
    errors=[]
    version=json.loads((root/'workflow-version.json').read_text())
    if version.get('plan_revision')!='r3' or type(version.get('contract_version')) is not int:errors.append('invalid_release_identity')
    for p in root.rglob('*.py'):
        if any(x in p.parts for x in ('.git','__pycache__')):continue
        try:ast.parse(p.read_text(),filename=str(p))
        except (SyntaxError,UnicodeError):errors.append('python_parse:'+str(p.relative_to(root)))
    counts={}
    for name in ('codex-macos','wsl-shared'):
        p=json.loads((root/'profiles'/(name+'.yaml')).read_text())
        try:counts[name]=len(render(root,p))
        except ValueError as e:errors.append('adapter:'+str(e))
    for name,expected in LEGACY.items():
        p=root/name
        if not p.exists():
            if not overlay:errors.append('missing_preserved_legacy:'+name)
            continue
        b=p.read_bytes();actual=hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
        if actual!=expected:errors.append('legacy_source_changed:'+name)
    # Installed adapters are derived. Committing another copy recreates drift.
    for p in (root/'adapters/codex/agents',root/'adapters/cursor/agents'):
        if p.is_dir() and any(p.iterdir()):errors.append('generated_adapters_still_tracked_or_present')
    return {'passed':not errors,'errors':errors,'generated_counts':counts,'overlay_only':overlay,'native_runtime_tested':False}

if __name__=='__main__':
    result=check(overlay='--overlay' in sys.argv)
    print(json.dumps(result,indent=2));raise SystemExit(0 if result['passed'] else 1)
