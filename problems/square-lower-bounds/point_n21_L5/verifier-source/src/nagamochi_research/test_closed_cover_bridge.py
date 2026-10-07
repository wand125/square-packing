from fractions import Fraction as F
import pytest
from closed_cover_bridge import dilate_packing,chain_capture
from score import square,contains
from itertools import product


def test_touching_squares_become_strictly_disjoint_including_rotated_pair():
    a=dilate_packing([(F(1,2),F(1,2),0),(F(3,2),F(1,2),0)],2,F(201,100))
    assert F(a['pairs'][0]['gap'])>0
    b=dilate_packing([(1,1,F(1,5)),(F(25,13),F(18,13),F(1,5))],3,4)
    assert F(b['pairs'][0]['gap'])>0
    with pytest.raises(ValueError):dilate_packing([(1,1,0),(1,1,0)],2,3)
    with pytest.raises(ValueError):dilate_packing([],2,2)


def test_two_chain_partition_captures_switching_corner_points_at_closed_ties():
    pts=[((x,y),1) for x in (F(1,2),F(3,2)) for y in (F(1,2),F(3,2))]
    box=(F(9,10),F(11,10),F(9,10),F(11,10),0,0)
    # Upper x and upper y predicates of top-right point split both coordinates.
    q=chain_capture(pts,box,[[12],[14]])
    assert F(q['baseline'])==0 and F(q['lower'])==1
    # With rotation, the four corner points can all be missed at centre (1,1).
    q=chain_capture(pts,box[:-2]+(F(0),F(1,100)),[[12],[14]])
    assert F(q['lower'])==0
    assert sum(w for p,w in pts if contains(square(F(1),F(1),F(1),F(1,100)),p))==0


def test_unproved_order_and_negative_weights_are_rejected():
    pts=[((F(1,2),1),1),((F(3,2),1),1)]
    box=(F(9,10),F(11,10),1,1,0,0)
    with pytest.raises(ValueError,match='ordering'):chain_capture(pts,box,[[4,0]])
    with pytest.raises(ValueError):chain_capture([((0,0),-1)],box,[[0]])


def test_two_chains_cover_a_nonzero_rotation_interval_without_fixed_points():
    pts=[((F(1,2),1),F(1,2)),((F(3,2),1),F(1,2)),
         ((1,F(1,2)),F(1,2)),((1,F(3,2)),F(1,2))]
    box=(F(9,10),F(11,10),F(9,10),F(11,10),F(-1,100),F(1,100))
    q=chain_capture(pts,box,[[4],[14]])
    assert F(q['baseline'])==0 and F(q['lower'])==1
    for x,y,t in product((F(9,10),F(1),F(11,10)),(F(9,10),F(1),F(11,10)),(F(-1,100),F(0),F(1,100))):
        actual=sum(w for p,w in pts if contains(square(x,y,F(1),t),p))
        assert actual>=F(q['lower'])


def test_quadratic_maximum_includes_interior_stationary_point():
    from closed_cover_bridge import quad_max
    assert quad_max(F(1),F(0),F(-1),F(-2),F(2))==1
    assert quad_max(F(-1),F(0),F(2),F(-2),F(2))==7
