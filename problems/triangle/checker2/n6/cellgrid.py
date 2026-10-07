"""Second checker for the n = 6 triangle certificates (exclusions + obstacle points).

Claim checked (SPEC, "Exclusion boxes and obstacle points"): every closed unit square Q(c, t) inside T_L
that is neither excluded (pose in a closed exclusion box) nor contains an obstacle point captures weight >= 1
from `points`; and the total weight is < n.

Method (independent of the first checker: no box subdivision in c, no Bernstein bounds, no vertex pairs).
Split u = tan(t/2) into intervals I = [ua, ub]. Let um be the rational midpoint, tm = t(um) (rational cos and
sin), and h = ub - ua >= |t - tm| for t in I (since dt/du = 2/(1+u^2) <= 2 and |u - um| <= h/2).
 * Inner squares.  If |(p - c).e_k(tm)| <= s := 1/2 - r h with r >= sqrt2/2, then |p - c| <= sqrt2/2 and
   |(p - c).e_k(t)| <= s + |p - c| |e_k(t) - e_k(tm)| <= s + (sqrt2/2) h <= 1/2 for every t in I.
   So a centre in the inner square of p (side 2s, axes e(tm), centred at p) captures p at every angle of I.
   The same holds for obstacle points (exemption at every angle of I).
 * Outer admissible region.  Q(c, t) in T iff n_k.c <= b_k - h_k(t), h_k(t) = max over the 4 corners
   sigma of n_k.R_t sigma, which is (sqrt2/2)-Lipschitz in t.  So every admissible pose with t in I has
   c in A+ = {n_k.c <= b_k - h_k(tm) + r h}.
 * Exclusions.  The u-grid contains every exclusion u-endpoint, so each interval is inside or outside the
   u-range of each exclusion; only boxes whose u-range contains I are used, as rectangles in c.
At the fixed frame e(tm) all inner squares are axis-parallel.  Their edges cut the plane into a grid; on each
open grid cell the captured weight and the obstacle cover are constant, and on the closed cell they can only be
larger (closed squares).  Every open cell meeting A+ must have weight >= 1, or lie in an inner obstacle square,
or have (cell n A+) inside an active exclusion rectangle.  If some cell fails, the interval is halved.

Rigour of the float parts.  Every float is an exact dyadic rational.  Edge coordinates are computed from exact
Q(sqrt3) data with error < 1e-13 and then moved inwards by PAD = 1e-12, so the float squares lie inside the exact
inner squares; ordering and membership of float coordinates are then exact.  A+ is padded outwards by PAD, a cell
counts as outside A+ only if a constraint is violated by more than TOL = 1e-10 in floats, a float weight sum is
trusted only outside [1 - 1e-9, 1 + 1e-9] (else recomputed exactly), and exclusion containment needs a float
margin of TOL.  Float evaluation errors here are below 1e-12.

Symmetry D3: the weighted point multiset is checked to be invariant exactly; u in [0, 1/7] with 1/7 > tan(pi/24)
proved exactly.  Only the identity image of a pose is tested against the exclusion boxes (stricter than SPEC).
"""
import argparse
import hashlib
import json
import os
import math
import sys
import time
from fractions import Fraction
from multiprocessing import Pool

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from q3 import Q3  # noqa: E402
from gmpy2 import mpq  # noqa: E402

SQ3 = math.sqrt(3.0)
R = mpq(7072, 10000)          # >= sqrt2/2 = 0.70710678...
PAD = 1e-12
TOL = 1e-10


def qf(q):
    return float(q.a) + float(q.b) * SQ3


