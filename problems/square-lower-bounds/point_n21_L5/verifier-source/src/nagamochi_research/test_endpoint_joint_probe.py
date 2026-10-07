from fractions import Fraction as F
from score import square
from endpoint_joint_probe import separation, probe


def test_separation_distinguishes_touching_from_interior_overlap():
    a=square(F(1),F(1),F(1),F(0))
    assert separation(a,square(F(2),F(1),F(1),F(0))) is not None
    assert separation(a,square(F(199,100),F(1),F(1),F(0))) is None
    assert len(probe()['pair_separations'])==10
