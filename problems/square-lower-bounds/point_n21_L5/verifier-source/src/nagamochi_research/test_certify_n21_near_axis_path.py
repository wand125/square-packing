from fractions import Fraction as F
import pytest
from certify_n21_near_axis_path import mul, sign_on_open_interval


def test_polynomial_product():
    assert mul([F(1), F(1)], [F(1), F(-1)]) == [1, 0, -1]


def test_open_endpoint_leading_coefficient():
    assert sign_on_open_interval([F(0), F(0), F(1), F(-2)], F(1, 4)) == (1, F(1, 2))
    assert sign_on_open_interval([F(0), F(-1), F(2)], F(1, 4)) == (-1, F(1, 2))
    assert sign_on_open_interval([F(0), F(0)], F(1, 4)) == (0, 0)


def test_does_not_claim_strict_sign_when_remainder_can_cancel():
    with pytest.raises(ValueError):
        sign_on_open_interval([F(-1), F(4)], F(1, 4))
