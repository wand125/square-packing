"""Exact arithmetic in Q(sqrt2): a + b*sqrt2 with rational a, b (gmpy2.mpq)."""
from gmpy2 import mpq


class Q2:
    __slots__ = ('a', 'b')

    def __init__(self, a=0, b=0):
        self.a = a if type(a) is type(mpq()) else mpq(a)
        self.b = b if type(b) is type(mpq()) else mpq(b)

    @staticmethod
    def parse(text):
        """'p/q', 'a+b*sqrt2', 'a-b*sqrt2' (a, b rationals); also plain 'b*sqrt2'."""
        s = str(text).replace(' ', '')
        if 'sqrt2' not in s:
            return Q2(mpq(s))
        body = s[:s.index('sqrt2')]
        if not body.endswith('*'):
            raise ValueError(f'cannot parse {text!r}')
        body = body[:-1]
        k = max(body.rfind('+'), body.rfind('-'))
        if k <= 0:
            return Q2(0, mpq(body))
        a, b = body[:k], body[k:]
        return Q2(mpq(a), mpq(b.lstrip('+')))

    def __add__(self, o):
        if not isinstance(o, Q2):
            o = Q2(o)
        return Q2(self.a + o.a, self.b + o.b)
    __radd__ = __add__

    def __neg__(self):
        return Q2(-self.a, -self.b)

    def __sub__(self, o):
        if not isinstance(o, Q2):
            o = Q2(o)
        return Q2(self.a - o.a, self.b - o.b)

    def __rsub__(self, o):
        return Q2(o) - self

    def __mul__(self, o):
        if not isinstance(o, Q2):
            o = mpq(o)
            return Q2(self.a * o, self.b * o)
        return Q2(self.a * o.a + 2 * self.b * o.b, self.a * o.b + self.b * o.a)
    __rmul__ = __mul__

    def conj(self):
        return Q2(self.a, -self.b)

    def norm(self):
        return self.a * self.a - 2 * self.b * self.b

    def __truediv__(self, o):
        if not isinstance(o, Q2):
            o = Q2(o)
        n = o.norm()
        if n == 0:
            raise ZeroDivisionError
        p = self * o.conj()
        return Q2(p.a / n, p.b / n)

    def sign(self):
        """Exact sign. a^2 = 2 b^2 has no nonzero rational solution, so opposite signs never cancel."""
        a, b = self.a, self.b
        sa = (a > 0) - (a < 0)
        sb = (b > 0) - (b < 0)
        if sa == sb or sb == 0:
            return sa
        if sa == 0:
            return sb
        d = a * a - 2 * b * b
        return sa if d > 0 else sb

    def is_zero(self):
        return self.a == 0 and self.b == 0

    def __eq__(self, o):
        if not isinstance(o, Q2):
            o = Q2(o)
        return self.a == o.a and self.b == o.b

    def __hash__(self):
        return hash((self.a, self.b))

    def __float__(self):
        return float(self.a) + float(self.b) * 1.4142135623730951

    def __repr__(self):
        return f'{self.a}+{self.b}*sqrt2' if self.b else f'{self.a}'


ZERO, ONE, SQRT2 = Q2(0), Q2(1), Q2(0, 1)
