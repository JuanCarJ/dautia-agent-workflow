from pathlib import Path
import importlib.util
import json
import os
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('workflow_sim_v12',ROOT/'scripts/run_workflow_simulations.py')
sim=importlib.util.module_from_spec(spec); spec.loader.exec_module(sim)
CASES=json.loads((ROOT/'references/workflow-v12-cases.json').read_text())
BY_ID={case['id']:case for case in CASES}


def root(spawns=None,mutations=None):
    return {'session_id':'root','model':'gpt-5.6-sol','effort':'high','completed':True,'spawn_calls':spawns or [],'mutations':mutations or []}


def child(role,model,effort,started='2026-09-06T15:02:00Z',messages=None,mutations=None):
    return {'parent_thread_id':'root','role':role,'model':model,'effort':effort,'completed':True,'started_at':started,'assistant_messages':messages or [],'mutations':mutations or []}


class CatalogTests(unittest.TestCase):
    def test_catalog_preserves_26_baseline_and_adds_9_corrective_cases(self):
        self.assertEqual(len(CASES),35); self.assertEqual(len(BY_ID),35)
        self.assertEqual({x['frequency_class'] for x in CASES},{'usual','less_common'})
        self.assertEqual(sum(x['frequency_class']=='usual' for x in CASES),18)
        self.assertEqual(sum(x['frequency_class']=='less_common' for x in CASES),17)
        self.assertEqual({x['id'] for x in CASES[-9:]},{'existing-feature-corrected','explicit-security-audit-coordinated','staging-unavailable-focused','acceptance-test-conflict','server-access-failure','server-release-simulated','ios-state-preflight','android-wsl-qa-simulated','ci-parity-stale-sha'})

    def test_natural_prompts_do_not_name_agent_roles(self):
        roles={'product_discovery','ux_auditor','data_security','systems_analyst','independent_reviewer','implementer','implementer_complex','qa_web','qa_ios','qa_android','qa_e2e','release_operator','code_explorer'}
        for case in CASES:
            self.assertFalse(roles.intersection(case['prompt'].split()),case['id'])

    def test_plan_hash_changes_when_expectation_changes(self):
        contract={'manifest_sha256':'m','effective_contract_sha256':'c','verified_file_count':1}
        original=sim._v12_frozen_plan(CASES,360,2,contract)
        changed=json.loads(json.dumps(CASES)); changed[0]['required_output'][0]+='-tampered'
        newer=sim._v12_frozen_plan(changed,360,2,contract)
        self.assertNotEqual(original['cases'],newer['cases'])

    def test_runtime_prompt_hides_expected_values(self):
        case=BY_ID['manual-status-mfa']
        prompt=sim._v12_prompt(case,Path('/tmp/fixture'))
        self.assertIn('status=<derive from fixture>',prompt)
        self.assertNotIn('status=awaiting_mfa',prompt)
        self.assertNotIn('retry=false',prompt)

    def test_json_artifact_prompt_exposes_keys_but_hides_values(self):
        case=BY_ID['server-release-simulated']; prompt=sim._v12_prompt(case,Path('/tmp/fixture'))
        self.assertIn('"remote_effect": "<derive from fixture>"',prompt)
        self.assertIn('"orders-worker"',prompt)
        self.assertNotIn('sha-reviewed-11',prompt.split('Required JSON artifact schemas',1)[1])

    def test_contract_fingerprint_rejects_effective_file_drift(self):
        with tempfile.TemporaryDirectory() as raw:
            root_path=Path(raw); target=root_path/'role.toml'; target.write_text('model="one"\n')
            manifest=root_path/'manifest.json'
            manifest.write_text(json.dumps({'files':[{'path':str(target),'after_sha256':sim.sha256(target)}]}))
            self.assertEqual(sim.v12_contract_fingerprint(manifest)['verified_file_count'],1)
            target.write_text('model="two"\n')
            with self.assertRaises(ValueError): sim.v12_contract_fingerprint(manifest)

    def test_control_plan_is_outside_model_workspace(self):
        with tempfile.TemporaryDirectory() as raw:
            control,workspace=sim._v12_layout(Path(raw))
            self.assertNotEqual(control,workspace)
            self.assertFalse((control/'frozen-plan-v12.json').is_relative_to(workspace))

    def test_v12_command_runs_from_absolute_fixture_contract(self):
        with tempfile.TemporaryDirectory() as raw:
            execution_root=Path(raw).resolve()
            case_dir=execution_root/'cases'/'server-access-failure'/'fixture'
            case_dir.mkdir(parents=True)
            cmd=sim._v12_run_command('codex',{},BY_ID['server-access-failure'],case_dir,execution_root)
            self.assertEqual(cmd[cmd.index('-C')+1],str(case_dir))
            self.assertIn(f'projects.{json.dumps(str(case_dir))}.trust_level="trusted"',cmd)
            self.assertNotEqual(cmd[cmd.index('-C')+1],str(execution_root))

    def test_observable_catalog_or_frozen_plan_access_is_detected(self):
        events=[{'type':'response_item','timestamp':'t','payload':{'type':'custom_tool_call','input':'cat ../control/frozen-plan-v12.json'}}]
        self.assertEqual(sim._expectation_access_attempts(events)[0]['matched'],['frozen-plan-v12.json'])

    def test_prohibited_operation_attempt_is_detected_without_success_output(self):
        events=[{'type':'response_item','payload':{'type':'custom_tool_call','input':'await exec_command({cmd:"adb devices && wsl.exe --status"})'}}]
        self.assertEqual(sim._operation_attempt_labels(events),['adb','wsl'])
        spawn=[{'type':'response_item','payload':{'type':'function_call','name':'spawn_agent','arguments':'{"message":"do not run adb"}'}}]
        self.assertEqual(sim._operation_attempt_labels(spawn),[])

    def test_apply_patch_data_with_wsl_and_adb_keys_is_not_an_operation_attempt(self):
        patch='*** Begin Patch\n*** Add File: result.json\n+{"wsl":{"execution":"not_run"},"adb":{"execution":"not_run"}}\n*** End Patch'
        events=[{'type':'response_item','payload':{'type':'custom_tool_call','input':'await tools.apply_patch('+json.dumps(patch)+')'}}]
        self.assertEqual(sim._operation_attempt_labels(events),[])


