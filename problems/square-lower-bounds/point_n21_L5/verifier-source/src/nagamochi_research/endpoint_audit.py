"""Audit the equality route for the saved finite n32 LP solution.
Exact finite scores and one enlarged-square witness, not a global cover.
"""
from fractions import Fraction as F
from pathlib import Path
import json
from bridge_lp import hits_exact,row_from_hits,poses
from bridge_contact import contact_poses

ROOT=Path('runs/endpoint_route_20260926')

def main():
    root=Path('runs/bridge_selected_20260926');d=json.loads((root/'results.json').read_text())
    old=json.loads(Path('runs/bridge_lp_20260926/results.json').read_text())
    pts=[tuple(map(F,p)) for p in d['points']];rs=d['rules'];po=d['point_orbits'];ro=d['rule_orbits']
    weights={w['column']:F(w['weight']).limit_denominator(10**6) for w in d['results']['points_thresholds_rules']['nonzero_columns']}
    assert all(0<j<1+len(po) for j in weights), 'This diagnostic expects a point-only selected optimum'
    mass=sum(w*d['costs'][j] for j,w in weights.items());assert mass==32
    active={i:weights[1+j] for j,o in enumerate(po) if 1+j in weights for i in o}
    ps=list(poses())+list(poses(True))+contact_poses([tuple(map(F,p)) for p in old['points']])
    scores=[];witness=None
    for x,y,t in ps:
        h=hits_exact((x,y,t),pts);score=sum(w*h[i] for i,w in active.items());scores.append(score)
        if score!=1 or witness is not None:continue
        c=(1-t*t)/(1+t*t);s=2*t/(1+t*t);side=1+F(1,10**6);radius=side*(abs(c)+abs(s))/2
        if not (radius<=x<=6-radius and radius<=y<=6-radius):continue
        enlarged=sum(w for i,w in active.items() if abs(c*(pts[i][0]-x)+s*(pts[i][1]-y))<=side/2 and abs(-s*(pts[i][0]-x)+c*(pts[i][1]-y))<=side/2)
        if enlarged==1:witness=dict(cx=str(x),cy=str(y),t=str(t),side=str(side),score=str(enlarged))
    assert min(scores)>=1 and witness is not None
    out=dict(mass=str(mass),poses=len(ps),minimum=str(min(scores)),tight_poses=scores.count(1),active_points=len(active),point_weights=[dict(point=list(map(str,pts[i])),weight=str(w)) for i,w in active.items()],enlarged_tight_witness=witness,scope='Finite point cover of mass exactly 32; global coverage not verified. Witness disproves per-square strict excess for these weights, not packing-level rigidity.')
    ROOT.mkdir(exist_ok=True);(ROOT/'results.json').write_text(json.dumps(out,indent=2));print(json.dumps({k:v for k,v in out.items() if k!='point_weights'}))

if __name__=='__main__':main()
