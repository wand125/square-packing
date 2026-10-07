from fractions import Fraction as F
import pytest
from bridge_probe import intersection,cover_accounting
from verify_bridge import mobius


def test_intersection_keeps_exact_coordinates():
    assert intersection([(F(0),F(0)),(F(1),F(1))],[(F(0),F(1)),(F(1),F(0))])==[(F(1,2),F(1,2))]
    assert not intersection([(0,0),(1,0)],[(2,0),(3,0)])


def test_intersecting_rule_expansion_and_bad_rule_rejection():
    bags=[[0,1,2],[0,3,4],[1,3,5],[2,4,5]]
    terms=mobius(bags,6)
    assert len(terms)==11 and sum(abs(t['coefficient']) for t in terms)==13
    with pytest.raises(AssertionError):mobius([[0],[1]],2)


def test_closed_and_shrunken_tiling_are_different_problems():
    r=cover_accounting()
    assert r['total']<13 and r['minimum_closed_tile']>=1
    assert r['minimum_eroded_tile']<1
