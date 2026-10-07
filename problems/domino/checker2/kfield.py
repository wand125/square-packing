"""Exact arithmetic in K = Q(alpha), alpha the largest real root of f(x) = 5x^3 + 8x^2 - 32x - 4.

An element is a + b*alpha + c*alpha^2 with rationals a, b, c (gmpy2.mpq).

* alpha^3 = (4 + 32 alpha - 8 alpha^2) / 5.
* f is irreducible over Q (no rational root among +-1, +-2, +-4, +-1/5, +-2/5, +-4/5), so a
  nonzero element has a nonzero value, and its sign is decided by evaluating it on a rational
  interval around alpha with exact interval arithmetic, halving the interval until the
  enclosure excludes 0.  The interval is bisected by the sign of f at the midpoint (never 0).
* `norm_poly` maps a polynomial in u with coefficients in K to a polynomial with rational
  coefficients, the norm N(P) = det(multiplication by P on the basis 1, alpha, alpha^2), whose
  real roots contain those of P.
"""
from gmpy2 import mpq

F5 = (mpq(-4), mpq(-32), mpq(8), mpq(5))       # f = 5x^3 + 8x^2 - 32x - 4, low degree first


def f_at(x):
    return ((5 * x + 8) * x - 32) * x - 4


class _Alpha:
    """The current isolating interval of alpha (shrinks only)."""
    lo = mpq(19302833, 10 ** 7)
    hi = mpq(19302834, 10 ** 7)

    @classmethod
    def check(cls):
        # f is increasing for x >= 1.1 (f' = 15x^2 + 16x - 32 > 0 there), so alpha is the unique
        # root in [lo, hi] once f(lo) < 0 < f(hi); and it is the largest real root, because f > 0
        # for every x > hi.
        assert cls.lo > mpq(11, 10) and f_at(cls.lo) < 0 < f_at(cls.hi)

    @classmethod
    def halve(cls):
        m = (cls.lo + cls.hi) / 2
        v = f_at(m)
        assert v != 0
        if v < 0:
            cls.lo = m
        else:
            cls.hi = m


_Alpha.check()


def _ival_mul(a, b):
    p = [a[0] * b[0], a[0] * b[1], a[1] * b[0], a[1] * b[1]]
    return (min(p), max(p))


