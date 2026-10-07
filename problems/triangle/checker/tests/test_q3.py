from fractions import Fraction as F

import pytest

from q3 import Q3, SQRT3


def test_parse_and_str():
    assert Q3.parse("2+2/3*sqrt3") == Q3(2, F(2, 3))
    assert Q3.parse("-sqrt3") == Q3(0, -1)
    assert Q3.parse("3/2-1/3*sqrt(3)") == Q3(F(3, 2), F(-1, 3))
    assert Q3.parse("7") == Q3(7)
    assert Q3.parse(str(Q3(F(-5, 7), F(3, 11)))) == Q3(F(-5, 7), F(3, 11))
    with pytest.raises(ValueError):
        Q3.parse("1.5x")


def test_arithmetic():
    a = Q3(1, 2)
    b = Q3(F(-3, 4), F(1, 5))
    assert a + b - b == a
    assert (a * b) / b == a
    assert SQRT3 * SQRT3 == Q3(3)
    assert a * a.inverse() == Q3(1)
    assert (1 - a) == Q3(0, -2)
    with pytest.raises(ZeroDivisionError):
        Q3(0) .inverse()


def test_sign_edge_cases():
    assert Q3(0).sign() == 0
    assert Q3(0, 0).is_zero()
    assert Q3(2, -1).sign() == 1          # 2 - sqrt3 > 0
    assert Q3(-2, 1).sign() == -1
    assert Q3(1, -1).sign() == -1         # 1 - sqrt3 < 0
    assert Q3(-1, 1).sign() == 1
    assert Q3(0, -1).sign() == -1
    assert Q3(F(-1, 3), 0).sign() == -1
    # a^2 = 3 b^2 never happens for nonzero rationals, so a + b sqrt3 != 0
    for a in range(-20, 21):
        for b in range(-20, 21):
            if (a, b) != (0, 0):
                assert Q3(a, b).sign() != 0
    # tight comparisons: 1732/1000 < sqrt3 < 1733/1000; 265/153 < sqrt3 < 1351/780
    assert Q3(F(1732, 1000)) < SQRT3 < Q3(F(1733, 1000))
    assert Q3(F(265, 153)) < SQRT3 < Q3(F(1351, 780))


def test_float():
    assert abs(float(Q3(2, F(2, 3))) - (2 + 2 / 3 ** 0.5)) < 1e-12
