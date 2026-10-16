#!/usr/bin/env python3
"""Production dependency scheduler adapted from the recorded cloud runner."""
import argparse
import concurrent.futures
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parent.parent
BUILD=ROOT/'.lake/build/lib/lean'
STATE=ROOT/'BUILD.step7-state'
DEADLINE_SECONDS=600

def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--jobs',type=int,default=1)
    ap.add_argument('--dry-run',action='store_true')
    args=ap.parse_args()
    if args.jobs<1:ap.error('--jobs must be positive')
    roots=['ClosedForm.FinalAudit']
    nodes={}
    def visit(name):
        if name in nodes:return
        p=ROOT/(name.replace('.','/')+'.lean')
        if not p.is_file():return # Mathlib/toolchain: installed prerequisites.
        imports=re.findall(r'^import\s+([\w.]+)',p.read_text(),re.M)
        nodes[name]=dict(source=p,imports=imports)
        for dep in imports:visit(dep)
    for root in roots:visit(root)
    forbidden_providers=set(nodes)&{'ClosedForm.StatementCore','ClosedForm.Algebra',
        'ClosedForm.Statement','ClosedForm.Audit'}
    if forbidden_providers:raise SystemExit('Local placeholder graph in cloud audit: '+str(forbidden_providers))
    if args.dry_run:
        print(json.dumps(dict(mode='cloud',jobs=args.jobs,modules=list(nodes),prebuilt_inputs=[]),indent=2));return 0
    STATE.mkdir(exist_ok=True)
    stop=STATE/'TIMEOUT'
    if (ROOT/'.lake/step5-timeout').exists():raise SystemExit('STOP: a local Lean run exceeded ten minutes')
    if stop.exists():raise SystemExit('STOP: a step-7 Lean run exceeded ten minutes; see '+str(stop))
    lock=ROOT/'.lake/step1-build.lock'
    fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600);os.write(fd,str(os.getpid()).encode());os.close(fd)
    env=dict(os.environ);env['PATH']=str(Path.home()/'.elan/bin')+':'+env['PATH'];env['LEAN_NUM_THREADS']='4'
    version=(ROOT/'lean-toolchain').read_text().strip()
    fingerprints={}
    def fingerprint(n):
        if n in fingerprints:return fingerprints[n]
        if n not in nodes:
            p=ROOT/(n.replace('.','/')+'.lean');o=BUILD/(n.replace('.','/')+'.olean')
            return hashlib.sha256((digest(p)+digest(o)).encode()).hexdigest() if p.is_file() and o.is_file() else n+version
        v=nodes[n]
        payload=digest(v['source'])+version+''.join(fingerprint(d) for d in v['imports'])
        fingerprints[n]=hashlib.sha256(payload.encode()).hexdigest();return fingerprints[n]
    for n in nodes:fingerprint(n)
    logdir=STATE/'logs';logdir.mkdir(exist_ok=True)
    tsv=ROOT/'BUILD.step7-cloud.tsv'
    fields=['module','status','wall_seconds','user_seconds','system_seconds','peak_rss_bytes','source_sha256','dependency_sha256','log']
    if not tsv.exists():tsv.write_text('\t'.join(fields)+'\n')
    def record(n):return STATE/(n+'.json')
    def target(n):return BUILD/(n.replace('.','/')+'.olean')
    def current(n):
        if not record(n).exists() or not target(n).exists():return False
        try:r=json.loads(record(n).read_text())
        except (ValueError,OSError):return False
        return r.get('exit_code')==0 and r.get('source_sha256')==digest(nodes[n]['source']) and r.get('dependency_sha256')==fingerprints[n] and r.get('olean_sha256')==digest(target(n))
    def run(n):
        p=nodes[n]['source'];out=target(n);out.parent.mkdir(parents=True,exist_ok=True)
        temporary=out.with_suffix('.step7.olean')
        runenv=env;cmd=['nice','-n','10','lake','env','lean']
        cmd+=['-o',str(temporary.relative_to(ROOT)),str(p.relative_to(ROOT))]
        logpath=logdir/(n+'.log');start=time.monotonic();timeout=False
        with logpath.open('w') as log:
            child=subprocess.Popen(cmd,cwd=ROOT,env=runenv,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
            try:
                while True:
                    pid,status,usage=os.wait4(child.pid,os.WNOHANG)
                    if pid:break
                    if time.monotonic()-start>=DEADLINE_SECONDS:
                        timeout=True;stop.write_text(n+'\n');os.killpg(child.pid,signal.SIGKILL)
                        _,status,usage=os.wait4(child.pid,0);break
                    time.sleep(.05)
            except BaseException:
                os.killpg(child.pid,signal.SIGKILL);os.wait4(child.pid,0);raise
            child.returncode=os.waitstatus_to_exitcode(status)
        r=dict(module=n,command=cmd,exit_code=child.returncode,timed_out=timeout,
            wall_seconds=round(time.monotonic()-start,3),user_seconds=round(usage.ru_utime,3),system_seconds=round(usage.ru_stime,3),
            peak_rss_bytes=usage.ru_maxrss if sys.platform=='darwin' else usage.ru_maxrss*1024,
            source_sha256=digest(p),dependency_sha256=fingerprints[n],log=str(logpath.relative_to(ROOT)),
            rss_source='wait4 lake env lean process including reaped children',
            mode='cloud')
        logtext=logpath.read_text()
        # A production structural theorem must never silently retain a placeholder.
        if child.returncode==0 and ('sorryAx' in logtext or 'declaration uses `sorry`' in logtext):
            r['exit_code']=1;r['audit_error']='unexpected sorry dependency'
        if r['exit_code']==0:
            temporary.replace(out);r['olean_sha256']=digest(out)
        else:temporary.unlink(missing_ok=True)
        record(n).write_text(json.dumps(r,indent=2)+'\n')
        return r
    completed=set();pending=set(nodes);running={};failed=False
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.jobs) as pool:
            while pending or running:
                if not failed and not stop.exists():
                    for n in sorted(pending):
                        if any(d in nodes and d not in completed for d in nodes[n]['imports']):continue
                        if current(n):
                            completed.add(n);pending.remove(n);print('SKIP '+n,flush=True)
                            continue
                        if len(running)>=args.jobs:break
                        pending.remove(n);running[pool.submit(run,n)]=n;print('START '+n,flush=True)
                if not running:
                    if pending and not failed and not stop.exists():
                        # Newly skipped dependencies may unlock the next layer.
                        if any(all(d not in nodes or d in completed for d in nodes[n]['imports']) for n in pending):continue
                        raise RuntimeError('dependency cycle: '+str(sorted(pending)))
                    break
                done,_=concurrent.futures.wait(running,timeout=1,return_when=concurrent.futures.FIRST_COMPLETED)
                for future in done:
                    n=running.pop(future);r=future.result();r['status']='ok' if r['exit_code']==0 else 'failed'
                    with tsv.open('a') as f:f.write('\t'.join(str(r.get(k,'')) for k in fields)+'\n')
                    print(f"{r['status'].upper()} {n}: {r['wall_seconds']} s, {r['peak_rss_bytes']} bytes peak RSS",flush=True)
                    if r['exit_code']:
                        failed=True;print((ROOT/r['log']).read_text(),flush=True)
                    else:completed.add(n)
        if stop.exists():return 124
        if failed:return 1
        audit='\n'.join((logdir/(name+'.log')).read_text() for name in
            ('ClosedForm.PublishedStructure','ClosedForm.PublishedSaving','ClosedForm.FinalAudit'))
        print(audit)
        (ROOT/'BUILD.step9-cloud-axioms.log').write_text(audit)
        with (ROOT/'BUILD.log').open('a') as receipt:
            receipt.write('\n=== Cloud structural/saving/main audit ===\n'+audit)
        return 0
    finally:lock.unlink()

if __name__=='__main__':sys.exit(main())
