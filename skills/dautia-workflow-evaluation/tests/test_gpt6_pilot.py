from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from run_gpt6_pilot import execution_passed, grader_fingerprint

class EvidenceTests(unittest.TestCase):
    def check(self, **kwargs):
        args=dict(exit_code=0,checks=[{'passed':True}],requested=('gpt-6-sol','medium'),observed=[('gpt-6-sol','medium')],tools=0,completed=True)
        args.update(kwargs)
        return execution_passed(**args)
    def test_grader_changes_invalidate_frozen_fingerprint(self):
        import tempfile
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/"grader.py"
            path.write_text("def grade(): return False\n")
            before=grader_fingerprint(path)
            path.write_text("def grade(): return True\n")
            self.assertNotEqual(before,grader_fingerprint(path))

    def test_requested_profile_without_observation_never_passes(self):
        self.assertFalse(self.check(observed=[]))
    def test_failed_turn_with_initial_context_never_passes(self):
        self.assertFalse(self.check(completed=False,exit_code=1))
    def test_mismatch_or_extra_tools_or_failed_case_never_passes(self):
        self.assertFalse(self.check(observed=[('gpt-5.6-sol','medium')]))
        self.assertFalse(self.check(tools=1))
        self.assertFalse(self.check(checks=[{'passed':False}]))
    def test_completed_matching_response_and_acceptance(self):
        self.assertTrue(self.check())

if __name__=='__main__': unittest.main()
