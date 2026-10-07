from fractions import Fraction as F
import pytest
from epsilon_conflict_family import pair_slope
from test_dual_conflict_probe import record


def test_endpoint_tangency_becomes_positive_for_every_epsilon():
    e=F(1,1000)
    a=record(F(1,2),F(1,2),0);b=record(F(3,2),F(1,2),0)
    end_b=record(F(3,2)-e/3,F(1,2),0)
    assert pair_slope(a,b,a,end_b,e)==F(1,3)


def test_initial_separation_and_orientation_change_are_rejected():
    a=record(F(1,2),F(1,2),0);b=record(F(8,5),F(1,2),0)
    c=record(1,F(1,2),0)
    with pytest.raises(AssertionError):pair_slope(a,b,a,c,F(1,1000))
    with pytest.raises(AssertionError):pair_slope(a,c,a,record(1,F(1,2),F(1,1000)),F(1,1000))
