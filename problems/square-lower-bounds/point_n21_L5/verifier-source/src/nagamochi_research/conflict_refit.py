"""Refit dual-derived rank rules on the same 2667 exact rational poses."""
import json,math
from pathlib import Path
from fractions import Fraction as F
from time import perf_counter
import numpy as np
from scipy.optimize import linprog
from conflict_rank_lp import orbit
import bridge_lp as b
from bridge_contact import contact_poses

ROOT=Path('runs/conflict_refit_20260926')

def main():
    import argparse
    ap=argparse.ArgumentParser();ap.add_argument("--batch",action="store_true");ap.add_argument("--deficits",action="store_true");args=ap.parse_args()
    root=ROOT if not args.batch else ROOT.with_name(ROOT.name+"_batch")
    if args.deficits:root=root.with_name(root.name+"_deficits")
    guided=Path("runs/conflict_guided_dual_20260926"+("_batch" if args.batch else ""))
    start=perf_counter();root.mkdir(exist_ok=False)
    old=json.loads((b.ROOT/'results.json').read_text());base=json.loads(Path('runs/bridge_selected_20260926/results.json').read_text());previous=json.loads(Path('runs/conflict_rank_20260926/lp.json').read_text());new=json.loads((guided/'results.json').read_text())
    pts=[tuple(map(F,p)) for p in base['points']];idx={p:i for i,p in enumerate(pts)}
    orbits=previous['new_orbits'][:];ranks=[1]*previous['pair_orbits']+[2]*previous['rank_orbits'];costs=previous['costs'][:];end=len(costs)
    for rule in new['best']:
        bags=[[tuple(map(F,p)) for p in bag] for bag in rule['bags']]
        images=sorted(orbit(bags));orbits.append([[[idx[p] for p in bag] for bag in r] for r in images]);ranks.append(rule['rank']);costs.append(rule['rank']*len(images))
    ps=list(b.poses())+list(b.poses(True))+contact_poses([tuple(map(F,p)) for p in old['points']]);rows=[]
    if args.deficits:
        deficits=json.loads(Path('runs/endpoint_cells_20260926/results.json').read_text())
        ps += [(F(w['cx']),F(w['cy']),F(w['t'])) for w in deficits['records'] if 'score' in w]
    for pose in ps:
        h=b.hits_exact(pose,pts);row=b.row_from_hits(h,base['rules'],base['point_orbits'],base['rule_orbits'])
        row += [sum(any(all(h[i] for i in bag) for bag in rule) for rule in o) for o in orbits];rows.append(row)
    a=np.array(rows,dtype=float);results={}
    for name,cols in [('previous',list(range(end))),('guided_clique',list(range(end+sum(r['kind']=='clique' for r in new['best'])))),('guided_both',list(range(len(costs))))]:
        lp=linprog([costs[j] for j in cols],A_ub=-a[:,cols],b_ub=-np.ones(len(rows)),bounds=(0,None),method='highs');assert lp.success
        ids=np.flatnonzero(-lp.ineqlin.marginals>1e-9);ys=[F(math.floor(float(-lp.ineqlin.marginals[i])*10**10),10**10) for i in ids]
        loads=[sum(y*rows[int(i)][j] for i,y in zip(ids,ys)) for j in cols];scale=max([F(1)]+[v/F(costs[j]) for j,v in zip(cols,loads)]);ys=[y/scale for y in ys]
        r=dict(mass=float(lp.fun),lower_bound=str(sum(ys)),columns=cols,weights=[float(w) for w in lp.x],dual=[dict(pose=list(map(str,ps[int(i)])),weight=str(y)) for i,y in zip(ids,ys)])
        assert all(sum(y*rows[int(i)][j] for i,y in zip(ids,ys))<=costs[j] for j in cols)
        results[name]=r;print(name,r['mass'],'new weights',r['weights'][end:],flush=True)
    out=dict(base='runs/bridge_selected_20260926/results.json',orbits=orbits,ranks=ranks,costs=costs,poses=len(ps),results=results,seconds=perf_counter()-start)
    (root/'results.json').write_text(json.dumps(out,indent=2));print('seconds',out['seconds'],flush=True)

if __name__=='__main__':main()
