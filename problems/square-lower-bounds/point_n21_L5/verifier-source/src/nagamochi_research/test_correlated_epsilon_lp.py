from fractions import Fraction as F
from copy import deepcopy
import pytest
from correlated_epsilon_lp import model
from epsilon_cell_envelope import parameters,geometry
from joint_angle_lp import rotation
from saturated_joint_search import search_model,replay_model,assemble_model


@pytest.mark.parametrize('restore_pairs',[False,True])
def test_epsilon_coefficients_match_independent_projection_widths(restore_pairs):
    q=parameters(4);data=model(q,[0],[0,1],restore_pairs);cells,_=geometry(q,[0]);na=len(cells)
    A,b,pairs,polys,angles=data;R=F(q['rot_inner'])
    for epsilon in (F(0),F(1,2000),F(1,1000)):
        sides=[1-epsilon/50]*na+[R]*2
        for pair in pairs:
            i,j=pair['i'],pair['j']
            for row,rhs in pair['options']:
                a,bb=row[2*i:2*i+2];threshold=F(0)
                for index in (i,j):
                    c,s=rotation(angles[index])
                    threshold+=sides[index]*(abs(a*c+bb*s)+abs(-a*s+bb*c))/2
                assert threshold==-rhs+row[-1]*epsilon


def test_nonpositive_bound_requires_the_strict_positive_scope():
    data=([[F(1)],[F(-1)]],[F(0),F(0)],[],[],[])
    q=search_model(data,positive_index=0)
    assert q['status']=='EXACT_NONPOSITIVE_COORDINATE'
    assert replay_model(data,q['tree'],positive_index=0)
    with pytest.raises(AssertionError):replay_model(data,q['tree'])
    bad=deepcopy(q['tree']);bad['bound']['upper_bound']='-1'
    with pytest.raises(AssertionError):replay_model(data,bad,positive_index=0)


def test_tiny_positive_epsilon_is_not_rounded_into_a_proof():
    data=([[F(1)],[F(-1)]],[F(1,10**12),F(0)],[],[],[])
    q=search_model(data,positive_index=0)
    assert not replay_model(data,q['tree'],positive_index=0)


def test_guaranteed_separation_uses_the_largest_inner_side():
    h=F(1,1000)
    def region(x):return [(x-h,-h),(x+h,-h),(x+h,h),(x-h,h)]
    polys=[region(F(0)),region(F(99,100))]
    assert not assemble_model(polys,[F(0)]*2,[F(98,100)]*2,[])[2]
    assert len(assemble_model(polys,[F(0)]*2,[F(98,100)]*2,[],guaranteed_sides=[F(1)]*2)[2])==1
