"""Fixed-budget weight repair inside a trust region around a stored template."""
import os
for name in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMBA_NUM_THREADS'):os.environ[name]='1'
import argparse,json,sys,time,hashlib
from pathlib import Path
from fractions import Fraction as F
import numpy as np
from scipy import sparse
from scipy.optimize import linprog


def bounded_weights(A,reference,lower=.9975,upper=1.05):
    w0=np.asarray(reference,float);A=sparse.csr_matrix(A)
    if A.shape[1]!=len(w0) or not 0<=lower<=1<=upper or np.any(w0<0) or not np.isfinite(w0).all() or w0.sum()<=0:
        raise ValueError('invalid trust region')
    m,n=A.shape;C=sparse.hstack([-A,np.ones((m,1))],format='csr')
    r=linprog(np.r_[np.zeros(n),-1.],A_ub=C,b_ub=np.zeros(m),
        A_eq=sparse.csr_matrix(np.r_[np.ones(n),0.].reshape(1,-1)),b_eq=[w0.sum()],
        bounds=list(zip(lower*w0,upper*w0))+[(0,None)],method='highs',
        options=dict(primal_feasibility_tolerance=1e-9,dual_feasibility_tolerance=1e-9))
    if not r.success:raise RuntimeError(r.message)
    w=np.maximum(r.x[:-1],0.);w*=w0.sum()/w.sum();minimum=float((A@w).min())
    if minimum<r.x[-1]-2e-7 or np.any(w<lower*w0-1e-8) or np.any(w>upper*w0+1e-8):raise RuntimeError('LP residual failure')
    return w,minimum


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--config',type=Path,required=True);a=ap.parse_args()
    cfg=json.loads(a.config.read_text());base=a.config.resolve().parent
    sys.path.insert(0,str((base/cfg['code_dir']).resolve()));sys.path.insert(0,str((base/cfg['research_dir']).resolve()))
    from unified_geometry import expand_primitives,matrix
    from mixed_grid_pricing import screening_poses,quality_metrics,refine_witnesses
    out=base/cfg['out'];out.mkdir(parents=True,exist_ok=False);started=time.perf_counter()
    path=base/cfg['checkpoint'];z=np.load(path,allow_pickle=False);ps=json.loads(str(z['primitives_json']))
    L=float(z['L']);B=float(z['B']);w0=z['weights'].copy();w0*=float(cfg['target'])/w0.sum();w=w0.copy()
    expanded=expand_primitives(ps,F(str(L)))
    def build(q):return sparse.vstack([sparse.csr_matrix(matrix(q[i:i+256],B,expanded)) for i in range(0,len(q),256)],format='csr')
    poses=np.vstack([z['poses'],screening_poses(L,B,count=4096,seed=20276000,boundary_fraction=.25)])
    A=build(poses);keys={tuple(np.round(p,13)) for p in poses};records=[]
    for iteration in range(cfg.get('rounds',3)):
        w,minimum=bounded_weights(A,w0,cfg.get('lower',.9975),cfg.get('upper',1.05))
        q=screening_poses(L,B,count=16384,seed=20276100+iteration,boundary_fraction=.25)
        v=build(q)@w
        refined,rv=refine_witnesses(q,v,L,B,lambda p:build(p)@w,starts=24)
        q=np.vstack([q,refined]);v=np.r_[v,rv]
        records.append(dict(iteration=iteration,rows=len(poses),training_minimum=minimum,screen_minimum=float(v.min()),
                            below_one=int(np.sum(v<1)),elapsed=time.perf_counter()-started))
        (out/'progress.json').write_text(json.dumps(dict(records=records),indent=2)+'\n')
        if iteration==cfg.get('rounds',3)-1 or v.min()>=1.0001:break
        new=[]
        for i in np.argsort(v):
            if v[i]>=1.0001:break
            key=tuple(np.round(q[i],13))
            if key not in keys:keys.add(key);new.append(q[i])
            if len(new)>=128:break
        if not new:break
        A=sparse.vstack([A,build(np.asarray(new))],format='csr');poses=np.vstack([poses,new])
    repair_seconds=time.perf_counter()-started
    np.savez_compressed(out/'resume-state.npz',poses=poses,weights=w,dual=np.zeros(len(poses)),primitives_json=json.dumps(ps),L=L,B=B,rhs=1.001)
    held=screening_poses(L,B,count=65536,seed=20275000,boundary_fraction=.25);held_matrix=build(held);values=held_matrix@w;original_values=held_matrix@w0
    report=dict(status='SAVED_BOUNDED_TEMPLATE_INITIAL',config=cfg,repair_seconds=repair_seconds,
        assessment_seconds=time.perf_counter()-started-repair_seconds,source_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
        source_code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        quality=quality_metrics(values,w.sum(),float(cfg['target'])),certified=False,
        original_quality=quality_metrics(original_values,w0.sum(),float(cfg['target'])))
    (out/'result.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)


if __name__=='__main__':main()
