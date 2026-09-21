"""Routing -> installed definition -> callable consumer, using synthetic transports.

No provider/model/desktop runtime is exercised by these tests.
"""
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import tomllib
import unittest
from unittest.mock import Mock, patch

from test_r3_core import ROOT, packet, response
from workflow_core import ContractError, fingerprint, policy, profile_selection
from workflow_dispatch import prepare_dispatch, dispatch_prepared
from workflow_store import export_events
import jev_support as jev
sys.path.insert(0, str(ROOT/'scripts'))
from render_agents import render


class RoutingPipelineTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name); self.agents = self.root/'agents'; self.agents.mkdir()
        self.profile = json.loads((ROOT/'profiles/codex-macos.yaml').read_text())
        self.generated = render(ROOT, self.profile)
        for path, raw in self.generated.items():
            if path.startswith('codex/'):
                (self.agents/Path(path).name).write_bytes(raw)
        definitions={Path(path).name:__import__('hashlib').sha256(raw).hexdigest()
                     for path,raw in self.generated.items() if path.startswith('codex/')}
        (self.agents/'dautia-r3-definitions.json').write_text(json.dumps({'schema_version':1,'definitions':definitions}))
        self.cfg = jev.defaults(); self.cfg.update(mode='selective', apply_features=['route'], cache_ttl_seconds=0)
        self.env = patch.dict(os.environ, {'TYPESAFE_API_KEY':'synthetic-test-only'})
        self.env.start(); self.addCleanup(self.env.stop)

    def work(self, difficulty='routine'):
        p = packet('write_product', 'implementer', 'IMPLEMENTATION')
        p['work'].update(decisions_resolved=True, execution_difficulty=difficulty)
        p['runtime']['available_profiles'] = list(policy()['profiles'])
        p['runtime']['available_targets'] = [Path(n).stem for n in self.generated if n.startswith('codex/')]
        return p

    def evaluate(self, p, **labels):
        labels = dict(information='sufficient', decisions='resolved', depth='routine', contradictions='none') | labels
        return jev.evaluate('route', p, self.cfg, self.root/'cfg', allow_network=True,
                            transport=lambda req,*_: response(req, labels))

    def test_medium_is_default_only_for_prepared_routine_implementer(self):
        self.cfg['mode'] = 'off'; p=self.work(); r=self.evaluate(p)
        self.assertEqual(r['selection']['selected'], 'sol_medium')
        self.assertEqual(r['dispatch_target'], 'implementer__sol_medium')
        self.assertFalse(r['network_called'])
        self.assertEqual(profile_selection('principal','read',analysis=False)['selected'], 'sol_high')
        self.assertEqual(profile_selection('implementer_complex','read',analysis=False)['selected'], 'sol_high')

    def test_high_fallback_for_unknown_difficulty(self):
        self.cfg['mode']='off'; r=self.evaluate(self.work('unknown'))
        self.assertEqual(r['selection']['selected'], 'sol_high')
        self.assertEqual(r['dispatch_target'], 'implementer__sol_high')

    def test_jev_is_consulted_for_defined_implementation(self):
        r=self.evaluate(self.work())
        self.assertTrue(r['network_called']); self.assertEqual(r['recommended_profile'],'sol_medium')
        self.assertEqual(r['selection']['selected'],'sol_medium')

    def test_jev_can_raise_effort_without_changing_writer_family(self):
        r=self.evaluate(self.work(),depth='deep')
        self.assertEqual(r['recommended_profile'],'sol_high')
        self.assertEqual(r['dispatch_target'],'implementer__sol_high')
        self.assertNotIn('astra_medium',r['selection']['candidates'])

    def test_explicit_demanding_context_does_not_auto_downgrade(self):
        r=self.evaluate(self.work('demanding'))
        self.assertFalse(r['network_called']); self.assertEqual(r['selection']['selected'],'sol_high')

    def test_unknown_difficulty_can_be_assessed_by_jev(self):
        r=self.evaluate(self.work('unknown'))
        self.assertEqual(r['selection']['selected'],'sol_medium')

    def test_missing_or_open_decisions_do_not_dispatch_or_call_jev(self):
        for value in (None,False):
            with self.subTest(value=value):
                p=self.work();p['work']['decisions_resolved']=value
                if value is None: del p['work']['decisions_resolved']
                r=self.evaluate(p)
                self.assertIsNone(r['selection']['selected']);self.assertIsNone(r['dispatch_target']);self.assertFalse(r['network_called'])

    def test_new_open_decision_becomes_analysis_not_astra_writer(self):
        p=self.work();r=self.evaluate(p,decisions='coupled',depth='deep')
        self.assertIsNone(r['recommended_profile']);self.assertIsNone(r['dispatch_target'])
        with self.assertRaisesRegex(ContractError,'resolve_analysis'):
            prepare_dispatch(p,r,self.agents)

    def test_shadow_observes_open_decision_without_applying_a_block(self):
        self.cfg['mode']='shadow';p=self.work();r=self.evaluate(p,decisions='coupled')
        self.assertEqual(r['selection']['selected'],'sol_medium')
        self.assertEqual(r['dispatch_target'],'implementer__sol_medium')
        self.assertNotIn('dispatch_blocked_reason',r)

    def test_shadow_and_disabled_apply_do_not_raise_effort(self):
        for mode,features in [('shadow',['route']),('selective',[])]:
            with self.subTest(mode=mode):
                self.cfg.update(mode=mode,apply_features=features);r=self.evaluate(self.work(),depth='deep')
                self.assertEqual(r['recommended_profile'],'sol_high');self.assertEqual(r['selection']['selected'],'sol_medium')

    def test_timeout_keeps_defined_default_and_no_fake_execution(self):
        p=self.work();r=jev.evaluate('route',p,self.cfg,self.root/'cfg',allow_network=True,transport=Mock(side_effect=TimeoutError()))
        self.assertEqual(r['status'],'fallback');self.assertEqual(r['selection']['selected'],'sol_medium')
        self.assertFalse(r['dispatch_performed']);self.assertIsNone(r['effective_model'])

    def test_missing_information_selective_requires_preparation(self):
        r=self.evaluate(self.work(),information='retrieve')
        self.assertEqual(r['status'],'retrieve_evidence_or_abstain');self.assertIsNone(r['dispatch_target'])

    def test_denied_profiles_and_capabilities_filtered_before_network(self):
        p=self.work();p['runtime']['denied_profiles']=['sol_medium']
        r=self.evaluate(p);self.assertIsNone(r['selection']['selected']);self.assertFalse(r['network_called'])
        p=self.work();p['work']['required_capabilities']=['xcode'];p['available_capabilities']=[]
        r=self.evaluate(p);self.assertEqual(r['selection']['reason'],'capability_unverified');self.assertFalse(r['network_called'])

    def test_budget_blocks_before_network(self):
        p=self.work();p['control']['budget_remaining']=False;r=self.evaluate(p)
        self.assertEqual(r['selection']['reason'],'budget_unavailable');self.assertFalse(r['network_called'])

    def test_no_unknown_provider_availability_is_promoted(self):
        p=self.work();del p['runtime']['available_profiles'];self.cfg['mode']='off';r=self.evaluate(p)
        self.assertEqual(r['selection']['status'],'availability_unverified');self.assertIsNone(r['dispatch_target'])

    def test_missing_loaded_target_is_not_replaced_by_base_alias(self):
        p=self.work();p['runtime']['available_targets']=['implementer'];r=self.evaluate(p)
        self.assertIsNone(r['dispatch_target'])
        with self.assertRaises(ContractError):prepare_dispatch(p,r,self.agents)

    def test_definition_mutation_is_rejected_before_spawn(self):
        p=self.work();r=self.evaluate(p);path=self.agents/'implementer__sol_medium.toml'
        path.write_text(path.read_text().replace('Execute', 'Mutated', 1))
        with self.assertRaisesRegex(ContractError,'definition_drift'):
            prepare_dispatch(p,r,self.agents)

    def test_all_explicit_solvable_profiles_have_generated_definitions(self):
        for key in ('sol_medium','sol_high','sol_xhigh'):
            with self.subTest(key=key):
                p=self.work();p['runtime']['explicit_override']={'profile':key,'source_kind':'user','source_refs':['user1']}
                r=self.evaluate(p);plan=prepare_dispatch(p,r,self.agents)
                self.assertEqual(plan['agent_type'],'implementer__'+key)
                self.assertFalse(r['network_called'])

    def test_astra_explicit_cannot_write_even_with_analysis_flag(self):
        p=self.work();p['work']['analysis']=True
        p['runtime']['explicit_override']={'profile':'astra_high','source_kind':'user','source_refs':['user1']}
        r=self.evaluate(p);self.assertEqual(r['selection']['reason'],'astra_not_execution_candidate')
        for n in self.generated:self.assertNotIn('implementer__astra',n)

    def test_generator_accepts_compatible_default_not_just_high(self):
        p=copy.deepcopy(self.profile);p['codex_agents']['code_explorer']=['gpt-5.6-sol','medium']
        files=render(ROOT,p);d=tomllib.loads(files['codex/code_explorer.toml'].decode())
        self.assertEqual(d['model_reasoning_effort'],'medium')
        p['codex_agents']['implementer']=['gpt-6-astra','medium']
        with self.assertRaises(ContractError):render(ROOT,p)

    def test_configurable_alias_cannot_override_qualified_dispatch(self):
        p=copy.deepcopy(self.profile);p['codex_agents']['implementer']=['gpt-5.6-sol','high']
        files=render(ROOT,p)
        self.assertEqual(tomllib.loads(files['codex/implementer.toml'].decode())['model_reasoning_effort'],'high')
        self.assertEqual(tomllib.loads(files['codex/implementer__sol_medium.toml'].decode())['model_reasoning_effort'],'medium')

    def test_astra_analytic_selection_reaches_matching_definition(self):
        p=packet();p['runtime']['available_targets']=[Path(n).stem for n in self.generated if n.startswith('codex/')]
        r=self.evaluate(p,decisions='coupled',depth='deep');plan=prepare_dispatch(p,r,self.agents)
        self.assertEqual(plan['agent_type'],'systems_analyst__astra_medium')
        self.assertEqual(plan['model_requested'],'gpt-6-astra')

    def test_prepared_request_is_consumed_by_exactly_one_spawn(self):
        p=self.work();r=self.evaluate(p);plan=prepare_dispatch(p,r,self.agents)
        spawn=Mock(return_value={'agent_id':'native-child-1'})
        result=dispatch_prepared(p,r,plan,self.agents,spawn,events_root=self.root/'events')
        spawn.assert_called_once();args=spawn.call_args.args[0]
        self.assertEqual(args['agent_type'],'implementer__sol_medium');self.assertIn('Select without moving camera.',args['message'])
        self.assertTrue(result['dispatch_performed']);self.assertFalse(result['delivery_received'])
        self.assertIsNone(result['model_reported']);self.assertIsNone(result['effort_reported'])
        events=export_events(self.root/'events','obj1')['events']
        self.assertEqual([e['event_type'] for e in events],['dispatch.requested','agent.started'])
        self.assertNotIn('message',json.dumps(events));self.assertNotIn('native-child-1',json.dumps(events))

    def test_dispatch_identity_ignores_variable_plan_timing_and_returns_id(self):
        p=self.work(); r=self.evaluate(p); plan=prepare_dispatch(p,r,self.agents)
        changed=copy.deepcopy(r); changed['duration_ms'] = r.get('duration_ms', 0) + 99
        changed_plan=prepare_dispatch(p, changed, self.agents)
        self.assertEqual(plan['dispatch_key'], changed_plan['dispatch_key'])
        self.assertNotEqual(plan['plan_hash'], changed_plan['plan_hash'])
        ledger=self.root/'ledger'; spawn=Mock(return_value={'agent_id':'native-child-1'})
        result=dispatch_prepared(p, changed, changed_plan, self.agents, spawn, ledger_root=ledger)
        self.assertEqual(result['status'], 'started'); self.assertTrue(result['dispatch_id'])
        reused=dispatch_prepared(p, changed, changed_plan, self.agents, spawn, ledger_root=ledger)
        self.assertEqual(reused['status'], 'dispatch_already_reserved'); spawn.assert_called_once()

    def test_stale_context_policy_or_target_never_spawns(self):
        for field in ('context','policy','target'):
            with self.subTest(field=field):
                p=self.work();r=self.evaluate(p);plan=prepare_dispatch(p,r,self.agents);spawn=Mock()
                if field=='context':p['outcome']='different goal'
                elif field=='policy':r['policy_hash']='0'*64
                else:r['dispatch_target']='implementer'
                with self.assertRaises(ContractError):dispatch_prepared(p,r,plan,self.agents,spawn)
                spawn.assert_not_called()

    def test_definition_drift_prevents_spawn(self):
        p=self.work();r=self.evaluate(p);plan=prepare_dispatch(p,r,self.agents)
        path=self.agents/'implementer__sol_medium.toml';path.write_text(path.read_text().replace('"medium"','"high"'))
        spawn=Mock()
        with self.assertRaises(ContractError):dispatch_prepared(p,r,plan,self.agents,spawn)
        spawn.assert_not_called()

    def test_runtime_reports_are_compared_and_not_retried(self):
        p=self.work();r=self.evaluate(p);plan=prepare_dispatch(p,r,self.agents)
        spawn=Mock(return_value={'agent_id':'c','model':'gpt-6-astra','model_reasoning_effort':'high'})
        result=dispatch_prepared(p,r,plan,self.agents,spawn)
        self.assertEqual(result['status'],'runtime_profile_mismatch');spawn.assert_called_once()

    def test_spawn_timeout_requires_reconciliation_not_retry(self):
        p=self.work();r=self.evaluate(p);plan=prepare_dispatch(p,r,self.agents);spawn=Mock(side_effect=TimeoutError())
        result=dispatch_prepared(p,r,plan,self.agents,spawn)
        self.assertEqual(result['status'],'dispatch_outcome_unknown');self.assertIsNone(result['dispatch_performed']);spawn.assert_called_once()

    def test_post_spawn_telemetry_failure_is_reconciliation_state(self):
        p=self.work();r=self.evaluate(p);plan=prepare_dispatch(p,r,self.agents)
        spawn=Mock(return_value={'agent_id':'child-telemetry','model':'gpt-5.6-sol','model_reasoning_effort':'medium'})
        with patch('workflow_dispatch.emit', side_effect=[None, RuntimeError('telemetry sink')]):
            result=dispatch_prepared(p,r,plan,self.agents,spawn,events_root=self.root/'events')
        self.assertEqual(result['status'],'dispatch_outcome_unknown')
        self.assertTrue(result['dispatch_performed']);self.assertEqual(result['reason'],'post_spawn_telemetry_unknown')
        spawn.assert_called_once()

    def test_cli_dispatch_plan_off_produces_same_profile_without_spawn(self):
        p=self.work();src=self.root/'packet.json';src.write_text(json.dumps(p));cfg=self.root/'config';state=self.root/'state'
        env=dict(os.environ,XDG_CONFIG_HOME=str(cfg),XDG_STATE_HOME=str(state))
        result=subprocess.run([sys.executable,str(ROOT/'skills/dautia-project-cycle/scripts/workflow_cli.py'),
                               'dispatch-plan',str(src),'--agents-dir',str(self.agents),'--cwd',str(self.root)],env=env,capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr);plan=json.loads(result.stdout)
        self.assertEqual(plan['agent_type'],'implementer__sol_medium');self.assertFalse(plan['dispatch_performed'])
        self.assertFalse((cfg/'dautia/jev-budget.sqlite3').exists())

    def test_principal_can_choose_ordinary_astra_without_jev_or_fake_user_override(self):
        p=packet();p['runtime']['principal_choice']={'profile':'astra_medium','evidence_refs':['coupling-analysis-1']}
        p['runtime']['available_targets']=['systems_analyst__astra_medium']
        self.cfg['mode']='off';r=self.evaluate(p);plan=prepare_dispatch(p,r,self.agents)
        self.assertEqual(plan['agent_type'],'systems_analyst__astra_medium');self.assertFalse(r['network_called'])
        self.assertEqual(r['selection']['reason'],'principal_evidence_selection')

    def test_principal_choice_cannot_enable_explicit_only_or_omit_evidence(self):
        for choice in ({'profile':'astra_high','evidence_refs':['one']},{'profile':'astra_medium'}):
            p=packet();p['runtime']['principal_choice']=choice
            p['runtime']['available_profiles']=list(policy()['profiles']);r=self.evaluate(p)
            self.assertEqual(r['selection']['status'],'blocked');self.assertFalse(r['network_called'])

    def test_invalid_runtime_filters_do_not_become_availability(self):
        with self.assertRaises(ContractError):
            profile_selection('ux_auditor','read',analysis=True,available='sol_high')

    def test_unsafe_profile_key_is_rejected_by_generator(self):
        import tempfile
        import shutil
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);shutil.copytree(ROOT/'roles',root/'roles')
            dest=root/'skills/dautia-project-cycle/config';dest.mkdir(parents=True)
            rules=policy();rules['profiles']['../escape']={'family':'sol','model':'gpt-5.6-sol','effort':'high'}
            (dest/'routing-policy.json').write_text(json.dumps(rules))
            with self.assertRaises(ContractError):render(root,self.profile)

    def test_fixture_can_be_prepared_but_not_dispatched_as_real_work(self):
        p=self.work();p['fixture_only']=True;r=self.evaluate(p);plan=prepare_dispatch(p,r,self.agents);spawn=Mock()
        with self.assertRaisesRegex(ContractError,'synthetic_fixture'):
            dispatch_prepared(p,r,plan,self.agents,spawn)
        spawn.assert_not_called()

    def test_both_host_profiles_produce_same_medium_high_variants(self):
        for name in ('codex-macos','wsl-shared'):
            files=render(ROOT,json.loads((ROOT/'profiles'/(name+'.yaml')).read_text()))
            for key in ('sol_medium','sol_high'):
                cfg=tomllib.loads(files['codex/implementer__'+key+'.toml'].decode())
                self.assertEqual(cfg['model_reasoning_effort'],policy()['profiles'][key]['effort'])


if __name__=='__main__':unittest.main()
