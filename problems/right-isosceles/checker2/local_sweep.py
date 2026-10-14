#!/usr/bin/env python3
"""Second checker for large squintan certificates: branch and bound with exact local sweeps.

Claim checked (as sweep_q2.py): every closed unit square Q inside T_L = {x >= 0, y >= 0, x + y <= L},
at any position and angle, contains certificate points of total weight >= 1 (points on the boundary
of Q count).  The certificate's `pairs` and `symmetry` fields are not used.

Why a new tool: sweep_q2.py sweeps the whole line arrangement at once.  With 505 points it has 2,032
lines and about 1.4e9 triples, which is out of reach.  Here the pose space is cut into boxes and the
exact sweep is run on each small box with only the few lines that cross it.

Poses Q(c, u) = c + R_t [-1/2, 1/2]^2, u = tan(t/2) in [0, 1] (every angle modulo pi/2).
A box is [u0, u1] x [x0, x1] x [y0, y1] with rational ends.  On [0, 1], cos t = (1 - u^2)/(1 + u^2)
decreases and sin t = 2u/(1 + u^2) increases, so their ranges on [u0, u1] are exact rational
intervals, and every quantity below is bounded by exact rational interval arithmetic.

Each box is closed in one of three ways:
  INADMISSIBLE  some vertex of Q is outside some side of T_L at every pose of the closed box;
  SURE          the points that lie in Q at every pose of the closed box weigh >= 1;
  SWEEP         exact local sweep (below), with minimum >= 1;
or split in two.

Exact local sweep of a box.  Let S be the weight of the points that are in Q on the whole closed box,
U the points whose membership changes in the box, and keep only the half-planes in c that are not
constant on the box: for p in U the sides "e.(p - c) >= -1/2" and "e.(p - c) <= 1/2" (e = e1, e2)
that are neither always true nor always false on the box, and the admissibility half-planes
"n.(vertex) <= b" that are not always true.  The region is int(box) meet int(D_u), cut by the box
sides and the kept admissibility lines.  For fixed u the capture is S plus the weight of the points of
U whose kept sides all hold, constant on each open cell of the arrangement; the minimum over the
open cells inside the region is found exactly over the sectors at its vertices (every cell is a
bounded convex polygon, so it has a vertex).  The arrangement inside the closed box changes type only
where three of the lines (box sides included) are concurrent; those u are roots of 3 x 3
determinants, isolated exactly (sympy), and one rational u is checked in each open gap of (u0, u1).
A triple is skipped when one of its pairs provably never meets inside the closed box on [u0, u1]
(interval bound of the intersection point).

Closure.  The capture is upper semicontinuous in (u, c).  T_L has inradius L (2 - sqrt2)/2 > sqrt2/2
(checked), so every D_u has interior and depends continuously on u; every admissible pose is a limit
of poses with c in int D_u, u in an open gap of some box and c in the open box (box boundaries have
measure zero).  So min >= 1 on those poses gives >= 1 everywhere.  Boxes closed INADMISSIBLE hold no
admissible pose (closed box); SURE boxes are covered directly.

Other frames and exclusions.  With "frame": "hyp" the container is T = {y >= 0, y <= x, y <= H - x},
H = L sqrt2, and coordinates may lie in Q(sqrt2).  A certificate may list closed exempt boxes in
(x, y, u) ("exclusions"); with symmetry D1 their mirror images are exempt too.  A box inside an
exempt box is closed as EXEMPT; a box about to be swept whose interior meets one is first split at
its face.  The n = 15 certificate uses the legs frame and no exclusions.
"""
import argparse
import hashlib
import json
import sys
import time
from fractions import Fraction
from itertools import combinations
from functools import cmp_to_key
from pathlib import Path

from gmpy2 import mpq

sys.set_int_max_str_digits(0)

import sweep_q2 as SW            # critical_intervals, sample_points (exact root isolation, own code)
from q2 import Q2