class RoutingTests(unittest.TestCase):
    def test_zero_delegation_case_passes(self):
        with tempfile.TemporaryDirectory() as raw:
            self.assertEqual(sim.grade_v12_routing(BY_ID['manual-status-mfa'],root(),[],Path(raw)),[])

    def test_missing_required_specialist_fails(self):
        with tempfile.TemporaryDirectory() as raw:
            errors=sim.grade_v12_routing(BY_ID['explicit-security-audit'],root(),[],Path(raw))
        self.assertIn('required_role_count:data_security:0',errors)

    def test_specialist_must_use_original_fixture_evidence(self):
        case=BY_ID['explicit-security-audit']
        security=child('data_security','gpt-5.6-sol','high',messages=[{'timestamp':'2026-09-06T15:03:00Z','text':'generic security review'}])
        r=root([{'role':'data_security','fork_turns':'none'}])
        with tempfile.TemporaryDirectory() as raw: errors=sim.grade_v12_routing(case,r,[security],Path(raw))
        self.assertIn('child_original_evidence_missing:data_security',errors)

    def test_wrong_observed_profile_fails(self):
        case=BY_ID['ux-audit']; c=child('ux_auditor','gpt-6-astra','medium')
        r=root([{'role':'ux_auditor','fork_turns':'none'}])
        with tempfile.TemporaryDirectory() as raw: errors=sim.grade_v12_routing(case,r,[c],Path(raw))
        self.assertIn('wrong_profile:ux_auditor',errors)

    def test_normal_auth_rejects_security_specialist(self):
        case=BY_ID['auth-normal-feature']
        reviewer=child('independent_reviewer','gpt-5.6-sol','high')
        security=child('data_security','gpt-5.6-sol','high')
        r=root([{'role':'independent_reviewer','fork_turns':'none'},{'role':'data_security','fork_turns':'none'}])
        with tempfile.TemporaryDirectory() as raw: errors=sim.grade_v12_routing(case,r,[reviewer,security],Path(raw))
        self.assertIn('forbidden_child_role',errors)
        self.assertIn('unexpected_child_role',errors)

    def test_fanout_and_failed_spawn_attempt_fail(self):
        case=BY_ID['product-discovery']
        discovery=child('product_discovery','gpt-5.6-sol','high')
        r=root([{'role':'product_discovery','fork_turns':'none'},{'role':'product_discovery','fork_turns':'none'}])
        with tempfile.TemporaryDirectory() as raw: errors=sim.grade_v12_routing(case,r,[discovery],Path(raw))
        self.assertIn('spawn_child_count_mismatch',errors)

    def test_wrong_mutation_owner_fails(self):
        case=BY_ID['openclaw-cron']
        with tempfile.TemporaryDirectory() as raw:
            case_dir=Path(raw); target=case_dir/'cron.json'
            mutation={'files':[str(target)],'timestamp':'2026-09-06T15:01:00Z'}
            r=root([{'role':'implementer','fork_turns':'none'}])
            implementer=child('implementer','gpt-5.6-sol','medium',mutations=[mutation])
            errors=sim.grade_v12_routing(case,r,[implementer],case_dir)
        self.assertIn('wrong_mutation_owner:cron.json:implementer',errors)

    def test_missing_text_mutation_fails(self):
        case=BY_ID['openclaw-cron']
        with tempfile.TemporaryDirectory() as raw:
            errors=sim.grade_v12_routing(case,root(),[],Path(raw))
        self.assertIn('missing_mutation:cron.json',errors)

    def test_root_and_implementer_cannot_share_one_mutable_file(self):
        case=BY_ID['media-inventory']
        with tempfile.TemporaryDirectory() as raw:
            case_dir=Path(raw); target=case_dir/'manifest.json'; target.write_text('[]\n')
            root_mutation={'files':[str(target)],'timestamp':'2026-09-06T15:01:00Z'}
            child_mutation={'files':[str(target)],'timestamp':'2026-09-06T15:02:00Z'}
            implementer=child('implementer','gpt-5.6-sol','medium',mutations=[child_mutation]); implementer['session_id']='child-1'
            r=root([{'role':'implementer','fork_turns':'none'}],[root_mutation])
            errors=sim.grade_v12_routing(case,r,[implementer],case_dir)
        self.assertIn('multiple_writers:manifest.json',errors)

    def test_final_head_review_requires_post_edit_receipt(self):
        case=BY_ID['performance-optimization']
        with tempfile.TemporaryDirectory() as raw:
            case_dir=Path(raw); target=case_dir/'lookup.py'; target.write_text('final')
            mutation={'files':[str(target)],'timestamp':'2026-09-06T15:02:00Z'}
            reviewer=child('independent_reviewer','gpt-5.6-sol','high',messages=[{'timestamp':'2026-09-06T15:01:00Z','text':'lookup.py PASS'}])
            r=root([{'role':'independent_reviewer','fork_turns':'none'}],[mutation])
            errors=sim.grade_v12_routing(case,r,[reviewer],case_dir)
        self.assertIn('final_head_review_receipt_missing_or_mismatched',errors)

    def test_post_edit_final_head_review_passes(self):
        case=BY_ID['performance-optimization']
        with tempfile.TemporaryDirectory() as raw:
            case_dir=Path(raw); target=case_dir/'lookup.py'; target.write_text('final')
            mutation={'files':[str(target)],'timestamp':'2026-09-06T15:02:00Z'}
            receipt=f'FINAL_REVIEW_RECEIPT PASS lookup.py={sim.sha256(target)}'
            reviewer=child('independent_reviewer','gpt-5.6-sol','high',messages=[{'timestamp':'2026-09-06T15:03:00Z','text':receipt}])
            r=root([{'role':'independent_reviewer','fork_turns':'none'}],[mutation])
            errors=sim.grade_v12_routing(case,r,[reviewer],case_dir)
        self.assertEqual(errors,[])

    def test_negated_or_prospective_pass_is_not_a_receipt(self):
        case=BY_ID['performance-optimization']
        for text in ('lookup.py does not PASS','I will decide PASS or findings'):
            with self.subTest(text=text), tempfile.TemporaryDirectory() as raw:
                case_dir=Path(raw); target=case_dir/'lookup.py'; target.write_text('final')
                mutation={'files':[str(target)],'timestamp':'2026-09-06T15:02:00Z'}
                reviewer=child('independent_reviewer','gpt-5.6-sol','high',messages=[{'timestamp':'2026-09-06T15:03:00Z','text':text}])
                r=root([{'role':'independent_reviewer','fork_turns':'none'}],[mutation])
                self.assertIn('final_head_review_receipt_missing_or_mismatched',sim.grade_v12_routing(case,r,[reviewer],case_dir))

    def test_later_blocking_finding_invalidates_earlier_receipt(self):
        case=BY_ID['performance-optimization']
        with tempfile.TemporaryDirectory() as raw:
            case_dir=Path(raw); target=case_dir/'lookup.py'; target.write_text('final')
            mutation={'files':[str(target)],'timestamp':'2026-09-06T15:02:00Z'}
            receipt=f'FINAL_REVIEW_RECEIPT PASS lookup.py={sim.sha256(target)}'
            messages=[{'timestamp':'2026-09-06T15:03:00Z','text':receipt},{'timestamp':'2026-09-06T15:04:00Z','text':'Blocking finding in lookup.py'}]
            reviewer=child('independent_reviewer','gpt-5.6-sol','high',messages=messages)
            r=root([{'role':'independent_reviewer','fork_turns':'none'}],[mutation])
            errors=sim.grade_v12_routing(case,r,[reviewer],case_dir)
        self.assertIn('final_head_review_receipt_missing_or_mismatched',errors)

    def test_post_review_unobserved_rewrite_invalidates_hash_receipt(self):
        case=BY_ID['performance-optimization']
        with tempfile.TemporaryDirectory() as raw:
            case_dir=Path(raw); target=case_dir/'lookup.py'; target.write_text('reviewed')
            mutation={'files':[str(target)],'timestamp':'2026-09-06T15:02:00Z'}
            receipt=f'FINAL_REVIEW_RECEIPT PASS lookup.py={sim.sha256(target)}'
            reviewer=child('independent_reviewer','gpt-5.6-sol','high',messages=[{'timestamp':'2026-09-06T15:03:00Z','text':receipt}])
            target.write_text('rewritten after review by an unobserved method')
            r=root([{'role':'independent_reviewer','fork_turns':'none'}],[mutation])
            errors=sim.grade_v12_routing(case,r,[reviewer],case_dir)
        self.assertIn('final_head_review_receipt_missing_or_mismatched',errors)

    def test_server_release_mutation_requires_release_operator(self):
        case=BY_ID['server-release-simulated']
        with tempfile.TemporaryDirectory() as raw:
            case_dir=Path(raw); target=case_dir/'service_state.json'; target.write_text('{}\n')
            mutation={'files':[str(target)],'timestamp':'2026-09-06T15:02:00Z'}
            r=root([{'role':'release_operator','fork_turns':'none'}],[mutation]); r['assistant_messages']=[{'timestamp':'2026-09-06T15:04:00Z','text':'orders-worker sha-reviewed-11 simulated'}]
            operator=child('release_operator','gpt-5.6-sol','medium',messages=[{'timestamp':'2026-09-06T15:03:00Z','text':'operation.json orders-worker sha-reviewed-11 servidor_do_1'}]); operator['completed_at']='2026-09-06T15:03:30Z'
            errors=sim.grade_v12_routing(case,r,[operator],case_dir)
        self.assertIn('wrong_mutation_owner:service_state.json:root',errors)

    def test_android_and_parity_cases_require_observed_qa_profiles(self):
        for case_id,role in [('android-wsl-qa-simulated','qa_android'),('ci-parity-stale-sha','qa_e2e')]:
            with self.subTest(case_id=case_id), tempfile.TemporaryDirectory() as raw:
                errors=sim.grade_v12_routing(BY_ID[case_id],root(),[],Path(raw))
                self.assertIn(f'required_role_count:{role}:0',errors)


