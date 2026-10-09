from fractions import Fraction as F

from poly import P, nonneg_on, to_bern, pmul, peval
from q2 import Q2


def test_bernstein_endpoints_and_exactness():
    p = P(1, -3, 0, 2)  # 1 - 3u + 2u^3
    a, b = Q2(F(1, 5)), Q2(2, -1)
    bc = to_bern(p, a, b)
    assert bc[0] == peval(p, a) and bc[-1] == peval(p, b)


def test_u_one_minus_u():
    assert nonneg_on(P(0, 1, -1), 0, 1)


def test_rejects_u_minus_tenth():
    assert not nonneg_on(P(F(-1, 10), 1), 0, 1)
    assert not nonneg_on(P(F(-1, 10), 1), 0, 1, snap=True)


def test_double_root_interior_needs_endpoint():
    sq = pmul(P(F(-1, 3), 1), P(F(-1, 3), 1))   # (u - 1/3)^2
    # dyadic halving never puts 1/3 at an endpoint: this is reported as "cannot prove"
    assert not nonneg_on(sq, 0, 1)
    # with the root at an interval endpoint the margin-zero case is accepted
    assert nonneg_on(sq, 0, F(1, 3)) and nonneg_on(sq, F(1, 3), 1)
    # exact root snapping (float-guided, exactly checked) finds the split point
    assert nonneg_on(sq, 0, 1, snap=True)


def test_q2_endpoints_margin_zero():
    r = Q2(-1, 1)                                # sqrt2 - 1 = tan(pi/8)
    lin = [-r, Q2(1)]                            # u - r
    assert nonneg_on(lin, r, 1)
    assert not nonneg_on(lin, r, 1, strict=True)
    assert nonneg_on(lin, Q2(F(42, 100)), 1, strict=True)
    assert not nonneg_on(lin, Q2(F(41, 100)), 1)
    assert nonneg_on(pmul(lin, lin), 0, r) and nonneg_on(pmul(lin, lin), r, 1)
