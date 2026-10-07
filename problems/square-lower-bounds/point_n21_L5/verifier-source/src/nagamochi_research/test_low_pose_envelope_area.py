from fractions import Fraction as F
from low_pose_envelope_area import envelope,union_area
from score import square


def test_union_overlaps_duplicates_and_touching():
    rs=[tuple(map(F,r)) for r in [(0,2,0,2),(1,3,1,3),(3,4,1,3),(0,2,0,2)]]
    assert union_area(rs)==9
    assert union_area([])==0


def test_envelope_contains_rotating_physical_square():
    box=tuple(map(F,['1','6/5','3/2','8/5','-5/12','5/12']))
    a,b,c,d=envelope(F(4),box)
    for x in box[:2]:
        for y in box[2:4]:
            for j in range(33):
                t=box[4]+(box[5]-box[4])*j/32
                assert all(a<=u<=b and c<=v<=d for u,v in square(x,y,F(1),t))
