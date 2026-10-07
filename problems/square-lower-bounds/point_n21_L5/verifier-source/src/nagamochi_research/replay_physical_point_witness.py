"""Independent point-in-every-physical-pose check using polynomial bounds.

Does not import the upstream checker, inherited point masks or its witnesses'
claimed truth values. Quartic Bernstein bounds are sufficient, not necessary.
"""
from fractions import Fraction as F
from math import comb
from itertools import product
from compile_box_capture_rows import quadmax


def add(a,b):
    return [ (a[i] if i<len(a) else 0)+(b[i] if i<len(b) else 0) for i in range(max(len(a),len(b))) ]


def scale(a,k):return [k*v for v in a]


def mul(a,b):
    out=[F(0)]*(len(a)+len(b)-1)
    for i,x in enumerate(a):
        for j,y in enumerate(b):out[i+j]+=x*y
    return out


def bernstein_nonpositive(poly,lo,hi):
    lo,hi=F(lo),F(hi);n=len(poly)-1
    power=[sum((F(poly[k])*comb(k,j)*lo**(k-j)*(hi-lo)**j for k in range(j,n+1)),F(0)) for j in range(n+1)]
    coefficients=[sum((power[j]*F(comb(i,j),comb(n,j)) for j in range(i+1)),F(0)) for i in range(n+1)]
    return max(coefficients)<=0


def contains(point,L,box):
    L=F(L);b=list(map(F,box));px,py=map(F,point)
    if L<=0 or len(b)!=6 or any(b[i]>b[i+1] for i in (0,2,4)) or not 0<=b[4]<=b[5]<=F(1,2):
        raise ValueError('Invalid physical pose box')
    r=[F(1),F(0),F(1)];a=[F(1),F(0),F(-1)];s=[F(0),F(2)]
    wall=[F(1),F(2),F(-1)];far=add(scale(r,2*L),scale(wall,-1))
    # For each projection's maximum, choose any of the two valid centre
    # lower/upper bounds: the rectangle endpoint or the container wall.
    for u,v,xi,yi in [(a,s,0,2),(scale(a,-1),scale(s,-1),1,3),(scale(s,-1),a,1,2),(s,scale(a,-1),0,3)]:
        accepted=False
        for wx,wy in product((False,True),repeat=2):
            if not wx and not wy:
                q=add(add(scale(u,2*(px-b[xi])),scale(v,2*(py-b[yi]))),scale(r,-1))
                q += [F(0)]*(3-len(q))
                ok=quadmax(q,b[4],b[5])<=0
            else:
                X=(wall if xi==0 else far) if wx else scale(r,2*b[xi])
                Y=(wall if yi==2 else far) if wy else scale(r,2*b[yi])
                dx=add(scale(r,2*px),scale(X,-1));dy=add(scale(r,2*py),scale(Y,-1))
                q=add(add(mul(u,dx),mul(v,dy)),scale(mul(r,r),-1))
                ok=bernstein_nonpositive(q,b[4],b[5])
            if ok:accepted=True;break
        if not accepted:return False
    return True


def replay(coords,weights,L,box,indices):
    if not indices or len(indices)!=len(set(indices)) or any(type(i)is not int or not 0<=i<len(coords) for i in indices):
        raise ValueError('Invalid point witness indices')
    if any(w<0 for w in weights):raise ValueError('Negative measure')
    for i in indices:
        if not contains(coords[i],L,box):raise ValueError('Point containment not proved: '+str(i))
    mass=sum((weights[i] for i in indices),F(0))
    if mass<1:raise ValueError('Insufficient witness mass')
    return mass
