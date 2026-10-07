from fractions import Fraction as F
from grid_special_case_probe import example,longest_projection_chain
from score import square


def test_nongrid_endpoint_packings_have_a_rigid_chain():
    for k in [4,5]:
        d=example(k)
        assert d['n']==k*k-4
        assert any(F(p[2])!=0 for p in d['poses'])
        assert max(c['length'] for c in d['chains'])==k


def test_separated_squares_need_not_have_disjoint_x_projections():
    polys=[square(1,1,1,0),square(1,2,1,0)]
    assert longest_projection_chain(polys,0)['length']==1
    assert longest_projection_chain(polys,1)['length']==2
