#!/usr/bin/env python3
"""Bounded read-only contract replay using Codex CLI; no API billing inference."""
from pathlib import Path
import argparse,json,subprocess,time,tomllib,re,os,shutil,hashlib
ROOT=Path(__file__).resolve().parents[1]

def grade(cases, result):
    rows=result.get('results',[]) if isinstance(result,dict) else []
    index={r.get('id'):r for r in rows if isinstance(r,dict)}
    unexpected=[r.get('id') if isinstance(r,dict) else None for r in rows if not isinstance(r,dict) or r.get('id') not in {c['id'] for c in cases}]
    counts={c['id']:sum(isinstance(r,dict) and r.get('id')==c['id'] for r in rows) for c in cases}
    checks=[]
    for c in cases:
        differences={}
        if unexpected:differences['unexpected_ids']=unexpected
        for k,v in c['expected'].items():
            allowed=c.get('acceptable',{}).get(k,[v])
            actual=index.get(c['id'],{}).get(k)
            if actual not in allowed:differences[k]={'allowed':allowed,'actual':actual}
        if counts[c['id']]!=1:differences['identity_count']=counts[c['id']]
        checks.append({'id':c['id'],'passed':not differences,'differences':differences})
    return checks

def routing_matches(observed, requested):
    return bool(observed) and all(x.get('model')==requested['model'] and x.get('effort')==requested['effort'] for x in observed)

