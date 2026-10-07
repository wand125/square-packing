"""Exact geometric point domination test for convex-square rule traces.
For each fixed angle, square centres capturing a bag form a rectangle in
rotated coordinates. Its corners determine points captured by every such square.
This finite-angle diagnostic is not an all-angle domination proof.
"""
from fractions import Fraction as F
import json
from bridge_lp import ROOT, transform


def mandatory(bag,pts,t):
    c=(1-t*t)/(1+t*t);s=2*t/(1+t*t)
    rot=lambda p:(c*p[0]+s*p[1],-s*p[0]+c*p[1])
    q=[rot(pts[i]) for i in bag]
    lo=[max(p[j] for p in q)-F(1,2) for j in (0,1)]
    hi=[min(p[j] for p in q)+F(1,2) for j in (0,1)]
    if any(a>b for a,b in zip(lo,hi)):return None
    # Full plane centre rectangle: ignoring container only strengthens domination.
    return {i for i,p in enumerate(pts) if all(hi[j]-F(1,2)<=rot(p)[j]<=lo[j]+F(1,2) for j in (0,1))}


def main():
    d=json.loads((ROOT/'results.json').read_text());pts=[tuple(map(F,p)) for p in d['points']]
    ts=[F(0),F(1,1000000),F(1,19),F(1,10),F(2,13),F(1,4),F(1,3),F(2,5),F(41,100)]
    records=[]
    for orbit in d['rule_orbits']:
        r=d['rules'][orbit[0]];records_by_angle=[];universal=set(range(len(pts)))
        for t in ts+[-t for t in ts if t]:
            sets=[mandatory(b,pts,t) for b in r];feasible=[v for v in sets if v is not None]
            shared=set.intersection(*feasible) if feasible else set(range(len(pts)))
            universal &= shared
            records_by_angle.append(dict(t=str(t),feasible_bags=len(feasible),common_points=sorted(shared)))
        records.append(dict(rule=orbit[0],orbit_size=len(orbit),fixed_point_dominators=sorted(universal),angles=records_by_angle))
    out=dict(rules=records,scope='Exact full-plane fixed-angle domination; angles finite, not global domination.')
    (ROOT/'dominance.json').write_text(json.dumps(out,indent=2))
    print(json.dumps([dict(rule=r['rule'],fixed_points=r['fixed_point_dominators'],angles_with_common_point=sum(bool(a['common_points']) for a in r['angles'])) for r in records]))

if __name__=='__main__':main()
