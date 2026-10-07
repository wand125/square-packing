"""Finite rational checks and exact dual bounds for four class weights.

Does not certify global packing bounds or the full Nagamochi theorem.
"""
import os
for name in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS'):
    os.environ[name]='1'
from fractions import Fraction as F
import argparse,json,math
from pathlib import Path
from time import perf_counter
import numpy as np
from scipy.optimize import linprog
from score import square,features,template,WEIGHTS


def samples(k):
    for delta in (F(1,100),F(1,10000),F(1,1000000)):
        side=1+delta
        for t in (F(0),F(1,10),F(1,4),F(2,5),F(41,100)):
            radius=side*((1-t*t)+2*t)/(2*(1+t*t))
            # Corners, side bands, central positions and both sides of point contacts.
            values={radius,k-radius,F(k,2),F(1),F(k-1),radius+delta,k-radius-delta}
            for j in range(1,2*k):
                for shift in (F(0),delta,-delta):
                    x=F(j,2)+shift
                    if radius <= x <= k-radius:
                        values.add(x)
            values=sorted(x for x in values if radius<=x<=k-radius)
            # D4 symmetry is exact for this template; only a wedge is needed here.
            for x in values:
                for y in values:
                    if y<=x<=F(k,2):
                        yield dict(k=k,delta=delta,t=t,cx=x,cy=y),square(x,y,side,t)


def analyse(k):
    started=perf_counter();rows=[];poses=[];minimum=None;argmin=None
    for pose,poly in samples(k):
        row=features(k,poly);value=sum(a*b for a,b in zip(row,WEIGHTS))
        if minimum is None or value<minimum:
            minimum,argmin=value,pose
        if value<=1:
            raise AssertionError(('baseline finite counterexample',pose,str(value)))
        rows.append(row);poses.append(pose)
    costs=template(k)[3]
    # Primal: min costs.w, A.w >= 1. Dual: max sum(y), A.T.y <= costs.
    a=np.array([[float(x) for x in row] for row in rows])
    lp=linprog([float(x) for x in costs],A_ub=-a,b_ub=-np.ones(len(rows)),bounds=(0,None),method='highs')
    if not lp.success:
        raise RuntimeError(lp.message)
    raw=-lp.ineqlin.marginals
    ids=np.flatnonzero(raw>1e-10)
    # Downward quantization followed by an exact common feasibility correction.
    weights=[F(math.floor(float(raw[i])*10**12),10**12) for i in ids]
    used=[sum(y*rows[int(i)][j] for i,y in zip(ids,weights)) for j in range(4)]
    scale=max([F(1)]+[v/c for v,c in zip(used,costs) if c])
    weights=[y/scale for y in weights]
    used=[sum(y*rows[int(i)][j] for i,y in zip(ids,weights)) for j in range(4)]
    assert all(v<=c for v,c in zip(used,costs)) and all(y>=0 for y in weights)
    bound=sum(weights)
    witnesses=[dict(pose=poses[int(i)],features=rows[int(i)],dual_weight=y) for i,y in zip(ids,weights)]
    return dict(k=k,samples=len(rows),minimum_baseline=minimum,argmin=argmin,
                original_mass=k*k-2,optimized_mass_float=float(lp.fun),class_weights=lp.x.tolist(),
                exact_finite_model_lower_bound=bound,exact_dual_loads=used,costs=costs,
                dual_witnesses=witnesses,seconds=perf_counter()-started,
                scope='Only this fixed geometry with four D4-invariant class weights; no global impossibility claim.')


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--ks',nargs='+',type=int,default=list(range(4,11)))
    ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=False)
    for k in a.ks:
        result=analyse(k)
        (a.out/f'k{k}.json').write_text(json.dumps(result,default=str,indent=2))
        print(json.dumps({x:result[x] for x in ['k','samples','optimized_mass_float','exact_finite_model_lower_bound','seconds']},default=str),flush=True)


if __name__=='__main__':
    main()