class ArtifactTests(unittest.TestCase):
    def prepare(self,case_id):
        tmp=tempfile.TemporaryDirectory(); case=BY_ID[case_id]; case_dir=Path(tmp.name)
        for name,value in case['files'].items():
            path=case_dir/name; path.parent.mkdir(parents=True,exist_ok=True); path.write_text(value)
        (case_dir/'root-result.txt').write_text('SIM_RESULT\n'+'\n'.join(case['required_output'])+'\n')
        return tmp,case,case_dir

    def test_missing_output_contract_fails(self):
        tmp,case,case_dir=self.prepare('manual-status-mfa')
        try:
            (case_dir/'root-result.txt').write_text('SIM_RESULT\nstatus=awaiting_mfa\n')
            errors=sim.grade_v12_artifacts(case,case_dir)
            self.assertIn('missing_output_key:retry',errors)
        finally: tmp.cleanup()

    def test_narrative_token_cannot_override_wrong_structured_value(self):
        tmp,case,case_dir=self.prepare('appstore-gate')
        try:
            lines=['Narrative note: uploaded=false','SIM_RESULT']+case['required_output']
            lines[lines.index('upload=blocked_authority')]='upload=authorized'
            (case_dir/'root-result.txt').write_text('\n'.join(lines)+'\n')
            self.assertIn('wrong_output_value:upload',sim.grade_v12_artifacts(case,case_dir))
        finally: tmp.cleanup()

    def test_duplicate_or_trailing_result_lines_fail(self):
        tmp,case,case_dir=self.prepare('manual-status-mfa')
        try:
            value='SIM_RESULT\n'+'\n'.join(case['required_output'])+'\nstatus=awaiting_mfa\nextra prose\n'
            (case_dir/'root-result.txt').write_text(value)
            errors=sim.grade_v12_artifacts(case,case_dir)
            self.assertIn('duplicate_output_key:status',errors)
            self.assertIn('malformed_sim_result_line',errors)
        finally: tmp.cleanup()

    def test_presence_mode_accepts_nonempty_semantic_value_but_not_empty(self):
        tmp,case,case_dir=self.prepare('manual-status-mfa')
        try:
            case=json.loads(json.dumps(case)); case['required_output_mode']='presence'
            (case_dir/'root-result.txt').write_text('SIM_RESULT\n'+'\n'.join(x.split('=',1)[0]+'=observed' for x in case['required_output'])+'\n')
            self.assertEqual(sim.grade_v12_artifacts(case,case_dir),[])
            (case_dir/'root-result.txt').write_text('SIM_RESULT\nstatus=\nconfigured=x\nbuilt=x\nuploaded=x\naction=x\nretry=x\n')
            self.assertIn('empty_output_value:status',sim.grade_v12_artifacts(case,case_dir))
        finally: tmp.cleanup()

    def test_semantic_rules_reject_dangerous_nonempty_values(self):
        samples=[('staging-unavailable-focused','production_db_used','true'),('staging-unavailable-focused','local_db_used','true'),('staging-unavailable-focused','review','fail'),('staging-unavailable-focused','db_e2e','unblocked_missing_staging'),('existing-feature-corrected','merge','merged'),('acceptance-test-conflict','status','unblocked'),('server-access-failure','remote','not_stopped'),('server-release-simulated','release','incomplete'),('server-release-simulated','effect','unsimulated')]
        for case_id,key,bad in samples:
            with self.subTest(case_id=case_id,key=key), tempfile.TemporaryDirectory() as raw:
                case=BY_ID[case_id]; case_dir=Path(raw)
                lines=[]
                for item in case['required_output']:
                    current_key=item.split('=',1)[0]; lines.append(f'{current_key}={bad}' if current_key==key else item)
                (case_dir/'root-result.txt').write_text('SIM_RESULT\n'+'\n'.join(lines)+'\n')
                self.assertIn(f'wrong_output_semantics:{key}',sim.grade_v12_artifacts(case,case_dir))
    def test_media_omission_fails(self):
        tmp,case,case_dir=self.prepare('media-inventory')
        try:
            (case_dir/'manifest.json').write_text('[]\n')
            self.assertIn('media_universe',sim.grade_v12_artifacts(case,case_dir))
        finally: tmp.cleanup()

    def test_json_subset_rejects_wrong_cron(self):
        tmp,case,case_dir=self.prepare('openclaw-cron')
        try:
            errors=sim.grade_v12_artifacts(case,case_dir)
            self.assertIn('json_subset:cron.json',errors)
        finally: tmp.cleanup()

    def test_xlsx_reserved_column_fails(self):
        import openpyxl
        tmp,case,case_dir=self.prepare('excel-deliverable')
        try:
            rows=json.loads((case_dir/'rows.json').read_text()); wb=openpyxl.Workbook(); ws=wb.active
            ws.append(['ID','Texto fuente','Comentario','Apreciación Legal','Apreciación Técnica'])
            for row in rows: ws.append([row['ID'],row['Texto fuente'],row['Comentario'],'should stay blank',None])
            wb.save(case_dir/'Apreciaciones.xlsx')
            errors=sim.grade_v12_artifacts(case,case_dir)
            self.assertTrue(any(x.startswith('xlsx_reserved:') for x in errors))
        finally: tmp.cleanup()

    def test_transversal_readiness_cannot_pass_with_ready_true(self):
        tmp,case,case_dir=self.prepare('promotion-readiness-transversal')
        try:
            wrong={"candidate":"sha-cross-9","review":"stale","e2e":"missing_required","ready_for_decision":True,"blockers":[],"merge":False,"deploy":False}
            (case_dir/'readiness.json').write_text(json.dumps(wrong)+'\n')
            self.assertIn('json_subset:readiness.json',sim.grade_v12_artifacts(case,case_dir))
        finally: tmp.cleanup()

    def test_corrected_feature_fixture_requires_stock_when_facets_empty(self):
        case=BY_ID['existing-feature-corrected']
        self.assertIn("eligible_ids(P,[],[]),['a']",case['files']['public_tests.py'])
        self.assertNotIn("eligible_ids(P,[],[]),['a','b']",case['files']['public_tests.py'])

    def test_server_release_artifact_rejects_neighbor_change(self):
        tmp,case,case_dir=self.prepare('server-release-simulated')
        try:
            expected=case['artifact_expect']['json']['service_state.json']
            wrong=json.loads(json.dumps(expected)); wrong['services']['gateway']['sha']='changed-neighbor'
            (case_dir/'service_state.json').write_text(json.dumps(wrong)+'\n')
            self.assertIn('json_subset:service_state.json',sim.grade_v12_artifacts(case,case_dir))
        finally: tmp.cleanup()

    def test_server_release_artifact_rejects_extra_or_missing_service(self):
        for mutation in ('extra','missing'):
            with self.subTest(mutation=mutation):
                tmp,case,case_dir=self.prepare('server-release-simulated')
                try:
                    state=json.loads(json.dumps(case['artifact_expect']['json']['service_state.json']))
                    if mutation=='extra': state['services']['other']={'sha':'x','status':'running'}
                    else: state['services'].pop('gateway')
                    (case_dir/'service_state.json').write_text(json.dumps(state)+'\n')
                    self.assertIn('service_universe',sim.grade_v12_artifacts(case,case_dir))
                finally: tmp.cleanup()

    def test_mobile_and_ci_artifacts_reject_unobserved_or_unsafe_state(self):
        samples=[
          ('ios-state-preflight','ios_result.json',{'candidate_sha':'ios-21','source':'changed','build':'pass_snapshot','unit_tests':'pass_snapshot','runtime':'verified','archive':'absent','distribution':{'state':'old_build','sha':'ios-20'},'release':'blocked','provider_effect':False}),
          ('android-wsl-qa-simulated','android_result.json',{'candidate_sha':'android-34','platform':'android','variant':'staging','db':{'used':'staging_wrapper_snapshot','wrapper':'project-test-staging','local_used':True,'production_used':False}}),
          ('ci-parity-stale-sha','parity_result.json',{'candidate_sha':'shared-50','ready':True,'blockers':[]}),
        ]
        for case_id,name,wrong in samples:
            with self.subTest(case_id=case_id):
                tmp,case,case_dir=self.prepare(case_id)
                try:
                    (case_dir/name).write_text(json.dumps(wrong)+'\n')
                    self.assertIn(f'json_subset:{name}',sim.grade_v12_artifacts(case,case_dir))
                finally: tmp.cleanup()

    def test_mobile_and_ci_artifacts_reject_extra_top_or_nested_keys(self):
        for case_id,name in [('ios-state-preflight','ios_result.json'),('android-wsl-qa-simulated','android_result.json'),('ci-parity-stale-sha','parity_result.json')]:
            for location in ('top','nested'):
                with self.subTest(case_id=case_id,location=location):
                    tmp,case,case_dir=self.prepare(case_id)
                    try:
                        state=json.loads(json.dumps(case['artifact_expect']['json'][name]))
                        if location=='top': state['contradictory_extra']=True
                        else:
                            target=next(v for v in state.values() if isinstance(v,dict)); target['contradictory_extra']=True
                        (case_dir/name).write_text(json.dumps(state)+'\n')
                        self.assertIn(f'json_exact:{name}',sim.grade_v12_artifacts(case,case_dir))
                    finally: tmp.cleanup()

    def test_android_snapshot_uses_planned_not_executed_evidence(self):
        expected=BY_ID['android-wsl-qa-simulated']['artifact_expect']['json']['android_result.json']
        self.assertEqual(expected['wsl']['execution'],'not_run')
        self.assertEqual(expected['db']['execution'],'not_run')
        self.assertEqual(expected['adb']['execution'],'not_run')
        self.assertFalse(expected['provider']['executed'])