HALF = mpq(1, 2)
ZERO = mpq(0)

# ---------------------------------------------------------------- rational polynomials in u
# lowest degree first, coefficients mpq

def trim(p):
    p = list(p)
    while p and p[-1] == 0:
        p.pop()
    return tuple(p)

def padd(p, q):
    n = max(len(p), len(q))
    return trim((p[i] if i < len(p) else ZERO) + (q[i] if i < len(q) else ZERO) for i in range(n))

def pneg(p):
    return tuple(-c for c in p)

def psub(p, q):
    return padd(p, pneg(q))

def pmul(p, q):
    if not p or not q:
        return ()
    r = [ZERO] * (len(p) + len(q) - 1)
    for i, a in enumerate(p):
        if a:
            for j, b in enumerate(q):
                r[i + j] += a * b
    return trim(r)

def pscale(p, k):
    return trim(c * k for c in p)

def peval(p, x):
    r = ZERO
    for c in reversed(p):
        r = r * x + c
    return r

D = (mpq(1), ZERO, mpq(1))          # 1 + u^2
C1 = (mpq(1), ZERO, mpq(-1))        # D cos t
S1 = (ZERO, mpq(2))                 # D sin t

# ---------------------------------------------------------------- rational intervals

def imul(a, b):
    p = (a[0] * b[0], a[0] * b[1], a[1] * b[0], a[1] * b[1])
    return (min(p), max(p))

def iadd(a, b):
    return (a[0] + b[0], a[1] + b[1])

def iscale(a, k):
    return (a[0] * k, a[1] * k) if k >= 0 else (a[1] * k, a[0] * k)

def ipoly(p, u):
    """Interval of the polynomial p on the interval u (Horner, exact)."""
    r = (ZERO, ZERO)
    for c in reversed(p):
        r = imul(r, u)
        r = (r[0] + c, r[1] + c)
    return r

def cos_sin(u0, u1):
    c = lambda u: (1 - u * u) / (1 + u * u)
    s = lambda u: 2 * u / (1 + u * u)
    return (c(u1), c(u0)), (s(u0), s(u1))

# ---------------------------------------------------------------- certificate

def load(path):
    raw = Path(path).read_bytes()
    cert = json.loads(raw)
    Lq = Q2.parse(cert['L'])
    frame = cert.get('frame', 'legs')
    if frame == 'legs':
        if Lq.b != 0:
            raise SystemExit('legs frame: rational L only')
        L = mpq(Lq.a)
        geo = Geo([((ZERO, mpq(-1)), ZERO), ((mpq(-1), ZERO), ZERO), ((mpq(1), mpq(1)), L)], L, L, L * L)
    elif frame == 'hyp':
        # T = {y >= 0, y <= x, y <= H - x}, H = L sqrt2 (rational when L is a rational multiple of sqrt2)
        Hq = Lq * Q2(0, 1)
        H = mpq(Hq.a) if Hq.b == 0 else Hq
        L2 = Lq * Lq
        if L2.b != 0:
            raise SystemExit('hyp frame: L^2 must be rational')
        # root grid over [0, X] x [0, X/2] with a rational X >= H
        X = H if Hq.b == 0 else mpq(int(float(Hq)) + 1)
        geo = Geo([((ZERO, mpq(-1)), ZERO), ((mpq(-1), mpq(1)), ZERO), ((mpq(1), mpq(1)), H)], X, X / 2, mpq(L2.a))
        geo.H = H
    else:
        raise SystemExit('unknown frame ' + frame)
    # exempt poses: the closed boxes of `exclusions` and their images under the certificate's symmetry
    for e in cert.get('exclusions', []):
        x0, x1 = (mpq(Q2.parse(v).a) for v in e['x'])
        y0, y1 = (mpq(Q2.parse(v).a) for v in e['y'])
        u0, u1 = (mpq(Q2.parse(v).a) for v in e['u'])
        if any(Q2.parse(v).b != 0 for k in 'xyu' for v in e[k]):
            raise SystemExit('irrational exclusion ends are not handled')
        geo.excl.append((u0, u1, x0, x1, y0, y1))
        sym = cert.get('symmetry', 'none')
        if sym == 'D1':
            # D1 maps (x, y, theta) to (X - x, y, -theta) in the hyp frame and (y, x, pi/2 - theta) in the
            # legs frame; -theta = pi/2 - theta mod pi/2, u -> (1 - u)/(1 + u), decreasing
            mu = lambda u: (1 - u) / (1 + u)
            if frame == 'hyp':
                if not isinstance(geo.H, type(mpq())):
                    raise SystemExit('exclusions with an irrational hypotenuse are not handled')
                geo.excl.append((mu(u1), mu(u0), geo.H - x1, geo.H - x0, y0, y1))
            else:
                geo.excl.append((mu(u1), mu(u0), y0, y1, x0, x1))
        elif sym != 'none':
            raise SystemExit('exclusions with symmetry ' + sym + ' are not handled')
    L = geo
    def num(text):
        # rational coordinates stay mpq (fast path); others are exact Q(sqrt2) numbers
        q = Q2.parse(text)
        return mpq(q.a) if q.b == 0 else q
    pts = [(num(p['x']), num(p['y']), mpq(p['w'])) for p in cert['points']]
    if any(w < 0 for _, _, w in pts):
        raise SystemExit('negative weight')
    if cert.get('features'):
        raise SystemExit('threshold features are not supported')
    return cert, L, pts, hashlib.sha256(raw).hexdigest()

