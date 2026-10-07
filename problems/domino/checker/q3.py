"""Exact arithmetic in the cubic number field K = Q(alpha), alpha = v4.

The class is called `Q3` for historical reasons (the checker was first written over Q(sqrt 3)
for a triangular container); here it implements the cubic field below.

The field
---------
alpha is the largest real root of

    f(x) = 5 x^3 + 8 x^2 - 32 x - 4      (alpha = 1.93028330671426938847...)

which is the short side of the best known packing of 4 unit squares in a 1 x 2 rectangle.
f has no rational root (rational root test: +-1, 2, 4, 1/5, 2/5, 4/5 all fail), so f is
irreducible over Q and 1, alpha, alpha^2 is a basis of K.  An element is stored as
(a, b, c) with exact Fractions and means a + b alpha + c alpha^2.

Products are reduced with alpha^3 = (-8 alpha^2 + 32 alpha + 4) / 5.  Inverses solve the
3 x 3 rational linear system e * x = 1 exactly.

Isolating interval
------------------
f'(x) = 15 x^2 + 16 x - 32 > 0 for x >= 1.1, so f is strictly increasing on [1.1, oo) and
has exactly one root there.  The checker starts from the rational interval

    I0 = [19302833/10^7, 19302834/10^7],   f(lo) < 0 < f(hi)  (checked exactly at import),

so alpha is the unique root of f in I0.

Exact comparisons
-----------------
sign(e) for e = a + b alpha + c alpha^2:
  * if b = c = 0 the sign of the rational a;
  * otherwise e(alpha) != 0, because a nonzero polynomial of degree <= 2 cannot vanish at an
    algebraic number of degree 3.  We evaluate e on the current isolating interval
    [lo, hi] (0 < lo) with exact interval arithmetic in Fractions:
        b alpha   in [min(b lo, b hi),   max(b lo, b hi)]
        c alpha^2 in [min(c lo^2, c hi^2), max(c lo^2, c hi^2)]
    If the resulting interval excludes 0 its sign is the answer.  Otherwise the interval of
    alpha is bisected at the rational midpoint m, keeping the half where f changes sign
    (f(m) != 0 since f has no rational root), and the evaluation is repeated.  This
    terminates because e(alpha) != 0 and the interval width halves each time.
  The refined interval is kept in a module global; it only ever shrinks around alpha, so it is
  always a valid isolating interval.
Equality is equality of the coordinate triples (valid since 1, alpha, alpha^2 is a basis).
Floats are used only by callers for guidance (__float__), never for a decision.

Text form: a rational "p/q", or "K[a;b;c]" for a + b alpha + c alpha^2 (no commas, so the
checker's comma separated --u-breaks still work).  "alpha" alone is accepted by parse.
"""
from __future__ import annotations

import re
from fractions import Fraction

_ZERO = Fraction(0)
_ONE = Fraction(1)

F_COEF = (Fraction(-4), Fraction(-32), Fraction(8), Fraction(5))   # f = -4 - 32x + 8x^2 + 5x^3


def f_eval(x: Fraction) -> Fraction:
    return ((5 * x + 8) * x - 32) * x - 4


_LO = Fraction(19302833, 10 ** 7)
_HI = Fraction(19302834, 10 ** 7)
assert f_eval(_LO) < 0 < f_eval(_HI), "isolating interval check failed"
assert 15 * Fraction(11, 10) ** 2 + 16 * Fraction(11, 10) - 32 > 0
ALPHA_FLOAT = 1.9302833067142693

# alpha^3 = R0 + R1 alpha + R2 alpha^2
_R0, _R1, _R2 = Fraction(4, 5), Fraction(32, 5), Fraction(-8, 5)


def isolating_interval():
    return _LO, _HI


def _refine():
    global _LO, _HI
    m = (_LO + _HI) / 2
    if f_eval(m) < 0:
        _LO = m
    else:
        _HI = m


