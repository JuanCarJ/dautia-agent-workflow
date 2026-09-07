"""Routing installs must not roll back unrelated host skills or touch launchers."""
import importlib.util
import json
from pathlib import Path
import tempfile
import subprocess
import unittest
from unittest.mock import patch
spec = importlib.util.spec_from_file_location('installer', Path(__file__).resolve().parents[1] / 'scripts/install.py')
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)

class RoutingInstallTests(unittest.TestCase):
    def test_dirty_source_never_claims_exact_committed_revision(self):
        for status, expected in [(" M AGENTS.md\n", "uncommitted:abc123"), ("", "abc123")]:
            with self.subTest(status=status), patch.object(installer.subprocess, 'run', side_effect=[
                subprocess.CompletedProcess([], 0, 'abc123\n'),
                subprocess.CompletedProcess([], 0, status),
            ]):
                self.assertEqual(installer.git_revision(), expected)

    def test_routing_install_preserves_unrelated_newer_assets_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as raw:
            home = Path(raw)
            unrelated = home / '.codex/skills/dautia-ci-cd/SKILL.md'
            unrelated.parent.mkdir(parents=True)
            unrelated.write_text('newer host version\n')
            launcher = home / '.local/bin/dautia-supabase'
            launcher.parent.mkdir(parents=True)
            launcher.write_text('custom host launcher\n')
            with patch.object(installer.Path, 'home', return_value=home), patch.dict('os.environ', {'CODEX_HOME': str(home / '.codex')}):
                with patch('sys.argv', ['install', '--profile', 'codex-macos', '--scope', 'routing', '--apply']):
                    self.assertEqual(installer.main(), 0)
                self.assertEqual(unrelated.read_text(), 'newer host version\n')
                self.assertEqual(launcher.read_text(), 'custom host launcher\n')
                cache = home / '.codex/skills/dautia-project-cycle/__pycache__/runtime.pyc'
                cache.parent.mkdir(parents=True, exist_ok=True)
                cache.write_bytes(b'local bytecode must not count as drift')
                state = json.loads((home / '.config/dautia/workflow-install.json').read_text())
                self.assertEqual(state['scope'], 'routing')
                with patch('sys.argv', ['install', '--profile', 'codex-macos', '--scope', 'routing', '--check']):
                    self.assertEqual(installer.main(), 0)
                with patch('sys.argv', ['install', '--profile', 'codex-macos', '--scope', 'all', '--check']):
                    self.assertEqual(installer.main(), 2)
if __name__ == '__main__':
    unittest.main()
