from fractions import Fraction as F

from q2 import Q2, SQRT2


def test_arith_and_sign():
    assert SQRT2 * SQRT2 == Q2(2)
    a = Q2(F(3, 2), F(-1, 3))
    assert (a * a.inverse()) == Q2(1)
    assert Q2(-1, 1).sign() == 1          # sqrt2 - 1 > 0
    assert Q2(F(3, 2), -1).sign() == 1    # 1.5 - 1.414 > 0
    assert Q2(F(7, 5), -1).sign() == -1   # 1.4 - 1.414 < 0
    assert Q2(0).sign() == 0


def test_parse():
    assert Q2.parse("5/2*sqrt2") == Q2(0, F(5, 2))
    assert Q2.parse("0+5/8*sqrt2") == Q2(0, F(5, 8))
    assert Q2.parse("3/2-1/3*sqrt(2)") == Q2(F(3, 2), F(-1, 3))
