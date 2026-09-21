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



class CoreTests(unittest.TestCase):
    def test_approved_consistent_packet(self):
        p=packet('write_product','implementer','IMPLEMENTATION')
        self.assertTrue(gate(p)['passed']); self.assertTrue(gate(p,'closeout')['passed'])
        self.assertFalse(gate(p)['authorizes_action'])

    def test_incomplete_read_reports_warning_but_incomplete_write_blocks(self):
        read = packet('read', 'systems_analyst', 'AUDIT'); read['context_complete'] = False
        result = gate(read)
        self.assertTrue(result['passed']); self.assertIn('context_incomplete', result['warnings'])
        write = packet('write_product', 'implementer', 'IMPLEMENTATION'); write['context_complete'] = False
        self.assertIn('context_incomplete', gate(write)['issues'])

    def test_evidence_contract_is_checked_by_gate_but_scratch_warns(self):
        p = packet(); p['project_context'] = {'project_id':'proj1','documentation_status':'scratch'}
        result = gate(p)
        self.assertTrue(result['passed']); self.assertIn('context_incomplete', result['warnings'])
        p['evidence'] = [{'id':'bad','status':'observed'}]
        self.assertTrue(any(x.startswith('invalid_evidence:') for x in gate(p)['issues']))

    def test_scratch_context_blocks_product_closeout_but_not_discovery(self):
        p = packet('write_product', 'implementer', 'IMPLEMENTATION')
        p['project_context'] = {'project_id':'proj1','documentation_status':'scratch'}
        self.assertIn('project_context_incomplete', gate(p, 'closeout')['issues'])
        self.assertTrue(gate(p)['passed'])

    def test_evidence_and_context_must_match_packet_identity(self):
        p = packet()
        p['project_context'] = {'project_id':'other','documentation_status':'complete'}
        self.assertIn('project_context_project_mismatch', gate(p)['issues'])
        p['project_context'] = {'project_id':'proj1','documentation_status':'complete'}
        p['evidence'] = [{'evidence_id':'e1','objective_id':'other','project_id':'proj1','stage':'audit',
                          'source_kind':'test','source_ref':'test-1','observed_at':'unknown',
                          'observation':'fixture','status':'observed','strength':'E2'}]
        self.assertIn('evidence_project_or_objective_mismatch:e1', gate(p)['issues'])

    def test_evidence_id_is_canonical_packet_key(self):
        p = packet()
        p['evidence'] = [{'evidence_id':'e1','objective_id':'obj1','project_id':'proj1','stage':'audit',
                          'source_kind':'test','source_ref':'test-1','observed_at':'unknown',
                          'observation':'fixture','status':'observed','strength':'E2'}]
        self.assertTrue(gate(p)['passed'])

    def test_complete_active_workstream_can_close_with_partial_project_docs(self):
        p = packet('write_product', 'implementer', 'IMPLEMENTATION')
        p['project_context'] = {
            'project_id':'proj1', 'documentation_status':'partial',
            'active_workstream':'functional',
            'workstreams':[{'id':'functional','documentation_status':'complete'},
                           {'id':'demo','documentation_status':'scratch'}],
        }
        self.assertNotIn('project_context_incomplete', gate(p, 'closeout')['issues'])

    def test_missing_active_workstream_blocks_product_closeout(self):
        p = packet('write_product', 'implementer', 'IMPLEMENTATION')
        p['project_context'] = {
            'project_id':'proj1', 'documentation_status':'complete',
            'active_workstream':'missing', 'workstreams':[],
        }
        self.assertIn('project_context_incomplete', gate(p, 'closeout')['issues'])

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

    def test_regression_activates_diagnosis_without_external_advisor(self):
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

    def test_required_dispatch_receipt_blocks_incomplete_or_generic_child(self):
        p=packet('write_product', 'implementer', 'IMPLEMENTATION')
        p['runtime'].update(dispatch_required=True, required_agent_type='implementer__sol_medium',
                            required_profile='sol_medium')
        issues = gate(p, 'closeout')['issues']
        self.assertIn('dispatch_receipt_required', issues)
        p['runtime']['dispatch_receipt'] = {
            'status': 'incomplete', 'agent_type': 'worker', 'fork_turns': 'all',
            'child_reference': 'child1', 'evidence': ['capacity-error'],
            'model_observed': 'gpt-5.6-sol', 'effort_observed': 'medium'}
        issues = gate(p, 'closeout')['issues']
        self.assertIn('child_incomplete', issues)
        self.assertIn('dispatch_agent_type_mismatch', issues)
        self.assertIn('dispatch_fork_turns_must_be_none', issues)

    def test_required_dispatch_receipt_accepts_exact_completed_child(self):
        p=packet('write_product', 'implementer', 'IMPLEMENTATION')
        p['runtime'].update(dispatch_required=True, required_agent_type='implementer__sol_medium',
                            required_profile='sol_medium', dispatch_receipt={
            'status':'completed', 'agent_type':'implementer__sol_medium', 'fork_turns':'none',
            'child_reference':'child1', 'evidence':['child-terminal-1'],
            'model_observed':'gpt-5.6-sol', 'effort_observed':'medium'})
        self.assertTrue(gate(p, 'closeout')['passed'])

    def test_broad_visual_change_needs_baseline_viewport_and_ux_review(self):
        p=packet('write_product', 'implementer', 'IMPLEMENTATION')
        p['work']['visual_scope'] = 'broad'
        issues = gate(p, 'closeout')['issues']
        self.assertIn('visual_design_baseline_required', issues)
        self.assertIn('visual_validation_required', issues)
        p['runtime'].update(
            design_baseline_evidence=['baseline-1'],
            visual_validation={'viewport':'1440x900', 'screenshots':['after-1'],
                                'responsive_checked':True, 'accessibility_checked':True})
        p['delegations']=[{'id':'ux1','required':True,'required_agent_type':'ux_auditor__sol_high',
                           'agent_type':'ux_auditor__sol_high','fork_turns':'none',
                           'model_observed':'gpt-5.6-sol','effort_observed':'high',
                           'state':'received','candidate_hash':fingerprint(p['candidate']),
                           'evidence':['ux-review-1']}]
        self.assertTrue(gate(p, 'closeout')['passed'])

    def test_broad_visual_change_rejects_generic_or_unbounded_ux_review(self):
        p=packet('write_product', 'implementer', 'IMPLEMENTATION'); p['work']['visual_scope']='redesign'
        p['runtime'].update(design_baseline_evidence=['baseline-1'],
                            visual_validation={'viewport':'390x844','screenshots':['after-1'],
                                               'responsive_checked':True,'accessibility_checked':True})
        p['delegations']=[{'id':'ux1','required':True,'required_agent_type':'ux_auditor__sol_high',
                           'agent_type':'worker','fork_turns':'all','model_observed':'gpt-5.6-sol',
                           'effort_observed':'high','state':'received',
                           'candidate_hash':fingerprint(p['candidate']),'evidence':['ux-review-1']}]
        issues=gate(p,'closeout')['issues']
        self.assertIn('delegation_agent_type_mismatch:ux1',issues)
        self.assertIn('delegation_fork_turns_must_be_none:ux1',issues)

    def test_broad_visual_change_cannot_pass_with_optional_ux_stub(self):
        p=packet('write_product', 'implementer', 'IMPLEMENTATION'); p['work']['visual_scope']='broad'
        p['runtime'].update(design_baseline_evidence=['baseline-1'],
                            visual_validation={'viewport':'1440x900','screenshots':['after-1'],
                                               'responsive_checked':True,'accessibility_checked':True})
        p['delegations']=[{'id':'ux1','required':False,'required_agent_type':'ux_auditor__sol_high',
                           'agent_type':'ux_auditor__sol_high','fork_turns':'none',
                           'model_observed':'gpt-5.6-sol','effort_observed':'high'}]
        self.assertIn('ux_auditor_delegation_required', gate(p, 'closeout')['issues'])

    def test_broad_visual_change_rejects_astra_above_medium(self):
        p=packet('write_product', 'implementer', 'IMPLEMENTATION'); p['work']['visual_scope']='broad'
        p['runtime'].update(design_baseline_evidence=['baseline-1'],
                            visual_validation={'viewport':'1440x900','screenshots':['after-1'],
                                               'responsive_checked':True,'accessibility_checked':True})
        p['delegations']=[{'id':'ux1','required':True,'required_agent_type':'ux_auditor__astra_high',
                           'agent_type':'ux_auditor__astra_high','fork_turns':'none',
                           'model_observed':'gpt-6-astra','effort_observed':'high',
                           'state':'received','candidate_hash':fingerprint(p['candidate']),
                           'evidence':['ux-review-1']}]
        self.assertIn('delegation_astra_effort_above_ceiling:ux1', gate(p, 'closeout')['issues'])

    def test_dispatch_receipt_cannot_relabel_target_profile_or_use_astra_for_writer(self):
        p=packet('write_product', 'implementer', 'IMPLEMENTATION')
        p['runtime'].update(dispatch_required=True, required_agent_type='implementer__sol_medium',
                            required_profile='sol_high', dispatch_receipt={
            'status':'completed','agent_type':'implementer__sol_medium','fork_turns':'none',
            'child_reference':'child1','evidence':['child-terminal-1'],
            'model_observed':'gpt-5.6-sol','effort_observed':'medium'})
        self.assertIn('dispatch_required_profile_mismatch', gate(p, 'closeout')['issues'])
        p['runtime'].update(required_agent_type='implementer__astra_medium', required_profile='astra_medium',
                            dispatch_receipt={'status':'completed','agent_type':'implementer__astra_medium',
                                              'fork_turns':'none','child_reference':'child1',
                                              'evidence':['child-terminal-1'],'model_observed':'gpt-6-astra',
                                              'effort_observed':'medium'})
        self.assertIn('dispatch_astra_role_not_analytic', gate(p, 'closeout')['issues'])

    def test_dispatch_receipt_cannot_use_astra_without_analysis_operation(self):
        p=packet('read', 'systems_analyst', 'AUDIT'); p['work']['analysis']=False
        p['runtime'].update(dispatch_required=True, required_agent_type='systems_analyst__astra_medium',
                            required_profile='astra_medium', dispatch_receipt={
            'status':'completed','agent_type':'systems_analyst__astra_medium','fork_turns':'none',
            'child_reference':'child1','evidence':['child-terminal-1'],
            'model_observed':'gpt-6-astra','effort_observed':'medium'})
        self.assertIn('dispatch_astra_requires_analysis', gate(p, 'closeout')['issues'])

    def test_dispatch_receipt_cannot_use_explicit_sol_profile_without_override(self):
        p=packet('read', 'systems_analyst', 'AUDIT')
        p['runtime'].update(dispatch_required=True, required_agent_type='systems_analyst__sol_xhigh',
                            required_profile='sol_xhigh', dispatch_receipt={
            'status':'completed','agent_type':'systems_analyst__sol_xhigh','fork_turns':'none',
            'child_reference':'child1','evidence':['child-terminal-1'],
            'model_observed':'gpt-5.6-sol','effort_observed':'xhigh'})
        self.assertIn('dispatch_explicit_override_required', gate(p, 'closeout')['issues'])

    def test_delegation_cannot_use_explicit_sol_profile_without_override(self):
        p=packet('write_product', 'implementer', 'IMPLEMENTATION')
        p['delegations']=[{'id':'analysis1','required':True,
                           'required_agent_type':'systems_analyst__sol_xhigh',
                           'agent_type':'systems_analyst__sol_xhigh','fork_turns':'none',
                           'model_observed':'gpt-5.6-sol','effort_observed':'xhigh',
                           'state':'received','candidate_hash':fingerprint(p['candidate']),
                           'evidence':['analysis-1']}]
        self.assertIn('delegation_explicit_override_required:analysis1', gate(p, 'closeout')['issues'])

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
        self.assertIsNone(result['selected']);self.assertEqual(result['status'],'blocked');self.assertEqual(result['reason'],'profile_above_astra_ceiling')
        result=profile_selection('systems_analyst','read',analysis=True,explicit=e,available=['sol_high'])
        self.assertIsNone(result['selected']);self.assertEqual(result['status'],'blocked')

    def test_unavailable_sol_does_not_select_astra(self):
        self.assertIsNone(profile_selection('systems_analyst','read',analysis=True,available=['astra_medium'])['selected'])

    def test_runtime_truth_unknown(self):
        result=profile_selection('implementer','write_product',analysis=False)
        self.assertIsNone(result['provider_observed']);self.assertFalse(result['changes_parent'])


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