def decision_vocabulary(cases):
    result={k:sorted({v for c in cases for v in c.get('acceptable',{}).get(k,[c['expected'][k]])} | {c['expected'][k] for c in cases}) for k in ['route','operation','close']}
    result['route']=['sol-low','sol-medium','sol-high','sol-xhigh','astra-low','astra-medium']
    return result

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--codex',default=shutil.which('codex'))
    p.add_argument('--profiles',nargs='+',default=['dautia-talk','dautia-technical','dautia-complex'])
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--timeout',type=int,default=180)
    p.add_argument('--run',action='store_true');p.add_argument('--dry-run',action='store_true')
    a=p.parse_args()
    if a.run and a.dry_run:p.error('Choose --run or --dry-run')
    if not 15<=a.timeout<=600:p.error('timeout must be 15..600 seconds')
    codex=Path.home()/'.codex';cfg=tomllib.loads((codex/'config.toml').read_text())
    profiles={}
    for name in a.profiles:
        if not re.fullmatch('dautia-[a-z]+',name):p.error('Only local dautia-* profiles permitted')
        d=tomllib.loads((codex/(name+'.config.toml')).read_text())
        profiles[name]={'model':d['model'],'effort':d['model_reasoning_effort']}
    cases=json.loads((ROOT/'references/pilot-cases.json').read_text())
    if not a.run:
        print(json.dumps({'mode':'dry-run','profiles':profiles,'cases':[c['id'] for c in cases],'timeout_seconds':a.timeout,'kind':'contract-replay-not-implementation-benchmark'},indent=2));return
    out=a.output.resolve();out.mkdir(parents=True,exist_ok=True);out.chmod(0o700)
    schema={'type':'object','properties':{'results':{'type':'array','items':{'type':'object','properties':{k:{'type':'string'} for k in ['id','route','operation','close','reason']},'required':['id','route','operation','close','reason'],'additionalProperties':False}}},'required':['results'],'additionalProperties':False}
    (out/'schema.json').write_text(json.dumps(schema))
    # Domain policy is explicit so the same contract is compared across all runs.
    contract=(codex/'AGENTS.md').read_text()+'\n'+(codex/'skills/dautia-project-cycle/references/model-routing.md').read_text()+'\n'+(codex/'skills/dautia-project-cycle/references/continuity.md').read_text()
    visible=[{k:v for k,v in c.items() if k not in ['expected','acceptable']} for c in cases]
    vocabulary=decision_vocabulary(cases)
    prompt='Evaluate these sanitized workflow scenarios under the supplied current contract. Do not execute tools or access files/network; this is a decision replay, not permission to do any scenario. Choose the best route/operation/close enum and give one brief reason. Judge scenario facts, not your own model identity.\nCONTRACT:\n'+contract+'\nENUMS:\n'+json.dumps(vocabulary)+'\nSCENARIOS:\n'+json.dumps(visible,ensure_ascii=False)
    contract_hash=hashlib.sha256(contract.encode()).hexdigest()
    fixture_hash=hashlib.sha256(json.dumps(cases,sort_keys=True).encode()).hexdigest()
    version=subprocess.run([a.codex,'--version'],capture_output=True,text=True,timeout=10).stdout.strip()
    records=[]
    for name,profile in profiles.items():
        last=out/(name+'-answer.json')
        cmd=[a.codex,'exec','-p',name,'--skip-git-repo-check','-s','read-only','--json','--output-schema',str(out/'schema.json'),'-o',str(last),'-C',str(out)]
        # Load real configuration/profiles, but isolate the replay from all external tools.
        for server in cfg.get('mcp_servers',{}):cmd+=['-c',f'mcp_servers.{server}.enabled=false']
        for plugin in cfg.get('plugins',{}):cmd+=['-c',f'plugins.{plugin}.enabled=false']
        cmd+=['-c','features.multi_agent=false','-c','web_search="disabled"','-c','notify=[]','-']
        start=time.monotonic();print(json.dumps({'running':name}),flush=True)
        try:
            r=subprocess.run(cmd,input=prompt,text=True,capture_output=True,timeout=a.timeout)
            # Logs belong only to this sanitized prompt; owner-only scratch.
            for suffix,data in [('events.jsonl',r.stdout),('stderr.txt',r.stderr)]:
                path=out/(name+'-'+suffix);path.write_text(data);path.chmod(0o600)
            if last.exists():last.chmod(0o600)
            result=json.loads(last.read_text()) if last.exists() else {}
            checks=grade(cases,result)
            usage=[];tool_events=0;thread_id=None
            for line in r.stdout.splitlines():
                try:e=json.loads(line)
                except ValueError:continue
                if e.get('type')=='thread.started':thread_id=e.get('thread_id')
                if e.get('type')=='turn.completed':usage.append(e.get('usage'))
                if e.get('item',{}).get('type') in ['command_execution','mcp_tool_call','web_search']:tool_events+=1
            # Runtime CLI may omit headers in JSON mode; never replace observed with requested.
            observed=[]
            if thread_id:
                for rollout in (codex/'sessions').glob('*/*/*/*'+thread_id+'*.jsonl'):
                    for line in rollout.open():
                        try: event=json.loads(line)
                        except ValueError: continue
                        if event.get('type')=='turn_context':
                            context=event.get('payload',{});observed.append({'model':context.get('model'),'effort':context.get('effort') or context.get('reasoning_effort')})
            actual_model=re.search(r'^model:\s*(\S+)',r.stderr,re.M)
            rec={'profile':name,'requested':profile,'observed_model_header':actual_model.group(1) if actual_model else None,'observed_turn_profiles':observed,'routing_matches':routing_matches(observed,profile),'runtime':a.codex,'runtime_version':version,'contract_sha256':contract_hash,'fixture_sha256':fixture_hash,'exit_code':r.returncode,'seconds':round(time.monotonic()-start,2),'checks':checks,'passed':sum(x['passed'] for x in checks),'cases':len(cases),'reported_usage':usage,'tool_events':tool_events,'billing_cost':None}
            if r.returncode:rec['error_excerpt']=r.stderr[-1200:]
        except subprocess.TimeoutExpired:
            rec={'profile':name,'requested':profile,'timeout':True,'seconds':a.timeout,'passed':0,'cases':len(cases),'billing_cost':None}
        records.append(rec);(out/'results.json').write_text(json.dumps({'kind':'contract-replay-not-implementation-benchmark','rubric_version':'1.3','records':records},ensure_ascii=False,indent=2));(out/'results.json').chmod(0o600);print(json.dumps({k:v for k,v in rec.items() if k not in ['checks']},ensure_ascii=False),flush=True)
        if rec.get('exit_code',0)!=0 or rec.get('timeout'): break
    raise SystemExit(0 if all(r.get('passed')==len(cases) and r.get('exit_code')==0 and r.get('tool_events')==0 and r.get('routing_matches') is True for r in records) and len(records)==len(profiles) else 1)
if __name__=='__main__':main()