class Cert:
    def __init__(self, path):
        raw = open(path, 'rb').read()
        self.sha = hashlib.sha256(raw).hexdigest()
        c = json.loads(raw)
        self.L = Q3.parse(c['L'])
        self.sym = c.get('symmetry', 'none')
        self.pts = [(Q3.parse(p['x']), Q3.parse(p['y']), Fraction(p['w'])) for p in c['points']]
        self.obs = [(Q3.parse(p['x']), Q3.parse(p['y'])) for p in c.get('obstacle_points', [])]
        self.exc = [tuple(tuple(Q3.parse(v) for v in e[k]) for k in ('x', 'y', 'u')) for e in c.get('exclusions', [])]
        for k in ('segments', 'pairs', 'features'):
            if c.get(k):
                raise SystemExit(f'field {k} not supported by this checker')
        for (_, _, (u0, u1)) in self.exc:
            if u0.b != 0 or u1.b != 0:
                raise SystemExit('exclusion u endpoints must be rational here')
        if self.obs and self.sym != 'none':
            raise SystemExit('obstacle points require symmetry none')
        self.total = sum(w for _, _, w in self.pts)
        assert all(w >= 0 for _, _, w in self.pts)
        # float arrays
        self.wx = np.array([qf(x) for x, _, _ in self.pts])
        self.wy = np.array([qf(y) for _, y, _ in self.pts])
        self.ww = np.array([float(w) for _, _, w in self.pts])
        self.wfrac = [w for _, _, w in self.pts]
        self.ox = np.array([qf(x) for x, _ in self.obs])
        self.oy = np.array([qf(y) for _, y in self.obs])
        self.excf = [((qf(x0), qf(x1)), (qf(y0), qf(y1)), (u0.a, u1.a)) for (x0, x1), (y0, y1), (u0, u1) in self.exc]
        Lf = qf(self.L)
        h = math.sqrt(3) / 2
        # sides: outward normal n_k, offset b_k (n_k.c <= b_k inside)
        self.sides = [((0.0, -1.0), 0.0), ((h, 0.5), h * Lf), ((-h, 0.5), 0.0)]


def d3_invariant(cert):
    L = cert.L
    half = Fraction(1, 2)

    def rot(x, y):  # rotation by 2pi/3 about the centroid G = (L/2, L/(2 sqrt3))
        gx = L * half
        gy = L * Q3(0, Fraction(1, 6))  # L sqrt3 / 6
        dx, dy = x - gx, y - gy
        c, s = Fraction(-1, 2), Q3(0, half)  # cos, sin of 2pi/3
        return gx + dx * c - dy * s, gy + dx * s + dy * c

    def key(x, y, w):
        return (x.a, x.b, y.a, y.b, w)
    base = sorted(key(x, y, w) for x, y, w in cert.pts)
    for f in (lambda x, y: rot(x, y), lambda x, y: (L - x, y)):
        img = sorted(key(*f(x, y), w) for x, y, w in cert.pts)
        if img != base:
            return False
    return True


def u_max_ok(U):
    # cos t(U) = (1-U^2)/(1+U^2) < (sqrt6+sqrt2)/4; use sqrt6 > 2449/1000, sqrt2 > 1414/1000.
    return (1 - U * U) / (1 + U * U) < (Fraction(2449, 1000) + Fraction(1414, 1000)) / 4


def edges(px, py, C, S, s):
    X = C * px + S * py
    Y = -S * px + C * py
    return X - s, X + s, Y - s, Y + s


