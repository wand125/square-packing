"""Exact arithmetic in the number field Q(sqrt 3).

A value is a + b*sqrt(3) with a, b of type fractions.Fraction.  Every comparison
is decided exactly: the sign of a + b*sqrt(3) is obtained from the signs of a, b
and, when they differ, from comparing a^2 with 3 b^2 (which can never be equal
for (a, b) != (0, 0) because sqrt(3) is irrational).
"""
from __future__ import annotations

import re
from fractions import Fraction

SQRT3_FLOAT = 1.7320508075688772

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


class Q3:
    """a + b*sqrt(3) with exact rational a, b."""

    __slots__ = ("a", "b")

    def __init__(self, a=0, b=0):
        if isinstance(a, Q3):
            if b != 0:
                raise TypeError("Q3(Q3, b) is not supported")
            self.a, self.b = a.a, a.b
            return
        self.a = _frac(a)
        self.b = _frac(b)

    @staticmethod
    def _mk(a: Fraction, b: Fraction) -> "Q3":
        r = object.__new__(Q3)
        r.a = a
        r.b = b
        return r

    def __reduce__(self):
        return (Q3, (self.a, self.b))

    # ---------------------------------------------------------------- parsing
    @staticmethod
    def parse(s) -> "Q3":
        """Parse "a", "a+b*sqrt3", "b*sqrt3", "-sqrt3", "3/2-1/3*sqrt(3)", ..."""
        if isinstance(s, Q3):
            return s
        if isinstance(s, (int, Fraction)):
            return Q3(s)
        if not isinstance(s, str):
            raise TypeError(f"cannot parse {s!r} as Q3")
        t = s.replace(" ", "").replace("sqrt(3)", "sqrt3").replace("√3", "sqrt3")
        if not t:
            raise ValueError("empty Q3 string")
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
            if term.endswith("sqrt3"):
                coef = term[: -len("sqrt3")]
                if coef.endswith("*"):
                    coef = coef[:-1]
                c = Fraction(1) if coef == "" else Fraction(coef)
                b += sign * c
            else:
                if not re.fullmatch(r"\d+(/\d+)?", term):
                    raise ValueError(f"bad rational term {term!r} in {s!r}")
                a += sign * Fraction(term)
        return Q3._mk(a, b)

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
        d = a * a - 3 * b * b
        # d == 0 is impossible for nonzero rationals (sqrt 3 is irrational)
        assert d != 0
        if a > 0:  # b < 0: sign is that of a - |b| sqrt3
            return 1 if d > 0 else -1
        return -1 if d > 0 else 1  # a < 0, b > 0

    def __float__(self) -> float:
        return float(self.a) + float(self.b) * SQRT3_FLOAT

    def __repr__(self) -> str:
        return f"Q3({self})"

    def __str__(self) -> str:
        if not self.b:
            return str(self.a)
        if not self.a:
            return f"{self.b}*sqrt3"
        sgn = "+" if self.b > 0 else "-"
        return f"{self.a}{sgn}{abs(self.b)}*sqrt3"

    def __hash__(self):
        return hash((self.a, self.b))

    # ---------------------------------------------------------------- arithmetic
    @staticmethod
    def _coerce(o) -> "Q3":
        if isinstance(o, Q3):
            return o
        if isinstance(o, (int, Fraction)):
            return Q3._mk(Fraction(o), _ZERO)
        return NotImplemented

    def __add__(self, o):
        o = Q3._coerce(o)
        if o is NotImplemented:
            return o
        return Q3._mk(self.a + o.a, self.b + o.b)

    __radd__ = __add__

    def __sub__(self, o):
        o = Q3._coerce(o)
        if o is NotImplemented:
            return o
        return Q3._mk(self.a - o.a, self.b - o.b)

    def __rsub__(self, o):
        o = Q3._coerce(o)
        if o is NotImplemented:
            return o
        return Q3._mk(o.a - self.a, o.b - self.b)

    def __neg__(self):
        return Q3._mk(-self.a, -self.b)

    def __pos__(self):
        return self

    def __mul__(self, o):
        if isinstance(o, Q3):
            a1, b1, a2, b2 = self.a, self.b, o.a, o.b
            if not b1:
                if not b2:
                    return Q3._mk(a1 * a2, _ZERO)
                return Q3._mk(a1 * a2, a1 * b2)
            if not b2:
                return Q3._mk(a1 * a2, b1 * a2)
            return Q3._mk(a1 * a2 + 3 * b1 * b2, a1 * b2 + b1 * a2)
        if isinstance(o, (int, Fraction)):
            return Q3._mk(self.a * o, self.b * o)
        return NotImplemented

    __rmul__ = __mul__

    def inverse(self) -> "Q3":
        a, b = self.a, self.b
        if not b:
            if not a:
                raise ZeroDivisionError("Q3 division by zero")
            return Q3._mk(1 / a, _ZERO)
        n = a * a - 3 * b * b
        return Q3._mk(a / n, -b / n)

    def __truediv__(self, o):
        if isinstance(o, (int, Fraction)):
            if o == 0:
                raise ZeroDivisionError("Q3 division by zero")
            return Q3._mk(self.a / o, self.b / o)
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
        return self.a == o.a and self.b == o.b

    def __ne__(self, o):
        return not self.__eq__(o)

    def _cmp(self, o) -> int:
        o = Q3._coerce(o)
        if o is NotImplemented:
            raise TypeError("cannot compare")
        return Q3._mk(self.a - o.a, self.b - o.b).sign()

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
SQRT3 = Q3(0, 1)
