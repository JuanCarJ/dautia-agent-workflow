"""Executed policy/protocol tests; none claims a model or product was exercised."""
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS=ROOT/'skills/dautia-project-cycle/scripts'
sys.path.insert(0,str(SCRIPTS)); sys.path.insert(0,str(ROOT/'skills/dautia-ci-cd/scripts'))
from workflow_core import ContractError, gate, fingerprint, next_action, profile_selection, load_json, invalidated_nodes
from workflow_cli import hook, refresh_sources
from workflow_store import bind, binding, emit, export_events, resource_lease, atomic_write
from workspace_audit import parse_status, snapshot, reconcile
from skill_catalog import frontmatter, inventory
import jev_support as jev


def packet(operation='read', role='systems_analyst', mode='AUDIT'):
    p={'schema_version':3,'objective_id':'obj1','project_id':'proj1','outcome':'Select without moving camera.',
       'work':{'mode':mode,'operation':operation,'role':role,'analysis':operation=='read','material':True,'target':'local'},
       'authority':{'source_kind':'user','source_refs':['user-request-1'],'project_id':'proj1','target':'local','operations':[operation], 'artifact_scope':'isolated-results'},
       'context_complete':True,'coherence_evidence':['review-criteria-1'],
       'requirements':[{'id':'R1','text':'Selection leaves camera unchanged.','expected':{'camera_changed':False}}],
       'test_expectations':[{'id':'T1','requirement_id':'R1','expected':{'camera_changed':False}}],
       'candidate':{'repositories':{'repo1':'a'*40},'artifact_digest':'b'*64,'config_digest':'c'*64},
       'sources':[{'id':'spec1','expected_hash':'d'*64,'observed_hash':'d'*64}],
       'skills':[{'id':'diagnosing-bugs','kind':'diagnosis','expected_hash':'e'*64,'loaded_hash':'e'*64}],
       'control':{'budget_remaining':True},'runtime':{'available_profiles':['sol_high','astra_low','astra_medium'],'harness':'codex','available_targets':['systems_analyst','systems_analyst__astra_low','systems_analyst__astra_medium']},
       'data_sharing':{'approved':True,'authority_ref':'synthetic-fixture-only'}}
    p['checks']=[{'id':'C1','requirement_id':'R1','status':'passed','candidate_hash':fingerprint(p['candidate']),
                  'acceptance_hash':fingerprint(p['requirements']),'evidence_kind':'tool_result','evidence':['fixture-observation-1']}]
    p['review']={'required':True,'status':'approved','author_run':'author1','reviewer_run':'reviewer1','evidence':['review-1'],
                 'candidate_hash':fingerprint(p['candidate']),'acceptance_hash':fingerprint(p['requirements'])}
    return p


def response(request, labels=None, confidence=.99):
    labels=labels or {}
    answers={}
    for key,q in request['questions'].items():
        selected=labels.get(key,next(iter(q['criteria'])))
        answers[key]={'type':'choice','choice':selected,'confidence':confidence,
                      'probabilities':{c:1.0 if c==selected else 0.0 for c in q['criteria']}}
    return {'model':request['model'],'answers':answers}