class K:
    __slots__ = ('a', 'b', 'c')

    def __init__(self, a=0, b=0, c=0):
        self.a = a if type(a) is type(mpq()) else mpq(a)
        self.b = b if type(b) is type(mpq()) else mpq(b)
        self.c = c if type(c) is type(mpq()) else mpq(c)

    @staticmethod
    def parse(text):
        s = str(text).replace(' ', '')
        if s.startswith('K[') and s.endswith(']'):
            a, b, c = s[2:-1].split(';')
            return K(mpq(a), mpq(b), mpq(c))
        return K(mpq(s))

    def _k(o):
        return o if isinstance(o, K) else K(o)

    def __add__(self, o):
        o = K._k(o)
        return K(self.a + o.a, self.b + o.b, self.c + o.c)
    __radd__ = __add__

    def __neg__(self):
        return K(-self.a, -self.b, -self.c)

    def __sub__(self, o):
        o = K._k(o)
        return K(self.a - o.a, self.b - o.b, self.c - o.c)

    def __rsub__(self, o):
        return K._k(o) - self

    def __mul__(self, o):
        if not isinstance(o, K):
            o = mpq(o)
            return K(self.a * o, self.b * o, self.c * o)
        # (a + b x + c x^2)(d + e x + g x^2), then reduce x^4 and x^3
        a, b, c, d, e, g = self.a, self.b, self.c, o.a, o.b, o.c
        r0 = a * d
        r1 = a * e + b * d
        r2 = a * g + b * e + c * d
        r3 = b * g + c * e
        r4 = c * g
        # x^3 = (4 + 32x - 8x^2)/5 ; x^4 = x * x^3 = (4x + 32x^2 - 8x^3)/5
        #     = (4x + 32x^2)/5 - 8/5 * (4 + 32x - 8x^2)/5
        r0 += r3 * mpq(4, 5) + r4 * mpq(-32, 25)
        r1 += r3 * mpq(32, 5) + r4 * (mpq(4, 5) - mpq(256, 25))
        r2 += r3 * mpq(-8, 5) + r4 * (mpq(32, 5) + mpq(64, 25))
        return K(r0, r1, r2)
    __rmul__ = __mul__

    def mat(self):
        """Matrix of multiplication by self on the basis (1, alpha, alpha^2), as columns."""
        cols = [self * K(1), self * K(0, 1), self * K(0, 0, 1)]
        return [[col.a, col.b, col.c] for col in cols]

    def inverse(self):
        if self.is_zero():
            raise ZeroDivisionError
        # solve M x = e1 for the coefficients of the inverse (M = multiplication matrix)
        M = [[self.mat()[j][i] for j in range(3)] for i in range(3)]   # rows
        aug = [M[i] + [mpq(1) if i == 0 else mpq(0)] for i in range(3)]
        for col in range(3):
            piv = next(r for r in range(col, 3) if aug[r][col] != 0)
            aug[col], aug[piv] = aug[piv], aug[col]
            pv = aug[col][col]
            aug[col] = [v / pv for v in aug[col]]
            for r in range(3):
                if r != col and aug[r][col] != 0:
                    fct = aug[r][col]
                    aug[r] = [aug[r][k] - fct * aug[col][k] for k in range(4)]
        inv = K(aug[0][3], aug[1][3], aug[2][3])
        assert (inv * self) == K(1)
        return inv

    def __truediv__(self, o):
        return self * K._k(o).inverse()

    def is_zero(self):
        return self.a == 0 and self.b == 0 and self.c == 0

    def sign(self):
        if self.b == 0 and self.c == 0:
            return (self.a > 0) - (self.a < 0)
        while True:
            lo, hi = _Alpha.lo, _Alpha.hi
            bx = _ival_mul((self.b, self.b), (lo, hi))
            cx = _ival_mul((self.c, self.c), (lo * lo, hi * hi))
            vlo = self.a + bx[0] + cx[0]
            vhi = self.a + bx[1] + cx[1]
            if vlo > 0:
                return 1
            if vhi < 0:
                return -1
            _Alpha.halve()

    def __eq__(self, o):
        o = K._k(o)
        return self.a == o.a and self.b == o.b and self.c == o.c

    def __hash__(self):
        return hash((self.a, self.b, self.c))

    def __float__(self):
        x = float((_Alpha.lo + _Alpha.hi) / 2)
        return float(self.a) + float(self.b) * x + float(self.c) * x * x

    def __repr__(self):
        return f'K[{self.a};{self.b};{self.c}]' if (self.b or self.c) else f'{self.a}'


def _pmul(p, q):
    if not p or not q:
        return []
    r = [mpq(0)] * (len(p) + len(q) - 1)
    for i, a in enumerate(p):
        if a:
            for j, b in enumerate(q):
                r[i + j] += a * b
    return r


def _padd(p, q):
    n = max(len(p), len(q))
    return [(p[i] if i < len(p) else 0) + (q[i] if i < len(q) else 0) for i in range(n)]


def _pneg(p):
    return [-x for x in p]


def norm_poly(p):
    """p: list of K coefficients (u-polynomial).  Returns rational coefficients of N(p)."""
    if all(c.b == 0 and c.c == 0 for c in p):
        return [c.a for c in p]
    # the multiplication matrix of p(u) has entries that are rational polynomials in u
    mats = [c.mat() for c in p]                      # mats[k][col][row]
    M = [[[mats[k][col][row] for k in range(len(p))] for col in range(3)] for row in range(3)]
    def m(r, c):
        return M[r][c]
    det = _padd(_padd(
        _pmul(m(0, 0), _padd(_pmul(m(1, 1), m(2, 2)), _pneg(_pmul(m(1, 2), m(2, 1))))),
        _pneg(_pmul(m(0, 1), _padd(_pmul(m(1, 0), m(2, 2)), _pneg(_pmul(m(1, 2), m(2, 0))))))),
        _pmul(m(0, 2), _padd(_pmul(m(1, 0), m(2, 1)), _pneg(_pmul(m(1, 1), m(2, 0))))))
    return det


ZERO, ONE = K(0), K(1)
