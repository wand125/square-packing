"""PL21: robust half-plane intersection common to a whole pose box."""
from fractions import Fraction as F
from endpoint_cells import clip_linear
from mixed_density_check import polygon_score,pose_lower_bound


def common_polygon(model,x0,x1,y0,y1,t0,t1):
    if x0>x1 or y0>y1 or not F(-1,2)<=t0<=t1<=F(1,2):raise ValueError('Invalid box')
    L,B=model[:2]
    cs=[(1-t*t)/(1+t*t) for t in (t0,t1)]
    cvals={min(cs),F(1) if t0<=0<=t1 else max(cs)}
    svals={2*t/(1+t*t) for t in (t0,t1)}
    poly=[(F(0),F(0)),(L,F(0)),(L,L),(F(0),L)]
    constraints=set()
    for c in cvals:
        for s in svals:
            for a,b in ((c,s),(-s,c),(-c,-s),(s,-c)):
                rhs=B/2+min(a*x0,a*x1)+min(b*y0,b*y1)
                constraints.add((a,b,rhs))
    for a,b,rhs in sorted(constraints):
        poly=clip_linear(poly,-a,-b,-rhs)
        if not poly:break
    return poly


def polygon_lower_bound(model,*box):
    poly=common_polygon(model,*box)
    d,a=polygon_score(poly,model[2],model[3]);return d+a


def best_lower_bound(model,*box):
    # Both bounds are valid independently; taking the maximum is safe.
    return max(pose_lower_bound(model,*box),polygon_lower_bound(model,*box))
