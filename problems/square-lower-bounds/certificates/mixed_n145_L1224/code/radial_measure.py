"""Experimental radial probability measures. Numerical quadrature is NOT proof.

disk: 1/(pi R^2); bump: 2(1-r^2/R^2)_+/(pi R^2);
annulus: uniform R/2 <= r <= R. All use full-plane unit mass.
Exact interval integration works for any rational rotated rectangular region,
including a common-core region from unified_measure.region.
"""
from fractions import Fraction as F
from functools import lru_cache
import math
import numpy as np
from numba import njit
from unified_measure import coefficient
from score import clip,area

@lru_cache(None)
def circle_polygons(m):
    """Rational points on the circle and intersections of adjacent tangents."""
    if not isinstance(m,int) or m<1:raise ValueError('positive subdivisions required')
    arc=[]
    for i in range(m):
        t=F(i,m);arc.append(((1-t*t)/(1+t*t),2*t/(1+t*t)))
    inner=[]
    for quadrant in range(4):
        for a,b in arc:
            for _ in range(quadrant):a,b=-b,a
            inner.append((a,b))
    outer=[]
    for (x,y),(u,v) in zip(inner,inner[1:]+inner[:1]):
        det=x*v-y*u;outer.append(((v-y)/det,(x-u)/det))
    return tuple(inner),tuple(outer)

def polygon_interval(kind,center,radius,reg,subdivisions=16,inner_ratio=F(1,2)):
    """Exact disk/bump/annulus bounds using rational circle polygons.

    For the bump integrate its quadratic density exactly on the clipped inner
    polygon. The remaining captured area is bounded by outer minus inner area,
    times density <= 1. No floating geometry enters the returned bounds.
    """
    if kind not in ('disk','bump','annulus'):raise ValueError('unknown kernel')
    px,py=map(F,center);R=F(radius);q=F(inner_ratio);c,s,u0,u1,v0,v1=reg
    if R<=0 or c*c+s*s!=1:raise ValueError('invalid circle/rotation')
    if not 0<=q<1:raise ValueError('inner ratio must be in [0,1)')
    if u0>=u1 or v0>=v1:return F(0),F(0)
    uc=c*px+s*py;vc=-s*px+c*py
    if u0<=uc-R and uc+R<=u1 and v0<=vc-R and vc+R<=v1:return F(1),F(1)
    du=max(u0-uc,F(0),uc-u1);dv=max(v0-vc,F(0),vc-v1)
    if du*du+dv*dv>=R*R:return F(0),F(0)
    if kind=='annulus' and max((u-uc)**2+(v-vc)**2 for u in (u0,u1) for v in (v0,v1))<=(R*q)**2:return F(0),F(0)
    inner,outer=circle_polygons(subdivisions)
    def clipped(poly,r):
        # Centered square-frame coordinates preserve the radial polynomial.
        p=[(r*x,r*y) for x,y in poly]
        for axis,bound,greater in ((0,u0-uc,True),(0,u1-uc,False),(1,v0-vc,True),(1,v1-vc,False)):
            p=clip(p,axis,bound,greater)
        return p
    pin=clipped(inner,R);pout=clipped(outer,R);a,b=area(pin),area(pout)
    scale=R*R
    if kind=='annulus':
        a,b=max(F(0),a-area(clipped(outer,R*q))),b-area(clipped(inner,R*q));scale*=1-q*q
    elif kind=='bump':
        moment=F(0)
        for (x,y),(u,v) in zip(pin,pin[1:]+pin[:1]):
            moment+=(x*v-y*u)*(x*x+x*u+u*u+y*y+y*v+v*v)/12
        value=a-moment/(R*R)
        a,b=value,value+b-a;scale/=2
    pl,pu=pi_bounds()
    return max(F(0),a/(pu*scale)),min(F(1),b/(pl*scale))

@lru_cache(None)
def pi_bounds():
    # Machin identity and alternating arctangent series, with exact remainder.
    def atan(q):
        s=sum(((-1)**i*F(1,(2*i+1)*q**(2*i+1)) for i in range(32)),F(0))
        return s,s+F(1,65*q**65)
    a,b=atan(5);c,d=atan(239)
    return 16*a-4*d,16*b-4*c

def interval(kind, center, radius, reg, depth=5):
    """Rational lower/upper captured mass; finite depth never implies success.

    Density bounds on dyadic cells times EXACT clipped cell area. Boundary
    curves have area zero. Entire support may extend outside the container:
    counting its full-plane mass remains a safe, possibly wasteful budget.
    """
    if kind not in ('disk','bump','annulus'):raise ValueError('unknown kernel')
    if not isinstance(depth,int) or not 0<=depth<=10:raise ValueError('invalid depth')
    px,py=map(F,center);R=F(radius)
    if R<=0:raise ValueError('positive radius required')
    c,s,u0,u1,v0,v1=reg
    if c*c+s*s!=1:raise ValueError('orthonormal region required')
    if u0>=u1 or v0>=v1:return F(0),F(0)
    u=c*px+s*py;v=-s*px+c*py
    if u0<=u-R and u+R<=u1 and v0<=v-R and v+R<=v1:return F(1),F(1)
    du=max(u0-u,F(0),u-u1);dv=max(v0-v,F(0),v-v1)
    if du*du+dv*dv>=R*R:return F(0),F(0)
    n=2**depth;h=2*R/n;lower=upper=F(0);R2=R*R
    for i in range(n):
        x0=-R+i*h;x1=x0+h
        for j in range(n):
            y0=-R+j*h;y1=y0+h
            near=lambda a,b:F(0) if a<=0<=b else min(a*a,b*b)
            d0=near(x0,x1)+near(y0,y1)
            d1=max(x0*x0,x1*x1)+max(y0*y0,y1*y1)
            if d0>=R2:continue
            if kind=='bump':lo=max(F(0),1-d1/R2);hi=1-d0/R2
            elif kind=='disk':lo=F(d1<=R2);hi=F(1)
            else:lo=F(d0>=R2/4 and d1<=R2);hi=F(d1>R2/4)
            if not hi:continue
            a=coefficient('rectangle',(px+x0,py+y0,px+x1,py+y1),reg)*h*h
            lower+=a*lo;upper+=a*hi
    pl,pu=pi_bounds();scale=R2*(F(1,2) if kind=='bump' else F(3,4) if kind=='annulus' else 1)
    return max(F(0),lower/(pu*scale)),min(F(1),upper/(pl*scale))

# Shared search arithmetic lives alongside the production pricing adapter.
# Frozen research bundles may instead place radial_numeric.py in this directory.
try:
    from radial_numeric import disk_integral, variable_matrix, numerical_matrix
except ModuleNotFoundError as exc:
    if exc.name != 'radial_numeric':
        raise
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'rectangle_budget_optimization'))
    from radial_numeric import disk_integral, variable_matrix, numerical_matrix