def check_interval(cert, ua, ub, want_detail=False):
    """Return (ok, info) for u in [ua, ub] (mpq)."""
    um = (ua + ub) / 2
    C = (1 - um * um) / (1 + um * um)
    S = 2 * um / (1 + um * um)
    h = ub - ua
    s = mpq(1, 2) - R * h
    if s <= 0:
        return False, 'interval too wide'
    Cf, Sf, sf, rh = float(C), float(S), float(s) - PAD, float(R * h)
    e1 = (Cf, Sf)
    e2 = (-Sf, Cf)
    # A+ in rotated coordinates: nu.c' <= off
    cons = []
    for (nx, ny), b in cert.sides:
        a1 = nx * e1[0] + ny * e1[1]
        a2 = nx * e2[0] + ny * e2[1]
        hk = 0.5 * (abs(a1) + abs(a2))
        cons.append((a1, a2, b - hk + rh + PAD))
    # triangle vertices of A+ (pairwise intersections)
    verts = []
    for i in range(3):
        for j in range(i + 1, 3):
            a1, b1, c1 = cons[i]
            a2, b2, c2 = cons[j]
            det = a1 * b2 - a2 * b1
            verts.append(((c1 * b2 - c2 * b1) / det, (a1 * c2 - a2 * c1) / det))
    vx = [v[0] for v in verts]
    vy = [v[1] for v in verts]
    bx0, bx1 = min(vx) - 1e-9, max(vx) + 1e-9
    by0, by1 = min(vy) - 1e-9, max(vy) + 1e-9
    # squares
    wl, wr, wb, wt = edges(cert.wx, cert.wy, Cf, Sf, sf)
    if len(cert.ox):
        ol, orr, ob, ot = edges(cert.ox, cert.oy, Cf, Sf, sf)
    else:
        ol = orr = ob = ot = np.zeros(0)
    xs = np.concatenate([wl, wr, ol, orr, [bx0, bx1]])
    ys = np.concatenate([wb, wt, ob, ot, [by0, by1]])
    xs = np.unique(xs[(xs >= bx0) & (xs <= bx1)])
    ys = np.unique(ys[(ys >= by0) & (ys <= by1)])
    nx, ny = len(xs) - 1, len(ys) - 1

    def irange(lo, hi, grid):
        # cells k with grid[k] >= lo and grid[k+1] <= hi  (cell inside [lo, hi])
        i0 = np.searchsorted(grid, lo, side='left')
        i1 = np.searchsorted(grid, hi, side='right') - 1
        return i0, i1  # cells i0 .. i1-1

    def accumulate(l, r, b, t, vals, dtype):
        D = np.zeros((nx + 1, ny + 1), dtype=dtype)
        i0, i1 = irange(l, r, xs)
        j0, j1 = irange(b, t, ys)
        m = (i1 > i0) & (j1 > j0)
        np.add.at(D, (i0[m], j0[m]), vals[m])
        np.add.at(D, (i1[m], j0[m]), -vals[m])
        np.add.at(D, (i0[m], j1[m]), -vals[m])
        np.add.at(D, (i1[m], j1[m]), vals[m])
        return np.cumsum(np.cumsum(D, axis=0), axis=1)[:nx, :ny], (i0, i1, j0, j1)

    W, widx = accumulate(wl, wr, wb, wt, cert.ww, np.float64)
    if len(cert.ox):
        O, _ = accumulate(ol, orr, ob, ot, np.ones(len(ol), dtype=np.int64), np.int64)
    else:
        O = np.zeros((nx, ny), dtype=np.int64)
    # cell meets A+ unless some constraint is violated at all 4 corners by > TOL
    meet = np.ones((nx, ny), dtype=bool)
    for a1, a2, off in cons:
        fx = np.minimum(a1 * xs[:-1], a1 * xs[1:])
        fy = np.minimum(a2 * ys[:-1], a2 * ys[1:])
        meet &= ~((fx[:, None] + fy[None, :] - off) > TOL)
    lowW = W < 1 + 1e-9
    bad = meet & (O == 0) & lowW
    if not bad.any():
        return True, None
    # exact weight for the near-1 cells; exclusions for the rest
    active = [e for e, (_, _, (u0, u1)) in zip(cert.excf, cert.exc) if u0.a <= ua and ub <= u1.a]
    wi0, wi1, wj0, wj1 = widx
    fails = []
    for i, j in zip(*np.nonzero(bad)):
        if W[i, j] > 1 - 1e-9:
            m = (wi0 <= i) & (i < wi1) & (wj0 <= j) & (j < wj1)
            if sum((cert.wfrac[k] for k in np.nonzero(m)[0]), Fraction(0)) >= 1:
                continue
        if active and cell_in_exclusion(xs[i], xs[i + 1], ys[j], ys[j + 1], Cf, Sf, cons, active):
            continue
        fails.append((i, j, float(W[i, j])))
        if not want_detail:
            break
    if not fails:
        return True, None
    cen = []
    for i, j, w in fails:
        cx, cy = 0.5 * (xs[i] + xs[i + 1]), 0.5 * (ys[j] + ys[j + 1])
        cen.append((float(Cf * cx - Sf * cy), float(Sf * cx + Cf * cy)))
    info = {'u': [float(ua), float(ub)], 'centre': list(cen[0]), 'W': fails[0][2], 'cells_failed': len(fails)}
    if want_detail:
        info['bbox'] = [min(c[0] for c in cen), max(c[0] for c in cen), min(c[1] for c in cen), max(c[1] for c in cen)]
    return False, info


def clip(poly, a1, a2, off):
    out = []
    n = len(poly)
    for k in range(n):
        p, q = poly[k], poly[(k + 1) % n]
        fp = a1 * p[0] + a2 * p[1] - off
        fq = a1 * q[0] + a2 * q[1] - off
        if fp <= 0:
            out.append(p)
        if (fp < 0 < fq) or (fq < 0 < fp):
            t = fp / (fp - fq)
            out.append((p[0] + t * (q[0] - p[0]), p[1] + t * (q[1] - p[1])))
    return out