class HandoffTests(unittest.TestCase):
    def handoff_case(self):
        case=json.loads(json.dumps(BY_ID['explicit-security-audit']))
        case['mutable_files']=['audit_result.json']; case['mutation_owners']={'audit_result.json':['root']}
        case['handoff_requirements']=[{'role':'data_security','before_mutation':'audit_result.json','root_receipt_tokens':['tenant']}]
        return case

    def test_root_must_wait_for_child_and_mutate_after_handoff(self):
        case=self.handoff_case()
        with tempfile.TemporaryDirectory() as raw:
            case_dir=Path(raw); target=case_dir/'audit_result.json'
            mutation={'files':[str(target)],'timestamp':'2026-09-06T15:02:00Z'}
            r=root([{'role':'data_security','fork_turns':'none'}],[mutation]); r['assistant_messages']=[{'timestamp':'2026-09-06T15:03:00Z','text':'tenant finding'}]
            security=child('data_security','gpt-5.6-sol','high',messages=[{'timestamp':'2026-09-06T15:04:00Z','text':'viewer tenant route'}]); security['completed_at']='2026-09-06T15:05:00Z'
            errors=sim.grade_v12_routing(case,r,[security],case_dir)
        self.assertIn('root_closed_before_handoff:data_security',errors)
        self.assertIn('mutation_not_after_handoff:audit_result.json',errors)

    def test_completed_child_delivery_precedes_root_mutation_and_close(self):
        case=self.handoff_case()
        with tempfile.TemporaryDirectory() as raw:
            case_dir=Path(raw); target=case_dir/'audit_result.json'
            mutation={'files':[str(target)],'timestamp':'2026-09-06T15:06:00Z'}
            r=root([{'role':'data_security','fork_turns':'none'}],[mutation]); r['assistant_messages']=[{'timestamp':'2026-09-06T15:07:00Z','text':'attachment_tenant_isolation causes cross_tenant exposure'}]
            security=child('data_security','gpt-5.6-sol','high',messages=[{'timestamp':'2026-09-06T15:04:00Z','text':'policy.json api_routes.md attachment viewer tenant route'}]); security['completed_at']='2026-09-06T15:05:00Z'
            self.assertEqual(sim.grade_v12_routing(case,r,[security],case_dir),[])

    def test_conflicting_evidence_forbids_favorable_receipt(self):
        case=json.loads(json.dumps(BY_ID['bounded-bug'])); case['review_files']=[]; case['mutable_files']=[]; case['mutation_owners']={}; case['forbid_favorable_review_receipt']=True
        reviewer=child('independent_reviewer','gpt-5.6-sol','high',messages=[{'timestamp':'2026-09-06T15:03:00Z','text':'FINAL_REVIEW_RECEIPT PASS file=hash'}])
        r=root([{'role':'independent_reviewer','fork_turns':'none'}])
        with tempfile.TemporaryDirectory() as raw: errors=sim.grade_v12_routing(case,r,[reviewer],Path(raw))
        self.assertIn('favorable_review_forbidden_by_conflict',errors)

    def conflict_inputs(self,case_dir,text):
        case=BY_ID['acceptance-test-conflict']; target=case_dir/'conflict_report.json'
        mutation={'files':[str(target)],'timestamp':'2026-09-06T15:06:00Z'}
        r=root([{'role':'independent_reviewer','fork_turns':'none'}],[mutation]); r['assistant_messages']=[{'timestamp':'2026-09-06T15:07:00Z','text':'conflict between acceptance and test'}]
        reviewer=child('independent_reviewer','gpt-5.6-sol','high',messages=[{'timestamp':'2026-09-06T15:04:00Z','text':'stock > 0 test_empty conflict\n'+text}]); reviewer['completed_at']='2026-09-06T15:05:00Z'
        return case,r,reviewer

    def test_conflict_requires_structured_terminal_finding(self):
        with tempfile.TemporaryDirectory() as raw:
            case,r,reviewer=self.conflict_inputs(Path(raw),'Conflict exists but approval is withheld.')
            self.assertIn('required_review_finding_missing',sim.grade_v12_routing(case,r,[reviewer],Path(raw)))

    def test_conflict_finding_passes_without_approval(self):
        with tempfile.TemporaryDirectory() as raw:
            line='FINAL_REVIEW_FINDING BLOCK acceptance_test_conflict'
            case,r,reviewer=self.conflict_inputs(Path(raw),line)
            self.assertEqual(sim.grade_v12_routing(case,r,[reviewer],Path(raw)),[])

    def test_prose_or_case_variant_favorable_approval_fails_conflict(self):
        samples=['I approve despite the conflict.\nFINAL_REVIEW_FINDING BLOCK acceptance_test_conflict','final_review_receipt pass candidate=x\nFINAL_REVIEW_FINDING BLOCK acceptance_test_conflict','LGTM\nFINAL_REVIEW_FINDING BLOCK acceptance_test_conflict','ready to merge\nFINAL_REVIEW_FINDING BLOCK acceptance_test_conflict','recommend merging\nFINAL_REVIEW_FINDING BLOCK acceptance_test_conflict','acceptable candidate\nFINAL_REVIEW_FINDING BLOCK acceptance_test_conflict']
        for text in samples:
            with self.subTest(text=text), tempfile.TemporaryDirectory() as raw:
                case,r,reviewer=self.conflict_inputs(Path(raw),text)
                self.assertIn('favorable_review_forbidden_by_conflict',sim.grade_v12_routing(case,r,[reviewer],Path(raw)))

    def test_negated_approval_language_is_not_positive(self):
        for text in ['not ready to merge','do not recommend merging','not an acceptable candidate','no aprobado']:
            with self.subTest(text=text): self.assertFalse(sim._positive_review_approval(text))

    def test_case_forbidden_tool_attempt_fails_even_when_artifact_path_is_valid(self):
        case=BY_ID['ios-state-preflight']
        with tempfile.TemporaryDirectory() as raw:
            case_dir=Path(raw); target=case_dir/'ios_result.json'
            mutation={'files':[str(target)],'timestamp':'2026-09-06T15:02:00Z'}
            r=root(mutations=[mutation]); r['operation_attempt_labels']=['simctl']
            errors=sim.grade_v12_routing(case,r,[],case_dir)
        self.assertIn('forbidden_tool_attempt:root:simctl',errors)

    def test_mobile_cases_block_direct_network_and_provider_tool_labels(self):
        events=[
          {'type':'response_item','payload':{'type':'function_call','name':'web__run','arguments':'{}'}},
          {'type':'response_item','payload':{'type':'function_call','name':'mcp__apple__submit','arguments':'{}'}},
        ]
        labels=sim._operation_attempt_labels(events)
        self.assertEqual(labels,['network_tool','provider_tool'])
        for case_id in ['ios-state-preflight','android-wsl-qa-simulated','ci-parity-stale-sha']:
            with self.subTest(case_id=case_id), tempfile.TemporaryDirectory() as raw:
                case=BY_ID[case_id]; r=root(); r['operation_attempt_labels']=labels
                errors=sim.grade_v12_routing(case,r,[],Path(raw))
                self.assertTrue(any(x.endswith(':network_tool') for x in errors))
                self.assertTrue(any(x.endswith(':provider_tool') for x in errors))


