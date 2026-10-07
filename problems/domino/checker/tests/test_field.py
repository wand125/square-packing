"""Tests for the field K = Q(alpha) and the n = 4 critical angle."""
import os
import random
import sys
from decimal import Decimal, getcontext
from fractions import Fraction as F

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from q3 import Q3, ALPHA, f_eval  # noqa: E402

getcontext().prec = 80


def _alpha_dec():
    lo, hi = Decimal("1.9302833"), Decimal("1.9302834")
    f = lambda x: ((5 * x + 8) * x - 32) * x - 4  # noqa: E731
    for _ in range(260):
        m = (lo + hi) / 2
        if f(m) < 0:
            lo = m
        else:
            hi = m
    return lo


A = _alpha_dec()


def _dec(e):
    q = lambda r: Decimal(r.numerator) / Decimal(r.denominator)  # noqa: E731
    return q(e.a) + q(e.b) * A + q(e.c) * A * A


def _rand(rng):
    return Q3(*(F(rng.randint(-60, 60), rng.randint(1, 30)) for _ in range(3)))


def test_no_rational_root():
    for p in (1, 2, 4):
        for q in (1, 5):
            for s in (1, -1):
                assert f_eval(F(s * p, q)) != 0


def test_sign_product_inverse():
    rng = random.Random(7)
    for _ in range(2000):
        x, y = _rand(rng), _rand(rng)
        assert abs(_dec(x * y) - _dec(x) * _dec(y)) < Decimal(10) ** -60
        if not x.is_zero():
            v = _dec(x)
            assert x.sign() == (1 if v > 0 else -1)
            assert x * x.inverse() == Q3(1)
            assert (x / y if not y.is_zero() else x) is not None


def test_near_zero_elements():
    # tiny but nonzero values: rational approximations of alpha and alpha^2
    for den in (10 ** 3, 10 ** 6, 10 ** 9):
        r = F(round(float(A) * den), den)
        e = ALPHA - r
        assert e.sign() == (1 if _dec(e) > 0 else -1)
        e2 = ALPHA * ALPHA - F(round(float(A * A) * den), den)
        assert e2.sign() == (1 if _dec(e2) > 0 else -1)


def test_critical_angle_identities():
    u = Q3.parse("K[-21/37;-11/37;15/37]")
    assert (u * u * u - 5 * u * u - u + 1).is_zero()
    s = (-2 * (u + 1) * (u + 1) * (u * u - 2 * u - 1)) / (u * u * u * u - 4 * u * u * u + 6 * u * u + 4 * u + 1)
    assert s == ALPHA
    assert Q3(0) < u < Q3(F(5, 12))


def test_parse_roundtrip():
    rng = random.Random(3)
    for _ in range(200):
        x = _rand(rng)
        assert Q3.parse(str(x)) == x
