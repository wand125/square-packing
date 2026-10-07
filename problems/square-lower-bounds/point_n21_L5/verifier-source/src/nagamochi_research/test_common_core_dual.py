from fractions import Fraction as F
from common_core_dual import maximum_closed_rectangle_load
from common_core_obstruction import separating_axis


def test_closed_boundaries_and_weighted_overlap():
    rs=[tuple(map(F,r)) for r in [(0,1,0,1),(1,2,1,2),(F(1,2),F(3,2),F(1,2),F(3,2))]]
    peak,w=maximum_closed_rectangle_load(rs,[2,3,4]);assert peak==9 and w==(1,1)
    xs={v for r in rs for v in r[:2]};ys={v for r in rs for v in r[2:]}
    assert peak==max(sum(a for (x0,x1,y0,y1),a in zip(rs,[2,3,4]) if x0<=x<=x1 and y0<=y<=y1) for x in xs for y in ys)


def test_disjointness_requires_strict_gap():
    P=[(F(0),F(0)),(F(1),F(0)),(F(1),F(1)),(F(0),F(1))]
    assert separating_axis(P,[(x+1,y) for x,y in P]) is None
    assert separating_axis(P,[(x+F(11,10),y) for x,y in P]) is not None
