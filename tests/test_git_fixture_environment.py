"""Git configuration belongs to the fixture; external filters remain guarded."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import test_r3_core as core
from workspace_audit import snapshot, reconcile


class GitFixtureEnvironmentTests(unittest.TestCase):
    def test_global_filter_cannot_contaminate_fixture_or_be_run_by_snapshot(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            config = root / 'global.gitconfig'
            marker = root / 'FILTER_MUST_NOT_RUN'
            config.write_text('[filter "fixture"]\n  clean = touch ' + str(marker) + '\n')
            with patch.dict(os.environ, {'GIT_CONFIG_GLOBAL': str(config),
                                          'GIT_CONFIG_SYSTEM': os.devnull,
                                          'GIT_CONFIG_NOSYSTEM': '1'}):
                # The test with no external filters must own its git environment.
                core.CatalogAndWorkspaceTests('test_readonly_git_snapshot_preserves_foreign').test_readonly_git_snapshot_preserves_foreign()
                # Outside that isolated fixture, the production guard must still fire.
                repo = root / 'repo'
                repo.mkdir()
                subprocess.run(['git', 'init', '-q', str(repo)], check=True)
                (repo / '.gitattributes').write_text('*.txt filter=fixture\n')
                (repo / 'foreign.txt').write_text('preserve this value')
                before = snapshot(repo, 'repo1', 'checkout1')
                after = snapshot(repo, 'repo1', 'checkout1')
                self.assertEqual(before['coverage'], 'partial')
                self.assertEqual(before['reason'], 'external_filter_present_comparison_not_executed')
                self.assertFalse(reconcile(before, after, [])['reconciled'])
                self.assertFalse(marker.exists())
                self.assertEqual((repo / 'foreign.txt').read_text(), 'preserve this value')


if __name__ == '__main__':
    unittest.main()
