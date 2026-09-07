"""Structural contract checks; behavioral authority/evidence is tested by replay.
No prose, exact model brand, word-count or historical file-count assertions.
"""
from pathlib import Path
import json,re,tomllib,unittest
C=Path.home()/'.codex';S=C/'skills/dautia-project-cycle'
class WorkflowContracts(unittest.TestCase):
 def test_config_and_discoverable_roles_resolve(self):
  cfg=tomllib.loads((C/'config.toml').read_text())
  self.assertTrue(cfg.get('model'));self.assertIn(cfg.get('model_reasoning_effort'),{'low','medium','high','xhigh','max','ultra'})
  self.assertNotIn('model',cfg['agents']);self.assertNotIn('model_reasoning_effort',cfg['agents'])
  roles={}
  for p in (C/'agents').glob('*.toml'):
   d=tomllib.loads(p.read_text());self.assertNotIn(d['name'],roles);roles[d['name']]=d
   self.assertTrue(d['description']);self.assertTrue(d['developer_instructions']);self.assertTrue(d.get('model'))
   self.assertIn(d.get('model_reasoning_effort'),{'low','medium','high','xhigh','max','ultra'})
  for name,d in cfg['agents'].items():
   if isinstance(d,dict) and 'config_file' in d:
    p=C/d['config_file'];self.assertTrue(p.is_file());self.assertEqual(tomllib.loads(p.read_text())['name'],name)
    if name in {'product_discovery','data_security','independent_reviewer','release_operator'}:self.assertEqual(d['description'],tomllib.loads(p.read_text())['description'])
 def test_routing_ceiling_and_role_contracts(self):
  cfg=tomllib.loads((C/'config.toml').read_text())
  self.assertFalse({'max','ultra'} & set(cfg['desktop']['enabled-reasoning-efforts']))
  self.assertEqual(cfg['agents']['default_subagent_reasoning_effort'],'high')
  self.assertEqual((cfg['model'],cfg['model_reasoning_effort']),('gpt-5.6-sol','high'))
  def allowed(d):
   return d['model_reasoning_effort'] in ({'low','medium'} if d['model']=='gpt-6-astra' else {'low','medium','high','xhigh'})
  self.assertTrue(allowed(cfg))
  for p in [*(C/'agents').glob('*.toml'),*C.glob('dautia-*.config.toml')]:
   self.assertTrue(allowed(tomllib.loads(p.read_text())),str(p))
  for name,model,effort in [('product_discovery','gpt-6-astra','low'),('implementer','gpt-5.6-sol','medium'),('ux_auditor','gpt-6-astra','low'),('systems_analyst','gpt-6-astra','medium'),('systems_implementer','gpt-6-astra','medium'),('release_operator','gpt-5.6-sol','medium'),('decision_gate','gpt-5.6-sol','high'),('implementer_complex','gpt-5.6-sol','high'),('qa_web','gpt-5.6-sol','high'),('qa_ios','gpt-5.6-sol','high'),('qa_android','gpt-5.6-sol','high'),('qa_e2e','gpt-5.6-sol','high')]:
   d=tomllib.loads((C/'agents'/f'{name}.toml').read_text())
   self.assertEqual((d['model'],d['model_reasoning_effort']),(model,effort))
  self.assertFalse((C/'dautia-deep.config.toml').exists())
 def test_habitual_and_defined_profiles_preserve_explicit_policy(self):
  for name,effort in [('talk','high'),('build','high'),('defined','medium'),('technical','high'),('quick','low'),('reason','xhigh'),('review','low'),('analysis','medium'),('complex','medium')]:
   d=tomllib.loads((C/f'dautia-{name}.config.toml').read_text())
   self.assertEqual(d['model_reasoning_effort'],effort,name)
   self.assertEqual(d['model'],'gpt-6-astra' if name in {'review','analysis','complex'} else 'gpt-5.6-sol',name)
 def test_profiles_are_minimal_model_overrides(self):
  profiles=list(C.glob('dautia-*.config.toml'));self.assertTrue(profiles)
  for p in profiles:
   d=tomllib.loads(p.read_text());self.assertEqual(set(d),{'model','model_reasoning_effort'})
   self.assertTrue(d['model']);self.assertIn(d['model_reasoning_effort'],{'low','medium','high','xhigh','max','ultra'})
 def test_disabled_duplicate_skills_are_recoverable(self):
  cfg=tomllib.loads((C/'config.toml').read_text());paths=[x['path'] for x in cfg.get('skills',{}).get('config',[])]
  self.assertEqual(len(paths),len(set(paths)))
  for d in cfg['skills']['config']:self.assertTrue(Path(d['path']).is_file(),d['path'])
  for path in [Path.home()/'.agents/skills/use-railway/SKILL.md',C/'skills/skill-creator/SKILL.md']:
   self.assertTrue(any(x['path']==str(path) and x['enabled'] is False for x in cfg['skills']['config']))
 def test_core_relative_references_resolve(self):
  paths=[C/'AGENTS.md',S/'SKILL.md',*(S/'references').glob('*.md')]
  for p in paths:
   for link in re.findall(r'\]\(([^)]+)\)',p.read_text()):
    if '://' in link or link.startswith('#'):continue
    target=(p.parent/link.split('#')[0]);self.assertTrue(target.exists(),f'{p}: {link}')
 def test_replay_scenarios_have_unique_identity_and_no_real_credentials(self):
  p=C/'skills/dautia-workflow-evaluation/references/pilot-cases.json';cases=json.loads(p.read_text());ids=[x['id'] for x in cases]
  self.assertEqual(len(ids),len(set(ids)));self.assertTrue(cases)
  for c in cases:
   self.assertTrue(c['request']);self.assertTrue(c['context']);self.assertEqual(set(c['expected']),{'route','operation','close'})
   self.assertNotRegex(json.dumps(c),r'(?:sk-|sb_secret_|eyJ)[A-Za-z0-9_-]{20,}')
if __name__=='__main__':unittest.main()