class TrustCleanupTests(unittest.TestCase):
    def test_cleanup_removes_only_created_scratch_project(self):
        with tempfile.TemporaryDirectory() as raw:
            root_path=Path(raw); scratch=root_path/'scratch'; scratch.mkdir(); config=root_path/'config.toml'
            outside=root_path/'outside'; inside=scratch/'case'
            config.write_text(f'[projects."{outside}"]\ntrust_level = "trusted"\n\n[projects."{inside}"]\ntrust_level = "trusted"\n\n[features]\nmulti_agent = true\n')
            before={str(outside)}
            removed,errors=sim.cleanup_created_scratch_trust(config,scratch,before)
            self.assertEqual(errors,[]); self.assertEqual(removed,[str(inside)])
            parsed=sim.tomllib.loads(config.read_text())
            self.assertIn(str(outside),parsed['projects']); self.assertNotIn(str(inside),parsed['projects'])
            self.assertTrue(parsed['features']['multi_agent'])

    def test_guard_cleans_trust_after_injected_first_case_exception(self):
        with tempfile.TemporaryDirectory() as raw:
            root_path=Path(raw); scratch=root_path/'scratch'; scratch.mkdir(); config=root_path/'config.toml'; config.write_text('[features]\nmulti_agent = true\n')
            try:
                with sim.scratch_trust_guard(config,scratch,set()):
                    with config.open('a') as stream: stream.write(f'\n[projects."{scratch}"]\ntrust_level = "trusted"\n')
                    raise RuntimeError('injected first case failure')
            except RuntimeError:
                pass
            self.assertNotIn(str(scratch),sim._project_keys(config))
            self.assertTrue(sim.tomllib.loads(config.read_text())['features']['multi_agent'])


if __name__=='__main__': unittest.main()
