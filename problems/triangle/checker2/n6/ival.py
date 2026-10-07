"""Small rigorous interval arithmetic on floats (outward rounding by one ulp after every operation).

cos/sin use libm (error < 1 ulp on the platforms we use) and are widened by 4 ulp-sized steps plus 1e-15,
with the exact extrema handled by locating multiples of pi/2 inside the argument interval
(pi itself is enclosed by [PI_LO, PI_HI]).
"""
import math

nd = math.nextafter
INF = math.inf
PI_LO = 3.141592653589793      # float(pi) < pi
PI_HI = nd(PI_LO, INF)


def down(x):
    return nd(x, -INF)


def up(x):
    return nd(x, INF)


class I:
    __slots__ = ('lo', 'hi')

    def __init__(self, lo, hi=None):
        if hi is None:
            hi = lo
        self.lo, self.hi = lo, hi

    def __add__(self, o):
        o = _c(o)
        return I(down(self.lo + o.lo), up(self.hi + o.hi))
    __radd__ = __add__

    def __neg__(self):
        return I(-self.hi, -self.lo)

    def __sub__(self, o):
        o = _c(o)
        return I(down(self.lo - o.hi), up(self.hi - o.lo))

    def __rsub__(self, o):
        return _c(o) - self

    def __mul__(self, o):
        o = _c(o)
        ps = (self.lo * o.lo, self.lo * o.hi, self.hi * o.lo, self.hi * o.hi)
        return I(down(min(ps)), up(max(ps)))
    __rmul__ = __mul__

    def abs(self):
        if self.lo >= 0:
            return self
        if self.hi <= 0:
            return -self
        return I(0.0, max(-self.lo, self.hi))

    def mid(self):
        return 0.5 * (self.lo + self.hi)

    def __repr__(self):
        return f'[{self.lo!r}, {self.hi!r}]'


def _c(x):
    return x if isinstance(x, I) else I(float(x), float(x)) if float(x) == x else I(down(float(x)), up(float(x)))


def exact(xf, err=1e-15):
    """enclosure of an exact real known to be within err of the float xf."""
    return I(down(xf - err), up(xf + err))


def _widen(a, b):
    e = 1e-15
    return down(a - e), up(b + e)


def cos(x):
    lo, hi = x.lo, x.hi
    vals = [math.cos(lo), math.cos(hi)]
    a, b = _widen(min(vals), max(vals))
    # extrema at k*pi: cos = +1 (k even) or -1 (k odd)
    k0 = math.floor(lo / PI_HI) - 1
    for k in range(k0, k0 + int((hi - lo) / PI_LO) + 4):
        # does some point of [k*PI_LO, k*PI_HI] (contains k*pi) meet [lo, hi]?
        kl, kh = sorted((k * PI_LO, k * PI_HI))
        if kh >= lo and kl <= hi:
            if k % 2 == 0:
                b = 1.0
            else:
                a = -1.0
    return I(max(a, -1.0), min(b, 1.0))


def sin(x):
    # sin(x) = cos(x - pi/2)
    return cos(x - I(PI_LO / 2, PI_HI / 2))
