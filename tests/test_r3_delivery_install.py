import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'skills/dautia-project-cycle/scripts'),str(ROOT/'skills/dautia-ci-cd/scripts')]
from workflow_core import ContractError
from delivery_v3 import validate_v3, select_provider
from audit_ingest import inspect_archive, REQUIRED
import install
from render_agents import render


def delivery():
    c={'schema_version':3,'project':'synthetic','product_topology':'multi-codebase','repository_layout':'multi-repo','configuration_status':'active','production_enabled':False,
       'repositories':[{'id':'api','path':'api','integration_branch':'main'},{'id':'ios','path':'ios','integration_branch':'dev'}],
       'codebases':[{'id':'api','repository':'api','path':'.','kind':'python','status':'active'},{'id':'ios','repository':'ios','path':'.','kind':'swift','status':'active'}],
       'targets':[{'id':i+'-integration','component':i,'environment':'integration','branch':b,'state':'observed','deploy_enabled':False,'target':i+'-local','checks':['unit'],'rollback_ref':'previous-verified-candidate'} for i,b in [('api','main'),('ios','dev')]],
       'provider_projects':[]}
    return c


class DeliveryTests(unittest.TestCase):
    def test_distinct_repository_branches(self):self.assertEqual(validate_v3(delivery()),[])
    def test_branch_conflict_only_own_repository(self):
        c=delivery();c['targets'][1]['branch']='main';self.assertIn('integration_target_mismatches_own_repository',validate_v3(c))
    def test_planned_production_cannot_deploy(self):
        c=delivery();t=copy.deepcopy(c['targets'][0]);t.update(id='api-prod',environment='production',state='planned',deploy_enabled=True);c['targets'].append(t)
        self.assertIn('planned_target_cannot_deploy',validate_v3(c));self.assertIn('production_disabled',validate_v3(c))
    def test_same_provider_environment_different_components(self):
        c=delivery()
        for i in ('api','ios'):
            t=copy.deepcopy(c['targets'][0]);t.update(id=i+'-stage',component=i,environment='staging',branch='staging',target=i+'-db');c['targets'].append(t)
            c['provider_projects'].append({'id':i+'-db','provider':'supabase','component':i,'environment':'staging','target_id':i+'-stage','workdir':'.','project_ref':('a' if i=='api' else 'b')*20})
        self.assertEqual(validate_v3(c),[])
        with self.assertRaises(ValueError):select_provider(c,'supabase','staging')
        self.assertEqual(select_provider(c,'supabase','staging','ios')['project_ref'],'b'*20)
    def test_supabase_checks_not_weakened(self):
        c=delivery();c['provider_projects']=[{'id':'db','provider':'supabase','component':'api','environment':'staging','target_id':'api-integration','workdir':'.','project_ref':'bad'}]
        self.assertIn('invalid_supabase_target',validate_v3(c));self.assertIn('provider_target_binding_missing',validate_v3(c))
    def test_unknown_provider_allowed_as_typed_target_not_invoked(self):
        c=delivery();c['provider_projects']=[{'id':'local','provider':'custom','component':'api','environment':'integration','target_id':'api-integration','workdir':'.'}]
        self.assertEqual(validate_v3(c),[])
    def test_credentials_rejected(self):
        c=delivery();c['password']='unsafe';self.assertIn('credential_key_forbidden',validate_v3(c))
    def test_path_traversal_rejected(self):
        c=delivery();c['repositories'][0]['path']='../other';self.assertIn('repository_path_not_contained',validate_v3(c))
    def test_draft_not_claimed_active(self):
        c={k:v for k,v in delivery().items() if k not in ('repositories','codebases','targets','provider_projects')};c.update(configuration_status='draft',activation_blocked_reason='target_unknown')
        self.assertEqual(validate_v3(c),[]);self.assertIn('active_configuration_required',validate_v3(c,require_active=True))
    def test_git_branch_observation_by_repository(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            for name,b in [('api','main'),('ios','dev')]:
                dest=root/name;subprocess.run(['git','init','-q','-b',b,str(dest)],check=True)
                subprocess.run(['git','-C',str(dest),'-c','user.name=Fixture','-c','user.email=fixture@example.invalid','commit','--allow-empty','-qm','fixture'],check=True)
            self.assertEqual(validate_v3(delivery(),root),[])


class InstallerTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.home=Path(self.temp.name)/'home';self.home.mkdir();self.config=self.home/'.config'
    def test_conflicts_are_not_overwritten(self):
        p=self.home/'asset';p.write_text('foreign')
        with self.assertRaises(ContractError):install.apply({str(p):(b'new',0o600)},self.config)
        self.assertEqual(p.read_text(),'foreign')
    def test_adopt_backup_and_rollback(self):
        p=self.home/'asset';p.write_bytes(b'prior');p.chmod(0o640)
        result=install.apply({str(p):(b'new',0o600)},self.config,adopt=True)
        self.assertEqual(p.read_bytes(),b'new')
        install.rollback(Path(result['backup']),self.config)
        self.assertEqual(p.read_bytes(),b'prior');self.assertEqual(p.stat().st_mode&0o777,0o640)
    def test_idempotence_preserves_extra(self):
        p=self.home/'assets/managed';p.parent.mkdir();foreign=p.parent/'extra';foreign.write_bytes(b'keep')
        files={str(p):(b'new',0o600)};install.apply(files,self.config);r=install.apply(files,self.config)
        self.assertEqual(r['changed_files'],0);self.assertEqual(foreign.read_bytes(),b'keep')
    def test_transaction_failure_restores(self):
        paths=[self.home/'a',self.home/'b']
        for p in paths:p.write_bytes(b'old')
        with self.assertRaises(OSError):install.apply({str(p):(b'new',0o600) for p in paths},self.config,adopt=True,fail_after=1)
        self.assertEqual([p.read_bytes() for p in paths],[b'old',b'old'])
    def test_rollback_refuses_later_edit(self):
        p=self.home/'asset';r=install.apply({str(p):(b'new',0o600)},self.config);p.write_bytes(b'later')
        with self.assertRaises(ContractError):install.rollback(Path(r['backup']),self.config)
        self.assertEqual(p.read_bytes(),b'later')
    def test_parent_permissions_preserved(self):
        p=self.home/'shared/bin/file';p.parent.mkdir(parents=True);p.parent.chmod(0o755)
        install.apply({str(p):(b'new',0o700)},self.config);self.assertEqual(p.parent.stat().st_mode&0o777,0o755)
    def test_root_config_only_requested_keys(self):
        raw=(b'# own comment\nmodel="other"\nmodel_reasoning_effort="low"\n'
             b'[agents]\ndefault_subagent_model="old"\ndefault_subagent_reasoning_effort="high"\nkeep=true\n'
             b'[agents.custom]\nmodel="preserve"\n[nested]\nvalue="keep"\n')
        profile=json.loads((ROOT/'profiles/codex-macos.yaml').read_text())
        rules=json.loads((ROOT/'skills/dautia-project-cycle/config/routing-policy.json').read_text())
        result=install.root_config(raw,profile,rules).decode();parsed=__import__('tomllib').loads(result)
        self.assertIn('model="preserve"',result);self.assertIn('# own comment',result)
        self.assertEqual((parsed['model'],parsed['model_reasoning_effort']),('gpt-6-sol','medium'))
        self.assertEqual((parsed['agents']['default_subagent_model'],parsed['agents']['default_subagent_reasoning_effort']),('gpt-6-sol','medium'))
        self.assertTrue(parsed['agents']['keep']);self.assertEqual(parsed['nested']['value'],'keep')
    def test_symlink_destination_rejected(self):
        target=self.home/'target';target.write_bytes(b'keep');link=self.home/'link';link.symlink_to(target)
        with self.assertRaises(ContractError):install.apply({str(link):(b'new',0o600)},self.config,adopt=True)
    def test_render_defaults_and_explicit_variants(self):
        # Synthetic complete role catalog isolates generator behavior from untested models.
        fixture=self.home/'repo';(fixture/'roles').mkdir(parents=True);(fixture/'skills/dautia-project-cycle/config').mkdir(parents=True)
        (fixture/'roles/_boundary.md').write_text('Do not broaden authority.')
        (fixture/'skills/dautia-project-cycle/config/routing-policy.json').write_bytes((ROOT/'skills/dautia-project-cycle/config/routing-policy.json').read_bytes())
        for r,mut in [('implementer','bounded_write'),('systems_analyst','read_only'),('data_security','read_only')]:
            (fixture/'roles'/(r+'.md')).write_text(f'---\nid: "{r}"\ndescription: "Role"\nmutability: "{mut}"\n---\nBounded procedure.\n')
        profile={'codex_agents':{'implementer':['gpt-6-sol','medium'],
                                 'systems_analyst':['gpt-6-astra','low'],
                                 'data_security':['gpt-6-sol','high']}}
        adapters=render(fixture,profile)
        import tomllib
        default=tomllib.loads(adapters['codex/implementer.toml'].decode());self.assertEqual(default['model'],'gpt-6-sol');self.assertEqual(default['model_reasoning_effort'],'medium')
        self.assertNotIn('codex/implementer__astra_low.toml',adapters)
        self.assertIn('codex/systems_analyst__astra_medium.toml',adapters)
        self.assertNotIn('codex/systems_analyst__astra_high.toml',adapters)
        self.assertEqual(tomllib.loads(adapters['codex/data_security.toml'].decode())['sandbox_mode'],'read-only')


class AuditIngestTests(unittest.TestCase):
    def make_zip(self, root, malicious=False):
        path=root/'audit.zip'
        files={n:(b'{}' if n.endswith('.json') else b'Fixture only') for n in REQUIRED-{'manifest.json'}}
        manifest={'files':[{'file':n,'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data)} for n,data in files.items()]}
        files['manifest.json']=json.dumps(manifest).encode()
        with zipfile.ZipFile(path,'w') as z:
            for n,data in files.items():z.writestr('audit/'+n,data)
            if malicious:z.writestr('../outside',b'bad')
        return path
    def test_valid_audit_not_action_authority(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);p=self.make_zip(root);r=inspect_archive(p)
            self.assertTrue(r['accepted']);self.assertFalse(r['authorizes_cleanup']);self.assertFalse(r['archive_extracted']);self.assertEqual(len(list(root.iterdir())),1)
    def test_archive_traversal_rejected_without_extraction(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ContractError):inspect_archive(self.make_zip(Path(d),True))
    def test_manifest_mismatch_blocks(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);p=self.make_zip(root)
            with zipfile.ZipFile(p,'a') as z:z.writestr('another/informe-git.md',b'changed')
            with self.assertRaises(ContractError):inspect_archive(p)


if __name__=='__main__':unittest.main()