class Geo:
    """Container sides n.c <= b, bounding box [0, X] x [0, Y] of the centres, twice the area (for the
    inradius test), and exempt boxes (u0, u1, x0, x1, y0, y1), closed."""
    def __init__(self, sides, X, Y, area2):
        self.sides, self.X, self.Y, self.area2, self.excl = sides, X, Y, area2, []
    def __str__(self):
        return f'X={self.X} Y={self.Y}'

def container_sides(L):
    return L.sides

def exempt_box(b, geo):
    for e in geo.excl:
        if e[0] <= b.u0 and b.u1 <= e[1] and e[2] <= b.x0 and b.x1 <= e[3] and e[4] <= b.y0 and b.y1 <= e[5]:
            return True
    return False

def exclusion_cut(b, geo):
    """A face of an exempt box strictly inside b when b's interior meets that box (else None)."""
    lo = (b.u0, b.x0, b.y0)
    hi = (b.u1, b.x1, b.y1)
    for e in geo.excl:
        if all(lo[k] < e[2 * k + 1] and e[2 * k] < hi[k] for k in range(3)):
            for k in range(3):
                for v in (e[2 * k], e[2 * k + 1]):
                    if lo[k] < v < hi[k]:
                        return k, v
    return None

# ---------------------------------------------------------------- box classification

class Box:
    __slots__ = ('u0', 'u1', 'x0', 'x1', 'y0', 'y1', 'depth')
    def __init__(self, u0, u1, x0, x1, y0, y1, depth=0):
        self.u0, self.u1, self.x0, self.x1, self.y0, self.y1, self.depth = u0, u1, x0, x1, y0, y1, depth
    def key(self):
        return [str(v) for v in (self.u0, self.u1, self.x0, self.x1, self.y0, self.y1)]

