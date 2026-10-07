"""In-memory exact geometry sharing across weights at one fixed rational angle.

No unvalidated on-disk cache is accepted. Compiled geometry includes zero weights.
Used for minimum-only batch comparisons; multi-counterexample collection is absent.
"""
from bisect import bisect_left,bisect_right
from dataclasses import dataclass
from fractions import Fraction as F
from exact_fixed_angle_separator import RangeMin,projection
from score import square,contains


@dataclass(frozen=True)
class Geometry:
    L: F
    D: int
    t: F
    coordinates: tuple
    us: tuple
    vs: tuple
    events: tuple
    queries: tuple


def compile_geometry(L,D,coordinates,t):
    L,t=F(L),F(t);coordinates=tuple(tuple(p) for p in coordinates)
    if not isinstance(D,int) or D<=0 or (L*D).denominator!=1 or not 0<=t<=F(1,2):
        raise ValueError('Invalid scale or angle')
    if any(len(p)!=2 or any(not isinstance(v,int) for v in p) for p in coordinates):
        raise ValueError('Need integer point coordinates')
    p,q=t.numerator,t.denominator;a=q*q-p*p;b=2*p*q;r=q*q+p*p;h=F(a+b,2*r)
    if L<=2*h:raise ValueError('Need full-dimensional centre domain')
    poly=[(2*D*(a*x+b*y),2*D*(-b*x+a*y)) for x,y in ((h,h),(L-h,h),(L-h,L-h),(h,L-h))]
    transformed=[(2*(a*x+b*y),2*(-b*x+a*y)) for x,y in coordinates]
    Umin,Umax=min(u for u,v in poly),max(u for u,v in poly)
    Vmin,Vmax=min(v for u,v in poly),max(v for u,v in poly);H=D*r
    us=sorted({Umin,Umax}|{F(u+s*H) for u,v in transformed for s in (-1,1)})
    vs=sorted({Vmin,Vmax}|{F(v+s*H) for u,v in transformed for s in (-1,1)})
    uid={u:i for i,u in enumerate(us)};vid={v:i for i,v in enumerate(vs)}
    events=[[] for u in us];queries=[]
    for i,(u,v) in enumerate(transformed):
        lo,hi=vid[v-H],vid[v+H]-1
        events[uid[u-H]].append((lo,hi,i,1));events[uid[u+H]].append((lo,hi,i,-1))
    for u0,u1 in zip(us,us[1:]):
        if u1<=Umin or u0>=Umax:queries.append(None);continue
        v0,v1=projection(poly,u0,u1)
        if v0>=v1:queries.append(None);continue
        lo=bisect_right(vs,v0)-1;hi=bisect_left(vs,v1)-1
        assert 0<=lo<=hi<len(vs)-1
        queries.append((lo,hi,v0,v1))
    return Geometry(L,D,t,coordinates,tuple(us),tuple(vs),
                    tuple(tuple(e) for e in events),tuple(queries))


def replay(cache,points):
    # Geometry is constructed in this process by compile_geometry, not deserialized.
    if tuple((x,y) for x,y,w in points)!=cache.coordinates:
        raise ValueError('Geometry or point order changed')
    weights=tuple(w for x,y,w in points)
    if any(not isinstance(w,int) or w<0 for w in weights):raise ValueError('Need nonnegative integer weights')
    tree=RangeMin(len(cache.vs)-1);best=None
    for i,query in enumerate(cache.queries):
        for lo,hi,j,sign in cache.events[i]:
            if weights[j]:tree.add(lo,hi,sign*weights[j])
        if query is None:continue
        lo,hi,v0,v1=query;mass,k=tree.query(lo,hi)
        if best is None or mass<best[0]:
            best=(mass,cache.us[i],cache.us[i+1],max(cache.vs[k],v0),min(cache.vs[k+1],v1))
    assert best is not None
    mass,u0,u1,v0,v1=best;v=(v0+v1)/2
    L,D,t=cache.L,cache.D,cache.t;p,q=t.numerator,t.denominator
    a=q*q-p*p;b=2*p*q;r=q*q+p*p;span=int(L*D);low=D*r*(a+b);high=2*span*r*r-low
    left=max(u0,(low+b*v)/a);right=min(u1,(high+b*v)/a)
    if b:left=max(left,(low-a*v)/b);right=min(right,(high-a*v)/b)
    else:assert low<a*v<high
    assert left<right;u=(left+right)/2
    cx=(a*u-b*v)/(2*D*r*r);cy=(b*u+a*v)/(2*D*r*r);h=F(a+b,2*r)
    assert h<cx<L-h and h<cy<L-h
    polygon=square(cx,cy,F(1),t)
    assert sum(w for x,y,w in points if contains(polygon,(F(x,D),F(y,D))))==mass
    return dict(t=str(t),minimum_numerator=mass,witness=dict(cx=str(cx),cy=str(cy),t=str(t)),
                witness_polygon_replayed=True,geometry_shared=True,all_angles_verified=False)
