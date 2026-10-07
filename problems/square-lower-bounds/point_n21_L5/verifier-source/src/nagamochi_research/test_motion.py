from fractions import Fraction as F
import pytest
from motion_pilot import sqrt_interval,focus_heights,rows,analyse_defects,capacity,strict_contains
from motion_centres import setup,build,replay
from score import square


def test_radical_and_continuous_vertical_premises():
    for n in (2,3):
        lo,hi=sqrt_interval(n)
        assert lo*lo<n<hi*hi
    for k in (5,6):
        for index in range(k):
            ys=focus_heights(k,index)
            assert ys[0]>0 and ys[-1]<k
            assert (ys[0]+F(1,2))**2<2 and (k-ys[-1]+F(1,2))**2<2
            assert all(0<(b-a)**2<=F(3,4) for a,b in zip(ys,ys[1:]))
            for j in (index-1,index):
                if 0<=j<k-1:assert ys[j+1]-ys[j]==F(4,5)
    assert F(capacity(7)['height_cap_interval'][0])>7
    assert F(capacity(7)['edge_focus_height_cap_interval'][1])<7
    assert all(F(capacity(k)['height_cap_interval'][1])<k for k in (8,9,10))


def test_open_box_boundary_and_shared_trajectories():
    poly=square(F(7,10),F(13,10),F(101,100),0)
    assert not strict_contains(poly,poly[0])
    assert all(strict_contains(poly,(F(x),F(y))) for x in ('0.4','1') for y in ('0.9','1.7'))


def test_known_n22_defect_control_and_n21_new_branches():
    control=analyse_defects(5,22,1)
    assert control['cases']==73 and control['no_safe_vertical_side']==0
    assert control['max_exceptional_long_rows']==1
    harder=analyse_defects(5,21,1)
    assert harder['no_safe_vertical_side']>0
    assert harder['max_exceptional_long_rows']>1


def test_centre_proof_tree_replay_and_rejection():
    for kind in ('middle','edge'):
        args=setup(kind);tree=build(*args)
        assert replay(tree,*args)>0
        with pytest.raises(AssertionError):replay('inside_target_disk',*args)
        with pytest.raises(AssertionError):replay([tree],*args)
