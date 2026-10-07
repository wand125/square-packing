"""Exact obstruction to using grid-avoider COUNT alone for n21 -> 5.

Five enlarged squares can coexist without capturing any internal grid point.
This is not a packing of 21 squares; interactions with the other boxes matter.
"""
from fractions import Fraction as F
from itertools import combinations
from pathlib import Path
import json
from score import square, cross, sub


def separation(a, b):
    for poly in (a,b):
        for p,q in zip(poly,poly[1:]+poly[:1]):
            dx,dy=sub(q,p);axis=(-dy,dx)
            aa=[sum(u*v for u,v in zip(axis,z)) for z in a]
            bb=[sum(u*v for u,v in zip(axis,z)) for z in b]
            if max(aa)<=min(bb):return dict(axis=list(map(str,axis)),left_max=str(max(aa)),right_min=str(min(bb)))
            if max(bb)<=min(aa):return dict(axis=list(map(str,axis)),left_max=str(max(bb)),right_min=str(min(aa)))
    return None


def probe():
    centres=[(F(3,2),F(3,2)),(F(3,2),F(7,2)),(F(5,2),F(5,2)),(F(7,2),F(3,2)),(F(7,2),F(7,2))]
    side=F(6,5);t=F(2,5);polys=[square(x,y,side,t) for x,y in centres]
    grid=[(F(i),F(j)) for i in range(1,5) for j in range(1,5)]
    for poly in polys:
        assert all(0<=x<=5 and 0<=y<=5 for x,y in poly)
        assert all(not all(cross(sub(b,a),sub(p,a))>0 for a,b in zip(poly,poly[1:]+poly[:1])) for p in grid)
    pairs=[]
    for i,j in combinations(range(5),2):
        proof=separation(polys[i],polys[j]);assert proof is not None
        pairs.append(dict(i=i,j=j,**proof))
    return dict(status='EXACT_FIVE_GRID_AVOIDERS',L='5',side=str(side),t=str(t),
                centres=[list(map(str,p)) for p in centres],pair_separations=pairs,
                grid_points=16,minimum_grid_avoiders_if_21_boxes=5,
                conclusion='The necessary five grid-avoiding boxes are not contradictory by themselves. A proof must also constrain coexistence with grid-capturing boxes.',
                limitation='Not a packing of 21 enlarged squares and not a counterexample to s(21)=5.')


if __name__=='__main__':
    result=probe();out=Path('runs/mixed_endpoint_bridge_20260927/grid-joint-probe.json')
    out.parent.mkdir(parents=True,exist_ok=True)
    with out.open('x') as f:json.dump(result,f,indent=2)
    print(result['status'],result['conclusion'])
