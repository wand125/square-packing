"""A rational net/core family for every rational 0<epsilon<=1.

This proves geometric containment and avoidance of the known core-grid
obstruction only. It does not construct a covering measure or prove s(21)=5.
"""
from fractions import Fraction as F
from math import isqrt
from mixed_net_audit import net_certificate


def family(epsilon,k=5):
    e=F(epsilon)
    if not 0<e<=1:raise ValueError('Require 0 < epsilon <= 1')
    if type(k) is not int or k<3:raise ValueError('Require integer k >= 3')
    d=2*(k-1);L=k-e;B=1-e/d
    # Rational T just above sqrt(2)-1, with gap < e/(8*d).
    Q=1
    while F(1,Q)>e/(8*d):Q*=2
    T=F(isqrt(2*Q*Q)+1-Q,Q)
    N=(d*T/e).__ceil__();D=T/N
    assert D<=e/d
    assert B*(1+D)<=1-e*e/(d*d)<1
    assert 1+(k-1)*B-L==e/2>0
    net=net_certificate(B,D,N)
    return dict(integer_endpoint=k,epsilon=str(e),L=str(L),B=str(B),step=str(D),last=N,
                containment_margin_lower=str(e*e/(d*d)),grid_barrier_slack=str(e/2),net=net,
                status='GEOMETRIC_FAMILY_ONLY_NO_COVERAGE')


def identity_certificate(k=5):
    # Coefficient identities, not sampled values of epsilon.
    if type(k) is not int or k<3:raise ValueError('Require integer k >= 3')
    d=2*(k-1);a=[F(1),F(-1,d)];b=[F(1),F(1,d)];product=[F(0)]*3
    for i,x in enumerate(a):
        for j,y in enumerate(b):product[i+j]+=x*y
    assert product==[F(1),F(0),F(-1,d*d)]
    assert [1+(k-1)*a[0]-k,(k-1)*a[1]+1]==[0,F(1,2)]
    return dict(containment_product_coefficients=list(map(str,product)),
                grid_slack_coefficients=['0','1/2'],
                scope='Algebraic identities for all epsilon; positive margin for 0<epsilon<=1. No covering inequality or budget construction.')


if __name__=='__main__':
    import json
    from pathlib import Path
    result=dict(identity=identity_certificate(),examples=[family(e) for e in ('1/80','1/100','1/1000','1/10000')])
    p=Path('runs/mixed_endpoint_bridge_20260927/integer-five-net-family.json')
    with p.open('x') as f:json.dump(result,f,indent=2)
    for r in result['examples']:print(r['epsilon'],r['L'],r['net']['count'])
