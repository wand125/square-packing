"""Small finite n32 comparison; no continuous cover or packing certificate.
D4 orbits are deduplicated as whole rules, each distinct rule costs one.
Every capture decision is rational; LP solutions use floating point and
dual witnesses are quantized and checked with Fraction.
"""
import os
for key in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','VECLIB_MAXIMUM_THREADS'):
    os.environ[key]='1'
from fractions import Fraction as F
from pathlib import Path
from time import perf_counter
import json, math
import numpy as np
from scipy.optimize import linprog
from bridge_probe import charge_atom
from assignment_pilot import points, SCALE

ROOT=Path('runs/bridge_lp_20260926')

def transform(p, g):
    x,y=p
    if g>=4:x,y=y,x
    if g%4&1:x=6-x
    if g%4&2:y=6-y
    return x,y

def canonical_rule(sites,bags):
    return tuple(sorted(tuple(sorted(sites[i] for i in bag)) for bag in bags))

def build(count=6, seeds=None):
    atoms=[charge_atom(seed) for seed in (seeds if seeds is not None else range(62671,62671+count))]
    rules=set()
    for a in atoms:
        sites=[tuple(map(F,p)) for p in a['sites']]
        for g in range(8):
            rules.add(canonical_rule([transform(p,g) for p in sites],a['winning_subsets']))
    rules=sorted(rules)
    original={transform((F(x,SCALE),F(y,SCALE)),g) for c in (0,1) for x,y in points(c) for g in range(8)}
    allpoints=sorted(original|{p for rule in rules for bag in rule for p in bag})
    index={p:i for i,p in enumerate(allpoints)}
    indexed=[[[index[p] for p in bag] for bag in rule] for rule in rules]
    # Each canonical rule has intersecting winning sets, hence global budget 1.
    assert all(set(a)&set(b) for rule in indexed for a in rule for b in rule)
    pointorbits=sorted({tuple(sorted({index[transform(p,g)] for g in range(8)})) for p in allpoints})
    ruleindex={r:i for i,r in enumerate(rules)}
    ruleorbits=sorted({tuple(sorted({ruleindex[tuple(sorted(tuple(sorted(transform(p,g) for p in bag)) for bag in rule))] for g in range(8)})) for rule in rules})
    return atoms,allpoints,indexed,pointorbits,ruleorbits,original

def poses(holdout=False):
    ts=[F(0),F(1,10),F(1,4),F(2,5)] if not holdout else [F(1,19),F(2,13),F(1,3),F(41,100)]
    for t in ts:
        radius=((1-t*t)+2*t)/(2*(1+t*t))
        values={radius,6-radius}
        values.update(F(j,4)+(F(1,8) if holdout else 0) for j in range(2,23))
        for x in sorted(values):
            for y in sorted(values):
                if radius<=y<=x<=3:yield (x,y,t)

def hits_exact(pose,pts):
    x,y,t=pose;c=(1-t*t)/(1+t*t);s=2*t/(1+t*t)
    return [int(abs(c*(u-x)+s*(v-y))<=F(1,2) and abs(-s*(u-x)+c*(v-y))<=F(1,2)) for u,v in pts]

def row_from_hits(h,rs,po,ro):
    fires=[int(any(all(h[i] for i in bag) for bag in rule)) for rule in rs]
    thresholds=[sum(h[i] for i in sorted({j for bag in rule for j in bag}))//3 for rule in rs]
    return [1]+[sum(h[i] for i in orbit) for orbit in po]+[sum(thresholds[i] for i in orbit) for orbit in ro]+[sum(fires[i] for i in orbit) for orbit in ro]

def matrix(ps,pts,rs,po,ro):
    # Fractions in every membership decision; these matrices have integer entries.
    return np.asarray([row_from_hits(hits_exact(p,pts),rs,po,ro) for p in ps],dtype=float)

def solve(a,cost,cols,ps,pts,rs,po,ro):
    costs=np.array([cost[i] for i in cols]);sub=a[:,cols]
    lp=linprog(costs,A_ub=-sub,b_ub=-np.ones(len(a)),bounds=(0,None),method='highs')
    if not lp.success:raise RuntimeError(lp.message)
    ids=np.flatnonzero(-lp.ineqlin.marginals>1e-9)
    ys=[F(math.floor(float(-lp.ineqlin.marginals[i])*10**10),10**10) for i in ids]
    rows=[[int(a[i,j]) for j in cols] for i in ids]
    loads=[sum(y*r[j] for y,r in zip(ys,rows)) for j in range(len(cols))]
    scale=max([F(1)]+[v/F(cost[c]) for v,c in zip(loads,cols)])
    ys=[y/scale for y in ys]
    assert all(sum(y*r[j] for y,r in zip(ys,rows))<=cost[c] for j,c in enumerate(cols))
    return dict(mass=float(lp.fun),exact_finite_lower_bound=str(sum(ys)),
                nonzero_columns=[dict(column=c,weight=float(w)) for c,w in zip(cols,lp.x) if w>1e-9],
                dual=[dict(pose=list(map(str,ps[int(i)])),weight=str(y)) for i,y in zip(ids,ys)]),lp.x

def main():
    started=perf_counter();ROOT.mkdir(exist_ok=False)
    atoms,pts,rs,po,ro,original=build()
    print('built',len(pts),len(rs),flush=True)
    ps=list(poses());hs=list(poses(True));a=matrix(ps,pts,rs,po,ro);h=matrix(hs,pts,rs,po,ro)
    p_end=1+len(po);t_end=p_end+len(ro)
    costs=[36]+[len(o) for o in po]+[2*len(o) for o in ro]+[len(o) for o in ro]
    models={'original_points':[0]+[1+i for i,o in enumerate(po) if pts[o[0]] in original],
            'all_points':list(range(p_end)),
            'points_thresholds':list(range(t_end)),
            'points_thresholds_rules':list(range(len(costs)))}
    results={}
    for name,cols in models.items():
        r,w=solve(a,costs,cols,ps,pts,rs,po,ro)
        r['holdout_minimum_before_refit']=float(np.min(h[:,cols]@w))
        both=np.vstack([a,h]);rr,ww=solve(both,costs,cols,ps+hs,pts,rs,po,ro)
        r['combined']=rr;results[name]=r
        print(name,r['mass'],r['holdout_minimum_before_refit'],rr['mass'],flush=True)
    out=dict(atoms=atoms,points=[[str(x),str(y)] for x,y in pts],rules=rs,point_orbits=po,rule_orbits=ro,
             costs=costs,models=models,results=results,training_poses=len(ps),holdout_poses=len(hs),seconds=perf_counter()-started,
             scope='Exact rational memberships and finite dual bounds. Primal weights float; no full coverage.')
    (ROOT/'results.json').write_text(json.dumps(out,indent=2))
    print('seconds',out['seconds'],flush=True)

if __name__=='__main__':main()
