"""Coherent grid-pattern LP, expanded back into ordinary nonnegative primitives.

Pattern columns couple weights of spatially related supports. This is a search
restriction, never an assumption about the packing or a certificate by itself.
"""
import os
for name in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMBA_NUM_THREADS'):os.environ[name]='1'
import argparse,json,time,sys,hashlib
from pathlib import Path
from fractions import Fraction as F
from collections import Counter
import numpy as np
from scipy import sparse
from unified_measure import primitive_key


def pattern_dictionary(L,k):
    L=F(str(L)); margin=F(1,1000)
    if not 3<=k<=100 or not 1<L:raise ValueError('invalid grid geometry')
    primitives=[];lookup={};patterns=[];names=[]
    def pattern(name,items):
        counts=Counter()
        for kind,g in items:
            coords=g[:2] if kind in ('disk','annulus') else g
            if not all(0<=v<=L for v in coords):continue
            key=primitive_key(kind,g,L)
            if key not in lookup:
                lookup[key]=len(primitives)
                primitives.append(dict(kind=kind,geometry=list(map(str,g)),family='grid_pattern'))
            counts[lookup[key]]+=1
        if counts:
            patterns.append({i:v/sum(counts.values()) for i,v in counts.items()});names.append(name)
    pattern('uniform',[('rectangle',(F(0),F(0),L,L))])
    for family,lines in [('scaled',[L*j/k for j in range(1,k)]),
                         ('wall',[1+j*(L-2)/(k-2) for j in range(k-1)]),
                         ('phase_plus',[L*j/k+L/k/40 for j in range(1,k)]),
                         ('phase_minus',[L*j/k-L/k/40 for j in range(1,k)])]:
        groups={}
        def add(kind,g,x,y,label):
            shell=max(0,int(min(x,L-x,y,L-y)))
            groups.setdefault((label,shell),[]).append((kind,g))
        for x in lines:
            for y in lines:
                add('point',(x,y),x,y,'point')
                for r in (F(3,200),F(3,50)):
                    add('disk',(x,y,r),x,y,f'disk-{r}')
                    add('annulus',(x,y,r,F(9,10)),x,y,f'annulus-{r}')
            edges=[margin]+lines+[L-margin]
            for a,b in zip(edges,edges[1:]):
                if a>=b:continue
                add('segment',(x,a,x,b),x,(a+b)/2,'segment')
                for w in (F(1,1000),F(1,200),F(1,50),F(3,50)):
                    add('rectangle',(x-w,a,x+w,b),x,(a+b)/2,f'band-{w}')
        for (label,shell),items in groups.items():pattern(f'{family}/{label}/shell-{shell}',items)
    rows=[];cols=[];values=[]
    for j,p in enumerate(patterns):
        for i,v in p.items():rows.append(i);cols.append(j);values.append(v)
    P=sparse.csr_matrix((values,(rows,cols)),shape=(len(primitives),len(patterns)))
    return primitives,P,names


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--config',type=Path,required=True);args=ap.parse_args()
    cfg=json.loads(args.config.read_text());base=args.config.resolve().parent
    sys.path.insert(0,str((base/cfg['code_dir']).resolve()))
    sys.path.insert(0,str((base/cfg['research_dir']).resolve()))
    from unified_geometry import expand_primitives,matrix
    from mixed_grid_pricing import initial_state,screening_poses,quality_metrics
    from unified_grid_search import solve_matrix
    out=base/cfg['out'];out.mkdir(parents=True,exist_ok=False);start=time.perf_counter();records=[]
    def write(name,data):(out/name).write_text(json.dumps(data,indent=2)+'\n')
    def log(**data):
        data['elapsed']=time.perf_counter()-start;records.append(data);write('progress.json',dict(records=records));print(json.dumps(data),flush=True)
    L=F(cfg['L']);B=.9977;rhs=1.001
    if not 0<float(cfg['target'])<cfg['n']:raise ValueError('invalid budget')
    primitives,P,names=pattern_dictionary(L,cfg['k']);expanded=expand_primitives(primitives,L)
    write('manifest.json',dict(config=cfg,source_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__),Path(__file__).with_name('mixed_grid_pricing.py'),Path(__file__).with_name('unified_geometry.py')]},certified=False))
    poses=np.vstack([initial_state(L)[1],screening_poses(L,count=cfg.get('training_samples',32768),seed=20264000,boundary_fraction=.25)])
    parts=[]
    for i in range(0,len(poses),128):
        A=matrix(poses[i:i+128],B,expanded)@P
        A[abs(A)<1e-12]=0;parts.append(sparse.csr_matrix(A))
    A=sparse.vstack(parts,format='csr');log(operation='matrix',rows=A.shape[0],patterns=A.shape[1],primitives=len(primitives))
    sol,report=solve_matrix(A,poses,rhs,np.zeros(len(poses)))
    weights=np.asarray(P@sol.weights).ravel()
    np.testing.assert_allclose(weights.sum(),sol.mass,rtol=1e-12)
    log(operation='lp',mass=sol.mass,minimum=sol.min_coverage,seconds=sol.seconds)
    active=np.flatnonzero(weights>0);active_expanded=expand_primitives([primitives[i] for i in active],L)
    holdout=screening_poses(L,count=16384,seed=20263000,boundary_fraction=.25)
    values=np.concatenate([matrix(holdout[i:i+256],B,active_expanded)@weights[active] for i in range(0,len(holdout),256)])
    quality=quality_metrics(values,sol.mass,float(cfg['target']));write('quality.json',quality)
    # Pattern dual is not a feasible dual for the expanded free dictionary.
    # Store zero as the ordinary row-selection seed, never mislabel it optimal.
    np.savez_compressed(out/'resume-state.npz',poses=poses,weights=weights,dual=np.zeros(len(poses)),primitives_json=json.dumps(primitives),L=float(L),B=B,rhs=rhs)
    np.savez_compressed(out/'pattern-solution.npz',weights=sol.weights,dual=sol.dual)
    sparse.save_npz(out/'pattern-map.npz',P);write('patterns.json',names)
    log(operation='finish',status='SAVED_PATTERN_INITIAL',quality=quality,globally_verified=False)


if __name__=='__main__':main()
