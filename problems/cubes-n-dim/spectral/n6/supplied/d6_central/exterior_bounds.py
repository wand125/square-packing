"""Proved exterior-power hierarchy: exact constants, floating exploratory values."""
from fractions import Fraction as F
from math import comb

def constants(n,k):
    c=n-k;q,r=divmod(n,c)
    P=q**(c-r)*(q+1)**r
    D=max(F(comb(m,k),m**(2*k)) for m in range(k,n))
    return F((k+1)*4**k,P)/D

def elementary(p):
    e=[1]+[0]*len(p)
    for value in p:
        for k in range(len(p),0,-1):e[k]+=value*e[k-1]
    return e

def exterior_values(p):
    n=len(p);e=elementary(p)
    return [(float(constants(n,k))*max(0,e[k+1]))**(1/(2*k)) for k in range(1,n)]

if __name__=='__main__':
    for k in range(1,6):
        D=max(F(comb(m,k),m**(2*k)) for m in range(k,6))
        assert D==F(1,k**(2*k))
        print('n=6 k=',k,'coefficient inside root=',constants(6,k))
    p=[.795,.05120,.05095,.04980,.04926,.00379]
    p=[v/sum(p) for v in p]
    import math
    target=2*(sum(map(math.sqrt,p))-1)
    print('Example gaps:',[v-target for v in exterior_values(p)])

def rational_tangent(n,a,t):
    """Exact positive supporting weights for H_k (before scalar D correction)."""
    a=list(map(F,a));t=list(map(F,t));assert len(a)==len(t)==n-1
    assert all(v>=0 for v in a+t)
    for m in range(1,n):
        assert sum(a[k-1]*F(comb(m,k),m**(2*k)) for k in range(1,min(m,n-1)+1))<=1
    D=1+sum((2*k-1)*a[k-1]*t[k-1]**(2*k) for k in range(1,n))
    return [2*k*a[k-1]*t[k-1]**(2*k-1)/D for k in range(1,n)]

def projected_invariant(p,R,k):
    """e_k of principal covariance compression, exact if p has Fractions."""
    import itertools
    result=0
    for I in itertools.combinations(R,k):
        prod=1
        for i in I:prod*=p[i]
        result+=prod*(1-sum(p[i] for i in I))
    return result

def projected_bound(p,R,k):
    n=len(p);m=len(R)
    D=max(F(comb(j,k),j**(2*k)) for j in range(k,n))
    if k==m:P=1
    else:
        q,r=divmod(m,m-k);P=q**(m-k-r)*(q+1)**r
    coeff=F(4**k,P)/D
    E=projected_invariant(p,R,k)
    return max(0,float(coeff)*float(E))**(1/(2*k))
