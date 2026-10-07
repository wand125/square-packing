from fractions import Fraction as F
from itertools import product
from local_search_lemma_measure import physical
from score import square


def test_physical_parameterization_keeps_closed_unit_box_inside():
    L=F(397,100)
    for u,v,t in product([F(0),F(1,2),F(1)],repeat=3):
        t=(t-F(1,2))*F(4,5)
        x,y,t=physical(L,(u,v,t))
        assert all(0<=a<=L and 0<=b<=L for a,b in square(x,y,F(1),t))
