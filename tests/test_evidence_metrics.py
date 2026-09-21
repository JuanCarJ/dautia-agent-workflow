import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'skills/dautia-project-cycle/scripts/evidence_metrics.py'
spec = importlib.util.spec_from_file_location('evidence_metrics', SCRIPT)
assert spec and spec.loader
metrics = importlib.util.module_from_spec(spec); spec.loader.exec_module(metrics)

class EvidenceMetricsTests(unittest.TestCase):
    def test_unknowns_and_unlabeled_cases_are_not_zero(self):
        result = metrics.summarize({'cases': [
            {'status':'advisory','gold_profile':'astra_medium','recommended_profile':'astra_medium','duration_ms':100},
            {'status':'abstain','gold_profile':'sol_high','recommended_profile':None,'duration_ms':200},
            {'status':None,'authorizes_action':False},
        ]})
        self.assertEqual(result['cases'], 3)
        self.assertEqual(result['gold_labeled'], 2)
        self.assertEqual(result['gold_compared'], 1)
        self.assertEqual(result['recommendation_precision'], 1.0)
        self.assertEqual(result['states']['unknown'], 1)
        self.assertTrue(result['unknowns_preserved'])

    def test_cli_reads_json(self):
        process = subprocess.run([sys.executable, str(SCRIPT), '-'], input=json.dumps({'cases': []}), text=True, capture_output=True)
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertEqual(json.loads(process.stdout)['cases'], 0)

    def test_placeholder_labels_are_not_comparable(self):
        result = metrics.summarize({'cases': [
            {'gold_profile':'unknown','recommended_profile':'unknown'},
        ]})
        self.assertEqual(result['gold_labeled'], 0)
        self.assertEqual(result['gold_compared'], 0)
        self.assertEqual(result['recommendations'], 0)

if __name__ == '__main__': unittest.main()