class CoreTests(unittest.TestCase):
    def test_approved_consistent_packet(self):
        p=packet('write_product','implementer','IMPLEMENTATION')
        self.assertTrue(gate(p)['passed']); self.assertTrue(gate(p,'closeout')['passed'])
        self.assertFalse(gate(p)['authorizes_action'])

    def test_contract_test_conflict_before_write(self):
        p=packet('write_product','implementer','IMPLEMENTATION'); p['test_expectations'][0]['expected']['camera_changed']=True
        self.assertIn('contract_test_conflict:T1',gate(p)['issues'])

    def test_orphan_test(self):
        p=packet();p['test_expectations'][0]['requirement_id']='missing'
        self.assertFalse(gate(p)['passed'])

    def test_read_only_no_fake_product_spec(self):
        p={'schema_version':3,'objective_id':'ssh1','project_id':'ops','work':{'role':'principal','mode':'AUDIT','operation':'read','material':False,'interface':'ssh','target':'host1','target_verified':True,'host_key_verified':True}}
        self.assertTrue(gate(p)['passed'])

    def test_ssh_identity_required(self):
        p=packet();p['work'].update(interface='ssh',host_key_verified=False)
        self.assertIn('ssh_identity_unverified',gate(p)['issues'])

    def test_audit_does_not_grant_writes(self):
        self.assertIn('read_mode_cannot_mutate_product',gate(packet('write_product','implementer'))['issues'])

    def test_security_optin(self):
        p=packet(role='data_security');self.assertFalse(gate(p)['passed']);p['work']['security_opt_in']=True;self.assertTrue(gate(p)['passed'])

    def test_qa_artifacts_not_product(self):
        p=packet('write_artifact','qa_ios');self.assertTrue(gate(p)['passed'])
        p['work']['operation']='write_product';self.assertIn('authorized_writer_required',gate(p)['issues'])

    def test_read_mode_can_capture_authorized_notes(self):
        p=packet('capture_docs');p['authority']['document_scope']='proposal-notes'
        self.assertTrue(gate(p)['passed'])

    def test_missing_authority_or_wrong_project(self):
        p=packet('write_product','implementer','IMPLEMENTATION');p['authority']['project_id']='other'
        self.assertIn('authority_scope_mismatch',gate(p)['issues'])

    def test_normative_delta_bound(self):
        p=packet('write_product','implementer','IMPLEMENTATION');c={'id':'delta1','classification':'normative','base_hash':'a','delta':{'R1':'new'}};p['spec_changes']=[c]
        self.assertFalse(gate(p)['passed'])
        c['approval']={'source_kind':'user','source_refs':['user-2'],'delta_hash':fingerprint({'base':'a','delta':{'R1':'new'}})}
        self.assertTrue(gate(p)['passed']);c['delta']['R1']='changed-again';self.assertFalse(gate(p)['passed'])

    def test_stale_sources_and_skills(self):
        p=packet();p['sources'][0]['observed_hash']='other';p['skills'][0]['loaded_hash']='other'
        self.assertEqual(len(gate(p)['issues']),2)

    def test_unknown_impact_blocks_its_writer(self):
        p=packet('write_product','implementer','IMPLEMENTATION');p['impacts']=[{'id':'i1','treatment':'unknown'}]
        self.assertIn('unresolved_impact:i1',gate(p)['issues'])
        p['work'].update(operation='read',role='systems_analyst');self.assertTrue(gate(p)['passed'])

    def test_no_change_requires_investigation(self):
        p=packet();p['impacts']=[{'id':'i1','treatment':'no_change_justified'}]
        self.assertIn('unjustified_no_change:i1',gate(p)['issues'])

    def test_regression_activates_diagnosis_without_jev(self):
        p=packet('write_product','implementer','IMPLEMENTATION');p['findings']=[{'id':'f1','kind':'regression','resolved':False}]
        self.assertEqual(next_action(p)['action'],'diagnose');self.assertFalse(gate(p)['passed'])

    def test_bugfix_needs_diagnostic_evidence(self):
        p=packet('write_product','implementer','IMPLEMENTATION');p['work']['bugfix']=True
        self.assertFalse(gate(p)['passed']);p['diagnostic']={'evidence':['experiment-1'],'hypothesis_state':'reproduced','discriminating_check':'before-after'}
        self.assertTrue(gate(p)['passed'])

    def test_old_candidate_cannot_close(self):
        p=packet();p['candidate']['artifact_digest']='changed'
        self.assertIn('criterion_unverified:R1',gate(p,'closeout')['issues'])

    def test_provider_disabled_not_live_pass(self):
        p=packet();p['requirements'][0]['provider_required']=True;p['checks'][0]['acceptance_hash']=fingerprint(p['requirements'])
        self.assertIn('criterion_unverified:R1',gate(p,'closeout')['issues'])

    def test_physical_not_simulator(self):
        p=packet();p['requirements'][0]['physical_required']=True;p['checks'][0]['acceptance_hash']=fingerprint(p['requirements'])
        p['checks'][0]['physical_device']=False;self.assertFalse(gate(p,'closeout')['passed'])

    def test_oracle_pass_on_broken_not_enough(self):
        p=packet();p['requirements'][0]['oracle_required']=True;p['checks'][0]['acceptance_hash']=fingerprint(p['requirements'])
        self.assertIn('criterion_unverified:R1',gate(p,'closeout')['issues'])
        p['checks'][0]['fail_before']=True
        self.assertNotIn('criterion_unverified:R1',gate(p,'closeout')['issues'])

    def test_retry_green_does_not_erase_red(self):
        p=packet();p['checks'][0]['prior_failed']=True
        self.assertIn('criterion_unverified:R1',gate(p,'closeout')['issues'])
        p['checks'][0]['failure_resolution']=['controlled-fixture-correction']
        self.assertTrue(gate(p,'closeout')['passed'])

    def test_product_review_cannot_be_disabled(self):
        p=packet('write_product','implementer','IMPLEMENTATION');p['review']={'required':False}
        self.assertIn('independent_review_incomplete',gate(p,'closeout')['issues'])

    def test_author_cannot_review_self(self):
        p=packet();p['review']['reviewer_run']='author1';self.assertFalse(gate(p,'closeout')['passed'])

    def test_child_ended_not_received(self):
        p=packet();p['delegations']=[{'id':'child1','state':'ended','candidate_hash':fingerprint(p['candidate']),'evidence':['e1']}]
        self.assertIn('handoff_missing_or_stale:child1',gate(p,'closeout')['issues'])

    def test_team_preparation_before_user(self):
        p=packet();p['pending']=[{'id':'test1','status':'needs_team_handoff','authorized':True,'available':True}]
        self.assertEqual(next_action(p)['action'],'team_handoff');self.assertFalse(gate(p,'closeout')['passed'])

    def test_independent_work_before_external_wait(self):
        p=packet();p['pending']=[{'id':'phone','status':'needs_user_physical_action'},{'id':'doubletap','status':'executable_now','available':True,'authorized':True}]
        self.assertEqual(next_action(p)['pending_id'],'doubletap')

    def test_pause_and_budget_beat_continuation(self):
        for control in ({'state':'paused'},{'state':'cancelled'},{'budget_remaining':False}):
            p=packet();p['control']=control;self.assertEqual(next_action(p)['action'],'stop')

    def test_external_effect_not_retried(self):
        p=packet('external_mutation','release_operator','RELEASE');p['work']['prior_effect_unknown']=True
        self.assertEqual(next_action(p)['action'],'reconcile');self.assertIn('reconcile_before_retry',gate(p)['issues'])

    def test_health_not_business_result(self):
        p=packet();p['work']['external_required']=True;p['external']={'outcome':'healthy'}
        self.assertIn('external_outcome_unverified',gate(p,'closeout')['issues'])

    def test_dirty_foreign_preserved_can_close(self):
        p=packet();p['workspaces']=[{'id':'w1','foreign_preserved':True,'own_residuals_unresolved':0}]
        self.assertTrue(gate(p,'closeout')['passed'])
        p['workspaces'][0]['own_residuals_unresolved']=1;self.assertFalse(gate(p,'closeout')['passed'])

    def test_transitive_selective_invalidation(self):
        nodes=[{'id':'api','sources':['spec']},{'id':'ios','depends_on':['api']},{'id':'unrelated','sources':['other']}]
        self.assertEqual(invalidated_nodes(nodes,{'spec'}),['api','ios'])

    def test_duplicate_json_and_nonfinite_rejected(self):
        for data in ('{"x":1,"x":2}','{"n":NaN}','{"n":Infinity}'):
            with self.assertRaises(ContractError):load_json(data)

    def test_invalid_boolean_does_not_pass(self):
        p=packet();p['requirements'][0]['required']='false'
        with self.assertRaises(ContractError):gate(p)


