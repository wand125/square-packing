#!/usr/bin/env python3
"""Second, independent checker for unavoidable weighted point sets in a right isosceles triangle.

Derived from ../../triangle/checker2/sweep.py (the n = 2, 3, 4 equilateral second checker) by
replacing the number field Q(sqrt3) with Q(sqrt2) (q2.py) and the container with
T_L = {x >= 0, y >= 0, x + y <= L}.

Claim checked: for every closed unit square Q contained in T_L, at any position and angle, the
weight of the certificate points lying in Q (boundary included) is at least 1.  The certificate's
`pairs` and `symmetry` fields are ignored: points are counted exactly in every cell, and every angle
u in [0, 1] is checked.

Method: an exact angular sweep of a line arrangement.
* Poses Q(c, t) = c + R_t [-1/2, 1/2]^2 with u = tan(t/2) in [0, 1]; cos t = (1-u^2)/D,
  sin t = 2u/D, D = 1+u^2.
* For fixed u, "Q inside T_L" is 12 half-planes in c (3 sides x 4 vertices) and "p in Q" is 4
  half-planes; each is A(u) x + B(u) y <= C(u) with polynomials over Q(sqrt2).
* The capture weight is constant on each open cell; the minimum over open cells inside the
  admissible region D_u is taken over the open sectors at arrangement vertices in D_u, exactly.
* The arrangement's type changes only at roots of the pair and triple determinants (and the
  coincidence minors of always-parallel pairs); multiplied by the Q(sqrt2)-conjugate they have
  rational coefficients, whose real roots in [0, 1] are isolated exactly (sympy).  One rational
  sample per open gap is checked.
* Closure: the capture weight is upper semicontinuous in (u, c), D_u is convex, varies
  continuously and contains a disc around the incentre for every u because the inradius
  L (2 - sqrt2)/2 exceeds sqrt2/2 (L > 1 + sqrt2, checked).  So the bound extends to every
  admissible pose, including margin-zero contacts and the critical angles.
"""
import argparse
import hashlib
import json
import sys
import time
from fractions import Fraction
from itertools import combinations
from pathlib import Path

from gmpy2 import mpq

sys.set_int_max_str_digits(0)   # exact root isolation can produce very long rationals

from q2 import Q2, ZERO, ONE

HALF = mpq(1, 2)

# ---------------------------------------------------------------- polynomials over Q(sqrt2)
# A polynomial is a tuple of Q2 coefficients, lowest degree first.


def padd(p, q):
    n = max(len(p), len(q))
    return trim(tuple((p[i] if i < len(p) else ZERO) + (q[i] if i < len(q) else ZERO) for i in range(n)))


def pneg(p):
    return tuple(-c for c in p)


def psub(p, q):
    return padd(p, pneg(q))


def pmul(p, q):
    if not p or not q:
        return ()
    r = [ZERO] * (len(p) + len(q) - 1)
    for i, a in enumerate(p):
        if a.is_zero():
            continue
        for j, b in enumerate(q):
            r[i + j] = r[i + j] + a * b
    return trim(tuple(r))


def pscale(p, k):
    return trim(tuple(c * k for c in p))


def trim(p):
    p = list(p)
    while p and p[-1].is_zero():
        p.pop()
    return tuple(p)


def peval(p, x):
    r = ZERO
    for c in reversed(p):
        r = r * x + c
    return r


def pconst(x):
    return trim((x if isinstance(x, Q2) else Q2(x),))


U = (ZERO, ONE)                      # u
D = (ONE, ZERO, ONE)                 # 1 + u^2
C1 = (ONE, ZERO, Q2(-1))             # (1 - u^2)  = D cos t
S1 = (ZERO, Q2(2))                   # 2u         = D sin t


def rational_norm(p):
    """p = p1 + sqrt2 p2 with rational p1, p2; return p1^2 - 2 p2^2 (rational coefficients),
    whose real roots contain those of p.  If p2 = 0 return p1."""
    p1 = [c.a for c in p]
    p2 = [c.b for c in p]
    if not any(p2):
        return p1
    def mul(x, y):
        r = [mpq(0)] * (len(x) + len(y) - 1)
        for i, a in enumerate(x):
            for j, b in enumerate(y):
                r[i + j] += a * b
        return r
    a = mul(p1, p1)
    b = mul(p2, p2)
    n = max(len(a), len(b))
    return [(a[i] if i < len(a) else 0) - 2 * (b[i] if i < len(b) else 0) for i in range(n)]

