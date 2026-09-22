#!/usr/bin/env python3
"""Frozen GPT-6 contract replay; fresh isolated Codex home, no product/provider actions.

OpenAI account use is real. Decision replay is not a product-quality benchmark.
Default is dry-run; --run requires the matching frozen manifest.
"""
from pathlib import Path
import argparse
import hashlib
import json
import os
import signal
import subprocess
import time
from run_replay import grade

ROOT = Path(__file__).resolve().parents[1]
PROFILES = {
    'baseline_high': ('gpt-5.6-sol', 'high'),
    'sol_medium': ('gpt-6-sol', 'medium'),
    'sol_high': ('gpt-6-sol', 'high'),
    'luna_high': ('gpt-6-luna', 'high'),
    'astra_low': ('gpt-6-astra', 'low'),
    'astra_medium': ('gpt-6-astra', 'medium'),
}


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def grader_fingerprint(path=None):
    return digest((path or Path(__file__).with_name('run_replay.py')).read_bytes())


def observed_profiles(home, thread_id):
    observed = []
    if not thread_id:
        return observed
    for path in (home / 'sessions').glob('*/*/*/*' + thread_id + '*.jsonl'):
        for line in path.read_text().splitlines():
            try:
                event = json.loads(line)
            except ValueError:
                continue
            if event.get('type') == 'turn_context':
                p = event['payload']
                observed.append((p.get('model'), p.get('effort') or p.get('reasoning_effort')))
    return observed


