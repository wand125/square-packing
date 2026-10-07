from fractions import Fraction as F
from fixed_support_dual_audit import exact_columns


def test_mass_normalized_basis_coefficients():
    d=dict(L='4',rectangles=[dict(rectangle=['0','0','4','4'])],points=[dict(point=['2','2']),dict(point=['0','0'])])
    assert exact_columns(d,(F(2),F(2),F(-1,3)),F(1))==[F(1,16),F(1),F(0)]
    assert exact_columns(d,(F(2),F(2),F(1,3)),F(1,2))==[F(1,64),F(1),F(0)]


def test_interleaved_basis_order_is_preserved():
    d=dict(L='4',primitives=[dict(kind='point',geometry=['2','2']),dict(kind='rectangle',geometry=['0','0','4','4']),dict(kind='point',geometry=['0','0'])])
    assert exact_columns(d,(F(2),F(2),F(-1,3)),F(1))==[F(1),F(1,16),F(0)]
