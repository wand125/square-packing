from fractions import Fraction as F
import numpy as np
from scipy.sparse import csr_matrix
from outside_anchor_probe import disjoint_cells,guaranteed_conflict,rational_cover
from test_dual_conflict_probe import record


def test_anchor_contact_and_cell_separation_have_different_meanings():
    e=F(1,1000);h=F(1,10000)
    a=record(F(1,2),F(1,2),0);b=record(F(3,2),F(1,2),0)
    end=record(F(3,2)-e/3,F(1,2),0)
    assert guaranteed_conflict(a,a,b,end,e,h)
    assert disjoint_cells(a,a,b,end,e,h)
    assert not guaranteed_conflict(a,a,b,b,e,h)


def test_cell_crossing_is_not_certified_as_disjoint():
    e=F(1,1000);h=F(1,10000);a=record(1,1,0)
    assert not disjoint_cells(record(F(9,10),1,0),record(F(11,10),1,0),a,a,e,h)


def test_grid_contact_recovers_with_a_still_strict_margin():
    e=F(1,1000);h=F(1190619,200000000)
    a=record(F(1,2),F(1,2),0);b=record(F(3,2),F(1,2),0)
    end=record(F(3,2)-e/3,F(1,2),0)
    assert not guaranteed_conflict(a,a,b,end,e,h,56)
    assert guaranteed_conflict(a,a,b,end,e,h,32)
    import pytest
    with pytest.raises(AssertionError):guaranteed_conflict(a,a,b,end,e,h,28)


def test_conditional_cover_keeps_all_unblocked_vertices():
    cuts=[[0,1],[1,2]];a=csr_matrix(np.array([[1,0],[1,1],[0,1]],float))
    assert F(rational_cover(a,cuts,[0,1,2])['upper'])==2
    assert F(rational_cover(a,cuts,[1,2])['upper'])==1
    assert F(rational_cover(a,cuts,[])['upper'])==0
