"""Exact arithmetic in the number field Q(sqrt 2).

A value is a + b*sqrt(2) with a, b of type fractions.Fraction.  Every comparison
is decided exactly: the sign of a + b*sqrt(2) is obtained from the signs of a, b
and, when they differ, from comparing a^2 with 2 b^2 (which can never be equal
for (a, b) != (0, 0) because sqrt(2) is irrational).
"""
from __future__ import annotations

import re
from fractions import Fraction

SQRT2_FLOAT = 1.4142135623730951

_ZERO = Fraction(0)
_ONE = Fraction(1)


def _frac(v) -> Fraction:
    if isinstance(v, Fraction):
        return v
    if isinstance(v, int):
        return Fraction(v)
    if isinstance(v, str):
        return Fraction(v)
    raise TypeError(f"cannot convert {type(v).__name__} to an exact rational")


class Q2:
    """a + b*sqrt(2) with exact rational a, b."""

    __slots__ = ("a", "b")

    def __init__(self, a=0, b=0):
        if isinstance(a, Q2):
            if b != 0:
                raise TypeError("Q2(Q2, b) is not supported")
            self.a, self.b = a.a, a.b
            return
        self.a = _frac(a)
        self.b = _frac(b)

    @staticmethod
    def _mk(a: Fraction, b: Fraction) -> "Q2":
        r = object.__new__(Q2)
        r.a = a
        r.b = b
        return r

    def __reduce__(self):
        return (Q2, (self.a, self.b))

    # ---------------------------------------------------------------- parsing
    @staticmethod
    def parse(s) -> "Q2":
        """Parse "a", "a+b*sqrt2", "b*sqrt2", "-sqrt2", "3/2-1/3*sqrt(2)", ..."""
        if isinstance(s, Q2):
            return s
        if isinstance(s, (int, Fraction)):
            return Q2(s)
        if not isinstance(s, str):
            raise TypeError(f"cannot parse {s!r} as Q2")
        t = s.replace(" ", "").replace("sqrt(2)", "sqrt2").replace("√2", "sqrt2")
        if not t:
            raise ValueError("empty Q2 string")
        # split into signed terms
        terms = re.findall(r"[+-]?[^+-]+", t)
        if "".join(terms) != t:
            raise ValueError(f"cannot parse {s!r}")
        a = Fraction(0)
        b = Fraction(0)
        for term in terms:
            sign = 1
            if term[0] in "+-":
                sign = -1 if term[0] == "-" else 1
                term = term[1:]
            if term.endswith("sqrt2"):
                coef = term[: -len("sqrt2")]
                if coef.endswith("*"):
                    coef = coef[:-1]
                c = Fraction(1) if coef == "" else Fraction(coef)
                b += sign * c
            else:
                if not re.fullmatch(r"\d+(/\d+)?", term):
                    raise ValueError(f"bad rational term {term!r} in {s!r}")
                a += sign * Fraction(term)
        return Q2._mk(a, b)

    # ---------------------------------------------------------------- basics
    def is_zero(self) -> bool:
        return not self.a and not self.b

    def is_rational(self) -> bool:
        return not self.b

    def sign(self) -> int:
        a, b = self.a, self.b
        if not b:
            return (a > 0) - (a < 0)
        if not a:
            return (b > 0) - (b < 0)
        if a > 0 and b > 0:
            return 1
        if a < 0 and b < 0:
            return -1
        d = a * a - 2 * b * b
        # d == 0 is impossible for nonzero rationals (sqrt 2 is irrational)
        assert d != 0
        if a > 0:  # b < 0: sign is that of a - |b| sqrt2
            return 1 if d > 0 else -1
        return -1 if d > 0 else 1  # a < 0, b > 0

    def __float__(self) -> float:
        return float(self.a) + float(self.b) * SQRT2_FLOAT

    def __repr__(self) -> str:
        return f"Q2({self})"

    def __str__(self) -> str:
        if not self.b:
            return str(self.a)
        if not self.a:
            return f"{self.b}*sqrt2"
        sgn = "+" if self.b > 0 else "-"
        return f"{self.a}{sgn}{abs(self.b)}*sqrt2"

    def __hash__(self):
        return hash((self.a, self.b))

    # ---------------------------------------------------------------- arithmetic
    @staticmethod
    def _coerce(o) -> "Q2":
        if isinstance(o, Q2):
            return o
        if isinstance(o, (int, Fraction)):
            return Q2._mk(Fraction(o), _ZERO)
        return NotImplemented

    def __add__(self, o):
        o = Q2._coerce(o)
        if o is NotImplemented:
            return o
        return Q2._mk(self.a + o.a, self.b + o.b)

    __radd__ = __add__

    def __sub__(self, o):
        o = Q2._coerce(o)
        if o is NotImplemented:
            return o
        return Q2._mk(self.a - o.a, self.b - o.b)

    def __rsub__(self, o):
        o = Q2._coerce(o)
        if o is NotImplemented:
            return o
        return Q2._mk(o.a - self.a, o.b - self.b)

    def __neg__(self):
        return Q2._mk(-self.a, -self.b)

    def __pos__(self):
        return self

    def __mul__(self, o):
        if isinstance(o, Q2):
            a1, b1, a2, b2 = self.a, self.b, o.a, o.b
            if not b1:
                if not b2:
                    return Q2._mk(a1 * a2, _ZERO)
                return Q2._mk(a1 * a2, a1 * b2)
            if not b2:
                return Q2._mk(a1 * a2, b1 * a2)
            return Q2._mk(a1 * a2 + 2 * b1 * b2, a1 * b2 + b1 * a2)
        if isinstance(o, (int, Fraction)):
            return Q2._mk(self.a * o, self.b * o)
        return NotImplemented

    __rmul__ = __mul__

    def inverse(self) -> "Q2":
        a, b = self.a, self.b
        if not b:
            if not a:
                raise ZeroDivisionError("Q2 division by zero")
            return Q2._mk(1 / a, _ZERO)
        n = a * a - 2 * b * b
        return Q2._mk(a / n, -b / n)

    def __truediv__(self, o):
        if isinstance(o, (int, Fraction)):
            if o == 0:
                raise ZeroDivisionError("Q2 division by zero")
            return Q2._mk(self.a / o, self.b / o)
        o = Q2._coerce(o)
        if o is NotImplemented:
            return o
        return self * o.inverse()

    def __rtruediv__(self, o):
        o = Q2._coerce(o)
        if o is NotImplemented:
            return o
        return o * self.inverse()

    # ---------------------------------------------------------------- comparisons
    def __eq__(self, o):
        o = Q2._coerce(o)
        if o is NotImplemented:
            return False
        return self.a == o.a and self.b == o.b

    def __ne__(self, o):
        return not self.__eq__(o)

    def _cmp(self, o) -> int:
        o = Q2._coerce(o)
        if o is NotImplemented:
            raise TypeError("cannot compare")
        return Q2._mk(self.a - o.a, self.b - o.b).sign()

    def __lt__(self, o):
        return self._cmp(o) < 0

    def __le__(self, o):
        return self._cmp(o) <= 0

    def __gt__(self, o):
        return self._cmp(o) > 0

    def __ge__(self, o):
        return self._cmp(o) >= 0


ZERO = Q2(0)
ONE = Q2(1)
SQRT2 = Q2(0, 1)
