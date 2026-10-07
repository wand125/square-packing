"""Refit dual-priced candidates, controlling for the added point support."""
import json
from fractions import Fraction as F
from pathlib import Path
from time import perf_counter
import bridge_lp as b
from bridge_contact import contact_poses

ROOT=Path('runs/bridge_selected_20260926')

def main():
    start=perf_counter();ROOT.mkdir(exist_ok=False)
    old=json.loads((b.ROOT/'results.json').read_text());pricing=json.loads((b.ROOT/'candidate-pricing.json').read_text())
    selected=[r['seed'] for r in pricing['records'] if F(r['reduced_cost'])<0]
    atoms,pts,rs,po,ro,original=b.build(seeds=list(range(62671,62677))+selected)
    # Keep exactly the same pose set for every model, including old-support control.
    ps=list(b.poses())+list(b.poses(True))+contact_poses([tuple(map(F,p)) for p in old['points']])
    a=b.matrix(ps,pts,rs,po,ro);pe=1+len(po);te=pe+len(ro)
    costs=[36]+[len(o) for o in po]+[2*len(o) for o in ro]+[len(o) for o in ro]
    oldpoints={tuple(map(F,p)) for p in old['points']}
    models={'old_points':[0]+[1+i for i,o in enumerate(po) if pts[o[0]] in oldpoints],
            'all_points':list(range(pe)),'points_thresholds':list(range(te)),
            'points_thresholds_rules':list(range(len(costs)))}
    results={}
    for name,cols in models.items():
        result,w=b.solve(a,costs,cols,ps,pts,rs,po,ro);results[name]=result
        print(name,result['mass'],flush=True)
    out=dict(selected_seeds=selected,atoms=atoms,points=[[str(x),str(y)] for x,y in pts],rules=rs,point_orbits=po,rule_orbits=ro,costs=costs,models=models,results=results,poses=len(ps),seconds=perf_counter()-start,scope='Same finite pose set; no global certificate.')
    (ROOT/'results.json').write_text(json.dumps(out,indent=2));print('seconds',out['seconds'],flush=True)

if __name__=='__main__':main()
