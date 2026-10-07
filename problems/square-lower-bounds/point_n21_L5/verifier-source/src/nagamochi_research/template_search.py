"""Verify a transferred measure unchanged before enabling counterexample repair.

This preserves the high-quality initial weights instead of immediately solving
an unrelated minimum-mass LP. All acceptance remains exact and global.
"""
import os
for name in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMBA_NUM_THREADS'):os.environ[name]='1'
import argparse,hashlib,json,sys,time,subprocess
from pathlib import Path
from fractions import Fraction as F
from collections import defaultdict
import numpy as np
from unified_measure import SCHEMA,RADIAL_SCHEMA,TRIMMED_SCHEMA,RADIAL_KINDS,orbit,validate,verify,net_check


def candidate_from_state(path,n,target):
    z=np.load(path,allow_pickle=False);ps=json.loads(str(z['primitives_json']));w=z['weights']
    if len(ps)!=len(w) or not np.isfinite(w).all() or np.any(w<0) or not 0<F(target)<n:raise ValueError('invalid template')
    # Exact normalization of saved decimal weights; no inherited proof claim.
    ws=[F(str(float(x))) for x in w];total=sum(ws,F(0))
    if total<=0:raise ValueError('empty template')
    d=dict(schema=RADIAL_SCHEMA if any(p['kind'] in RADIAL_KINDS for p in ps) else SCHEMA,
        n=n,L=str(float(z['L'])),B=str(float(z['B'])),net=json.loads(str(z['net_json'])) if 'net_json' in z else dict(step='83/40000',last=200),
        primitives=[dict(kind=p['kind'],geometry=p['geometry'],mass=str(x*F(target)/total)) for p,x in zip(ps,ws) if x],total_mass=str(F(target)))
    if 'core_json' in z:
        d['schema']=TRIMMED_SCHEMA;d['core']=json.loads(str(z['core_json']))
    validate(d);net_check(d);return d