def classify(box, L, pts, near):
    """Returns (kind, sure_weight, undecided, adm_keep).

    undecided: list of (index, [sides]) with side = (axis 'e1'/'e2', sign +1 for "<= 1/2", -1 for ">= -1/2").
    adm_keep: list of (side k, sx, sy) admissibility constraints not always true on the box."""
    cI, sI = cos_sin(box.u0, box.u1)
    xI, yI = (box.x0, box.x1), (box.y0, box.y1)
    adm_keep = []
    for k, ((nx, ny), b) in enumerate(container_sides(L)):
        for sx in (-HALF, HALF):
            for sy in (-HALF, HALF):
                # vertex = c + (sx cos - sy sin, sx sin + sy cos)
                vx = iadd(xI, iadd(iscale(cI, sx), iscale(sI, -sy)))
                vy = iadd(yI, iadd(iscale(sI, sx), iscale(cI, sy)))
                g = iadd(iscale(vx, nx), iscale(vy, ny))
                g = (g[0] - b, g[1] - b)
                if g[0] > 0:
                    return 'inadmissible', None, None, None
                if g[1] > 0:
                    adm_keep.append((k, sx, sy))
    sure = ZERO
    und = []
    nsI = (-sI[1], -sI[0])
    for i in near:
        px, py, w = pts[i]
        rx = (px - box.x1, px - box.x0)
        ry = (py - box.y1, py - box.y0)
        e1 = iadd(imul(rx, cI), imul(ry, sI))
        e2 = iadd(imul(rx, nsI), imul(ry, cI))
        out = False
        sides = []
        for name, iv in (('e1', e1), ('e2', e2)):
            if iv[0] > HALF or iv[1] < -HALF:
                out = True
                break
            if iv[1] > HALF:
                sides.append((name, 1))
            if iv[0] < -HALF:
                sides.append((name, -1))
        if out:
            continue
        if not sides:
            sure += w
        else:
            und.append((i, sides))
    return 'open', sure, und, adm_keep

# ---------------------------------------------------------------- exact local sweep

def build_lines(box, L, pts, und, adm_keep):
    """Half-planes A x + B y <= C (polynomials in u).  Region lines first, then per point."""
    lines = []
    one = (mpq(1),)
    lines.append(((mpq(-1),), (), (-box.x0,)))      # x >= x0
    lines.append((one, (), (box.x1,)))               # x <= x1
    lines.append(((), (mpq(-1),), (-box.y0,)))      # y >= y0
    lines.append(((), one, (box.y1,)))               # y <= y1
    sides = container_sides(L)
    for k, sx, sy in adm_keep:
        (nx, ny), b = sides[k]
        vx = psub(pscale(C1, sx), pscale(S1, sy))
        vy = padd(pscale(S1, sx), pscale(C1, sy))
        lines.append((pscale(D, nx), pscale(D, ny), psub(pscale(D, b), padd(pscale(vx, nx), pscale(vy, ny)))))
    nreg = len(lines)
    groups = []
    e = {'e1': (C1, S1), 'e2': (pneg(S1), C1)}
    halfD = pscale(D, HALF)
    for i, sides_ in und:
        px, py, w = pts[i]
        g = []
        for name, sgn in sides_:
            ex, ey = e[name]
            ep = padd(pscale(ex, px), pscale(ey, py))
            if sgn == 1:      # e.(p - c) <= 1/2  <=>  -e.c <= -e.p + 1/2
                lines.append((pneg(ex), pneg(ey), padd(pneg(ep), halfD)))
            else:             # e.(p - c) >= -1/2 <=>  e.c <= e.p + 1/2
                lines.append((ex, ey, padd(ep, halfD)))
            g.append(len(lines) - 1)
        groups.append((g, w))
    return lines, nreg, groups

def det2(a, b, c, d):
    return psub(pmul(a, d), pmul(b, c))

def pair_meets(li, lj, box, uI):
    """False only if lines i, j provably have no common point in the closed box for u in uI."""
    Ai, Bi, Ci = li
    Aj, Bj, Cj = lj
    den = ipoly(det2(Ai, Bi, Aj, Bj), uI)
    if den[0] <= 0 <= den[1]:
        return True
    nx = ipoly(det2(Ci, Bi, Cj, Bj), uI)
    ny = ipoly(det2(Ai, Ci, Aj, Cj), uI)
    inv = (1 / den[1], 1 / den[0])
    x = imul(nx, inv)
    y = imul(ny, inv)
    return not (x[1] < box.x0 or x[0] > box.x1 or y[1] < box.y0 or y[0] > box.y1)

