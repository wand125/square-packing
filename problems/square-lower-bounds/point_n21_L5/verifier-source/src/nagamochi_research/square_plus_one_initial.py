"""Offline maximin templates for N=k*k+1 with distributed lattice seams.

A uniform component is retained as a coverage floor; all other nonnegative
point/line/rectangle/radial weights can adapt. Finite samples never certify.
"""
import os
for name in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMBA_NUM_THREADS'):os.environ[name]='1'
import argparse,json,sys,time,hashlib
from pathlib import Path
from fractions import Fraction as F
import numpy as np
from scipy import sparse
from scipy.optimize import linprog
from unified_measure import primitive_key


def seam_pool(L,k):
    L=F(str(L));delta=L-k
    if k<3 or not 0<delta<1:raise ValueError('require k < L < k+1')
    pool=[];seen=set()
    def add(kind,g):
        g=list(map(F,g));coords=g[:2] if kind in ('disk','annulus') else g
        if any(not 0<x<L for x in coords):return
        key=primitive_key(kind,g,L)
        if key not in seen:seen.add(key);pool.append(dict(kind=kind,geometry=list(map(str,g)),family='distributed_seam'))
    # Move a mismatch seam through every row/column instead of stretching all gaps.
    for seam in range(1,k):
        lines=[F(j)+(delta if j>=seam else 0) for j in range(1,k)]
        for x in lines:
            for y in lines:add('point',[x,y])
        x=F(seam)+delta/2
        for j in range(k):
            a=F(j)+F(1,1000);b=min(F(j+1)+delta,L-F(1,1000))
            add('segment',[x,a,x,b])
            for h in (delta/2+F(1,500),F(1,20)):
                add('rectangle',[x-h,a,x+h,b])
            y=(a+b)/2
            for r in (delta+F(1,50),F(1,4)):
                add('disk',[x,y,r]);add('annulus',[x,y,r,F(9,10)])
    return pool


def fixed_budget(A,target,uniform_fraction=0):
    A=sparse.csr_matrix(A);m,n=A.shape
    if not 0<=uniform_fraction<=1:raise ValueError('uniform fraction')
    c=np.r_[np.zeros(n),-1.];bounds=[(uniform_fraction*target,None)]+[(0,None)]*(n-1)+[(0,None)]
    result=linprog(c,A_ub=sparse.hstack([-A,np.ones((m,1))],format='csr'),b_ub=np.zeros(m),
        A_eq=sparse.csr_matrix(np.r_[np.ones(n),0].reshape(1,-1)),b_eq=[target],bounds=bounds,method='highs',
        options=dict(primal_feasibility_tolerance=1e-8,dual_feasibility_tolerance=1e-8))
    if not result.success:raise RuntimeError(result.message)
    w=result.x[:-1]
    if np.any(w< -1e-8) or abs(w.sum()-target)>1e-7 or (A@w).min()<result.x[-1]-2e-7:raise RuntimeError('LP residual')
    return np.maximum(w,0),float(result.x[-1])


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--config',type=Path,required=True);a=ap.parse_args();cfg=json.loads(a.config.read_text());base=a.config.resolve().parent
    for key in ('code_dir','research_dir'):sys.path.insert(0,str((base/cfg[key]).resolve()))
    from unified_geometry import expand_primitives,matrix
    from unified_grid_search import structured
    from mixed_grid_pricing import candidate_pool,initial_state,screening_poses,quality_metrics,refine_witnesses
    k=cfg['k'];L=F(cfg['L']);B=F('.9977');target=float(cfg['target'])
    if cfg['n']!=k*k+1 or not 0<target<cfg['n']:raise ValueError('square plus one required')
    out=base/cfg['out'];out.mkdir(parents=True,exist_ok=False);start=time.perf_counter();records=[]
    def emit(**d):
        d['elapsed']=time.perf_counter()-start;records.append(d);p=out/'progress.tmp';p.write_text(json.dumps(dict(records=records),indent=2));p.replace(out/'progress.json');print(json.dumps(d),flush=True)
    if cfg.get('checkpoint'):
        z=np.load(base/cfg['checkpoint'],allow_pickle=False)
        if float(z['L'])!=float(L) or float(z['B'])!=float(B):raise ValueError('checkpoint geometry')
        ps=json.loads(str(z['primitives_json']));poses=z['poses'];w=z['weights']
    else:
        ps,poses,w,dual=initial_state(L,B,1.001)
        candidates=candidate_pool(L,k+1,ps,w,per_kind=cfg.get('per_kind',64),seed=20277000)+structured(L,k+1)
        if cfg.get('seams',True):candidates+=seam_pool(L,k)
        seen={primitive_key(p['kind'],p['geometry'],L) for p in ps}
        for p in candidates:
            key=primitive_key(p['kind'],p['geometry'],L)
            if key not in seen:seen.add(key);ps.append(p)
    expanded=expand_primitives(ps,L)
    def build(q):return sparse.vstack([sparse.csr_matrix(matrix(q[i:i+128],float(B),expanded)) for i in range(0,len(q),128)],format='csr')
    poses=np.vstack([poses,screening_poses(L,B,count=8192,seed=20277100,boundary_fraction=.25)])
    A=build(poses);keys={tuple(np.round(p,13)) for p in poses};history=[]
    for it in range(cfg.get('rounds',8)):
        w,floor=fixed_budget(A,target,cfg.get('uniform_fraction',.5))
        np.savez_compressed(out/'resume-state.npz',primitives_json=json.dumps(ps),weights=w,poses=poses,dual=np.zeros(len(poses)),L=float(L),B=float(B),rhs=1.001)
        q=screening_poses(L,B,count=32768,seed=cfg.get('screen_seed',20277200)+it,boundary_fraction=.25)
        if cfg.get('event_screen',False):
            from event_screening import event_poses
            q=np.vstack([q,event_poses(ps,w,L,B,per_angle=8192,seed=20280000+it)])
        values=build(q)@w
        refined,rv=refine_witnesses(q,values,L,B,lambda x:build(x)@w,starts=24)
        q=np.vstack([q,refined]);values=np.r_[values,rv]
        emit(operation='offline_template',iteration=it,rows=len(poses),columns=len(ps),mass=float(w.sum()),training_minimum=floor,screen_minimum=float(values.min()),below_one=int(np.sum(values<1)),globally_verified=False)
        if it+1==cfg.get('rounds',8):break
        new=[]
        for i in np.argsort(values):
            if values[i]>=max(1.0001,floor+1e-6):break
            key=tuple(np.round(q[i],13))
            if key not in keys:keys.add(key);new.append(q[i])
            if len(new)>=256:break
        if not new:break
        A=sparse.vstack([A,build(np.asarray(new))],format='csr');poses=np.vstack([poses,new])
    generation_seconds=time.perf_counter()-start
    held=screening_poses(L,B,count=65536,seed=cfg.get('holdout_seed',20278000),boundary_fraction=.25);vals=build(held)@w
    uniform=target*float(B/L)**2
    report=dict(config=cfg,offline_seconds=generation_seconds,assessment_seconds=time.perf_counter()-start-generation_seconds,
        quality=quality_metrics(vals,w.sum(),target),uniform_baseline=quality_metrics(np.full(len(held),uniform),target,target),
        source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),certified=False)
    (out/'result.json').write_text(json.dumps(report,indent=2)+'\n');emit(operation='finish',status='SAVED_FINITE_INITIAL',globally_verified=False)

if __name__=='__main__':main()
