"""Univariate polynomials over the number field K (module q3) and exact Bernstein positivity tests.

A polynomial is a list of Q3 coefficients, index = power of u.

Bernstein coefficients of p on an interval [a, b] (a < b, both in Q3) are the
coefficients of q(t) = p(a + (b - a) t) in the degree-n Bernstein basis
C(n, k) t^k (1 - t)^(n - k) of [0, 1].  Standard facts used for soundness:

* The basis functions are >= 0 on [0, 1] and sum to 1, so
  min_k b_k <= p(u) for u in [a, b].  All b_k >= 0 implies p >= 0 on [a, b];
  all b_k > 0 implies p > 0 on [a, b].
* b_0 = p(a) and b_n = p(b).  So b_0 < 0 or b_n < 0 is a genuine witness of
  negativity, and a zero of p at an endpoint shows up as b_0 = 0 or b_n = 0.
* De Casteljau at t = 1/2 gives the exact Bernstein coefficients on the two
  halves [a, m] and [m, b], m = (a + b)/2.

Everything here is exact; floats are used only in `snap_roots` to *propose*
candidate split points, which are then checked exactly.
"""
from __future__ import annotations

from fractions import Fraction
from math import comb

from q3 import Q3, ZERO

DEG = 4  # all Bernstein vectors in the checker use this common degree


# ------------------------------------------------------------------ polynomials
def P(*coefs) -> list:
    return [Q3.parse(c) if not isinstance(c, Q3) else c for c in coefs]


def ptrim(p):
    p = list(p)
    while p and p[-1].is_zero():
        p.pop()
    return p


def padd(p, q):
    n = max(len(p), len(q))
    return [(p[i] if i < len(p) else ZERO) + (q[i] if i < len(q) else ZERO) for i in range(n)]


def psub(p, q):
    n = max(len(p), len(q))
    return [(p[i] if i < len(p) else ZERO) - (q[i] if i < len(q) else ZERO) for i in range(n)]


def pscale(p, c):
    return [x * c for x in p]


def pmul(p, q):
    if not p or not q:
        return []
    r = [ZERO] * (len(p) + len(q) - 1)
    for i, x in enumerate(p):
        if x.is_zero():
            continue
        for j, y in enumerate(q):
            if y.is_zero():
                continue
            r[i + j] = r[i + j] + x * y
    return r


def peval(p, u):
    r = ZERO
    for c in reversed(p):
        r = r * u + c
    return r


def pfloat(p):
    return [float(c) for c in p]


def feval(pf, u: float) -> float:
    r = 0.0
    for c in reversed(pf):
        r = r * u + c
    return r


# ------------------------------------------------------------------ Bernstein
_TABLE_CACHE: dict = {}


def _key(a: Q3, b: Q3):
    return (a.a, a.b, a.c, b.a, b.b, b.c)


def bern_table(a: Q3, b: Q3, n: int = DEG):
    """table[j] = Bernstein coefficients (degree n) of u^j on [a, b], j = 0..n."""
    key = _key(a, b) + (n,)
    t = _TABLE_CACHE.get(key)
    if t is not None:
        return t
    if len(_TABLE_CACHE) > 20000:
        _TABLE_CACHE.clear()
    h = b - a
    table = []
    for j in range(n + 1):
        # (a + h t)^j = sum_i C(j, i) a^(j-i) h^i t^i
        q = [ZERO] * (n + 1)
        for i in range(j + 1):
            q[i] = (a_pow(a, j - i) * a_pow(h, i)) * comb(j, i)
        bc = []
        for k in range(n + 1):
            s = ZERO
            for i in range(k + 1):
                if not q[i].is_zero():
                    s = s + q[i] * Fraction(comb(k, i), comb(n, i))
            bc.append(s)
        table.append(bc)
    _TABLE_CACHE[key] = table
    return table


def a_pow(x: Q3, k: int) -> Q3:
    r = Q3(1)
    for _ in range(k):
        r = r * x
    return r


def to_bern(p, a: Q3, b: Q3, n: int = DEG):
    """Exact degree-n Bernstein coefficients of p on [a, b] (requires deg p <= n)."""
    p = ptrim(p)
    if len(p) > n + 1:
        raise ValueError("polynomial degree exceeds Bernstein degree")
    table = bern_table(a, b, n)
    out = [ZERO] * (n + 1)
    for j, c in enumerate(p):
        if c.is_zero():
            continue
        row = table[j]
        for k in range(n + 1):
            out[k] = out[k] + c * row[k]
    return out


