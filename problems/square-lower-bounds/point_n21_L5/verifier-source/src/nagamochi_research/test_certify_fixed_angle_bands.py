from fractions import Fraction as F
import pytest
from certify_fixed_angle_bands import band,merge_bands


def test_band_endpoints_satisfy_containment():
    for t in [F(0),F(1,1000),F(1,8),F(1,2)]:
        for side in [F(1),F(9999,10000),F(1,2)]:
            lo,hi,q=band(t,side)
            assert 0<=lo<=t<=hi<=F(1,2)
            for u in [lo,(lo+hi)/2,hi]:
                delta=abs((u-t)/(1+u*t))
                assert delta<=q
                assert side*(1+2*delta-delta*delta)/(1+delta*delta)<=1


def test_invalid_band_parameters():
    for t,s in [(F(-1),F(1)),(F(0),F(0)),(F(0),F(2))]:
        with pytest.raises(ValueError):band(t,s)


def test_union_touching_nested_and_gaps():
    intervals=[(F(1,10),F(1,5)),(F(0),F(1,10)),(F(1,20),F(3,20)),(F(2,5),F(1,2))]
    merged,gaps=merge_bands(intervals)
    assert merged==[(F(0),F(1,5)),(F(2,5),F(1,2))]
    assert gaps==[(F(1,5),F(2,5))]
    assert merge_bands([])==([] ,[(F(0),F(1,2))])
    assert merge_bands([(F(0),F(1,2))])[1]==[]
