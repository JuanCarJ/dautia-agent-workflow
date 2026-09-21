import hashlib
import json
import multiprocessing
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'skills/dautia-project-cycle/scripts'), str(ROOT / 'skills/dautia-ci-cd/scripts')]
from workflow_core import ContractError, gate
from workflow_delivery import reserve_dispatch, mark_started, record_delivery, continuation
from qa_artifacts import prepare_workspace, write_evidence, inspect_write_boundary
from workflow_report import report
from component_evidence import validate_component_evidence
from test_r3_core import packet

def _reserve_once(root: str) -> str:
    h = lambda x: hashlib.sha256(x.encode()).hexdigest()
    return reserve_dispatch(Path(root), objective_id='obj1', project_id='proj1', block_id='block1',
                            attempt='attempt1', profile='sol_high', candidate_hash=h('c'),
                            packet_hash=h('p'), dispatch_key=h('k'))['status']


class ComplementTests(unittest.TestCase):
    def test_delivery_reconciles_duplicate_stale_and_pause(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); h = lambda x: hashlib.sha256(x.encode()).hexdigest()
            first = reserve_dispatch(root, objective_id='obj1', project_id='proj1', block_id='block1', attempt='attempt1', profile='sol_high', candidate_hash=h('c'), packet_hash=h('p'), dispatch_key=h('k'))
            self.assertEqual(first['status'], 'reserved')
            did = first['dispatch']['dispatch_id']
            self.assertEqual(reserve_dispatch(root, objective_id='obj1', project_id='proj1', block_id='block1', attempt='attempt1', profile='sol_high', candidate_hash=h('c'), packet_hash=h('p'), dispatch_key=h('k'))['status'], 'reused')
            mark_started(root, did, 'child1')
            self.assertEqual(mark_started(root, did, 'child1')['status'], 'already_started')
            self.assertEqual(mark_started(root, did, 'child2')['status'], 'reconcile_required')
            self.assertEqual(record_delivery(root, did, candidate_hash=h('changed'), packet_hash=h('p'), delivery={}, objective_state='RUNNING')['status'], 'stale')
            self.assertEqual(record_delivery(root, did, candidate_hash=h('c'), packet_hash=h('p'), delivery={}, objective_state='RUNNING')['status'], 'stale')
            self.assertEqual(continuation(root, did)['action'], 'reconcile')

    def test_delivery_requires_started_and_normalizes_terminal_states(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); h = lambda x: hashlib.sha256(x.encode()).hexdigest()
            reserved = reserve_dispatch(root, objective_id='obj1', project_id='proj1', block_id='block1', attempt='attempt1', profile='sol_high', candidate_hash=h('c'), packet_hash=h('p'), dispatch_key=h('k'))
            did = reserved['dispatch']['dispatch_id']
            self.assertEqual(record_delivery(root, did, candidate_hash=h('c'), packet_hash=h('p'), delivery={'status':'ok'}, objective_state='running')['status'], 'delivery_before_start')
            mark_started(root, did, 'child1')
            self.assertEqual(record_delivery(root, did, candidate_hash=h('c'), packet_hash=h('p'), delivery={'status':'ok'}, objective_state='interrupted')['status'], 'late_ignored')
            self.assertEqual(record_delivery(root, did, candidate_hash=h('c'), packet_hash=h('p'), delivery={'status':'ok','checks':['C1'],'pending':[]}, objective_state='RUNNING')['status'], 'delivered')
            self.assertEqual(continuation(root, did, objective_state='COMPLETE')['action'], 'stop')

    def test_concurrent_reservation_has_one_winner(self):
        if 'fork' not in multiprocessing.get_all_start_methods():
            self.skipTest('requires POSIX fork for the local-host ledger')
        with tempfile.TemporaryDirectory() as tmp:
            with multiprocessing.get_context('fork').Pool(8) as pool:
                statuses = pool.map(_reserve_once, [tmp] * 16)
            self.assertEqual(statuses.count('reserved'), 1)
            self.assertEqual(statuses.count('reused'), 15)

    def test_qa_boundary_writes_only_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); evidence = root / 'evidence'; product = root / 'product'
            descriptor = prepare_workspace(root / 'state', evidence, product)
            self.assertFalse(descriptor['product_write_granted'])
            result = write_evidence(evidence, 'run/result.json', b'{}')
            self.assertTrue(result['written'])
            boundary = inspect_write_boundary(evidence, product, product / 'x')
            self.assertTrue(boundary['inside_product']); self.assertFalse(boundary['write_allowed_by_helper'])
            with self.assertRaises(ContractError): write_evidence(evidence, '../product/x', b'x')

    def test_qa_prepare_rejects_nested_product_before_mutating_permissions(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); product = root / 'product'; product.mkdir(mode=0o755)
            nested = product / 'evidence'
            with self.assertRaises(ContractError): prepare_workspace(root / 'state', nested, product)
            self.assertEqual(product.stat().st_mode & 0o777, 0o755)

    def test_component_evidence_and_gate_are_proportional(self):
        p = packet(); p['component_evidence'] = [{'component':'web','repository':'repo','candidate_sha':'a'*40,'status':'independent','checks':['c1'],'depends_on':[]}]
        self.assertTrue(gate(p)['passed'])
        with self.assertRaises(ContractError):
            validate_component_evidence([{'component':'web','repository':'repo','candidate_sha':'bad','status':'independent','checks':[]}])
        with self.assertRaises(ContractError):
            validate_component_evidence([{'component':'web','repository':'','candidate_sha':'a'*40,'status':'independent','checks':[]}])

    def test_component_closeout_blocks_required_blocked_but_allows_unrelated_independent(self):
        p = packet(); p['required_components'] = ['ios']; p['shared_contracts'] = ['contract_changed']
        p['component_evidence'] = [
            {'component':'ios','repository':'repo','candidate_sha':'a'*40,'status':'blocked','checks':['c1'],'depends_on':['api']},
            {'component':'docs','repository':'repo','candidate_sha':'b'*40,'status':'independent','checks':[],'depends_on':[]},
        ]
        self.assertTrue(gate(p)['passed'])
        self.assertIn('required_component_blocked:ios', gate(p, 'closeout')['issues'])
        with self.assertRaises(ContractError):
            validate_component_evidence(p['component_evidence'], ['ios'], ['contract_changed'])

    def test_component_closeout_requires_evidence_when_components_are_declared(self):
        p = packet(); p['required_components'] = ['ios']
        self.assertIn('required_component_evidence_missing:ios', gate(p, 'closeout')['issues'])

    def test_report_keeps_unknowns_and_limit(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            from workflow_store import emit
            emit(root, {'event_type':'objective.opened','objective_id':'obj1','project_id':'proj1','status':'unknown','observation_kind':'local_validator','authorizes_action':False})
            emit(root, {'event_type':'agent.started','objective_id':'obj1','project_id':'proj1','profile_requested':'sol_high','status':'started','observation_kind':'host_adapter','authorizes_action':False})
            result = report(root, 30)
            self.assertEqual(result['observable_objectives'], 1); self.assertTrue(result['unknowns_preserved'])
            self.assertFalse(result['raw_prompts_included'])
            with self.assertRaises(ValueError): report(root, 31)

    def test_jev_projection_drops_unknown_private_fields(self):
        import jev_support as jev
        p = packet(); p['requirements'][0]['transcript'] = 'PRIVATE FULL CHAT'
        p['requirements'][0]['expected']['private_transcript'] = 'SECRETCHAT'
        p['requirements'][0]['expected']['nested'] = {'prompt': 'PRIVATE'}
        request = jev.build_request('brief', p, jev.defaults())
        rendered = json.dumps(request)
        self.assertNotIn('transcript', rendered); self.assertNotIn('PRIVATE FULL CHAT', rendered)
        self.assertNotIn('SECRETCHAT', rendered); self.assertNotIn('PRIVATE', rendered)

    def test_route_projection_includes_bounded_evidence_frontier(self):
        import jev_support as jev
        p = packet()
        p['impacts'] = [{'id': 'impact-1', 'treatment': 'covered', 'rationale': 'bounded',
                         'blocking': False, 'check_ids': ['C1'], 'evidence': ['obs-1']}]
        p['pending'] = [{'id': 'pending-1', 'required': False, 'status': 'none',
                         'authorized': True, 'available': True, 'monitor_confirmed': False}]
        p['findings'] = [{'id': 'finding-1', 'kind': 'evidence',
                          'summary': 'source and acceptance are aligned', 'resolved': True,
                          'evidence': ['obs-1']}]
        request = jev.build_request('route', p, jev.defaults())
        for field in ('sources', 'impacts', 'pending', 'findings'):
            self.assertIn(field, request['state'])
        p['findings'][0]['summary_private_prompt'] = 'PRIVATE'
        request = jev.build_request('route', p, jev.defaults())
        self.assertNotIn('summary_private_prompt', json.dumps(request))


if __name__ == '__main__': unittest.main()