def point_candidate(d):
    L,B,n,_,mass,_=validate(d);atoms=defaultdict(F)
    for p in d['primitives']:
        if p['kind']!='point':raise ValueError('pure point candidate required')
        for xy in orbit('point',p['geometry'],L):atoms[xy]+=F(p['mass'])/8
    entries=sorted((xy,w) for xy,w in atoms.items() if w)
    return dict(n=n,L=str(L),B=str(B),sites=[list(map(str,xy)) for xy,w in entries],
        point_cols=[[i] for i in range(len(entries))],charge_cols=[],weights=[str(w) for xy,w in entries])


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--config',type=Path,required=True);a=ap.parse_args()
    cfg=json.loads(a.config.read_text());base=a.config.resolve().parent
    for key in ('threshold_dir','code_dir','research_dir'):
        if key in cfg:sys.path.insert(0,str((base/cfg[key]).resolve()))
    out=(base/cfg['out']).resolve();out.mkdir(parents=True,exist_ok=True)
    def write(path,d):
        t=path.with_suffix(path.suffix+'.tmp');t.write_text(json.dumps(d,indent=2)+'\n');t.replace(path)
    progress=out/'progress.json';records=json.loads(progress.read_text())['records'] if progress.exists() else [];start=time.monotonic()
    def emit(**d):
        d['elapsed']=time.monotonic()-start;records.append(d);write(progress,dict(records=records));print(json.dumps(d),flush=True)
    source=(base/cfg['checkpoint']).resolve();candidate=candidate_from_state(source,cfg['n'],cfg['target'])
    if F(candidate['L'])!=F(cfg['L']):raise ValueError('L mismatch')
    manifest=dict(config=cfg,input_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),owner='codex-squarepacking',method='working_lp',source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    mp=out/'manifest.json'
    if mp.exists() and json.loads(mp.read_text())!=manifest:raise ValueError('resume manifest mismatch')
    write(mp,manifest);write(out/'candidate.json',candidate)
    if records and records[-1].get('status') in ('CERTIFIED','SAVED_SEARCH_RESULT'):return
    proof=out/'proof.json';work=json.loads(proof.read_text()) if proof.exists() else None
    emit(operation='initial_template',status='EXACT_VERIFYING',mass=candidate['total_mass'],columns=len(candidate['primitives']),globally_verified=False)
    pure=candidate['schema']!=TRIMMED_SCHEMA and all(p['kind']=='point' for p in candidate['primitives']) and candidate['net']==dict(step='83/40000',last=200)
    if pure:
        from verify_point_sweep import verify as sweep
        pc=point_candidate(candidate);write(out/'point-candidate.json',pc)
        def checkpoint(w):
            write(proof,w);emit(operation='proof',status=w['status'],directions_completed=len(w['directions']),globally_verified=w['status']=='CERTIFIED')
        work=sweep(pc,work,checkpoint,use_symmetry=True)
        if work['status']=='UNCOVERED':
            witnesses=[[float(F(w['cx'])),float(F(w['cy'])),float(F(w['sin'])/(1+F(w['cos'])))] for w in work['witnesses']]
    else:
        while True:
            work=verify(candidate,work,max_boxes=cfg.get('exact_chunk_boxes',8),checkpoint=lambda w:write(proof,w),
                integral_subdivisions=32,max_integral_subdivisions=256)
            write(proof,work);emit(operation='proof',status=work['status'],boxes=work['boxes'],directions_completed=work['directions_completed'])
            if work['status']=='CERTIFIED':break
            if work['status']=='UNCOVERED':
                w=work['witness'];witnesses=[[float(F(w['cx'])),float(F(w['cy'])),float(F(w['t']))]];break
            if work.get('reason')=='INTEGRAL_PRECISION' or work['boxes']>=cfg.get('exact_review_boxes',20000):
                emit(operation='finish',status='SAVED_EXACT_REVIEW',globally_verified=False);return
    if work['status']=='CERTIFIED':
        write(out/'certificate.json',candidate);emit(operation='finish',status='CERTIFIED',globally_verified=True);return
    # Dedicated generator owns trimmed-core repair; never use square coefficients.
    if candidate['schema']==TRIMMED_SCHEMA:
        write(out/'counterexamples.json',dict(poses=witnesses));emit(operation='finish',status='SAVED_TRIMMED_COUNTEREXAMPLES',globally_verified=False);return
    # Only an exact counterexample authorizes changing the original weights.
    z=np.load(source,allow_pickle=False);poses=np.vstack([z['poses'],witnesses]);seed=out/'repair-start.npz'
    ps=json.loads(str(z['primitives_json']));weights=z['weights'].copy()
    # A newly found empty region must not make the retained-column LP infeasible.
    # A zero-weight uniform column leaves the original measure unchanged.
    ps.append(dict(kind='rectangle',geometry=['0','0',candidate['L'],candidate['L']],family='repair_uniform'))
    weights=np.r_[weights,0.]
    np.savez_compressed(seed,poses=poses,weights=weights,dual=np.zeros(len(poses)),primitives_json=json.dumps(ps),L=z['L'],B=z['B'],rhs=1.001)
    repair=dict(cfg['repair'],n=cfg['n'],L=cfg['L'],B=candidate['B'],net=candidate['net'],target=cfg['target'],k=cfg['k'],checkpoint=str(seed),out=str(out/'search'),
        code_dir=str((base/cfg['code_dir']).resolve()),research_dir=str((base/cfg['research_dir']).resolve()),owner='codex-squarepacking',method='working_lp')
    if repair.get('radial_pricing'):repair['radial_code_dir']=repair['research_dir']
    rp=out/'repair-config.json';write(rp,repair)
    if (out/'search').exists():
        emit(operation='finish',status='SAVED_REPAIR_RESUME_REQUIRED',globally_verified=False);return
    emit(operation='repair',status='SEARCHING',exact_counterexamples=len(witnesses),globally_verified=False)
    command=[sys.executable,str(Path(__file__).with_name('unified_grid_search.py')),'--config',str(rp)]
    process=subprocess.Popen(command);last_seen=None
    while True:
        child_progress=out/'search/progress.json'
        if child_progress.exists():
            child_records=json.loads(child_progress.read_text())['records']
            if child_records and child_records[-1]!=last_seen:
                last_seen=child_records[-1];event=dict(last_seen);event['phase']='counterexample_repair';event['child_elapsed']=event.pop('elapsed',None);emit(**event)
        if process.poll() is not None:break
        time.sleep(1)
    if process.returncode:raise RuntimeError(f'repair exited {process.returncode}')
    last=json.loads((out/'search/progress.json').read_text())['records'][-1]
    if last.get('status')=='CERTIFIED':
        write(out/'certificate.json',json.loads((out/'search/certificate.json').read_text()))
    emit(operation='finish',status='CERTIFIED' if last.get('status')=='CERTIFIED' else 'SAVED_SEARCH_RESULT',search_status=last.get('status'),globally_verified=last.get('status')=='CERTIFIED')

if __name__=='__main__':main()
