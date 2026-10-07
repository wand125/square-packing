from fractions import Fraction as F
import pytest
from packing_lemmas import (angle_envelope, normalized_axis_bounds,
                            fixed_core_sides, region_capacity_one)
from fixed_orientation_cover import angle_envelope as legacy_envelope
from score import square, cross, sub


def test_core_containment_including_n12_n21_and_large_targets():
    for k in (4, 5, 6, 7, 8, 9, 10):
        for e in (F(1,1000000), F(1,1000), F(1,25)):
            b=normalized_axis_bounds(k,e)
            assert b['capacity']==(k-1)**2 and b['axis_side']>1
            A,R=fixed_core_sides(k,e,F(1,100),F(1,100000))
            for t,side,h in ((F(0),A,b['halfwidth']), (F(1,100),R,F(1,100000))):
                for j in range(-4,5):
                    outer=square(0,0,1/b['sigma'],t+h*j/4)
                    inner=square(0,0,side,t)
                    assert all(cross(sub(v,u),sub(p,u))>0
                               for u,v in zip(outer,outer[1:]+outer[:1]) for p in inner)


def test_envelope_preserves_existing_exact_values():
    for t,h in ((F(1,100),F(1,100000)),(F(1,2),F(1,10)),(F(0),F(0))):
        assert angle_envelope(t,h)==legacy_envelope(t,h)


def test_capacity_needs_both_axes_and_accepts_closed_boundary():
    assert region_capacity_one([(0,0),(1,0),(1,1),(0,1)],0,1)
    assert not region_capacity_one([(0,0),(1,0),(1,2),(0,2)],0,1)
    assert region_capacity_one(square(0,0,1,F(1,3)),F(1,3),1)
    assert not region_capacity_one(square(0,0,F(101,100),F(1,3)),F(1,3),1)


def test_invalid_scopes_rejected():
    for e in (0,-1,3):
        with pytest.raises(ValueError): normalized_axis_bounds(4,e)
    with pytest.raises(TypeError): normalized_axis_bounds(4,0.001)
    with pytest.raises(ValueError): fixed_core_sides(4,'1/1000','1/100','1/100000',1)
    with pytest.raises(ValueError): angle_envelope(0,'1/100')


def test_doubled_axis_band_retains_strict_containment_at_endpoints():
    from packing_lemmas import axis_core_halfwidth
    for B in (F(34,100),F(99,100),F(999999,1000000)):
        h=axis_core_halfwidth(B)
        assert B*(1+2*h)==1
        inner=square(0,0,B,0)
        for t in (-h,-h/2,F(0),h/2,h):
            outer=square(0,0,1,t)
            assert all(cross(sub(v,u),sub(p,u))>0
                       for u,v in zip(outer,outer[1:]+outer[:1]) for p in inner)
    with pytest.raises(ValueError):axis_core_halfwidth(1)


def test_cross_orientation_conflicts_include_closed_contact():
    from packing_lemmas import regions_force_core_intersection as conflict
    assert conflict([(0,0)],[(1,0)],0,0,1,1)  # Closed cores touch.
    assert not conflict([(0,0)],[(F(1001,1000),0)],0,0,1,1)
    assert conflict([(0,0),(F(1,10),0)],[(0,F(1,10))],0,F(1,3),1,1)
    assert not conflict([(0,0),(3,0)],[(0,0)],0,0,1,1)  # One bad vertex suffices.


def test_layered_low_capture_bound_against_all_small_charge_assignments():
    from itertools import product
    from packing_lemmas import low_capture_bound
    # Exhaustive assignments include equality at each threshold.
    for excess in product((F(0),F(1,2),F(1),F(3,2)),repeat=3):
        levels=[F(1,2),F(1),F(3,2)]
        capacities=[sum(x<d for x in excess) for d in levels]
        got=low_capture_bound([1,2],[F(1,3),F(2,3)],levels,capacities)
        assert got<=F(5,3)+sum(excess)