class RoutingTests(unittest.TestCase):
    def test_role_defaults_preserve_root_high_and_implementer_medium(self):
        from workflow_core import READ_ROLES,WRITE_ROLES
        for role in READ_ROLES|WRITE_ROLES:
            with self.subTest(role=role):
                self.assertEqual(profile_selection(role,'read',analysis=True)['selected'],'sol_medium' if role=='implementer' else 'sol_high')

    def test_no_astra_writer(self):
        self.assertEqual(profile_selection('implementer','write_product',analysis=False,decisions_resolved=True,execution_difficulty='routine',recommendation='astra_medium')['selected'],'sol_medium')

    def test_analytical_advisory_allowed(self):
        self.assertEqual(profile_selection('ux_auditor','read',analysis=True,recommendation='astra_low',available=['sol_high','astra_low'])['selected'],'astra_low')

    def test_shadow_does_not_change_default(self):
        self.assertEqual(profile_selection('ux_auditor','read',analysis=True,recommendation='astra_low',shadow=True)['selected'],'sol_high')

    def test_explicit_high_no_silent_downgrade(self):
        e={'profile':'astra_high','source_kind':'user','source_refs':['user1']}
        result=profile_selection('systems_analyst','read',analysis=True,explicit=e,available=['astra_high'])
        self.assertEqual(result['selected'],'astra_high')
        result=profile_selection('systems_analyst','read',analysis=True,explicit=e,available=['sol_high'])
        self.assertIsNone(result['selected']);self.assertEqual(result['status'],'blocked')

    def test_unavailable_sol_does_not_select_astra(self):
        self.assertIsNone(profile_selection('systems_analyst','read',analysis=True,available=['astra_medium'])['selected'])

    def test_runtime_truth_unknown(self):
        result=profile_selection('implementer','write_product',analysis=False)
        self.assertIsNone(result['provider_observed']);self.assertFalse(result['changes_parent'])


class JevTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)/'cfg';self.events=Path(self.temp.name)/'events'
        self.cfg=jev.defaults();self.cfg['mode']='shadow';self.cfg['cache_ttl_seconds']=0
        self.env=patch.dict(os.environ,{'TYPESAFE_API_KEY':'synthetic-test-only'});self.env.start();self.addCleanup(self.env.stop)

    def test_off_no_transport(self):
        self.cfg['mode']='off';transport=Mock();r=jev.evaluate('route',packet(),self.cfg,self.root,allow_network=True,transport=transport)
        transport.assert_not_called();self.assertFalse(r['network_called'])

    def test_network_explicit(self):
        transport=Mock();jev.evaluate('route',packet(),self.cfg,self.root,transport=transport);transport.assert_not_called()

    def test_unprepared_writer_requires_readiness_before_route_call(self):
        transport=Mock();r=jev.evaluate('route',packet('write_product','implementer','IMPLEMENTATION'),self.cfg,self.root,allow_network=True,transport=transport)
        transport.assert_not_called();self.assertEqual(r['selection']['reason'],'implementation_readiness_required');self.assertIsNone(r['selection']['selected'])

    def test_complex_analysis_shadow_then_selective(self):
        labels={'information':'sufficient','decisions':'coupled','depth':'deep','contradictions':'multiple'}
        transport=lambda req,*_:response(req,labels)
        r=jev.evaluate('route',packet(),self.cfg,self.root,allow_network=True,transport=transport)
        self.assertEqual(r['recommended_profile'],'astra_medium');self.assertEqual(r['selection']['selected'],'sol_high')
        self.cfg['mode']='selective';self.cfg['apply_features']=['route']
        r=jev.evaluate('route',packet(),self.cfg,self.root,allow_network=True,transport=transport)
        self.assertEqual(r['dispatch_target'],'systems_analyst__astra_medium');self.assertFalse(r['dispatch_performed'])

    def test_focal_routine_does_not_force_astra(self):
        labels={'information':'sufficient','decisions':'focal','depth':'routine','contradictions':'none'}
        r=jev.evaluate('route',packet(),self.cfg,self.root,allow_network=True,transport=lambda req,*_:response(req,labels))
        self.assertEqual(r['recommended_profile'],'sol_high')

    def test_missing_evidence_not_more_intelligence(self):
        labels={'information':'retrieve','decisions':'coupled','depth':'deep','contradictions':'multiple'}
        r=jev.evaluate('route',packet(),self.cfg,self.root,allow_network=True,transport=lambda req,*_:response(req,labels))
        self.assertIsNone(r['recommended_profile'])

    def test_confidence_abstention(self):
        r=jev.evaluate('brief',packet(),self.cfg,self.root,allow_network=True,transport=lambda req,*_:response(req,confidence=.1))
        self.assertEqual(r['status'],'abstain')

    def test_bad_model_or_invalid_type_fallback(self):
        for raw in ({'model':'other','answers':{}},{'model':self.cfg['model'],'answers':{'R1':{'type':'noul'}}}):
            with self.subTest(raw=raw):
                r=jev.evaluate('brief',packet(),self.cfg,self.root,allow_network=True,transport=lambda *args:raw)
                self.assertEqual(r['status'],'fallback');self.assertFalse(r['certifies_completion'])

    def test_no_secret_or_unapproved_state(self):
        for p in (packet(),packet()):
            if p==packet(): p['analysis_brief']='password=do-not-send-this-value'
            transport=Mock();r=jev.evaluate('brief',p,self.cfg,self.root,allow_network=True,transport=transport)
            transport.assert_not_called();self.assertEqual(r['status'],'fallback')
        p=packet();p['data_sharing']['approved']=False;transport=Mock()
        jev.evaluate('brief',p,self.cfg,self.root,allow_network=True,transport=transport);transport.assert_not_called()

    def test_budget_store_enforces_cap(self):
        self.cfg['max_requests_per_objective_per_day']=1
        r=jev.evaluate('brief',packet(),self.cfg,self.root,allow_network=True,transport=lambda req,*_:response(req))
        self.assertTrue(r['network_called']);transport=Mock()
        r=jev.evaluate('brief',packet(),self.cfg,self.root,allow_network=True,transport=transport)
        self.assertEqual(r['reason'],'request_quota_exhausted');transport.assert_not_called()

    def test_cache_bound_to_objective_and_state(self):
        self.cfg['cache_ttl_seconds']=300;transport=Mock(side_effect=lambda req,*_:response(req));p=packet()
        jev.evaluate('brief',p,self.cfg,self.root,allow_network=True,transport=transport)
        r=jev.evaluate('brief',p,self.cfg,self.root,allow_network=True,transport=transport)
        self.assertTrue(r['cache_hit']);self.assertEqual(transport.call_count,1)
        p['objective_id']='obj2';jev.evaluate('brief',p,self.cfg,self.root,allow_network=True,transport=transport)
        self.assertEqual(transport.call_count,2)
        p['outcome']='new';jev.evaluate('brief',p,self.cfg,self.root,allow_network=True,transport=transport)
        self.assertEqual(transport.call_count,3)

    def test_context_preserves_core_and_negative(self):
        self.cfg['mode']='selective';self.cfg['apply_features']=['context'];p=packet()
        p['optional_context']=[{'id':'pin','pinned':True},{'id':'neg','negative_evidence':True},{'id':'drop','recoverable':True}]
        r=jev.evaluate('context',p,self.cfg,self.root,allow_network=True,transport=lambda req,*_:response(req,{'drop':'irrelevant'}))
        self.assertEqual(r['selected_context_ids'],['pin','neg']);self.assertIn('requirements',p)

    def test_each_stage_uses_valid_typed_request(self):
        p=packet();p['impacts']=[{'id':'i1','treatment':'indirect_validation','check_ids':['C1']}]
        p['optional_context']=[{'id':'c1','recoverable':True,'text':'optional'}]
        for stage in jev.STAGES:
            with self.subTest(stage=stage):
                req=jev.build_request(stage,p,self.cfg);self.assertTrue(req['questions'])
                self.assertEqual(set(jev.parse_response(response(req),req)),set(req['questions']))


class StoreAndHookTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)/'state';self.cwd=Path(self.temp.name)/'work';self.cwd.mkdir()

    def test_resource_exclusion_and_generation(self):
        self.assertTrue(resource_lease(self.root,'simulator1','a','g1')['acquired'])
        self.assertFalse(resource_lease(self.root,'simulator1','b','g2')['acquired'])
        self.assertFalse(resource_lease(self.root,'simulator1','a','old',True)['released'])
        self.assertTrue(resource_lease(self.root,'simulator1','a','g1',True)['released'])

    def test_hook_prevents_known_conflict_before_mock_edit(self):
        p=packet('write_product','implementer','IMPLEMENTATION');p['test_expectations'][0]['expected']=True
        bind(self.root,'s1',self.cwd,p,'g1');result=hook({'cwd':str(self.cwd),'session_id':'s1','hook_event_name':'PreToolUse','tool_name':'apply_patch','tool_input':{}},self.root)
        self.assertEqual(result['hookSpecificOutput']['permissionDecision'],'deny');self.assertEqual(list(self.cwd.iterdir()),[])

    def test_stop_continuation_bounded(self):
        p=packet();p['pending']=[{'id':'p1','status':'needs_preparation','available':True,'authorized':True}]
        bind(self.root,'s1',self.cwd,p,'g1');h={'cwd':str(self.cwd),'session_id':'s1','hook_event_name':'Stop','stop_hook_active':False}
        self.assertEqual(hook(h,self.root)['decision'],'block');self.assertEqual(hook(h,self.root)['decision'],'block');self.assertEqual(hook(h,self.root),{})

    def test_interrupt_never_restarts(self):
        p=packet();p['pending']=[{'id':'p1','status':'executable_now','available':True,'authorized':True}]
        bind(self.root,'s1',self.cwd,p,'g1');h={'cwd':str(self.cwd),'session_id':'s1','hook_event_name':'Interrupt'}
        self.assertEqual(hook(h,self.root),{});h['hook_event_name']='Stop';self.assertEqual(hook(h,self.root),{})

    def test_child_does_not_inherit_parent_binding(self):
        bind(self.root,'s1',self.cwd,packet(),'g1')
        self.assertEqual(hook({'cwd':str(self.cwd),'session_id':'s1','hook_event_name':'PreToolUse','agent_id':'child','tool_name':'apply_patch'},self.root),{})

    def test_wrong_workspace_binding_rejected(self):
        bind(self.root,'s1',self.cwd,packet(),'g1')
        with self.assertRaises(ContractError):binding(self.root,'s1',self.cwd/'other')

    def test_real_source_change_invalidates_packet(self):
        p=packet();source=self.cwd/'SPEC.md';source.write_text('old')
        import hashlib
        p['sources']=[{'id':'spec','path':'SPEC.md','expected_hash':hashlib.sha256(b'old').hexdigest()}]
        self.assertTrue(gate(refresh_sources(p,self.cwd))['passed']);source.write_text('new')
        self.assertIn('stale_source:spec',gate(refresh_sources(p,self.cwd))['issues'])

    def test_metadata_only_and_dedup(self):
        e={'event_type':'objective.opened','objective_id':'obj1','event_id':'e1'}
        self.assertTrue(emit(self.root,e)['recorded']);self.assertTrue(emit(self.root,e)['recorded'])
        exported=export_events(self.root,'obj1');self.assertEqual(exported['event_count'],1)
        self.assertFalse(emit(self.root,{**e,'prompt':'private'})['recorded'])

    def test_symlink_state_rejected(self):
        target=Path(self.temp.name)/'target';target.mkdir();self.root.symlink_to(target,target_is_directory=True)
        with self.assertRaises(ContractError):resource_lease(self.root,'sim1','a','g1')

    def test_cli_error_exit(self):
        src=Path(self.temp.name)/'bad.json';src.write_text('{"schema_version":3}')
        result=subprocess.run([sys.executable,str(SCRIPTS/'workflow_cli.py'),'gate','preflight',str(src)],capture_output=True)
        self.assertEqual(result.returncode,2)


