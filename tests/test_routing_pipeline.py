"""Deterministic routing and dispatch checks without a provider advisor."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock

from test_r3_core import packet
from workflow_core import ContractError, fingerprint, policy, profile_selection, routing_arguments
from workflow_dispatch import prepare_dispatch, dispatch_prepared, validate_spawn_report
from workflow_store import export_events
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from render_agents import render


class RoutingPipelineTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.agents = self.root / 'agents'; self.agents.mkdir()
        profile = json.loads((ROOT / 'profiles/codex-macos.yaml').read_text())
        generated = render(ROOT, profile)
        for path, raw in generated.items():
            if path.startswith('codex/'):
                (self.agents / Path(path).name).write_bytes(raw)
        definitions = {Path(path).name: hashlib.sha256(raw).hexdigest()
                       for path, raw in generated.items() if path.startswith('codex/')}
        (self.agents / 'dautia-r3-definitions.json').write_text(
            json.dumps({'schema_version': 1, 'definitions': definitions}))
        self.targets = [Path(path).stem for path in generated if path.startswith('codex/')]

    def work(self, difficulty='routine'):
        p = packet('write_product', 'implementer', 'IMPLEMENTATION')
        p['work'].update(decisions_resolved=True, execution_difficulty=difficulty)
        p['runtime']['available_profiles'] = list(policy()['profiles'])
        p['runtime']['available_targets'] = self.targets
        p['runtime'].update(dispatch_required=True,
                            required_agent_type='implementer__' + ('sol_medium' if difficulty == 'routine' else 'sol_high'),
                            required_profile='sol_medium' if difficulty == 'routine' else 'sol_high')
        return p

    def decision(self, p):
        selection = profile_selection(**routing_arguments(p))
        selected = selection.get('selected')
        return {
            'schema_version': 1, 'stage': 'route',
            'status': 'selected' if selected else 'blocked',
            'selection': selection,
            'dispatch_target': p['work']['role'] + '__' + selected if selected else None,
            'context_hash': fingerprint(p), 'policy_hash': fingerprint(policy()),
            'dispatch_blocked_reason': selection.get('reason') if not selected else None,
            'network_called': False, 'authorizes_action': False,
        }

    def test_medium_is_deterministic_for_prepared_routine_work(self):
        p = self.work(); decision = self.decision(p)
        self.assertEqual(decision['selection']['selected'], 'sol_medium')
        self.assertEqual(decision['dispatch_target'], 'implementer__sol_medium')
        self.assertFalse(decision['network_called'])

    def test_high_is_deterministic_for_demanding_work(self):
        self.assertEqual(self.decision(self.work('demanding'))['selection']['selected'], 'sol_high')

    def test_unknown_execution_difficulty_requires_classification(self):
        selection=self.decision(self.work('unknown'))['selection']
        self.assertIsNone(selection['selected'])
        self.assertEqual(selection['reason'],'execution_difficulty_classification_required')

    def test_analysis_can_choose_astra_medium_with_evidence(self):
        p = packet(); p['runtime']['available_profiles'] = list(policy()['profiles'])
        p['runtime']['available_targets'] = self.targets
        p['runtime']['principal_choice'] = {'profile': 'astra_medium', 'evidence_refs': ['coupling-analysis-1']}
        decision = self.decision(p)
        self.assertEqual(decision['selection']['selected'], 'astra_medium')
        self.assertEqual(decision['dispatch_target'], 'systems_analyst__astra_medium')

    def test_astra_above_medium_is_rejected(self):
        rules=copy.deepcopy(policy())
        rules['profiles']['astra_high']={'model':'gpt-6-astra','effort':'high','family':'astra'}
        override = {'profile': 'astra_high', 'source_kind': 'user', 'source_refs': ['user1']}
        result = profile_selection('systems_analyst', 'read', analysis=True,
                                   explicit=override, available=['astra_high'],rules=rules)
        self.assertEqual(result['status'], 'blocked')
        self.assertEqual(result['reason'], 'profile_above_astra_ceiling')

    def test_dispatch_is_exactly_once_and_reconciled(self):
        p = self.work(); decision = self.decision(p)
        plan = prepare_dispatch(p, decision, self.agents)
        spawn = Mock(return_value={'agent_id': 'native-child-1',
                                   'agent_type': 'implementer__sol_medium',
                                   'fork_turns': 'none', 'model': 'gpt-6-sol',
                                   'model_reasoning_effort': 'medium'})
        ledger = self.root / 'ledger'
        result = dispatch_prepared(p, decision, plan, self.agents, spawn,
                                   events_root=self.root / 'events', ledger_root=ledger)
        self.assertEqual(result['status'], 'started')
        self.assertTrue(result['native_callback_metadata_matched'])
        self.assertFalse(result['native_enforcement_verified'])
        self.assertFalse(result['model_provenance']['provider_verified'])
        self.assertEqual(result['model_provenance']['reported_source'],'native_callback_metadata')
        self.assertTrue(result['dispatch_id'])
        reused = dispatch_prepared(p, decision, plan, self.agents, spawn,
                                   ledger_root=ledger)
        self.assertEqual(reused['status'], 'dispatch_already_reserved')
        spawn.assert_called_once()
        self.assertEqual([e['event_type'] for e in export_events(self.root / 'events', 'obj1')['events']],
                         ['dispatch.requested', 'agent.started'])

    def test_spawn_report_requires_exact_role_and_bounded_depth(self):
        p = self.work(); plan = prepare_dispatch(p, self.decision(p), self.agents)
        self.assertEqual(validate_spawn_report(plan, {
            'agent_type': 'implementer__sol_medium', 'fork_turns': 'none',
            'model': 'gpt-6-sol', 'model_reasoning_effort': 'medium'}), [])
        self.assertIn('agent_type_mismatch', validate_spawn_report(plan, {
            'agent_type': 'worker', 'fork_turns': 'none', 'model': 'gpt-6-sol',
            'model_reasoning_effort': 'medium'}))
        self.assertIn('fork_turns_must_be_none', validate_spawn_report(plan, {
            'agent_type': 'implementer__sol_medium', 'fork_turns': 'all',
            'model': 'gpt-6-sol', 'model_reasoning_effort': 'medium'}))

    def test_dispatch_contract_violation_is_preserved_after_child_start(self):
        p = self.work(); decision = self.decision(p); plan = prepare_dispatch(p, decision, self.agents)
        spawn = Mock(return_value={'agent_id': 'native-child-2', 'agent_type': 'worker',
                                   'fork_turns': 'all', 'model': 'gpt-6-sol',
                                   'model_reasoning_effort': 'medium'})
        result = dispatch_prepared(p, decision, plan, self.agents, spawn)
        self.assertEqual(result['status'], 'dispatch_contract_violation')
        self.assertTrue(result['dispatch_performed'])
        self.assertFalse(result['native_enforcement_verified'])
        self.assertFalse(result['native_callback_metadata_matched'])
        self.assertIn('agent_type_mismatch', result['dispatch_contract_issues'])

    def test_luna_is_bounded_to_read_roles_and_exact_receipt(self):
        p=packet('read','code_explorer','AUDIT');p['work']['analysis']=True
        p['runtime'].update(available_profiles=list(policy()['profiles']),available_targets=self.targets,
                            dispatch_required=True,required_agent_type='code_explorer__luna_high',
                            required_profile='luna_high')
        decision=self.decision(p);self.assertEqual(decision['selection']['selected'],'luna_high')
        plan=prepare_dispatch(p,decision,self.agents)
        self.assertEqual((plan['model_requested'],plan['effort_requested']),('gpt-6-luna','high'))
        denied=profile_selection('release_operator','external_mutation',analysis=False,
                                 explicit={'profile':'luna_high','source_kind':'user','source_refs':['user1']},
                                 available=['luna_high'])
        self.assertEqual(denied['reason'],'luna_not_read_candidate')

    def test_dispatch_requires_requirement_to_be_bound_in_packet(self):
        p = self.work(); p['runtime'].pop('dispatch_required'); p['runtime'].pop('required_agent_type'); p['runtime'].pop('required_profile')
        with self.assertRaisesRegex(ContractError, 'dispatch_requirement_not_bound'):
            prepare_dispatch(p, self.decision(p), self.agents)

    def test_unresolved_decisions_block_before_dispatch(self):
        p = self.work(); p['work']['decisions_resolved'] = False
        result = self.decision(p)
        self.assertIsNone(result['selection']['selected'])
        with self.assertRaises(ContractError):
            prepare_dispatch(p, result, self.agents)

    def test_dispatch_cli_is_offline_and_does_not_require_external_advisor(self):
        source = ROOT / 'skills/dautia-project-cycle/scripts/workflow_cli.py'
        self.assertNotIn('jev_support', source.read_text())


if __name__ == '__main__':
    unittest.main()
