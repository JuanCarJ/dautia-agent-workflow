#!/usr/bin/env python3
"""Transactional, merge-preserving workflow installer. Default is preview only.

No secret configuration, live session, project checkout or hook trust is changed.
Unknown installed edits are conflicts unless explicitly adopted with a backup.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import shlex
import stat
import subprocess
import sys
import tempfile
import time
import tomllib
import uuid
from contextlib import contextmanager

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'skills/dautia-project-cycle/scripts'))
from workflow_core import ContractError, canonical, load_json
from workflow_store import atomic_write, private_dir, read_private, safe_path
from render_agents import render


def git_revision(repo: Path = ROOT) -> str:
    try:
        head = subprocess.run(["git", "--no-optional-locks", "-c", "core.fsmonitor=false", "-C", str(repo), "rev-parse", "HEAD"], text=True, capture_output=True, timeout=5)
        if head.returncode: return "unavailable"
        status = subprocess.run(["git", "--no-optional-locks", "-c", "core.fsmonitor=false", "-C", str(repo), "status", "--porcelain=v2", "--untracked-files=normal"], text=True, capture_output=True, timeout=5)
        return ("uncommitted:" if status.returncode or status.stdout else "") + head.stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        return "unavailable"


def sha(data: bytes) -> str: return hashlib.sha256(data).hexdigest()


def root_config(data: bytes) -> bytes:
    text=data.decode();tomllib.loads(text)
    lines=text.splitlines(keepends=True);out=[];at_root=True
    for line in lines:
        if line.lstrip().startswith('['):at_root=False
        if at_root and __import__('re').match(r'^\s*(model|model_reasoning_effort)\s*=',line):continue
        out.append(line)
    new='model = "gpt-5.6-sol"\nmodel_reasoning_effort = "high"\n'+''.join(out)
    tomllib.loads(new);return new.encode()


def payloads(repo: Path, home: Path, profile_name: str, scope: str='workflow', configure_root: bool=False) -> dict[str,tuple[bytes,int]]:
    if profile_name not in ('codex-macos','wsl-shared'):raise ContractError('unknown_profile')
    profile=load_json((repo/'profiles'/(profile_name+'.yaml')).read_bytes())
    codex=Path(os.environ.get('CODEX_HOME',str(home/'.codex'))).expanduser()
    config=Path(os.environ.get('XDG_CONFIG_HOME',str(home/'.config'))).expanduser()
    if not codex.is_absolute() or not config.is_absolute():raise ContractError('install_roots_must_be_absolute')
    skill_root=home/'.agents/skills' if profile_name=='wsl-shared' else codex/'skills'
    result={str(codex/'AGENTS.md'):((repo/'AGENTS.md').read_bytes(),0o600)}
    result[str(config/'dautia/workflow-version.json')]=((repo/'workflow-version.json').read_bytes(),0o600)
    chosen={'dautia-project-cycle'} if scope=='routing' else {'dautia-project-cycle','dautia-ci-cd'}
    if scope=='all':chosen={p.name for p in (repo/'skills').iterdir() if p.is_dir() and not p.is_symlink()}
    for name in sorted(chosen):
        directory=repo/'skills'/name
        if not directory.is_dir():raise ContractError('required_source_skill_missing')
        for source in directory.rglob('*'):
            if source.is_symlink():raise ContractError('source_symlink_refused')
            if not source.is_file() or any(part in ('__pycache__','.git','.pytest_cache') for part in source.parts) or source.suffix=='.pyc':continue
            mode=0o700 if source.stat().st_mode&0o111 else 0o600
            result[str(skill_root/name/source.relative_to(directory))]=(source.read_bytes(),mode)
    adapters=render(repo,profile)
    definitions={name.split('/',1)[1]:sha(data) for name,data in adapters.items() if name.startswith('codex/')}
    result[str(codex/'agents/dautia-r3-definitions.json')]=(canonical({'schema_version':1,'definitions':definitions})+b'\n',0o600)
    for name,data in adapters.items():
        kind,filename=name.split('/',1)
        if kind=='codex':result[str(codex/'agents'/filename)]=(data,0o600)
        elif 'cursor' in profile['harnesses']:result[str(home/'.cursor/agents'/filename)]=(data,0o600)
    if 'cursor' in profile['harnesses']:
        result[str(home/'.cursor/rules/dautia-workflow.mdc')]=(b'---\nalwaysApply: true\n---\n'+(repo/'AGENTS.md').read_bytes(),0o600)
    launchers={'dautia-workflow':skill_root/'dautia-project-cycle/scripts/workflow_cli.py','dautia-jev':skill_root/'dautia-project-cycle/scripts/jev_support.py'}
    if scope!='routing':launchers['dautia-supabase']=skill_root/'dautia-ci-cd/scripts/dautia_supabase.py'
    for name,entry in launchers.items():
        text='#!/bin/sh\nset -eu\nexec '+shlex.quote(sys.executable)+' '+shlex.quote(str(entry))+' "$@"\n'
        result[str(home/'.local/bin'/name)]=(text.encode(),0o700)
    hooks={'description':'DautIA r3 candidate. Review and smoke-test before installing as a trusted hooks.json.','hooks':{}}
    command=shlex.quote(sys.executable)+' '+shlex.quote(str(skill_root/'dautia-project-cycle/scripts/workflow_cli.py'))+' hook'
    for event in ('PreToolUse','Stop','Interrupt','PreCompact'):
        group={'hooks':[{'type':'command','command':command,'timeout':3 if event=='Interrupt' else 10}]}
        if event=='PreToolUse':group['matcher']='Bash|apply_patch|Write|Edit'
        hooks['hooks'][event]=[group]
    result[str(config/'dautia/hooks.r3.candidate.json')]=(canonical(hooks)+b'\n',0o600)
    if configure_root:
        p=codex/'config.toml';data=p.read_bytes() if p.exists() else b''
        result[str(p)]=(root_config(data),0o600)
    return result


def install_write(path: Path, data: bytes, mode: int) -> None:
    """Atomic destination write without chmod of existing shared parent directories."""
    safe_path(path)
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd, name = tempfile.mkstemp(prefix=".dautia-install-", dir=path.parent)
    try:
        os.fchmod(fd, mode)
        with os.fdopen(fd, "wb") as stream:
            stream.write(data); stream.flush(); os.fsync(stream.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name): os.unlink(name)


def inspect(files: dict, installed: dict, adopt: bool=False) -> list[dict]:
    result=[]
    for name,(data,mode) in sorted(files.items()):
        path=Path(name);safe_path(path)
        exists=path.exists()
        if exists and not path.is_file():raise ContractError('destination_not_regular')
        old=path.read_bytes() if exists else None
        current=sha(old) if old is not None else None
        tracked=installed.get(name,{})
        same=current==sha(data) and (not exists or stat.S_IMODE(path.stat().st_mode)==mode)
        conflict=exists and current!=sha(data) and tracked.get('sha256')!=current and not adopt
        result.append({'destination':name,'before_hash':current,'after_hash':sha(data),'mode':mode,
                       'state':'unchanged' if same else 'conflict' if conflict else 'update' if exists else 'create'})
    return result


@contextmanager
def install_lock(config: Path):
    import fcntl
    directory=config/'dautia';private_dir(directory);path=directory/'installer.lock';safe_path(path)
    fd=os.open(path,os.O_CREAT|os.O_RDWR|getattr(os,'O_NOFOLLOW',0),0o600)
    with os.fdopen(fd,'rb+') as f:
        fcntl.flock(f,fcntl.LOCK_EX)
        try:yield
        finally:fcntl.flock(f,fcntl.LOCK_UN)


def apply(files: dict, config: Path, *, adopt=False, fail_after: int | None=None) -> dict:
    with install_lock(config):
        registry=config/'dautia/installed-r3.json'
        prior=load_json(read_private(registry)) if registry.exists() else {'files':{}}
        changes=inspect(files,prior['files'],adopt)
        if any(x['state']=='conflict' for x in changes):raise ContractError('installed_edits_need_reconciliation')
        if all(x['state']=='unchanged' for x in changes):
            return {'installed':True,'changed_files':0,'backup':None,'hooks_activated':False,'sessions_changed':False}
        backup=config/'dautia/workflow-backups'/('r3-'+str(time.time_ns())+'-'+uuid.uuid4().hex[:8]);private_dir(backup)
        records=[]
        for index,item in enumerate(changes):
            if item['state']=='unchanged':continue
            path=Path(item['destination']);data=path.read_bytes() if path.exists() else None
            mode=stat.S_IMODE(path.stat().st_mode) if path.exists() else None
            if data is not None:atomic_write(backup/str(index),data)
            records.append({**item,'backup_file':str(index) if data is not None else None,'before_mode':mode})
        manifest={'schema_version':1,'records':records,'registry_before':prior}
        atomic_write(backup/'manifest.json',canonical(manifest))
        written=[]
        try:
            for item in records:
                path=Path(item['destination'])
                current=sha(path.read_bytes()) if path.exists() else None
                if current!=item['before_hash']:raise ContractError('install_concurrent_edit')
                data,mode=files[str(path)];install_write(path,data,mode);written.append(item)
                if fail_after is not None and len(written)>=fail_after:raise OSError('injected_test_failure')
            new=dict(prior['files'])
            for name,(data,mode) in files.items():new[name]={'sha256':sha(data),'mode':mode}
            atomic_write(registry,canonical({'schema_version':1,'files':new,'last_backup':backup.name,'source_revision':git_revision(),'native_runtime_verified':False}))
        except Exception:
            for item in reversed(written):
                path=Path(item['destination'])
                if not path.is_file() or sha(path.read_bytes())!=item['after_hash']:continue
                if item['backup_file'] is None:path.unlink()
                else:install_write(path,read_private(backup/item['backup_file'],64_000_000),item['before_mode'])
            raise
        return {'installed':True,'changed_files':len(records),'backup':str(backup),'hooks_activated':False,'sessions_changed':False}


def rollback(backup: Path, config: Path) -> dict:
    with install_lock(config):
        expected=config/'dautia/workflow-backups'
        safe_path(backup)
        if backup.parent.resolve()!=expected.resolve():raise ContractError('invalid_backup_location')
        manifest=load_json(read_private(backup/'manifest.json'));records=manifest.get('records')
        if not isinstance(records,list) or not isinstance(manifest.get('registry_before'),dict): raise ContractError('invalid_backup_manifest')
        destinations=set()
        for item in records:
            if not isinstance(item,dict) or not isinstance(item.get('destination'),str) or not Path(item['destination']).is_absolute(): raise ContractError('invalid_backup_record')
            if item['destination'] in destinations: raise ContractError('duplicate_backup_destination')
            destinations.add(item['destination'])
            stored=item.get('backup_file')
            if stored is not None and (not isinstance(stored,str) or not stored.isdigit()): raise ContractError('backup_file_not_contained')
            if stored is not None and (type(item.get('before_mode')) is not int or not 0 <= item['before_mode'] <= 0o777): raise ContractError('invalid_backup_mode')
        # No automatic force: later local edits must not be lost.
        for item in records:
            path=Path(item['destination']);safe_path(path)
            if not path.is_file() or sha(path.read_bytes())!=item['after_hash']:raise ContractError('rollback_would_overwrite_later_edits')
            if item['backup_file'] is not None:
                data=read_private(backup/item['backup_file'],64_000_000)
                if sha(data)!=item['before_hash']:raise ContractError('backup_hash_mismatch')
        for item in reversed(records):
            path=Path(item['destination'])
            if item['backup_file'] is None:path.unlink()
            else:install_write(path,read_private(backup/item['backup_file'],64_000_000),item['before_mode'])
        atomic_write(config/'dautia/installed-r3.json',canonical(manifest['registry_before']))
        return {'restored':True,'files':len(records),'product_cleanup':False}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--profile',choices=('codex-macos','wsl-shared'),default='codex-macos');p.add_argument('--scope',choices=('routing','workflow','all'),default='workflow')
    mode=p.add_mutually_exclusive_group();mode.add_argument('--apply',action='store_true');mode.add_argument('--check',action='store_true');mode.add_argument('--rollback',type=Path)
    p.add_argument('--adopt-existing',action='store_true');p.add_argument('--configure-root',action='store_true');a=p.parse_args()
    home=Path.home();config=Path(os.environ.get('XDG_CONFIG_HOME',str(home/'.config'))).expanduser()
    try:
        if not config.is_absolute():raise ContractError('install_roots_must_be_absolute')
        if a.rollback:result=rollback(a.rollback,config)
        else:
            files=payloads(ROOT,home,a.profile,a.scope,a.configure_root)
            if a.apply:result=apply(files,config,adopt=a.adopt_existing)
            else:
                registry=config/'dautia/installed-r3.json';prior=load_json(read_private(registry)) if registry.exists() else {'files':{}}
                changes=inspect(files,prior['files'],a.adopt_existing)
                result={'preview':True,'files':changes,'consistent':all(x['state']=='unchanged' for x in changes),'network_called':False}
        print(json.dumps(result,ensure_ascii=True,indent=2));return 1 if a.check and not result.get('consistent') else 0
    except (OSError,ValueError,TypeError,KeyError,ContractError) as exc:
        print(json.dumps({'installed':False,'reason':str(exc) if isinstance(exc,ContractError) else 'installation_io_or_schema_error'}),file=sys.stderr);return 2


if __name__=='__main__':raise SystemExit(main())