def event_polys(lines, box):
    uI = (box.u0, box.u1)
    n = len(lines)
    meets = {}
    for i, j in combinations(range(n), 2):
        meets[(i, j)] = pair_meets(lines[i], lines[j], box, uI)
    polys = []
    skipped = 0
    for i, j, k in combinations(range(n), 3):
        if not (meets[(i, j)] and meets[(i, k)] and meets[(j, k)]):
            skipped += 1
            continue
        Ai, Bi, Ci = lines[i]
        Aj, Bj, Cj = lines[j]
        Ak, Bk, Ck = lines[k]
        d = padd(padd(pmul(Ai, det2(Bj, Cj, Bk, Ck)), pneg(pmul(Bi, det2(Aj, Cj, Ak, Ck)))),
                 pmul(Ci, det2(Aj, Bj, Ak, Bk)))
        if d:
            polys.append(d)
    return polys, skipped, meets

def rat_poly(p):
    """A rational polynomial whose real roots contain those of p (p times its conjugate if needed)."""
    if not any(isinstance(c, Q2) and c.b != 0 for c in p):
        return tuple(mpq(c.a) if isinstance(c, Q2) else c for c in p)
    return trim(mpq(c) for c in SW.rational_norm(tuple(c if isinstance(c, Q2) else Q2(c) for c in p)))

def no_root_inside(p, u0, u1):
    """True if p certainly has no root in the open interval (u0, u1) (Descartes after Mobius map)."""
    # u = (u0 + u1 z)/(1 + z), z in (0, inf); q(z) = (1 + z)^deg p(u)
    n = len(p) - 1
    if n <= 0:
        return True
    q = [ZERO] * (n + 1)
    # (u0 + u1 z)^k (1 + z)^(n - k)
    for k, c in enumerate(p):
        if not c:
            continue
        t = (mpq(1),)
        for _ in range(k):
            t = pmul(t, (u0, u1))
        for _ in range(n - k):
            t = pmul(t, (mpq(1), mpq(1)))
        for i, v in enumerate(t):
            q[i] += c * v
    signs = [v > 0 for v in q if v != 0]
    changes = sum(1 for a, b in zip(signs, signs[1:]) if a != b)
    return changes == 0

def F(v):
    return Fraction(int(v.numerator), int(v.denominator))

def roots_and_samples(polys, u0, u1):
    keep = [p for p in polys if not no_root_inside(rat_poly(p), u0, u1)]
    u0, u1 = F(u0), F(u1)
    if not keep:
        return [], [SW.simplest_between(u0, u1)], 0
    q2polys = [tuple(c if isinstance(c, Q2) else Q2(c) for c in p) for p in keep]
    ivs, _, _ = SW.critical_intervals(q2polys, u0, u1)
    # the closed box ends are handled by closure; keep roots strictly inside (u0, u1) only
    ivs = [(a, b) for a, b in ivs if not (a == b and (a == u0 or a == u1))]
    for a, b in ivs:
        if a < u0 or b > u1 or (a != b and (a == u0 or b == u1)):
            raise RuntimeError('isolating interval not inside (u0, u1)')
    samples = SW.sample_points(ivs, u0, u1)
    return ivs, samples, len(keep)

def _ray_cmp(p, q):
    hp = 0 if (p[1] > 0 or (p[1] == 0 and p[0] > 0)) else 1
    hq = 0 if (q[1] > 0 or (q[1] == 0 and q[0] > 0)) else 1
    if hp != hq:
        return hp - hq
    c = p[0] * q[1] - p[1] * q[0]
    return -1 if c > 0 else (1 if c < 0 else 0)

