"""R3 migration keeps unrelated assets, reports source drift and validates launchers."""
import contextlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import install as installer

class RoutingInstallTests(unittest.TestCase):
    def test_dirty_source_never_claims_exact_committed_revision(self):
        for status,expected in [(' M AGENTS.md\n','uncommitted:abc123'),('','abc123')]:
            with self.subTest(status=status),patch.object(installer.subprocess,'run',side_effect=[subprocess.CompletedProcess([],0,'abc123\n'),subprocess.CompletedProcess([],0,status)]):
                self.assertEqual(installer.git_revision(),expected)
    def test_routing_installs_preserve_unrelated_assets_and_real_launcher(self):
        for profile in ('codex-macos','wsl-shared'):
            with self.subTest(profile=profile),tempfile.TemporaryDirectory(prefix='dautia test ') as raw:
                home=Path(raw)/'home with spaces';home.mkdir()
                codex=home/'custom codex';config=home/'custom config'
                unrelated=codex/'skills/dautia-ci-cd/SKILL.md';unrelated.parent.mkdir(parents=True);unrelated.write_text('newer host version\n')
                launcher=home/'.local/bin/dautia-supabase';launcher.parent.mkdir(parents=True);launcher.write_text('custom host launcher\n')
                env={'HOME':str(home),'CODEX_HOME':str(codex),'XDG_CONFIG_HOME':str(config),'XDG_STATE_HOME':str(home/'state')}
                with patch.dict(os.environ,env):
                    files=installer.payloads(ROOT,home,profile,'routing')
                    result=installer.apply(files,config);self.assertTrue(result['installed'])
                    self.assertEqual(unrelated.read_text(),'newer host version\n');self.assertEqual(launcher.read_text(),'custom host launcher\n')
                    cli=home/'.local/bin/dautia-workflow'
                    p=subprocess.run([str(cli),'doctor'],text=True,capture_output=True,env=os.environ.copy(),timeout=10)
                    self.assertEqual(p.returncode,0,p.stderr);self.assertFalse(json.loads(p.stdout)['network_called'])
                    self.assertEqual(installer.apply(files,config)['changed_files'],0)
                    expected=home/'.agents/skills' if profile=='wsl-shared' else codex/'skills'
                    self.assertIn(str(expected),cli.read_text())
                    self.assertTrue((config/'dautia/workflow-version.json').is_file())
                    self.assertFalse((codex/'hooks.json').exists())
    def test_backup_path_cannot_escape(self):
        with tempfile.TemporaryDirectory() as raw:
            root=Path(raw);config=root/'config';p=root/'file'
            result=installer.apply({str(p):(b'new',0o600)},config)
            backup=Path(result['backup']);m=json.loads((backup/'manifest.json').read_text());m['records'][0]['backup_file']='../secret'
            (backup/'manifest.json').write_text(json.dumps(m))
            with self.assertRaises(installer.ContractError):installer.rollback(backup,config)
            self.assertEqual(p.read_bytes(),b'new')

if __name__=='__main__':unittest.main()