def execution_passed(exit_code, checks, requested, observed, tools, completed):
    return (exit_code == 0 and completed and bool(checks) and all(c['passed'] for c in checks)
            and bool(observed) and all(tuple(p) == tuple(requested) for p in observed) and tools == 0)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--codex', required=True)
    parser.add_argument('--profiles', nargs='+', choices=PROFILES, default=['baseline_high', 'sol_high', 'sol_medium', 'luna_high', 'astra_low'])
    parser.add_argument('--timeout', type=int, default=180)
    parser.add_argument('--auth-file', type=Path, default=Path.home()/'.codex/auth.json')
    parser.add_argument('--run', action='store_true')
    args = parser.parse_args()
    if not 15 <= args.timeout <= 600:
        parser.error('timeout must be 15..600 seconds')
    repo = args.repo.resolve()
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=True, mode=0o700)
    out.chmod(0o700)
    cases_raw = (ROOT/'references/gpt6-pilot-cases.json').read_bytes()
    cases = json.loads(cases_raw)
    sources = [repo/'AGENTS.md', repo/'skills/dautia-project-cycle/references/model-routing.md', repo/'skills/dautia-project-cycle/config/routing-policy.json']
    contract = '\n'.join(p.read_text() for p in sources)
    version = subprocess.check_output([args.codex, '--version'], text=True, timeout=10).strip()
    frozen = {'kind':'decision-replay-not-product-benchmark','cases_sha256':digest(cases_raw),
              'contract_sha256':digest(contract.encode()),'runner_sha256':digest(Path(__file__).read_bytes()),
              'grader_sha256':grader_fingerprint(),
              'profiles':{k:PROFILES[k] for k in args.profiles},'codex':str(Path(args.codex).resolve()),
              'codex_version':version,'timeout':args.timeout}
    # Normalize tuples before comparing the persisted JSON manifest.
    frozen = json.loads(json.dumps(frozen))
    manifest = out/'frozen.json'
    if not args.run:
        if manifest.exists() and json.loads(manifest.read_text()) != frozen:
            parser.error('existing frozen plan differs; choose a new output directory')
        manifest.write_text(json.dumps(frozen, indent=2)+'\n')
        print(json.dumps({'dry_run':True,'cases':len(cases),'profiles':args.profiles,'manifest':str(manifest)}))
        return 0
    if not manifest.is_file() or json.loads(manifest.read_text()) != frozen:
        parser.error('run requires a matching prior dry-run')
    if not args.auth_file.is_file():
        parser.error('an existing Codex auth file is required; no login or secret printing')
    home = out/'isolated-codex-home'
    home.mkdir(mode=0o700)
    auth = home/'auth.json'
    auth.symlink_to(args.auth_file.resolve())
    (home/'config.toml').write_text('approval_policy = "never"\nsandbox_mode = "read-only"\nweb_search = "disabled"\n[features]\nmulti_agent = false\n')
    workspace = out/'workspace'
    workspace.mkdir()
    schema = {'type':'object','properties':{'results':{'type':'array','items':{'type':'object','properties':{k:{'type':'string'} for k in ['id','route','operation','close','reason']},'required':['id','route','operation','close','reason'],'additionalProperties':False}}},'required':['results'],'additionalProperties':False}
    schema_path = out/'schema.json'
    schema_path.write_text(json.dumps(schema))
    visible = [{k:v for k,v in c.items() if k not in ('expected','acceptable')} for c in cases]
    vocabulary = {key:sorted({v for c in cases for v in c.get('acceptable',{}).get(key,[c['expected'][key]])}) for key in ('route','operation','close')}
    prompt = 'Evaluate these sanitized cases under the supplied contract. Do not execute tools. This is a decision replay, not permission to perform the cases. Choose one route/operation/close from the enums and one brief reason. Judge the facts, not your own model identity. operation read-only forbids mutation; pure-work-only permits pure code edits/tests but forbids DB/provider actions; implement-local permits only the approved local delta. A checklist is read-only and release-blocked while mandatory evidence is missing.\nCONTRACT\n'+contract+'\nENUMS\n'+json.dumps(vocabulary)+'\nCASES\n'+json.dumps(visible,ensure_ascii=False)
    env = dict(os.environ, CODEX_HOME=str(home))
    records = []
    try:
        for name in args.profiles:
            model, effort = PROFILES[name]
            answer = out/(name+'-answer.json')
            command = [args.codex,'exec','--skip-git-repo-check','-s','read-only','--json','-m',model,'-c','model_reasoning_effort='+json.dumps(effort),'--output-schema',str(schema_path),'-o',str(answer),'-C',str(workspace),'-']
            print(json.dumps({'running':name}), flush=True)
            started = time.monotonic()
            proc = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env, start_new_session=True)
            timed_out = False
            try:
                stdout, stderr = proc.communicate(prompt, timeout=args.timeout)
            except subprocess.TimeoutExpired:
                timed_out = True
                os.killpg(proc.pid, signal.SIGTERM)
                try:
                    stdout, stderr = proc.communicate(timeout=5)
                except subprocess.TimeoutExpired:
                    os.killpg(proc.pid, signal.SIGKILL)
                    stdout, stderr = proc.communicate()
            for suffix, content in [('events.jsonl',stdout),('stderr.txt',stderr)]:
                path = out/(name+'-'+suffix)
                path.write_text(content)
                path.chmod(0o600)
            events = []
            for line in stdout.splitlines():
                try: events.append(json.loads(line))
                except ValueError: pass
            thread = next((e.get('thread_id') for e in events if e.get('type')=='thread.started'),None)
            completed = any(e.get('type')=='turn.completed' for e in events)
            tools = sum(e.get('item',{}).get('type') in ('command_execution','mcp_tool_call','web_search') for e in events)
            try: result = json.loads(answer.read_text()) if answer.is_file() else {}
            except ValueError: result = {}
            checks = grade(cases,result)
            observed = observed_profiles(home,thread)
            row = {'profile':name,'requested':[model,effort],'observed':observed,'completed':completed,
                   'exit_code':proc.returncode,'timed_out':timed_out,'seconds':round(time.monotonic()-started,2),
                   'checks':checks,'passed_count':sum(c['passed'] for c in checks),'case_count':len(cases),'tool_events':tools,
                   'reported_usage':[e.get('usage') for e in events if e.get('type')=='turn.completed'],
                   'billing_cost':None,'passed':execution_passed(proc.returncode,checks,(model,effort),observed,tools,completed)}
            records.append(row)
            (out/'results.json').write_text(json.dumps({'frozen':frozen,'records':records,'limitations':['Decision replay is not autonomous delegation or product validation.','Runtime context plus completed response proves client-reported profile, not independent provider internals.','No subscription savings or product quality conclusion.']},indent=2)+'\n')
            print(json.dumps({k:v for k,v in row.items() if k not in ('checks','reported_usage')}),flush=True)
            if timed_out or proc.returncode:
                break
    finally:
        if auth.is_symlink(): auth.unlink()
    return 0 if len(records)==len(args.profiles) and all(r['passed'] for r in records) else 1


if __name__ == '__main__':
    raise SystemExit(main())
