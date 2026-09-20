"""Approved r3 defaults and generated adapters; not a model quality benchmark."""
import json
from pathlib import Path
import sys
import tomllib
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from render_agents import render
ROLES={'code_explorer','data_security','decision_gate','documental','implementer','implementer_complex','independent_reviewer','product_discovery','qa_android','qa_e2e','qa_ios','qa_web','release_operator','systems_analyst','systems_implementer','ux_auditor'}

class ModelProfileTests(unittest.TestCase):
    def test_codex_profiles_match_approved_routing(self):
        for name in ('codex-macos','wsl-shared'):
            with self.subTest(profile=name):
                p=json.loads((ROOT/'profiles'/(name+'.yaml')).read_text())
                self.assertEqual(p['codex_root'],{'model':'gpt-5.6-sol','reasoning_effort':'high'})
                self.assertEqual(p['codex_agents'],{r:['gpt-5.6-sol','high'] for r in ROLES})
    def test_cursor_declares_runtime_inheritance_without_enforcement_claim(self):
        p=json.loads((ROOT/'profiles/wsl-shared.yaml').read_text())['cursor_agents']
        self.assertEqual(p['model'],'inherit');self.assertIn('not enforced',p['policy'])
    def test_generated_adapters_match_real_canonical_roles(self):
        p=json.loads((ROOT/'profiles/codex-macos.yaml').read_text()); files=render(ROOT,p)
        for role in ROLES:
            data=tomllib.loads(files['codex/'+role+'.toml'].decode())
            self.assertEqual(data['name'],role);self.assertEqual(data['model'],'gpt-5.6-sol');self.assertEqual(data['model_reasoning_effort'],'high')
            self.assertTrue(data['developer_instructions'].endswith((ROOT/'roles/_boundary.md').read_text()))
        for writer in ('implementer','implementer_complex','systems_implementer','release_operator'):
            self.assertNotIn('codex/'+writer+'__astra_medium.toml',files)
        self.assertEqual(tomllib.loads(files['codex/data_security.toml'].decode())['sandbox_mode'],'read-only')

if __name__=='__main__':unittest.main()
