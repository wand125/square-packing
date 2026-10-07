"""PL27: per-density-component vertex minima for a translated convex core.

Brunn--Minkowski gives quasi-concavity of overlap volume under translation.
We sum minima PER rectangle; taking the minimum of total vertex scores would
not in general be valid for a mixture of densities.
"""
from fractions import Fraction as F
from robust_pose_core import common_polygon
from score import area, clip, contains


def translated_lower_bound(model,x0,x1,y0,y1,t0,t1):
    return _translated_bound(common_polygon,model,x0,x1,y0,y1,t0,t1)


def translated_correlated_lower_bound(model,*box):
    """PL27 with the stronger PL28 rotation common core; same centre hull."""
    from correlated_pose_core import correlated_polygon
    return _translated_bound(correlated_polygon,model,*box)


def _translated_bound(core_builder,model,x0,x1,y0,y1,t0,t1):
    L,B,rects,points,*_=model
    if x0>x1 or y0>y1:raise ValueError('Reversed centre interval')
    middle=L/2
    K=core_builder((L,B),middle,middle,middle,middle,t0,t1)
    if not K or area(K)==0:return F(0)
    polygons=[[(u+x-middle,v+y-middle) for u,v in K]
              for x,y in sorted({(x0,y0),(x0,y1),(x1,y0),(x1,y1)})]
    boxes=[(min(u for u,v in P),min(v for u,v in P),
            max(u for u,v in P),max(v for u,v in P)) for P in polygons]
    result=F(0)
    for a,b,c,d,rho in rects:
        if not rho:continue
        if any(c<=u or a>=w or d<=v or b>=z for u,v,w,z in boxes):continue
        minimum=None
        for P in polygons:
            q=P
            for axis,bound,greater in ((0,a,True),(0,c,False),(1,b,True),(1,d,False)):
                q=clip(q,axis,bound,greater)
            value=area(q)
            minimum=value if minimum is None else min(minimum,value)
            if not minimum:break
        result+=rho*minimum
    result+=sum((w for p,w in points if all(contains(P,p) for P in polygons)),F(0))
    return result
