from fractions import Fraction as F
import random
import pytest
from near_axis_projection import strip_projection, sign_band
from exact_fixed_angle_separator import projection
from certify_n21_near_axis_path import sign_on_open_interval


def test_projection_against_independent_polygon_edges():
    rng = random.Random(9282300)
    # Integer endpoints and nearby noninteger containers; tiny and broad angles.
    for L in map(F, ('4', '5', '6', '7', '8', '3.97', '4.999', '5.98')):
        for t in map(F, ('1/1000000000000', '1/1000', '1/7', '1/2')):
            D = 1000
            a, b, r = 1-t*t, 2*t, 1+t*t
            h = (a+b)/(2*r)
            poly = [(2*D*(a*x+b*y), 2*D*(-b*x+a*y))
                    for x,y in ((h,h),(L-h,h),(L-h,L-h),(h,L-h))]
            us = sorted({u for u,v in poly})
            pairs = [(u,u) for u in us] + list(zip(us, us[1:]))
            pairs += [(us[0]-2,us[0]-1),(us[-1]+1,us[-1]+2)]
            pairs += [tuple(sorted(F(rng.randrange(-1000,25000))
                                  for _ in range(2))) for _ in range(15)]
            for u0,u1 in pairs:
                assert strip_projection(L,D,t,u0,u1) == projection(poly,u0,u1)


def test_sign_band_handles_vanishing_coefficients_and_root():
    assert sign_band([0,0,0]) == (0,F(1,1000))
    sign,T = sign_band([0,0,1,-10**12], F(1))
    assert (sign,T) == (1,F(1,2*10**12))
    assert sign_on_open_interval([0,0,1,-10**12],T)[0] == 1
    assert sign_band([0,-1,10**12],F(1)) == (-1,T)
    with pytest.raises(ValueError):
        sign_on_open_interval([0,0,1,-10**12],F(1,10**12))
    for cap in (0,2):
        with pytest.raises(ValueError): sign_band([1],cap)


def test_projection_rejects_singular_or_empty_container():
    for t in (F(0),F(1)):
        with pytest.raises(ValueError): strip_projection(5,1000,t,0,1)
    with pytest.raises(ValueError): strip_projection(1,1000,F(1,2),0,1)
