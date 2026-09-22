"""Approved GPT6 defaults and generated adapters; not a model quality benchmark."""
import json
from pathlib import Path
import sys
import tomllib
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'skills/dautia-project-cycle/scripts')]
from render_agents import render
from workflow_core import role_profiles
EXPECTED={
    'code_explorer':['gpt-6-luna','high'], 'data_security':['gpt-6-sol','high'],
    'decision_gate':['gpt-6-sol','high'], 'documental':['gpt-6-sol','medium'],
    'implementer':['gpt-6-sol','medium'], 'implementer_complex':['gpt-6-sol','high'],
    'independent_reviewer':['gpt-6-sol','medium'], 'product_discovery':['gpt-6-sol','medium'],
    'qa_android':['gpt-6-sol','medium'], 'qa_e2e':['gpt-6-sol','medium'],
    'qa_ios':['gpt-6-sol','medium'], 'qa_web':['gpt-6-sol','medium'],
    'release_operator':['gpt-6-sol','medium'], 'systems_analyst':['gpt-6-astra','low'],
    'systems_implementer':['gpt-6-sol','high'], 'ux_auditor':['gpt-6-astra','low'],
}

class ModelProfileTests(unittest.TestCase):
    def test_codex_profiles_match_approved_routing(self):
        for name in ('codex-macos','wsl-shared'):
            with self.subTest(profile=name):
                p=json.loads((ROOT/'profiles'/(name+'.yaml')).read_text())
                self.assertEqual(p['codex_root'],{'model':'gpt-6-sol','reasoning_effort':'medium'})
                self.assertEqual(p['codex_agents'],EXPECTED)
    def test_cursor_declares_runtime_inheritance_without_enforcement_claim(self):
        p=json.loads((ROOT/'profiles/wsl-shared.yaml').read_text())['cursor_agents']
        self.assertEqual(p['model'],'inherit');self.assertIn('not enforced',p['policy'])
    def test_generated_adapters_match_defaults_and_finite_eligibility(self):
        p=json.loads((ROOT/'profiles/codex-macos.yaml').read_text()); files=render(ROOT,p)
        for role,(model,effort) in EXPECTED.items():
            data=tomllib.loads(files['codex/'+role+'.toml'].decode())
            self.assertEqual((data['name'],data['model'],data['model_reasoning_effort']),(role,model,effort))
            self.assertTrue(data['developer_instructions'].endswith((ROOT/'roles/_boundary.md').read_text()))
            generated={Path(name).stem.rsplit('__',1)[1] for name in files if name.startswith('codex/'+role+'__')}
            self.assertEqual(generated,set(role_profiles(role)))
        for writer in ('implementer','implementer_complex','systems_implementer','release_operator'):
            self.assertFalse(any(name.startswith('codex/'+writer+'__astra_') for name in files))
            self.assertNotIn('codex/'+writer+'__luna_high.toml',files)
        self.assertIn('codex/code_explorer__luna_high.toml',files)
        self.assertIn('codex/documental__luna_high.toml',files)
        self.assertFalse(any('__astra_high.toml' in name for name in files))
        self.assertEqual(tomllib.loads(files['codex/data_security.toml'].decode())['sandbox_mode'],'read-only')

if __name__=='__main__':unittest.main()
