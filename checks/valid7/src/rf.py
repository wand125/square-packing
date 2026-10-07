"""Rational functions of u over Q with a sample point, for symbolic execution of the exact solver.

Every comparison made on an RF is decided by its sign at the sample point u*, and the polynomial whose sign was
used is recorded as a *guard*.  If every guard keeps its sign on an open interval I containing u*, the whole
computation (every branch) is the same for every u in I, so its outputs are the same rational functions on I.
An RF that is not identically zero but vanishes at u* raises Resample: the trace is not stable at u*.
"""
from fractions import Fraction
import flint

P = flint.fmpq_poly
Q = flint.fmpq


class Resample(Exception):
    pass


class Ctx:
    def __init__(self, u):
        self.u = Q(u.numerator, u.denominator) if isinstance(u, Fraction) else Q(u)
        self.guards = {}

    def var(self):
        return RF(P([0, 1]), P([1]), self)


def _q(x):
    if isinstance(x, Fraction):
        return Q(x.numerator, x.denominator)
    return Q(x)


class RF:
    __slots__ = ('n', 'd', 'c', '_v')

    def __init__(self, n, d, c, reduce=True):
        if reduce:
            if d.degree() > 0 or n.degree() > 0:
                g = n.gcd(d)
                if g.degree() > 0:
                    n, d = n // g, d // g
            lc = d[d.degree()]
            if lc != 1:
                n, d = n / lc, d / lc
        self.n, self.d, self.c, self._v = n, d, c, None

    def lift(self, x):
        if isinstance(x, RF):
            return x
        return RF(P([_q(x)]), P([1]), self.c, reduce=False)

    def __add__(self, o):
        o = self.lift(o)
        if self.d == o.d:
            return RF(self.n + o.n, self.d, self.c)
        return RF(self.n * o.d + o.n * self.d, self.d * o.d, self.c)
    __radd__ = __add__

    def __sub__(self, o):
        o = self.lift(o)
        if self.d == o.d:
            return RF(self.n - o.n, self.d, self.c)
        return RF(self.n * o.d - o.n * self.d, self.d * o.d, self.c)

    def __rsub__(self, o):
        return self.lift(o) - self

    def __neg__(self):
        return RF(-self.n, self.d, self.c, reduce=False)

    def __mul__(self, o):
        o = self.lift(o)
        return RF(self.n * o.n, self.d * o.d, self.c)
    __rmul__ = __mul__

    def __truediv__(self, o):
        o = self.lift(o)
        if o.n == 0:
            raise ZeroDivisionError
        return RF(self.n * o.d, self.d * o.n, self.c)

    def __rtruediv__(self, o):
        return self.lift(o) / self

    def value(self):
        if self._v is None:
            self._v = self.n(self.c.u) / self.d(self.c.u)
        return self._v

    def sign(self):
        if self.n == 0:
            return 0
        v = self.value()
        if v == 0:
            raise Resample()
        g = self.n * self.d          # same sign as self wherever d != 0
        key = str(g)                 # dedupe identical guards
        if key not in self.c.guards:
            self.c.guards[key] = g
        return 1 if v > 0 else -1

    def __lt__(self, o): return (self - o).sign() < 0
    def __le__(self, o): return (self - o).sign() <= 0
    def __gt__(self, o): return (self - o).sign() > 0
    def __ge__(self, o): return (self - o).sign() >= 0

    def __eq__(self, o):
        o = self.lift(o)
        return self.n * o.d == o.n * self.d          # identity of rational functions (no guard)

    def __ne__(self, o):
        return not self.__eq__(o)

    def __hash__(self):
        return hash((str(self.n), str(self.d)))

    def __abs__(self):
        return -self if self.sign() < 0 else self

    def __repr__(self):
        return f'({self.n})/({self.d})'


# ---------------- exact real-root tools (Sturm) ----------------

def squarefree(p):
    g = p.gcd(p.derivative())
    return p // g if g.degree() > 0 else p


def sturm(p):
    seq = [p, p.derivative()]
    while seq[-1].degree() > 0 or (seq[-1].degree() == 0 and False):
        r = -(seq[-2] % seq[-1])
        if r == 0:
            break
        seq.append(r)
    return seq


def _var(seq, x):
    s = [q(x) for q in seq]
    s = [v for v in s if v != 0]
    return sum(1 for a, b in zip(s, s[1:]) if (a > 0) != (b > 0))


def count_roots(seq, lo, hi):
    """Number of distinct real roots in (lo, hi] of the squarefree polynomial seq[0]."""
    return _var(seq, lo) - _var(seq, hi)


def isolate(p, lo, hi):
    """Disjoint intervals (l, r] covering the distinct real roots of p in (lo, hi], one root each; no interval
    endpoint other than possibly hi is a root.  Exact (Sturm + bisection at non-roots)."""
    p = squarefree(p)
    if p.degree() <= 0:
        return []
    seq = sturm(p)
    out, stack = [], [(lo, hi)]
    while stack:
        l, r = stack.pop()
        k = count_roots(seq, l, r)
        if k == 0:
            continue
        if k == 1:
            out.append((l, r)); continue
        m = (l + r) / 2
        while p(m) == 0:
            m = (l + 2 * m) / 3
        stack += [(l, m), (m, r)]
    return sorted(out)


def roots_open(p, lo, hi):
    """Isolating intervals (l, r] of the distinct real roots of p in the open interval (lo, hi)."""
    lo, hi = Q(lo), Q(hi)
    out = isolate(p, lo, hi)
    if p(hi) == 0:
        out = [iv for iv in out if iv[1] != hi]   # the interval ending at hi holds the root hi itself
    return out


def nonneg_on(p, lo, hi):
    """Exact: p(x) >= 0 for all x in [lo, hi].  No root of odd multiplicity strictly inside, p >= 0 at both ends,
    and p > 0 at one interior point that is not a root."""
    lo, hi = Q(lo), Q(hi)
    if p == 0:
        return True
    if p(lo) < 0 or p(hi) < 0:
        return False
    c, facs = p.factor_squarefree()
    odd = P([1])
    for q, k in facs:
        if k % 2 == 1:
            odd = odd * q
    if odd.degree() > 0:
        seq = sturm(squarefree(odd))
        inside = count_roots(seq, lo, hi) - (1 if odd(hi) == 0 else 0)
        if inside > 0:
            return False
    s = (lo + hi) / 2
    while p(s) == 0:
        s = (s + hi) / 2
    return p(s) > 0
