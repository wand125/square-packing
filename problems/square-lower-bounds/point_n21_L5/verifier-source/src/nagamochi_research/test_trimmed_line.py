from fractions import Fraction as F
from trimmed_line_pilot import strict_score,resource


def test_boundary_line_and_atoms_are_not_counted_as_open_interior():
    poly=[(F(0),F(0)),(F(1),F(0)),(F(1),F(1)),(F(0),F(1))]
    value=strict_score(4,poly,resource(4,trim=False,exact=True))
    assert isinstance(value,F) and value==0


def test_removing_line_tails_has_exact_deficit_with_half_endpoint_weights():
    poly=[tuple(map(F,p)) for p in [('0.90209','0.02001'),('1.90199','0.00001'),('1.92199','0.99991'),('0.92209','1.01991')]]
    value=strict_score(4,poly,resource(4,exact=True))
    assert value==F(13016561896478827,13332000000000000)<1
    assert strict_score(4,poly,resource(4,trim=False,exact=True))>1