def cell_in_exclusion(x0, x1, y0, y1, C, S, cons, active):
    corners = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    poly = corners
    for a1, a2, off in cons:
        # pad outwards so the float polygon contains the exact cell n A+
        poly = clip(poly, a1, a2, off + TOL)
        if not poly:
            return True
    for (ex0, ex1), (ey0, ey1), _ in active:
        ok = True
        for (a, b) in poly:
            X = C * a - S * b
            Y = S * a + C * b
            if not (ex0 + TOL < X < ex1 - TOL and ey0 + TOL < Y < ey1 - TOL):
                ok = False
                break
        if ok:
            return True
    return False


_CERT = None


def _init(path, window=None):
    global _CERT
    _CERT = Cert(path)
    if window:
        x0, x1, y0, y1, E = [Q3.parse(v) for v in window.split(',')]
        _CERT.exc.append(((x0, x1), (y0, y1), (Q3(0), E)))
        _CERT.excf.append(((qf(x0), qf(x1)), (qf(y0), qf(y1)), (mpq(0), E.a)))


def _work(task):
    ua, ub, min_w = task
    stack = [(ua, ub)]
    done, worst = 0, None
    while stack:
        a, b = stack.pop()
        ok, info = check_interval(_CERT, a, b)
        if ok:
            done += 1
            continue
        if b - a <= min_w:
            return {'ok': False, 'fail': info, 'intervals': done}
        m = (a + b) / 2
        stack.append((m, b))
        stack.append((a, m))
    return {'ok': True, 'intervals': done}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('cert')
    ap.add_argument('--n', type=int, required=True)
    ap.add_argument('--pieces', type=int, default=2000, help='initial u pieces')
    ap.add_argument('--min-width', default='1/100000000')
    ap.add_argument('--jobs', type=int, default=1)
    ap.add_argument('--out')
    ap.add_argument('--window', help='x0,x1,y0,y1,E: centres in this box with u in [0, E] are left to sweepwin.py')
    a = ap.parse_args()
    t0 = time.time()
    cert = Cert(a.cert)
    if a.window:
        x0, x1, y0, y1, E = [Q3.parse(v) for v in a.window.split(',')]
        cert.exc.append(((x0, x1), (y0, y1), (Q3(0), E)))
        cert.excf.append(((qf(x0), qf(x1)), (qf(y0), qf(y1)), (mpq(0), E.a)))
    res = {'cert_sha256': cert.sha, 'L': f'{cert.L.a}+{cert.L.b}*sqrt3', 'points': len(cert.pts),
           'obstacle_points': len(cert.obs), 'exclusions': len(cert.exc), 'symmetry': cert.sym,
           'total_weight': str(cert.total), 'n': a.n, 'total_below_n': cert.total < a.n,
           'window_left_to_sweepwin': a.window}
    if cert.sym == 'D3':
        U = Fraction(1, 7)
        res['d3_invariant'] = d3_invariant(cert)
        res['U_exceeds_tan_pi_24'] = u_max_ok(U)
        hi = mpq(1, 7)
    else:
        hi = mpq(1)
    breaks = {mpq(0), hi}
    for (_, _, (u0, u1)) in cert.exc:
        for u in (u0.a, u1.a):
            if 0 < u < hi:
                breaks.add(u)
    breaks = sorted(breaks)
    tasks = []
    min_w = mpq(Fraction(a.min_width))
    for lo, up in zip(breaks, breaks[1:]):
        k = max(1, int(a.pieces * float(up - lo) / float(hi)))
        for i in range(k):
            tasks.append((lo + (up - lo) * i / k, lo + (up - lo) * (i + 1) / k, min_w))
    with Pool(a.jobs, initializer=_init, initargs=(a.cert, a.window)) as pool:
        out = pool.map(_work, tasks, chunksize=1)
    fails = [o['fail'] for o in out if not o['ok']]
    res['u_intervals_checked'] = sum(o['intervals'] for o in out)
    res['failed_pieces'] = len(fails)
    res['failures'] = fails[:20]
    ok = not fails and res['total_below_n'] and res.get('d3_invariant', True) and res.get('U_exceeds_tan_pi_24', True)
    res['status'] = 'verified' if ok else 'failed'
    res['seconds'] = round(time.time() - t0, 1)
    js = json.dumps(res, indent=1, default=str)
    print(js)
    if a.out:
        open(a.out, 'w').write(js + '\n')


if __name__ == '__main__':
    main()
