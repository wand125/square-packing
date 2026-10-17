"""Rationally certified lower bound for sqrt(2) Tr sqrt(diag(p)-p p^T)-2 sum sqrt(p)+2.
mpmath is only a witness generator. Every claimed lower bound is certified by
exact Fraction arithmetic and integer square-root inequalities.
"""
from fractions import Fraction as F
from math import isqrt


def sqrt_bounds(x, bits=100):
    x=F(x)
    if x < 0: raise ValueError('negative radicand')
    scale=1 << bits
    k=isqrt((x.numerator << (2*bits))//x.denominator)
    lo=F(k,scale)
    hi=lo if lo*lo == x else F(k+1,scale)
    return lo,hi


def spectral_q_lower(p, bits=100, return_witness=False):
    p=tuple(map(F,p))
    n=len(p)
    assert all(x>=0 for x in p) and sum(p)==1
    C=[[p[i]*(1-p[i]) if i==j else -p[i]*p[j] for j in range(n)] for i in range(n)]
    # Numerical operations merely generate the rational witness A.
    import mpmath as mp
    with mp.workdps(65):
        M=mp.matrix([[mp.mpf(x.numerator)/x.denominator for x in row] for row in C])
        E,Q=mp.eigsy(M)
        roots=[mp.sqrt(max(mp.mpf(0),E[k])) for k in range(n)]
        scale=1<<bits
        A=[[F(0) for _ in range(n)] for _ in range(n)]
        for i in range(n):
            for j in range(i,n):
                x=sum(Q[i,k]*Q[j,k]*roots[k] for k in range(n))
                A[i][j]=A[j][i]=F(int(mp.nint(x*scale)),scale)
    return certify_witness(p,A,bits=bits,return_witness=return_witness)


def certify_witness(p,A,bits=100,return_witness=False):
    """Verify a supplied rational witness with no floating-point operations."""
    p=tuple(map(F,p))
    n=len(p)
    assert all(x>=0 for x in p) and sum(p)==1
    assert len(A)==n and all(len(row)==n for row in A)
    A=[[F(x) for x in row] for row in A]
    assert all(A[i][j]==A[j][i] for i in range(n) for j in range(n))
    C=[[p[i]*(1-p[i]) if i==j else -p[i]*p[j] for j in range(n)] for i in range(n)]
    delta=max(sum(abs(C[i][j]-sum(A[i][k]*A[k][j] for k in range(n))) for j in range(n)) for i in range(n))
    _,sqrt_delta_hi=sqrt_bounds(delta,bits)
    trace_lower=sum(A[i][i] for i in range(n))-n*sqrt_delta_hi
    trace_lower=max(F(0),trace_lower)
    sqrt2_lo,_=sqrt_bounds(F(2),bits)
    q_lower=sqrt2_lo*trace_lower - 2*sum(sqrt_bounds(x,bits)[1] for x in p)+2
    if return_witness:
        return q_lower, {'A': A, 'delta':delta, 'trace_lower':trace_lower}
    return q_lower

if __name__=='__main__':
    import time
    t=time.time()
    for p in [(F(3,4),)+(F(1,16),)*4,(F(1,5),)*5,(F(3,4),F(1,4),F(0),F(0),F(0))]:
        q,w=spectral_q_lower(p,return_witness=True)
        print('p=',p,'q_lower=',float(q),'delta=',float(w['delta']))
    print('seconds',time.time()-t)
