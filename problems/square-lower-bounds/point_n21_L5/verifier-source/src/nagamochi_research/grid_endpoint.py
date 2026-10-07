"""A delta-uniform necessary condition for packing 32 enlarged squares.
Exact rational checks accompany the symbolic grid-witness argument.
"""
from fractions import Fraction as F
from pathlib import Path
import json


def grid_witness(cx,cy,side,t,k=6):
    c=(1-t*t)/(1+t*t);s=2*t/(1+t*t)
    width=side/(abs(c)+abs(s))
    if width<=1:return None
    # The centred axis-parallel inscribed square has side width>1.
    def integer_inside(z):
        low=z-width/2;high=z+width/2
        candidates=[i for i in range(1,k) if low<i<high]
        assert candidates
        return candidates[0]
    p=(integer_inside(cx),integer_inside(cy))
    assert abs(c*(p[0]-cx)+s*(p[1]-cy))<side/2
    assert abs(-s*(p[0]-cx)+c*(p[1]-cy))<side/2
    return p


def main():
    root=Path('runs/grid_endpoint_20260926');root.mkdir(exist_ok=True);checks=0
    for delta in (F(1,1000),F(1,10**6),F(1,10**9)):
        for t in (F(0),delta/10,delta/4):
            side=1+delta;c=(1-t*t)/(1+t*t);s=2*t/(1+t*t);r=side*(abs(c)+abs(s))/2
            assert side>abs(c)+abs(s)
            for x in (r,F(3,2),F(3),6-r):
                for y in (r,F(3,2),F(3),6-r):
                    assert grid_witness(x,y,side,t) is not None;checks+=1
    out=dict(checks=checks,grid_points=25,maximum_grid_capturing_disjoint_boxes=25,necessary_grid_avoiding_boxes_for_n32=7,
             condition='After reducing orientation to theta in [0,pi/4], every grid-avoiding box must satisfy 1+delta <= cos(theta)+sin(theta).',
             rational_form='2*t*(1-t) >= delta*(1+t*t), t=tan(theta/2).',
             scope='Symbolic necessary condition valid for every delta>0; not sufficient to rule out 32 boxes. Samples only test the implementation.')
    (root/'results.json').write_text(json.dumps(out,indent=2));print(json.dumps(out))

if __name__=='__main__':main()
