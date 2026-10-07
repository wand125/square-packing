from fractions import Fraction as F
from n45_small_motion import heights,snapshot
from n45_anchor_repair import certificate


def test_n45_rational_height_and_shift_conditions():
    for focus in range(7):
        ys,shift=heights(focus)
        assert ys[0]==F(457,500) and ys[-1]==7-F(457,500)
        assert max(b-a for a,b in zip(ys,ys[1:]))**2<=F(3,4)
        for j in (focus-1,focus):
            if 0<=j<6:assert (ys[j+1]-ys[j])**2+(F(1,2)+shift)**2<=1
        c=1-focus%2
        assert len(snapshot(c,focus,'row-left',F(1)))==len(snapshot(c,focus,'vertical',F(0)))


def test_wall_cubic_condition_is_strict():
    d=certificate(F(847,1000),F(39,40))
    assert len(d['leaves'])==64
    assert all(F(x)>0 for leaf in d['leaves'] for x in leaf['coefficients'])