def check_at(lines, nreg, groups, sure, u, meets):
    """Exact minimum capture over the open cells of int(box) meet int(D_u) at rational u."""
    uq = mpq(u.numerator, u.denominator)
    Lv = [(peval(A, uq), peval(B, uq), peval(C, uq)) for A, B, C in lines]
    n = len(Lv)
    best = None
    wit = None
    nv = 0
    for i, j in combinations(range(n), 2):
        if not meets[(i, j)]:
            continue
        Ai, Bi, Ci = Lv[i]
        Aj, Bj, Cj = Lv[j]
        det = Ai * Bj - Aj * Bi
        if det == 0:
            continue
        x = (Ci * Bj - Cj * Bi) / det
        y = (Ai * Cj - Aj * Ci) / det
        slack = [None] * n
        out = False
        for k in range(nreg):
            if k in (i, j):
                continue
            s = Lv[k][2] - Lv[k][0] * x - Lv[k][1] * y
            if s < 0:
                out = True
                break
            slack[k] = s
        if out:
            continue
        nv += 1
        for k in range(nreg, n):
            if k not in (i, j):
                slack[k] = Lv[k][2] - Lv[k][0] * x - Lv[k][1] * y
        # Lines through the vertex: i, j and any line with zero slack.  At a sample u this happens only
        # for triples whose determinant vanishes identically (always concurrent, so not an event), e.g. the
        # apex of the two slanted sides on a box face.  Sectors are taken between consecutive rays.
        through = [i, j] + [k for k in range(n) if k not in (i, j) and slack[k] == 0]
        rays = []
        for t in through:
            r = (-Lv[t][1], Lv[t][0])
            for sg in (1, -1):
                q = (r[0] * sg, r[1] * sg)
                if not any(q[0] * o[1] - q[1] * o[0] == 0 and q[0] * o[0] + q[1] * o[1] > 0 for o in rays):
                    rays.append(q)
        rays.sort(key=cmp_to_key(_ray_cmp))
        for a_ in range(len(rays)):
            r1, r2 = rays[a_], rays[(a_ + 1) % len(rays)]
            d = (r1[0] + r2[0], r1[1] + r2[1])
            def ok(k):
                if slack[k] is None or slack[k] == 0 or k in (i, j):
                    v = Lv[k][0] * d[0] + Lv[k][1] * d[1]
                    if v == 0:
                        raise RuntimeError('sector direction on a line')
                    return v < 0
                return slack[k] > 0
            if not all(ok(k) for k in range(nreg)):
                continue
            w = sure
            for g, wp in groups:
                if all(ok(k) for k in g):
                    w += wp
            if best is None or w < best:
                best = w
                wit = ((str(x), str(y)), (str(d[0]), str(d[1])))
    return best, nv, wit

def sweep_box(box, L, pts, sure, und, adm_keep):
    lines, nreg, groups = build_lines(box, L, pts, und, adm_keep)
    polys, skipped, meets = event_polys(lines, box)
    ivs, samples, nkeep = roots_and_samples(polys, box.u0, box.u1)
    best = None
    wit = None
    for u in samples:
        b, _, w = check_at(lines, nreg, groups, sure, u, meets)
        if b is not None and (best is None or b < best):
            best, wit = b, (str(u), w)
    return best, dict(lines=len(lines), triples=len(polys), skipped=skipped, polys_with_roots=nkeep,
                      roots=len(ivs), samples=len(samples)), wit

# ---------------------------------------------------------------- branch and bound

def near_points(box, pts, cand):
    """Points within (closed) distance sqrt2/2 of the centre box, by a coarse exact test (sound)."""
    r = mpq(71, 100)                 # > sqrt2/2
    out = []
    for i in cand:
        px, py, _ = pts[i]
        if box.x0 - r <= px <= box.x1 + r and box.y0 - r <= py <= box.y1 + r:
            out.append(i)
    return out