class CatalogAndWorkspaceTests(unittest.TestCase):
    def test_real_description_not_separator(self):
        fields,_=frontmatter('---\nname: example\ndescription: >-\n  First line\n  second line\n---\nBody')
        self.assertEqual(fields['description'],'First line second line')

    def test_collision_no_deletion(self):
        with tempfile.TemporaryDirectory() as d:
            roots=[Path(d)/'a',Path(d)/'b']
            for r in roots:
                (r/'same').mkdir(parents=True);(r/'same/SKILL.md').write_text('---\nname: same\ndescription: Useful method\n---\ntext')
            result=inventory(roots);self.assertEqual(result['collisions'],['same']);self.assertFalse(result['automatic_deletion'])
            self.assertIsNone(result['skills'][0]['loaded'])

    def test_status_nul_paths(self):
        raw=b'1 .M N... 100644 100644 100644 a b file with spaces\0? newline\nfile\0'
        items=parse_status(raw);self.assertEqual(items[0]['path'],'file with spaces');self.assertEqual(items[1]['path'],'newline\nfile')

    @patch.dict(os.environ, {'GIT_CONFIG_GLOBAL': os.devnull, 'GIT_CONFIG_SYSTEM': os.devnull, 'GIT_CONFIG_NOSYSTEM': '1'})
    def test_readonly_git_snapshot_preserves_foreign(self):
        with tempfile.TemporaryDirectory() as d:
            repo=Path(d);subprocess.run(['git','init','-q',d],check=True)
            f=repo/'foreign.txt';f.write_text('do not lose')
            before=snapshot(repo,'repo1','w1');after=snapshot(repo,'repo1','w1')
            r=reconcile(before,after,[]);self.assertTrue(r['reconciled'], {'before': before, 'after': after, 'result': r});self.assertEqual(f.read_text(),'do not lose')
            (repo/'own.txt').write_text('work')
            r=reconcile(before,snapshot(repo,'repo1','w1'),['own.txt']);self.assertEqual(r['own_residual_paths'],['own.txt']);self.assertFalse(r['disposable'])

    def test_mixed_file_not_owned_whole(self):
        b={'repo_id':'r','checkout_id':'w','coverage':'complete_for_status_entries','entries':[{'path':'a','content_hash':'h','status':'.M'}]}
        self.assertIsNone(reconcile(b,b,['a'])['foreign_preserved'])


if __name__=='__main__':unittest.main()
