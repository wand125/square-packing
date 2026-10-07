"""Compare geometric pair-union charges and odd-cycle rank-union charges.
All models share rational poses and point support; exact finite duals saved.
"""
import json,math
from fractions import Fraction as F
from time import perf_counter
import numpy as np
from scipy.optimize import linprog
from conflict_rank import ROOT
import bridge_lp as b
from bridge_contact import contact_poses


def canon(bags):return tuple(sorted(tuple(sorted(bag)) for bag in bags))

def orbit(rule):return {canon([[b.transform(p,g) for p in bag] for bag in rule]) for g in range(8)}

def main():
    start=perf_counter();base=json.loads(__import__('pathlib').Path('runs/bridge_selected_20260926/results.json').read_text())
    old=json.loads((b.ROOT/'results.json').read_text());data=json.loads((ROOT/'rules.json').read_text())
    pts=[tuple(map(F,p)) for p in base['points']];idx={p:i for i,p in enumerate(pts)}
    ranks=set();pairs=set()
    for cycle in data['cycles']:
        bags=[[tuple(map(F,p)) for p in bag] for bag in cycle['bags']]
        ranks.update(orbit(bags))
        for i,j in cycle['edges']:pairs.update(orbit([bags[i],bags[j]]))
    rank_orbits=sorted({tuple(sorted(orbit(r))) for r in ranks});pair_orbits=sorted({tuple(sorted(orbit(r))) for r in pairs})
    neworbits=pair_orbits+rank_orbits
    indexed=[[[[idx[p] for p in bag] for bag in rule] for rule in o] for o in neworbits]
    costs=base['costs']+[len(o) for o in pair_orbits]+[2*len(o) for o in rank_orbits]
    ps=list(b.poses())+list(b.poses(True))+contact_poses([tuple(map(F,p)) for p in old['points']])
    rows=[]
    for pose in ps:
        hits=b.hits_exact(pose,pts);row=b.row_from_hits(hits,base['rules'],base['point_orbits'],base['rule_orbits'])
        row += [sum(any(all(hits[i] for i in bag) for bag in rule) for rule in o) for o in indexed]
        rows.append(row)
    a=np.asarray(rows,dtype=float);end=len(base['costs']);pe=end+len(pair_orbits)
    models={'existing':list(range(end)),'pair_cliques':list(range(pe)),'rank_cycles':list(range(len(costs)))};results={}
    for name,cols in models.items():
        c=[costs[i] for i in cols];lp=linprog(c,A_ub=-a[:,cols],b_ub=-np.ones(len(a)),bounds=(0,None),method='highs');assert lp.success
        ids=np.flatnonzero(-lp.ineqlin.marginals>1e-9);ys=[F(math.floor(float(-lp.ineqlin.marginals[i])*10**10),10**10) for i in ids]
        loads=[sum(y*rows[int(i)][j] for y,i in zip(ys,ids)) for j in cols];scale=max([F(1)]+[v/F(costs[j]) for v,j in zip(loads,cols)])
        ys=[y/scale for y in ys];assert all(sum(y*rows[int(i)][j] for y,i in zip(ys,ids))<=costs[j] for j in cols)
        r=dict(mass=float(lp.fun),lower_bound=str(sum(ys)),new_nonzero=[dict(column=j,weight=float(w)) for j,w in zip(cols,lp.x) if j>=end and w>1e-9],dual=[dict(pose=list(map(str,ps[int(i)])),weight=str(y)) for i,y in zip(ids,ys)])
        results[name]=r;print(name,r['mass'],r['new_nonzero'],flush=True)
        if name=='pair_cliques':
            pricing=[]
            for j in range(pe,len(costs)):
                load=sum(y*rows[int(i)][j] for y,i in zip(ys,ids))
                pricing.append(dict(orbit=j-pe,cost=costs[j],dual_load=str(load),reduced_cost=str(costs[j]-load)))
            (ROOT/'pricing.json').write_text(json.dumps(pricing,indent=2))
    result=dict(base='runs/bridge_selected_20260926/results.json',poses=len(ps),pair_orbits=len(pair_orbits),rank_orbits=len(rank_orbits),new_orbits=indexed,costs=costs,models=models,results=results,seconds=perf_counter()-start)
    (ROOT/'lp.json').write_text(json.dumps(result,indent=2));print('seconds',result['seconds'],flush=True)

if __name__=='__main__':main()
