"""Fit a convex mixture of initial measures on a separate training corpus."""
import os
for name in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMBA_NUM_THREADS'):os.environ[name]='1'
import argparse,json,sys,time,hashlib
from pathlib import Path
from fractions import Fraction as F
import numpy as np
from scipy.optimize import linprog
from unified_measure import primitive_key


def minimax_blend(scores):
    C=np.asarray(scores,float)
    if C.ndim!=2 or not min(C.shape) or not np.isfinite(C).all():raise ValueError('invalid scores')
    n=C.shape[1]
    r=linprog(np.r_[np.zeros(n),-1.],A_ub=np.c_[-C,np.ones(len(C))],b_ub=np.zeros(len(C)),
        A_eq=np.array([np.r_[np.ones(n),0.]]),b_eq=[1.],bounds=[(0.,1.)]*n+[(None,None)],method='highs')
    if not r.success:raise RuntimeError(r.message)
    alpha=np.maximum(r.x[:-1],0.);alpha/=alpha.sum()
    return alpha,float((C@alpha).min())


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--config',type=Path,required=True);a=ap.parse_args()
    cfg=json.loads(a.config.read_text());base=a.config.resolve().parent
    sys.path.insert(0,str((base/cfg['code_dir']).resolve()));sys.path.insert(0,str((base/cfg['research_dir']).resolve()))
    from unified_geometry import expand_primitives,matrix
    from mixed_grid_pricing import screening_poses,quality_metrics
    from radial_pricing import physical_poses
    out=base/cfg['out'];out.mkdir(parents=True,exist_ok=False);started=time.perf_counter()
    states=[];hashes=[]
    for name in cfg['states']:
        path=base/name;z=np.load(path,allow_pickle=False);ps=json.loads(str(z['primitives_json']))
        states.append((ps,z['weights'],z['poses'],float(z['L']),float(z['B'])))
        hashes.append(hashlib.sha256(path.read_bytes()).hexdigest())
    L,B=states[0][3:];target=float(cfg['target'])
    if any((s[3],s[4])!=(L,B) for s in states):raise ValueError('state geometry mismatch')
    if not 0<target<cfg['n']:raise ValueError('invalid target')
    training=screening_poses(L,B,count=32768,seed=20271000,boundary_fraction=.25)
    catalog=None
    if cfg.get('pose_catalog'):
        path=base/cfg['pose_catalog'];catalog=physical_poses(np.load(path,allow_pickle=False)['poses'],L,B)
        training=np.vstack([training,catalog])
    def values(ps,w,poses):
        ids=np.flatnonzero(w>0);expanded=expand_primitives([ps[i] for i in ids],F(str(L)))
        return np.concatenate([matrix(poses[i:i+256],B,expanded)@w[ids] for i in range(0,len(poses),256)])
    C=np.column_stack([values(ps,w*target/w.sum(),training) for ps,w,*_ in states])
    alpha,minimum=minimax_blend(C)
    lookup={};primitives=[];weights=[]
    for ratio,(ps,w,*_) in zip(alpha,states):
        if ratio==0:continue
        for p,v in zip(ps,w*target/w.sum()*ratio):
            if v<=0:continue
            key=primitive_key(p['kind'],p['geometry'],F(str(L)))
            if key not in lookup:lookup[key]=len(primitives);primitives.append(p);weights.append(0.)
            weights[lookup[key]]+=float(v)
    weights=np.array(weights);weights*=target/weights.sum()
    np.testing.assert_allclose(values(primitives,weights,training[:128]),(C@alpha)[:128],rtol=1e-10,atol=1e-10)
    poses=np.unique(np.vstack([training]+[s[2] for s in states]),axis=0)
    np.savez_compressed(out/'resume-state.npz',poses=poses,weights=weights,dual=np.zeros(len(poses)),primitives_json=json.dumps(primitives),L=L,B=B,rhs=1.001)
    held=screening_poses(L,B,count=131072,seed=20268000,boundary_fraction=.25)
    report=dict(status='SAVED_MIXTURE_INITIAL',ratios=alpha.tolist(),training_minimum=minimum,training_rows=len(training),
        quality=quality_metrics(values(primitives,weights,held),weights.sum(),target),certified=False,
        state_sha256=hashes,source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    if catalog is not None:report['catalog_quality']=quality_metrics(values(primitives,weights,catalog),weights.sum(),target)
    report['seconds']=time.perf_counter()-started
    (out/'result.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)


if __name__=='__main__':main()
