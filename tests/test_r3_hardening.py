import copy
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from concurrent.futures import ThreadPoolExecutor
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'tests'),str(ROOT/'skills/dautia-project-cycle/scripts'),str(ROOT/'skills/dautia-ci-cd/scripts')]
from test_r3_core import packet
from test_r3_delivery_install import delivery
from workflow_cli import hook, safe_read_command, main
from workflow_store import bind, resource_lease, emit, export_events
from delivery_v3 import validate_v3
from check_checkout import require_integration_bindings, CheckoutError

class HardeningTests(unittest.TestCase):
    def test_closeout_integration_is_bound_per_repository(self):
        observations=[{'repository':'mobile','integration_branch':'dev'}, {'repository':'api','integration_branch':'main'}]
        p={'workspaces':[{'id':'w1','repo_id':'mobile','integration_branch':'dev','integration_required':True}, {'id':'w2','repo_id':'api','integration_branch':'main','integration_required':True}]}
        self.assertTrue(require_integration_bindings(p,observations))
        for invalid in ({'workspace':{'integration_required':True}}, {'workspaces':p['workspaces'][:1]}, {'workspaces':[dict(p['workspaces'][0],integration_branch='main'),p['workspaces'][1]]}):
            with self.subTest(invalid=invalid),self.assertRaises(CheckoutError):require_integration_bindings(invalid,observations)
    def test_malformed_nested_delivery_is_rejected(self):
        for section,field in [('codebases','repository'),('targets','component'),('provider_projects','component')]:
            for value in ([],{},True,None):
                with self.subTest(section=section,value=value):
                    c=delivery()
                    if section=='provider_projects':c[section]=[{'id':'provider','provider':'custom','component':'api','environment':'integration','target_id':'api-integration','workdir':'.'}]
                    c[section][0][field]=value
                    self.assertTrue(validate_v3(c))
    def test_shell_convenience_does_not_accept_git_output_or_external_filters(self):
        for command in ('git diff --output=tracked.txt','git log --ext-diff','rg --pre=program x','rg --hostname-bin=program x','tail -f out','cat a > b'):
            self.assertFalse(safe_read_command(command),command)
        self.assertTrue(safe_read_command('cat README.md'))
    def test_prepared_ssh_read_is_exact_and_scoped(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);p=packet();p['work'].update(interface='ssh',host_key_verified=True,target_verified=True,target='host1',read_commands=['ssh host1 uptime'])
            p['authority'].update(operations=['read'],target='host1')
            bind(root,'session',root,p,'one')
            base={'hook_event_name':'PreToolUse','session_id':'session','cwd':str(root),'tool_name':'Bash'}
            self.assertEqual(hook(dict(base,tool_input={'command':'ssh host1 uptime'}),root),{})
            result=hook(dict(base,tool_input={'command':'ssh host1 reboot'}),root)
            self.assertEqual(result['hookSpecificOutput']['permissionDecision'],'deny')
    def test_lease_concurrent_writers_have_one_winner(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            with ThreadPoolExecutor(max_workers=4) as pool:
                results=list(pool.map(lambda i: resource_lease(root,'simulator','owner'+str(i),'g1'),range(4)))
            self.assertEqual(sum(x['acquired'] for x in results),1)
    def test_telemetry_can_be_disabled_without_blocking(self):
        with tempfile.TemporaryDirectory() as d,patch.dict(os.environ,{'DAUTIA_TELEMETRY':'off'}):
            root=Path(d);r=emit(root,{'event_type':'objective.opened','objective_id':'task1'})
            self.assertTrue(r['disabled']);self.assertFalse((root/'events').exists())
    def test_identical_events_deduplicate_without_conflict(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);e={'event_id':'e1','event_type':'objective.opened','objective_id':'task1','occurred_at':'2026-09-20T00:00:00+00:00'}
            self.assertTrue(emit(root,e)['recorded']);self.assertTrue(emit(root,e)['recorded'])
            result=export_events(root,'task1');self.assertEqual(result['event_count'],1);self.assertEqual(result['warnings'],[])
    def test_fixture_cannot_be_bound(self):
        import contextlib,io
        with tempfile.TemporaryDirectory() as d,contextlib.redirect_stderr(io.StringIO()):
            r=Path(d);p=packet();p['fixture_only']=True;f=r/'packet.json';f.write_text(json.dumps(p))
            self.assertEqual(main(['--state-root',str(r/'state'),'bind',str(f),'--session','s','--generation','g','--cwd',str(r)]),2)

if __name__=='__main__':unittest.main()