def run_root(args):
    box, L, pts, K, maxdepth = args[:5]
    stop_early = len(args) > 5 and args[5]
    stats = dict(inadmissible=0, sure=0, sweep=0, split=0, max_depth=0, lines_max=0, samples=0, roots=0)
    worst = None
    worst_at = None
    stack = [(box, list(range(len(pts))))]
    while stack:
        b, cand = stack.pop()
        stats['max_depth'] = max(stats['max_depth'], b.depth)
        near = near_points(b, pts, cand)
        kind, sure, und, adm = classify(b, L, pts, near)
        if kind == 'inadmissible':
            stats['inadmissible'] += 1
            continue
        if sure >= 1:
            stats['sure'] += 1
            continue
        if exempt_box(b, L):
            stats['exempt'] = stats.get('exempt', 0) + 1
            continue
        cut = exclusion_cut(b, L) if (len(und) <= K or b.depth >= maxdepth) else None
        if cut is not None:
            stats['split'] += 1
            k, v = cut
            d1 = b.depth + 1
            if k == 0:
                kids = [Box(b.u0, v, b.x0, b.x1, b.y0, b.y1, d1), Box(v, b.u1, b.x0, b.x1, b.y0, b.y1, d1)]
            elif k == 1:
                kids = [Box(b.u0, b.u1, b.x0, v, b.y0, b.y1, d1), Box(b.u0, b.u1, v, b.x1, b.y0, b.y1, d1)]
            else:
                kids = [Box(b.u0, b.u1, b.x0, b.x1, b.y0, v, d1), Box(b.u0, b.u1, b.x0, b.x1, v, b.y1, d1)]
            for kd in kids:
                stack.append((kd, near))
            continue
        if len(und) <= K or b.depth >= maxdepth:
            best, st, wit = sweep_box(b, L, pts, sure, und, adm)
            stats['sweep'] += 1
            stats['lines_max'] = max(stats['lines_max'], st['lines'])
            stats['samples'] += st['samples']
            stats['roots'] += st['roots']
            if best is not None and (worst is None or best < worst):
                worst, worst_at = best, (b.key(), wit)
            if stop_early and worst is not None and worst < 1:
                break
            continue
        stats['split'] += 1
        du = (b.u1 - b.u0) * mpq(7, 5)
        dx, dy = b.x1 - b.x0, b.y1 - b.y0
        d1 = b.depth + 1
        if du >= dx and du >= dy:
            m = (b.u0 + b.u1) / 2
            kids = [Box(b.u0, m, b.x0, b.x1, b.y0, b.y1, d1), Box(m, b.u1, b.x0, b.x1, b.y0, b.y1, d1)]
        elif dx >= dy:
            m = (b.x0 + b.x1) / 2
            kids = [Box(b.u0, b.u1, b.x0, m, b.y0, b.y1, d1), Box(b.u0, b.u1, m, b.x1, b.y0, b.y1, d1)]
        else:
            m = (b.y0 + b.y1) / 2
            kids = [Box(b.u0, b.u1, b.x0, b.x1, b.y0, m, d1), Box(b.u0, b.u1, b.x0, b.x1, m, b.y1, d1)]
        for k in kids:
            stack.append((k, near))
    return box.key(), stats, (str(worst) if worst is not None else None), worst_at

