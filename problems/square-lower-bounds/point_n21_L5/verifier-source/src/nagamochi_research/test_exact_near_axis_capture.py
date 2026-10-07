from fractions import Fraction as F
import pytest
from exact_near_axis_capture import halfangle
from score import square,contains


def test_positive_and_negative_band_contain_the_aligned_core():
    B=F(999999,1000000);b=F(99999,100000);T=halfangle(B,b)
    assert T==F(1,222220)
    for t in (-T,-T/2,F(0),T/2,T):
        rotated=square(2,2,B,t)
        assert all(contains(rotated,p) for p in square(2,2,b,F(0)))
        c=(1-t*t)/(1+t*t);s=2*t/(1+t*t)
        assert b*(c+abs(s))<=B
    with pytest.raises(ValueError):halfangle(b,B)
