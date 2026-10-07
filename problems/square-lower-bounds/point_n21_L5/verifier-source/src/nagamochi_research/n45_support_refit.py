"""Finite n45 support-expansion pilot; rational captures, no full certificate."""
from fractions import Fraction as F
from pathlib import Path
from time import perf_counter
import json, math
from motion_pilot import rows
import numpy as np
from scipy.optimize import linprog

ROOT=Path('runs/n45_support_refit_20260926')
def transform(p,g):
    x,y=p
    if g>=4:x,y=y,x
    return (7-x if g%4&1 else x,7-y if g%4&2 else y)

def poses(holdout=False):
    delta=F(1,10**8 if holdout else 10**6)
    for t in ((F(1,5),F(41,100)) if holdout else (F(0),F(1,3),F(2,5))):
        rad=(1+delta)*(1+2*t-t*t)/(2*(1+t*t))
        vals={rad,F(7,2)}|{F(j,4)+(F(1,8) if holdout else 0) for j in range(2,15)}
        vals=sorted(v for v in vals if rad<=v<=F(7,2))
        for x in vals:
            for y in vals:
                if y<=x:yield (x,y,t,delta)

def hit(p,pose):
    x,y,t,d=pose;u,v=p;c=(1-t*t)/(1+t*t);s=2*t/(1+t*t)
    return int(abs(c*(u-x)+s*(v-y))<(1+d)/2 and abs(-s*(u-x)+c*(v-y))<(1+d)/2)

def main():
    start=perf_counter()
    base={transform(p,g) for col in (0,1) for p in rows(7,colour=col) for g in range(8)}
    extra={(F(i,2),F(j,2)) for i in range(1,14) for j in range(1,14)}
    orbits=sorted({tuple(sorted({transform(p,g) for g in range(8)})) for p in base|extra})
    cost=[49]+[len(o) for o in orbits]
    train=list(poses());test=list(poses(True));ps=train+test
    a=[[1]+[sum(hit(p,pose) for p in o) for o in orbits] for pose in ps]
    arr=np.array(a,float);out={}
    for name,cols in [('row_points',[0]+[i+1 for i,o in enumerate(orbits) if o[0] in base]),('plus_half_grid',list(range(len(cost))))]:
        cc=[cost[i] for i in cols]
        lp=linprog(cc,A_ub=-arr[:len(train),cols],b_ub=-np.ones(len(train)),bounds=(0,None),method='highs');assert lp.success
        holdout=float(np.min(arr[len(train):,cols]@lp.x))
        fit=linprog(cc,A_ub=-arr[:,cols],b_ub=-np.ones(len(ps)),bounds=(0,None),method='highs');assert fit.success
        ids=np.flatnonzero(-fit.ineqlin.marginals>1e-9)
        ys=[F(math.floor(float(-fit.ineqlin.marginals[i])*10**10),10**10) for i in ids]
        loads=[sum(y*a[int(i)][j] for y,i in zip(ys,ids)) for j in cols]
        scale=max([F(1)]+[v/c for v,c in zip(loads,cc)]);ys=[y/scale for y in ys]
        assert all(sum(y*a[int(i)][j] for y,i in zip(ys,ids))<=cost[j] for j in cols)
        out[name]=dict(columns=cols,training_mass=float(lp.fun),holdout_minimum=holdout,refit_mass=float(fit.fun),exact_finite_lower_bound=str(sum(ys)),dual=[dict(index=int(i),weight=str(y)) for i,y in zip(ids,ys)],weights=fit.x.tolist())
    result=dict(scope='Finite poses only; strict point capture and D4-invariant weights. Constant charge cost49 is an area-derived upper bound. No all-domain coverage or integer equality.',point_orbits=orbits,costs=cost,poses=ps,training_count=len(train),holdout_count=len(test),models=out,seconds=perf_counter()-start)
    ROOT.mkdir(exist_ok=True);(ROOT/'results.json').write_text(json.dumps(result,default=str,indent=2))
    print(json.dumps(dict(training=len(train),holdout=len(test),seconds=result['seconds'],models={k:{kk:vv for kk,vv in v.items() if kk not in ('columns','weights','dual')} for k,v in out.items()})))
if __name__=='__main__':main()
