from fractions import Fraction as F
from grid_endpoint import grid_witness
from endpoint_cells import clip_linear
from score import area


def test_grid_gate_strictness_at_endpoint():
    assert grid_witness(F(1,2),F(1,2),F(1),F(0)) is None
    assert grid_witness(F(1001,2000),F(1001,2000),F(1001,1000),F(0))==(1,1)
    assert grid_witness(F(3,2),F(3,2),F(1001,1000),F(1,3)) is None


def test_rational_centre_domain_clipping():
    poly=[(F(0),F(0)),(F(2),F(0)),(F(2),F(2)),(F(0),F(2))]
    cut=clip_linear(poly,F(1),F(1),F(3))
    assert area(cut)==F(1,2)
    assert all(x+y>=3 for x,y in cut)
