"""Deterministic routing and dispatch checks without a provider advisor."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock

from test_r3_core import packet
from workflow_core import ContractError, fingerprint, policy, profile_selection, routing_arguments
from workflow_dispatch import prepare_dispatch, dispatch_prepared
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

    def test_high_is_deterministic_for_demanding_or_unknown_work(self):
        for difficulty in ('demanding', 'unknown'):
            with self.subTest(difficulty=difficulty):
                self.assertEqual(self.decision(self.work(difficulty))['selection']['selected'], 'sol_high')

    def test_analysis_can_choose_astra_medium_with_evidence(self):
        p = packet(); p['runtime']['available_profiles'] = list(policy()['profiles'])
        p['runtime']['available_targets'] = self.targets
        p['runtime']['principal_choice'] = {'profile': 'astra_medium', 'evidence_refs': ['coupling-analysis-1']}
        decision = self.decision(p)
        self.assertEqual(decision['selection']['selected'], 'astra_medium')
        self.assertEqual(decision['dispatch_target'], 'systems_analyst__astra_medium')

    def test_astra_above_medium_is_rejected(self):
        override = {'profile': 'astra_high', 'source_kind': 'user', 'source_refs': ['user1']}
        result = profile_selection('systems_analyst', 'read', analysis=True,
                                   explicit=override, available=['astra_high'])
        self.assertEqual(result['status'], 'blocked')
        self.assertEqual(result['reason'], 'profile_above_astra_ceiling')

    def test_dispatch_is_exactly_once_and_reconciled(self):
        p = self.work(); decision = self.decision(p)
        plan = prepare_dispatch(p, decision, self.agents)
        spawn = Mock(return_value={'agent_id': 'native-child-1', 'model': 'gpt-5.6-sol',
                                   'model_reasoning_effort': 'medium'})
        ledger = self.root / 'ledger'
        result = dispatch_prepared(p, decision, plan, self.agents, spawn,
                                   events_root=self.root / 'events', ledger_root=ledger)
        self.assertEqual(result['status'], 'started')
        self.assertTrue(result['dispatch_id'])
        reused = dispatch_prepared(p, decision, plan, self.agents, spawn,
                                   ledger_root=ledger)
        self.assertEqual(reused['status'], 'dispatch_already_reserved')
        spawn.assert_called_once()
        self.assertEqual([e['event_type'] for e in export_events(self.root / 'events', 'obj1')['events']],
                         ['dispatch.requested', 'agent.started'])

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