# ---------------------------------------------------------------- certificate and lines


def load(path):
    raw = Path(path).read_bytes()
    cert = json.loads(raw)
    L = Q2.parse(cert['L'])
    pts = [(Q2.parse(p['x']), Q2.parse(p['y']), mpq(p['w'])) for p in cert['points']]
    if any(w < 0 for _, _, w in pts):
        raise SystemExit('negative weight')
    if cert.get('features'):
        raise SystemExit('threshold features are not supported by this checker')
    return cert, L, pts, hashlib.sha256(raw).hexdigest()


def container_sides(L, container):
    """Sides n.q <= b of the container T_L = {x >= 0, y >= 0, x + y <= L}."""
    if container != 'rit':
        raise ValueError(container)
    return [((ZERO, Q2(-1)), ZERO),                     # y >= 0
            ((Q2(-1), ZERO), ZERO),                     # x >= 0
            ((ONE, ONE), L)]                            # x + y <= L


def build_lines(L, pts, container='rit'):
    """Half-planes A x + B y <= C as polynomial triples in u (all multiplied by D > 0).

    Returns (lines, n_admissible); lines[k] = (A, B, C, tag)."""
    sides = container_sides(L, container)
    lines = []
    for k, ((nx, ny), b) in enumerate(sides):
        for sx in (-HALF, HALF):
            for sy in (-HALF, HALF):
                # vertex R_t (sx, sy) times D = (sx (1-u^2) - sy 2u, sx 2u + sy (1-u^2))
                vx = psub(pscale(C1, sx), pscale(S1, sy))
                vy = padd(pscale(S1, sx), pscale(C1, sy))
                A = pscale(D, nx)
                B = pscale(D, ny)
                C = psub(pscale(D, b), padd(pscale(vx, nx), pscale(vy, ny)))
                lines.append((A, B, C, ('adm', k, float(sx), float(sy))))
    nadm = len(lines)
    e1 = (C1, S1)                                       # D * (cos t, sin t)
    e2 = (pneg(S1), C1)                                 # D * (-sin t, cos t)
    for i, (px, py, w) in enumerate(pts):
        for name, (ex, ey) in (('e1', e1), ('e2', e2)):
            ep = padd(pscale(ex, px), pscale(ey, py))  # D e.p
            halfD = pscale(D, HALF)
            # e.c <= e.p + 1/2   and   -e.c <= -e.p + 1/2
            lines.append((ex, ey, padd(ep, halfD), ('cap', i, name, '+')))
            lines.append((pneg(ex), pneg(ey), padd(pneg(ep), halfD), ('cap', i, name, '-')))
    return lines, nadm


def det2(a, b, c, d):
    return psub(pmul(a, d), pmul(b, c))


def event_polys(lines):
    """Polynomials whose real roots contain every u at which the arrangement changes type."""
    polys = []
    n = len(lines)
    for i, j in combinations(range(n), 2):
        Ai, Bi, Ci, _ = lines[i]
        Aj, Bj, Cj, _ = lines[j]
        cross = det2(Ai, Bi, Aj, Bj)
        if cross:
            polys.append(cross)
        else:  # parallel for all u: coincidence events
            for m in (det2(Ai, Ci, Aj, Cj), det2(Bi, Ci, Bj, Cj)):
                if m:
                    polys.append(m)
    for i, j, k in combinations(range(n), 3):
        Ai, Bi, Ci, _ = lines[i]
        Aj, Bj, Cj, _ = lines[j]
        Ak, Bk, Ck, _ = lines[k]
        d = padd(padd(pmul(Ai, det2(Bj, Cj, Bk, Ck)), pneg(pmul(Bi, det2(Aj, Cj, Ak, Ck)))),
                 pmul(Ci, det2(Aj, Bj, Ak, Bk)))
        if d:
            polys.append(d)
    return polys