def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('cert')
    ap.add_argument('--n', type=int)
    ap.add_argument('--jobs', type=int, default=1)
    ap.add_argument('--K', type=int, default=12, help='sweep a box when at most K points are undecided')
    ap.add_argument('--maxdepth', type=int, default=40)
    ap.add_argument('--uslices', type=int, default=20)
    ap.add_argument('--grid', type=int, default=8, help='root boxes per axis in c (over [0, L])')
    ap.add_argument('--only', help='comma list of root indices to run (for splitting a run)')
    ap.add_argument('--out')
    ap.add_argument('--log', help='append one JSON line per finished root box; with --resume, skip roots already there')
    ap.add_argument('--resume', action='store_true')
    ap.add_argument('--stop-early', action='store_true', help='stop at the first box with capture < 1 (shows failure only)')
    a = ap.parse_args(argv)
    t0 = time.time()
    cert, L, pts, sha = load(a.cert)
    # inradius r = 2 area / perimeter > sqrt2/2.  Legs a: area2 = a^2, perimeter a (2 + sqrt2), r = a/(2 + sqrt2)
    # > sqrt2/2 <=> a > 1 + sqrt2 <=> (a - 1)^2 > 2 with a > 1; a^2 = area2.
    a2 = L.area2
    if not (a2 > 1 and (a2 + 1 - 2) ** 2 > 4 * a2 * 1 and a2 + 1 - 2 > 0):
        raise SystemExit('legs > 1 + sqrt2 is required by the closure argument')
    roots = []
    U = [mpq(k, a.uslices) for k in range(a.uslices + 1)]
    GX = [L.X * mpq(k, a.grid) for k in range(a.grid + 1)]
    GY = [L.Y * mpq(k, a.grid) for k in range(a.grid + 1)]
    for k in range(a.uslices):
        for i in range(a.grid):
            for j in range(a.grid):
                roots.append(Box(U[k], U[k + 1], GX[i], GX[i + 1], GY[j], GY[j + 1]))
    idx = list(range(len(roots)))
    if a.only:
        idx = [int(v) for v in a.only.split(',')]
    results = []
    done_keys = set()
    if a.resume and a.log and Path(a.log).exists():
        for line in Path(a.log).read_text().splitlines():
            if line.strip():
                r = json.loads(line)
                if r[0][0] == sha and tuple(r[0][1]) not in done_keys:
                    done_keys.add(tuple(r[0][1]))
                    results.append(tuple(r[1:]))
    jobs = [(roots[k], L, pts, a.K, a.maxdepth, a.stop_early) for k in idx if tuple(roots[k].key()) not in done_keys]
    logf = open(a.log, 'a') if a.log else None
    def record(r):
        results.append(r)
        print(json.dumps(r), file=sys.stderr, flush=True)
        if logf:
            logf.write(json.dumps([[sha, r[0]], *r]) + '\n')
            logf.flush()
    if a.jobs > 1:
        from multiprocessing import Pool
        with Pool(a.jobs) as pool:
            for r in pool.imap_unordered(run_root, jobs, chunksize=1):
                record(r)
                if a.stop_early and r[2] is not None and mpq(r[2]) < 1:
                    pool.terminate()
                    break
    else:
        for j in jobs:
            r = run_root(j)
            record(r)
            if a.stop_early and r[2] is not None and mpq(r[2]) < 1:
                break
    tot = {}
    worst = None
    worst_at = None
    for key, st, w, wa in results:
        for k, v in st.items():
            tot[k] = max(tot.get(k, 0), v) if k in ('max_depth', 'lines_max') else tot.get(k, 0) + v
        if w is not None and (worst is None or mpq(w) < worst):
            worst, worst_at = mpq(w), wa
    weights = [w for _, _, w in pts]
    complete = len(idx) == len(roots) and len(results) == len(roots)
    status = 'verified' if complete and (worst is None or worst >= 1) else (
        'failed' if worst is not None and worst < 1 else 'partial')
    summary = dict(certificate=str(a.cert), sha256=sha, L=str(L), points=len(pts),
                   total_weight=str(sum(weights)), root_boxes=len(roots), roots_run=len(idx),
                   K=a.K, maxdepth=a.maxdepth, counts=tot, min_sweep_capture=str(worst),
                   min_at=worst_at, status=status, seconds=round(time.time() - t0, 1))
    if a.n is not None:
        summary['n'] = a.n
        summary['total_below_n'] = sum(weights) < a.n
    text = json.dumps(summary, indent=2)
    print(text)
    if a.out:
        Path(a.out).write_text(text + '\n')
    return 0 if status == 'verified' else 1

if __name__ == '__main__':
    sys.exit(main())
