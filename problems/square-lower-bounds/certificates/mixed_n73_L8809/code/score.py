"""Exact rational evaluation of the integer-square Nagamochi template (k >= 3).

Finite evaluations do not prove unavoidability. Closed-set scoring is used;
packing-level applications must prevent shared-boundary double counting.
The historical endpoint weight 9/20 is retained for reproduction, not as a
coverage guarantee: tokoharu's 2026-09-26 counterexample scores < 1 exactly.
See docs/flow/2026-09/2026-09-26-152-nagamochi-counterexample.md.
"""
from fractions import Fraction as F


def cross(a, b):
    return a[0]*b[1]-a[1]*b[0]


def sub(a, b):
    return a[0]-b[0], a[1]-b[1]


def square(cx, cy, side, t):
    """t = tan(theta/2), so all coordinates remain rational."""
    cx, cy, side, t = map(F, (cx, cy, side, t))
    c, s = (1-t*t)/(1+t*t), 2*t/(1+t*t)
    h = side/2
    return [(cx+c*x-s*y, cy+s*x+c*y) for x,y in [(-h,-h),(h,-h),(h,h),(-h,h)]]


def clip(poly, axis, bound, keep_greater):
    if not poly:
        return []
    def signed(p):
        return (p[axis]-bound)*(1 if keep_greater else -1)
    out=[]
    for a,b in zip(poly, poly[1:]+poly[:1]):
        da,db=signed(a),signed(b)
        if da >= 0:
            out.append(a)
        if (da < 0 < db) or (db < 0 < da):
            u=da/(da-db)
            out.append(tuple(a[i]+u*(b[i]-a[i]) for i in (0,1)))
    return out


def area(poly):
    if not poly:
        return F(0)
    return abs(sum(cross(a,b) for a,b in zip(poly,poly[1:]+poly[:1])))/2


def contains(poly, p):
    return all(cross(sub(b,a),sub(p,a)) >= 0 for a,b in zip(poly,poly[1:]+poly[:1]))


def segment_length(poly, a, b):
    """The template only uses horizontal/vertical segments."""
    direction=sub(b,a);lo,hi=F(0),F(1)
    for v,w in zip(poly,poly[1:]+poly[:1]):
        edge=sub(w,v);base=cross(edge,sub(a,v));slope=cross(edge,direction)
        if slope == 0:
            if base < 0:
                return F(0)
        elif slope > 0:
            lo=max(lo,-base/slope)
        else:
            hi=min(hi,-base/slope)
    return max(F(0),hi-lo)*(abs(direction[0])+abs(direction[1]))


def template(k):
    if not isinstance(k,int) or k < 3:
        raise ValueError('integer k >= 3 required')
    r=F(9,10)
    lines=[((r,1),(k-r,1)),((r,k-1),(k-r,k-1)),
           ((1,r),(1,k-r)),((k-1,r),(k-1,k-r))]
    q=[p for line in lines for p in line]
    p=[pt for i in range(2,k-1) for pt in [(i,r),(i,k-r),(r,i),(k-r,i)]]
    costs=[F((k-2)**2),4*(k-2*r),F(8),F(4*k-12)]
    return lines,q,p,costs


def features(k, poly):
    lines,q,p,_=template(k)
    central=poly
    for axis in (0,1):
        central=clip(central,axis,F(1),True)
        central=clip(central,axis,F(k-1),False)
    return [area(central),sum(segment_length(poly,a,b) for a,b in lines),
            F(sum(contains(poly,pt) for pt in q)),F(sum(contains(poly,pt) for pt in p))]


WEIGHTS=[F(1),F(1,2),F(9,20),F(1,2)]


def score(k,poly):
    return sum(a*b for a,b in zip(features(k,poly),WEIGHTS))