def critical_intervals(polys, lo=0, hi=1):
    """Disjoint isolating intervals (a, b) in [0, 1] of all distinct real roots, sorted."""
    import sympy
    u = sympy.Symbol('u')
    seen = set()
    rat = []
    for p in polys:
        r = rational_norm(p)
        while r and r[-1] == 0:
            r.pop()
        if len(r) <= 1:
            continue
        # primitive, sign-normalised, as integer coefficients
        den = 1
        for c in r:
            den = den * c.denominator // _gcd(den, c.denominator)
        ints = [int(c * den) for c in r]
        g = 0
        for c in ints:
            g = _gcd(g, abs(c))
        ints = [c // g for c in ints]
        if ints[-1] < 0:
            ints = [-c for c in ints]
        key = tuple(ints)
        if key in seen:
            continue
        seen.add(key)
        rat.append(sympy.Poly(list(reversed(ints)), u, domain='ZZ'))
    # square-free factors, deduplicated, then joint isolation (sympy merges common roots)
    factors = {}
    for P in rat:
        for f, _ in P.factor_list()[1]:
            if f.degree() >= 1:
                f = f.monic() if f.LC() < 0 else f
                factors[tuple(f.all_coeffs())] = f
    fl = list(factors.values())
    lo, hi = Fraction(lo), Fraction(hi)
    if not fl:                      # no event polynomial of positive degree: no critical angle
        return [], len(rat), 0
    ivs = sympy.intervals(fl, inf=sympy.Rational(lo.numerator, lo.denominator),
                          sup=sympy.Rational(hi.numerator, hi.denominator))
    Q = lambda x: Fraction(int(sympy.Rational(x).p), int(sympy.Rational(x).q))
    out = []
    for (a, b), which in ivs:
        a, b = Q(a), Q(b)
        fs = [fl[k] for k in which]
        out.append([a, b, fs])
    # Make every non-degenerate interval open-isolating: no factor vanishes at its endpoints,
    # and it stays strictly inside (0, 1) unless the root is exactly 0 or 1.
    def val(f, x):
        return Fraction(sympy.Rational(f.eval(sympy.Rational(x.numerator, x.denominator))))
    for iv in out:
        a, b, fs = iv
        if a == b:
            continue
        f = fs[0]
        for _ in range(400):
            fa, fb = val(f, a), val(f, b)
            if fa != 0 and fb != 0 and a > lo and b < hi:
                break
            if fa == 0 and (a == b):
                break
            m = (a + b) / 2
            fm = val(f, m)
            if fm == 0:
                a = b = m
                break
            if fa == 0 or (fa * fm < 0 and fb != 0):
                # root in (a, m) unless a itself is the root
                if fa == 0:
                    a = b = a
                    break
                b = m
            else:
                if fb == 0:
                    a = b = b
                    break
                a = m
        else:
            raise RuntimeError('could not refine isolating interval')
        # all factors listed for this interval share the root: check sign changes
        for g in fs:
            if a != b and not val(g, a) * val(g, b) < 0:
                raise RuntimeError('shared root not bracketed by every factor')
            if a == b and val(g, a) != 0:
                raise RuntimeError('degenerate interval is not a common root')
        iv[0], iv[1] = a, b
    def halve(iv):
        a, b, fs = iv
        if a == b:
            return
        m = (a + b) / 2
        f = fs[0]
        fm = val(f, m)
        if fm == 0:
            iv[0] = iv[1] = m
        elif val(f, a) * fm < 0:
            iv[1] = m
        else:
            iv[0] = m
    out.sort(key=lambda iv: (iv[0], iv[1]))
    for _ in range(400):
        clash = [k for k in range(len(out) - 1) if not out[k][1] < out[k + 1][0]]
        if not clash:
            break
        for k in clash:
            if out[k][0] == out[k][1] == out[k + 1][0] == out[k + 1][1]:
                raise RuntimeError('two intervals at the same exact root')
            halve(out[k]); halve(out[k + 1])
        out.sort(key=lambda iv: (iv[0], iv[1]))
    else:
        raise RuntimeError('could not separate isolating intervals')
    out = [(a, b) for a, b, _ in out]
    return out, len(rat), len(fl)


def _gcd(a, b):
    while b:
        a, b = b, a % b
    return a


def simplest_between(lo, hi):
    """The simplest rational strictly between lo < hi (Stern-Brocot)."""
    lo, hi = Fraction(lo), Fraction(hi)
    assert lo < hi
    import math
    fl = math.floor(lo)
    if fl + 1 < hi:
        return Fraction(fl + 1)
    if lo == fl:
        # lo integer, hi <= lo + 1
        pass
    # continued-fraction style search
    a, b = lo - fl, hi - fl
    if a == 0:
        n = 1
        while Fraction(1, n) >= b:
            n += 1
        return fl + Fraction(1, n)
    return fl + 1 / simplest_between(1 / b, 1 / a)


def sample_points(intervals, lo=0, hi=1):
    """One rational in each open gap of (0, 1) minus the roots.  Each root lies in its closed
    isolating interval [a, b]: exactly at a when a == b, else strictly inside (a, b) with
    0 < a and b < 1.  The gaps are (0, a_1), (b_k, a_{k+1}) and (b_last, 1)."""
    bounds = [Fraction(lo)]
    for a, b in intervals:
        bounds += [a, b]
    bounds.append(Fraction(hi))
    samples = []
    for lo, hi in zip(bounds[0::2], bounds[1::2]):
        if lo < hi:
            samples.append(simplest_between(lo, hi))
        elif lo > hi:
            raise RuntimeError('unsorted intervals')
    return samples


# ---------------------------------------------------------------- check at one u


def eval_lines(lines, u):
    uq = Q2(mpq(u.numerator, u.denominator))
    return [(peval(A, uq), peval(B, uq), peval(C, uq)) for A, B, C, _ in lines]


def check_at(lines, nadm, weights, u, want_witness=False):
    """Exact minimum capture weight over the open cells of int D_u at rational u.

    Returns (min_weight, stats, witness) where witness (if requested and min < 1) is
    (vertex, sector direction, captured point indices)."""
    L = eval_lines(lines, u)
    fl = [(float(a), float(b), float(c)) for a, b, c in L]
    n = len(L)
    npts = len(weights)
    best = None
    witness = None
    stats = dict(vertices=0, in_region=0, sectors=0)
    for i, j in combinations(range(n), 2):
        Ai, Bi, Ci = L[i]
        Aj, Bj, Cj = L[j]
        det = Ai * Bj - Aj * Bi
        if det.is_zero():
            continue
        stats['vertices'] += 1
        # float pre-screen: order admissibility constraints by apparent violation
        fdet = fl[i][0] * fl[j][1] - fl[j][0] * fl[i][1]
        fx = (fl[i][2] * fl[j][1] - fl[j][2] * fl[i][1]) / fdet
        fy = (fl[i][0] * fl[j][2] - fl[j][0] * fl[i][2]) / fdet
        order = sorted(range(nadm), key=lambda k: fl[k][2] - fl[k][0] * fx - fl[k][1] * fy)
        x = (Ci * Bj - Cj * Bi) / det
        y = (Ai * Cj - Aj * Ci) / det
        slack = [None] * n
        outside = False
        for k in order:
            if k in (i, j):
                continue
            s = (L[k][2] - L[k][0] * x - L[k][1] * y).sign()
            slack[k] = s
            if s < 0:
                outside = True
                break
        if outside:
            continue
        stats['in_region'] += 1
        for k in range(nadm, n):
            if k not in (i, j):
                slack[k] = (L[k][2] - L[k][0] * x - L[k][1] * y).sign()
        through = [k for k in range(n) if k not in (i, j) and slack[k] == 0]
        if through:
            raise RuntimeError(f'u={u} is not generic: lines {i},{j},{through[0]} concurrent')
        ti = (-Bi, Ai)
        tj = (-Bj, Aj)
        for si in (1, -1):
            for sj in (1, -1):
                d = (ti[0] * si + tj[0] * sj, ti[1] * si + tj[1] * sj)
                def inside(k):
                    if k == i or k == j:
                        return (L[k][0] * d[0] + L[k][1] * d[1]).sign() < 0
                    return slack[k] > 0
                if not all(inside(k) for k in range(nadm)):
                    continue
                stats['sectors'] += 1
                cap = []
                wsum = mpq(0)
                for p in range(npts):
                    base = nadm + 4 * p
                    if all(inside(k) for k in range(base, base + 4)):
                        cap.append(p)
                        wsum += weights[p]
                if best is None or wsum < best:
                    best = wsum
                    if want_witness:
                        witness = ((x, y), d, cap)
    return best, stats, witness


def verify_witness(L, pts, u, v, d, max_halvings=200, container='rit'):
    """Turn a (vertex, sector) of weight < 1 into an explicit pose and re-check it exactly."""
    uq = Q2(mpq(u.numerator, u.denominator))
    Dv = 1 + uq * uq
    ct, st = (1 - uq * uq) / Dv, (2 * uq) / Dv
    eps = mpq(1, 2)
    for _ in range(max_halvings):
        c = (v[0] + d[0] * eps, v[1] + d[1] * eps)
        corners = [(c[0] + ct * sx - st * sy, c[1] + st * sx + ct * sy)
                   for sx in (-HALF, HALF) for sy in (-HALF, HALF)]
        ok = all((n[0] * q[0] + n[1] * q[1] - b).sign() <= 0
                 for q in corners for n, b in container_sides(L, container))
        if ok:
            w = mpq(0)
            for px, py, pw in pts:
                dx, dy = px - c[0], py - c[1]
                a = dx * ct + dy * st
                b = -dx * st + dy * ct
                if (HALF - a).sign() >= 0 and (HALF + a).sign() >= 0 and (HALF - b).sign() >= 0 and (HALF + b).sign() >= 0:
                    w += pw
            if w < 1:
                return dict(u=str(u), centre=[str(c[0]), str(c[1])], captured_weight=str(w),
                            admissible=True, note='explicit pose, checked exactly')
        eps /= 2
    return None


def _check_idx(args):
    k, *rest = args
    return k, check_at(*rest)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('cert')
    ap.add_argument('--n', type=int, help='number of squares; report whether the total weight is < n')
    ap.add_argument('--jobs', type=int, default=1)
    ap.add_argument('--out', help='write the JSON summary here')
    ap.add_argument('--container', choices=['rit'], default='rit',
                    help='rit: the right isosceles triangle x >= 0, y >= 0, x + y <= L')
    ap.add_argument('--stop-early', action='store_true', help='stop at the first sample with weight < 1 (the run then only shows failure)')
    a = ap.parse_args(argv)
    t0 = time.time()
    cert, L, pts, sha = load(a.cert)
    # The closure argument needs a disc of centres inside every D_u: the inscribed circle of the
    # container must exceed the square's circumradius sqrt2/2 (checked exactly).
    # inradius L (2 - sqrt2) / 2 > sqrt2/2  <=>  L > 1 + sqrt2 (checked exactly)
    if not (L - Q2(1, 1)).sign() > 0:
        raise SystemExit('L > 1 + sqrt2 is required by the closure argument')
    lines, nadm = build_lines(L, pts, a.container)
    polys = event_polys(lines)
    ivs, nrat, nfac = critical_intervals(polys)
    samples = sample_points(ivs)
    t1 = time.time()
    weights = [w for _, _, w in pts]
    if a.jobs > 1:
        from multiprocessing import Pool
        with Pool(a.jobs) as pool:
            if a.stop_early:
                results, done = [None] * len(samples), []
                it = pool.imap_unordered(_check_idx, [(k, lines, nadm, weights, u) for k, u in enumerate(samples)])
                for k, r in it:
                    results[k] = r
                    if r[0] < 1:
                        pool.terminate()
                        break
                keep = [k for k in range(len(samples)) if results[k] is not None]
                samples = [samples[k] for k in keep]
                results = [results[k] for k in keep]
            else:
                results = pool.starmap(check_at, [(lines, nadm, weights, u) for u in samples], chunksize=1)
    else:
        results = [check_at(lines, nadm, weights, u) for u in samples]
    worst = min(r[0] for r in results)
    worst_u = [str(u) for u, r in zip(samples, results) if r[0] == worst][:10]
    summary = dict(certificate=str(a.cert), container=a.container, sha256=sha, L=str(L), points=len(pts),
                   total_weight=str(sum(weights)), lines=len(lines),
                   event_polynomials=len(polys), distinct_rational_polys=nrat, irreducible_factors=nfac,
                   critical_roots_in_0_1=len(ivs), samples=len(samples),
                   vertices_checked=sum(r[1]['vertices'] for r in results),
                   sectors_checked=sum(r[1]['sectors'] for r in results),
                   min_capture_weight=str(worst), min_attained_at_u=worst_u,
                   seconds_events=round(t1 - t0, 2), seconds_total=round(time.time() - t0, 2))
    if worst < 1:
        u = next(u for u, r in zip(samples, results) if r[0] == worst)
        _, _, wit = check_at(lines, nadm, weights, u, want_witness=True)
        summary['counterexample'] = verify_witness(L, pts, u, wit[0], wit[1], container=a.container)
    summary['status'] = 'verified' if worst >= 1 else 'failed'
    if a.n is not None:
        summary['n'] = a.n
        summary['total_below_n'] = sum(weights) < a.n
    text = json.dumps(summary, indent=2)
    print(text)
    if a.out:
        Path(a.out).write_text(text + '\n')
    return 0 if summary['status'] == 'verified' else 1


if __name__ == '__main__':
    sys.exit(main())