def _frac(v) -> Fraction:
    if isinstance(v, Fraction):
        return v
    if isinstance(v, int):
        return Fraction(v)
    if isinstance(v, str):
        return Fraction(v)
    raise TypeError(f"cannot convert {type(v).__name__} to an exact rational")


class Q3:
    """a + b*alpha + c*alpha^2 with exact rational a, b, c (alpha = v4)."""

    __slots__ = ("a", "b", "c")

    def __init__(self, a=0, b=0, c=0):
        if isinstance(a, Q3):
            if b != 0 or c != 0:
                raise TypeError("Q3(Q3, b, c) is not supported")
            self.a, self.b, self.c = a.a, a.b, a.c
            return
        self.a = _frac(a)
        self.b = _frac(b)
        self.c = _frac(c)

    @staticmethod
    def _mk(a: Fraction, b: Fraction, c: Fraction) -> "Q3":
        r = object.__new__(Q3)
        r.a = a
        r.b = b
        r.c = c
        return r

    def __reduce__(self):
        return (Q3, (self.a, self.b, self.c))

    # ---------------------------------------------------------------- parsing
    @staticmethod
    def parse(s) -> "Q3":
        if isinstance(s, Q3):
            return s
        if isinstance(s, (int, Fraction)):
            return Q3(s)
        if not isinstance(s, str):
            raise TypeError(f"cannot parse {s!r}")
        t = s.replace(" ", "")
        if t == "alpha":
            return Q3._mk(_ZERO, _ONE, _ZERO)
        m = re.fullmatch(r"K\[([^;\]]+);([^;\]]+);([^;\]]+)\]", t)
        if m:
            return Q3._mk(Fraction(m.group(1)), Fraction(m.group(2)), Fraction(m.group(3)))
        if not re.fullmatch(r"-?\d+(/\d+)?", t):
            raise ValueError(f"cannot parse {s!r} as an element of Q(alpha)")
        return Q3._mk(Fraction(t), _ZERO, _ZERO)

    # ---------------------------------------------------------------- basics
    def key(self):
        return (self.a, self.b, self.c)

    def is_zero(self) -> bool:
        return not self.a and not self.b and not self.c

    def is_rational(self) -> bool:
        return not self.b and not self.c

    def sign(self) -> int:
        a, b, c = self.a, self.b, self.c
        if not b and not c:
            return (a > 0) - (a < 0)
        while True:
            lo, hi = _LO, _HI
            t1, t2 = b * lo, b * hi
            s1, s2 = c * lo * lo, c * hi * hi
            mn = a + min(t1, t2) + min(s1, s2)
            mx = a + max(t1, t2) + max(s1, s2)
            if mn > 0:
                return 1
            if mx < 0:
                return -1
            _refine()

    def __float__(self) -> float:
        return float(self.a) + float(self.b) * ALPHA_FLOAT + float(self.c) * ALPHA_FLOAT * ALPHA_FLOAT

    def __repr__(self) -> str:
        return f"Q3({self})"

    def __str__(self) -> str:
        if not self.b and not self.c:
            return str(self.a)
        return f"K[{self.a};{self.b};{self.c}]"

    def __hash__(self):
        return hash((self.a, self.b, self.c))

    # ---------------------------------------------------------------- arithmetic
    @staticmethod
    def _coerce(o) -> "Q3":
        if isinstance(o, Q3):
            return o
        if isinstance(o, (int, Fraction)):
            return Q3._mk(Fraction(o), _ZERO, _ZERO)
        return NotImplemented

    def __add__(self, o):
        o = Q3._coerce(o)
        if o is NotImplemented:
            return o
        return Q3._mk(self.a + o.a, self.b + o.b, self.c + o.c)

    __radd__ = __add__

    def __sub__(self, o):
        o = Q3._coerce(o)
        if o is NotImplemented:
            return o
        return Q3._mk(self.a - o.a, self.b - o.b, self.c - o.c)

    def __rsub__(self, o):
        o = Q3._coerce(o)
        if o is NotImplemented:
            return o
        return Q3._mk(o.a - self.a, o.b - self.b, o.c - self.c)

    def __neg__(self):
        return Q3._mk(-self.a, -self.b, -self.c)

    def __pos__(self):
        return self

    def __mul__(self, o):
        if isinstance(o, (int, Fraction)):
            return Q3._mk(self.a * o, self.b * o, self.c * o)
        if not isinstance(o, Q3):
            return NotImplemented
        a1, b1, c1, a2, b2, c2 = self.a, self.b, self.c, o.a, o.b, o.c
        if not b2 and not c2:
            return Q3._mk(a1 * a2, b1 * a2, c1 * a2)
        if not b1 and not c1:
            return Q3._mk(a1 * a2, a1 * b2, a1 * c2)
        # (a1 + b1 x + c1 x^2)(a2 + b2 x + c2 x^2) = d0 + d1 x + d2 x^2 + d3 x^3 + d4 x^4
        d0 = a1 * a2
        d1 = a1 * b2 + b1 * a2
        d2 = a1 * c2 + b1 * b2 + c1 * a2
        d3 = b1 * c2 + c1 * b2
        d4 = c1 * c2
        # x^4 = x * x^3 = R0 x + R1 x^2 + R2 x^3  ->  fold into d3
        if d4:
            d1 += d4 * _R0
            d2 += d4 * _R1
            d3 += d4 * _R2
        if d3:
            d0 += d3 * _R0
            d1 += d3 * _R1
            d2 += d3 * _R2
        return Q3._mk(d0, d1, d2)

    __rmul__ = __mul__

    def inverse(self) -> "Q3":
        if self.is_zero():
            raise ZeroDivisionError("division by zero in Q(alpha)")
        if self.is_rational():
            return Q3._mk(1 / self.a, _ZERO, _ZERO)
        # columns: e*1, e*alpha, e*alpha^2 ; solve M x = (1,0,0)
        cols = [self, self * Q3._mk(_ZERO, _ONE, _ZERO), self * Q3._mk(_ZERO, _ZERO, _ONE)]
        M = [[cols[j].key()[i] for j in range(3)] + [_ONE if i == 0 else _ZERO] for i in range(3)]
        for col in range(3):
            piv = next(r for r in range(col, 3) if M[r][col] != 0)
            M[col], M[piv] = M[piv], M[col]
            pv = M[col][col]
            M[col] = [v / pv for v in M[col]]
            for r in range(3):
                if r != col and M[r][col] != 0:
                    fac = M[r][col]
                    M[r] = [vr - fac * vc for vr, vc in zip(M[r], M[col])]
        res = Q3._mk(M[0][3], M[1][3], M[2][3])
        assert (self * res) == Q3._mk(_ONE, _ZERO, _ZERO)
        return res

    def __truediv__(self, o):
        if isinstance(o, (int, Fraction)):
            if o == 0:
                raise ZeroDivisionError("division by zero in Q(alpha)")
            return Q3._mk(self.a / o, self.b / o, self.c / o)
        o = Q3._coerce(o)
        if o is NotImplemented:
            return o
        return self * o.inverse()

    def __rtruediv__(self, o):
        o = Q3._coerce(o)
        if o is NotImplemented:
            return o
        return o * self.inverse()

    # ---------------------------------------------------------------- comparisons
    def __eq__(self, o):
        o = Q3._coerce(o)
        if o is NotImplemented:
            return False
        return self.a == o.a and self.b == o.b and self.c == o.c

    def __ne__(self, o):
        return not self.__eq__(o)

    def _cmp(self, o) -> int:
        o = Q3._coerce(o)
        if o is NotImplemented:
            raise TypeError("cannot compare")
        return Q3._mk(self.a - o.a, self.b - o.b, self.c - o.c).sign()

    def __lt__(self, o):
        return self._cmp(o) < 0

    def __le__(self, o):
        return self._cmp(o) <= 0

    def __gt__(self, o):
        return self._cmp(o) > 0

    def __ge__(self, o):
        return self._cmp(o) >= 0


ZERO = Q3(0)
ONE = Q3(1)
ALPHA = Q3(0, 1)