def bsub(x, y):
    return [p - q for p, q in zip(x, y)]


def badd(x, y):
    return [p + q for p, q in zip(x, y)]


def split_half(bc):
    """De Casteljau at t = 1/2: exact Bernstein coefficients of both halves."""
    half = Fraction(1, 2)
    left = [bc[0]]
    right = [bc[-1]]
    cur = list(bc)
    while len(cur) > 1:
        cur = [(cur[i] + cur[i + 1]) * half for i in range(len(cur) - 1)]
        left.append(cur[0])
        right.append(cur[-1])
    right.reverse()
    return left, right


def bern_nonneg(bc, depth: int = 12, strict: bool = False) -> bool:
    """Prove p >= 0 (strict: p > 0) on the interval from its Bernstein coefficients.

    Returns True only if proved.  Returns False as soon as an endpoint value is
    exactly negative (resp. <= 0 for strict), or when `depth` halvings do not
    suffice.  A True answer is always a proof; False is just "not proved".
    """
    s0 = bc[0].sign()
    s1 = bc[-1].sign()
    if strict:
        if s0 <= 0 or s1 <= 0:
            return False
        if all(c.sign() > 0 for c in bc[1:-1]):
            return True
    else:
        if s0 < 0 or s1 < 0:
            return False
        if all(c.sign() >= 0 for c in bc[1:-1]):
            return True
    if depth <= 0:
        return False
    left, right = split_half(bc)
    return bern_nonneg(left, depth - 1, strict) and bern_nonneg(right, depth - 1, strict)


def nonneg_on(p, a, b, depth: int = 12, strict: bool = False, snap: bool = False) -> bool:
    """Prove p >= 0 (strict: > 0) on [a, b] exactly.

    With `snap=True`, if plain dyadic subdivision fails, rational roots of p
    inside (a, b) proposed by a float search are checked exactly (p(r) == 0)
    and used as extra split points.  This lets margin-zero touches at a
    rational interior point be certified: they become endpoint zeros.
    """
    a = Q3.parse(a) if not isinstance(a, Q3) else a
    b = Q3.parse(b) if not isinstance(b, Q3) else b
    if not a < b:
        raise ValueError("need a < b")
    p = ptrim(p)
    if not p:
        return not strict
    n = max(DEG, len(p) - 1)
    if bern_nonneg(to_bern(p, a, b, n), depth, strict):
        return True
    if not snap:
        return False
    roots = snap_roots(p, a, b)
    if not roots:
        return False
    pts = [a] + roots + [b]
    return all(
        bern_nonneg(to_bern(p, pts[i], pts[i + 1], n), depth, strict) for i in range(len(pts) - 1)
    )


def snap_roots(p, a: Q3, b: Q3, samples: int = 400, max_den: int = 10**6):
    """Exact rational roots of p strictly inside (a, b), guessed from floats."""
    pf = pfloat(p)
    dpf = [i * c for i, c in enumerate(pf)][1:]
    fa, fb = float(a), float(b)
    cands = set()
    xs = [fa + (fb - fa) * i / samples for i in range(samples + 1)]
    for f in (pf, dpf):
        vals = [feval(f, x) for x in xs]
        for i in range(samples):
            lo, hi = xs[i], xs[i + 1]
            if vals[i] == 0 or vals[i] * vals[i + 1] < 0 or (
                i + 1 < samples and abs(vals[i + 1]) <= abs(vals[i]) and abs(vals[i + 1]) <= abs(feval(f, xs[i + 2]))
            ):
                # refine by bisection on f (sign change) or just take the grid point
                x = _bisect(f, lo, hi) if vals[i] * vals[i + 1] < 0 else hi
                cands.add(Fraction(x).limit_denominator(max_den))
    out = []
    for r in sorted(cands):
        rq = Q3(r)
        if a < rq < b and peval(p, rq).is_zero():
            out.append(rq)
    return out


def _bisect(f, lo, hi, it=80):
    flo = feval(f, lo)
    for _ in range(it):
        mid = (lo + hi) / 2
        fm = feval(f, mid)
        if (fm < 0) == (flo < 0):
            lo, flo = mid, fm
        else:
            hi = mid
    return (lo + hi) / 2
