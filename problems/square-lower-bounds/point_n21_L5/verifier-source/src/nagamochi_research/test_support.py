import numpy as np
from fractions import Fraction as F
from support_pilot import basis, matrix, exact_row, orbit
from score import square, features


def test_float_kernel_against_exact_geometry():
    for k in (4,10):
        cols=basis(k,True,True)
        poses=[]
        for t in (F(0),F(1,3),F(-1,3)):
            d=F(1,10**8);radius=(1+d)*(1-t*t+2*abs(t))/(2*(1+t*t))
            for x,y in ((radius,radius),(F(3,2)-d,radius),(F(3,2)+d,radius),(F(k,2),F(k,2))):
                poses.append(dict(cx=x,cy=y,delta=d,t=t))
        expected=np.array([[float(v) for v in exact_row(k,cols,p)] for p in poses])
        np.testing.assert_allclose(matrix(k,cols,poses),expected,rtol=1e-11,atol=1e-11)


def test_refinement_preserves_original_support_and_cost():
    for k in (4,7,10):
        cols=basis(k)
        weights=[]
        q_orbit=orbit(k,[(F(9,10),F(1))])
        for col in cols:
            weights.append(F(1) if col['kind']=='area' else F(1,2) if col['kind']=='line'
                           else F(9,20) if col['support']==q_orbit else F(1,2))
        assert sum(c['cost']*w for c,w in zip(cols,weights))==k*k-2
        for t in (F(0),F(1,3),F(-1,3)):
            p=dict(cx=F(3,2),cy=F(3,2),delta=F(1,100),t=t)
            row=features(k,square(p['cx'],p['cy'],1+p['delta'],t))
            assert sum(v*w for v,w in zip(exact_row(k,cols,p),weights))==sum(v*w for v,w in zip(row,[F(1),F(1,2),F(9,20),F(1,2)]))
