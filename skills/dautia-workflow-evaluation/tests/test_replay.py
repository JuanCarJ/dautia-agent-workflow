from pathlib import Path
import importlib.util,unittest,json
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('replay',ROOT/'scripts/run_replay.py');r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
class ReplayTests(unittest.TestCase):
 def setUp(self):self.cases=json.loads((ROOT/'references/pilot-cases.json').read_text());self.result={'results':[dict(id=c['id'],**c['expected']) for c in self.cases]}
 def test_routing_requires_observed_matching_profile(self):
  requested={'model':'example-model','effort':'medium'}
  self.assertFalse(r.routing_matches([],requested))
  self.assertFalse(r.routing_matches([{'model':'other','effort':'medium'}],requested))
  self.assertFalse(r.routing_matches([{'model':'example-model','effort':'high'}],requested))
  self.assertTrue(r.routing_matches([requested],requested))
 def test_missing_case_cannot_pass(self):
  self.result['results'].pop();self.assertFalse(all(x['passed'] for x in r.grade(self.cases,self.result)))
 def test_duplicate_case_cannot_pass(self):
  self.result['results'].append(self.result['results'][0]);self.assertFalse(r.grade(self.cases,self.result)[0]['passed'])
 def test_repeating_uncertain_operation_fails(self):
  self.result['results'][3]['operation']='retry-post';self.assertFalse(r.grade(self.cases,self.result)[3]['passed'])
 def test_valid_proportional_alternatives_pass(self):
  self.result['results'][0]['close']='integration-evidence-no-deploy';self.result['results'][3]['route']='sol-high';self.assertTrue(all(x['passed'] for x in r.grade(self.cases,self.result)))
 def test_unexpected_case_fails(self):
  self.result['results'].append({'id':'invented'});self.assertFalse(all(x['passed'] for x in r.grade(self.cases,self.result)))
 def test_production_as_staging_fails(self):
  self.result['results'][2]['operation']='test-production';self.assertFalse(r.grade(self.cases,self.result)[2]['passed'])

class VocabularyTests(unittest.TestCase):
    def test_accepted_alternatives_are_exposed(self):
        import importlib.util
        from pathlib import Path
        path=Path(__file__).resolve().parents[1]/'scripts/run_replay.py'
        spec=importlib.util.spec_from_file_location('replay_vocab',path)
        mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
        cases=[{'expected':{'route':'sol-medium','operation':'read','close':'focal'},'acceptable':{'close':['focal','integration']}}]
        vocab=mod.decision_vocabulary(cases)
        self.assertIn('integration',vocab['close'])
        self.assertIn('astra-low',vocab['route']);self.assertIn('sol-xhigh',vocab['route'])
        self.assertNotIn('astra-high',vocab['route'])

if __name__=='__main__':unittest.main()
