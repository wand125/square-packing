"""Exact minimum of mu(Q(c, t)) over the centres of a box at one angle; generic in the number type of u.

With u a Fraction this is an exact fixed-angle solver.  With u an RF (src/rf.py) the same code runs symbolically:
every branch is decided at the sample point and logged as a guard, and the candidate values come out as rational
functions of u (Tier B).

Lemma F1 (piecewise quadratic).  For t not a multiple of pi/2, c -> mu(Q(c, t)) is continuous; it is a polynomial
of degree <= 2 on every face of the arrangement of the lines
  (a) vertex v_k(t) of Q on a line of the cover geometry (a mass line, or the line of a polygon edge);
  (b) edge e of Q through a breakpoint P (where the linear density on a mass line changes, or a polygon vertex).
Inside a face the incidence pattern is fixed: each segment's captured length is affine in c, each polygon's
captured area is a polynomial of degree <= 2.
Lemma F2 (no interior minima).  On a face, the polygon term g(c) = area((Q(c)) ∩ S) is either identically 0 or
positive, and on {g > 0} the function sqrt(g) is concave (Brunn-Minkowski).  So Hess(g) = 2 grad h grad h^T +
2 h Hess(h) with h = sqrt(g) has at most one positive eigenvalue, and so does Hess(mu) (the segment part is affine).
A quadratic with this property attains its minimum over a closed convex face on the boundary (if it is PSD it has
rank <= 1 and is affine along its kernel).  Hence the minimum over the box is attained at a vertex of the
arrangement restricted to the box, or at the 1-D critical point of an edge between two consecutive vertices.
"""
from fractions import Fraction as F
from collections import defaultdict

HALF = F(1, 2)


def cs(u):
    d = 1 + u * u
    return (1 - u * u) / d, 2 * u / d


def frame(u):
    c, s = cs(u)
    verts = [((c * a - s * b) / 2, (s * a + c * b) / 2) for a, b in [(1, 1), (-1, 1), (-1, -1), (1, -1)]]
    normals = [(c, s), (-s, c), (-c, -s), (s, -c)]
    return c, s, verts, normals


def clip(poly, a, b, k):
    """Keep a x + b y <= k (Sutherland-Hodgman, closed)."""
    out = []
    n = len(poly)
    for i in range(n):
        P, R = poly[i], poly[(i + 1) % n]
        fp = a * P[0] + b * P[1] - k
        fr = a * R[0] + b * R[1] - k
        if fp <= 0:
            out.append(P)
        if (fp < 0 and fr > 0) or (fr < 0 and fp > 0):
            t = fp / (fp - fr)
            out.append((P[0] + t * (R[0] - P[0]), P[1] + t * (R[1] - P[1])))
    return out


def area(poly):
    n = len(poly)
    s = 0
    for i in range(n):
        s = s + poly[i][0] * poly[(i + 1) % n][1] - poly[(i + 1) % n][0] * poly[i][1]
    return s / 2


class Local:
    """The part of the cover that can meet a square centred in the box (numeric, independent of u)."""
    def __init__(self, cov, x0, x1, y0, y1, reach=F(7072, 10000)):
        X0, X1, Y0, Y1 = x0 - reach, x1 + reach, y0 - reach, y1 + reach
        hit = lambda a, b: not (max(a[0], b[0]) < X0 or min(a[0], b[0]) > X1 or
                                max(a[1], b[1]) < Y0 or min(a[1], b[1]) > Y1)
        self.segs = [(a, b, w) for a, b, w in cov.segs if hit(a, b)]
        self.polys = [(vs, w / area(vs)) for vs, w, *_ in cov.polys
                      if hit((min(v[0] for v in vs), min(v[1] for v in vs)),
                             (max(v[0] for v in vs), max(v[1] for v in vs)))]
        self.pts = [p for p in cov.pts if X0 <= p[0] <= X1 and Y0 <= p[1] <= Y1]
        # geometry: mass lines and density breakpoints (from all segments on a line, so densities are right)
        lin = defaultdict(F)
        for (ax, ay), (bx, by), w in cov.segs:
            L = abs(bx - ax) + abs(by - ay)
            if ax == bx:
                key, lo, hi = ('v', ax), min(ay, by), max(ay, by)
            else:
                key, lo, hi = ('h', ay), min(ax, bx), max(ax, bx)
            lin[(key, lo, hi)] += w / L
        per = defaultdict(list)
        for (key, lo, hi), d in lin.items():
            per[key].append((lo, hi, d))
        lines, bps = set(), set()
        for key, pieces in per.items():
            ts = sorted({t for lo, hi, _ in pieces for t in (lo, hi)})
            dens = lambda t: sum(d for lo, hi, d in pieces if lo < t < hi)
            for i, t in enumerate(ts):
                left = dens((ts[i - 1] + t) / 2) if i else 0
                right = dens((t + ts[i + 1]) / 2) if i + 1 < len(ts) else 0
                if left != right:
                    P = (key[1], t) if key[0] == 'v' else (t, key[1])
                    if X0 <= P[0] <= X1 and Y0 <= P[1] <= Y1:
                        bps.add(P)
            v = key[1]
            if (key[0] == 'v' and X0 <= v <= X1) or (key[0] == 'h' and Y0 <= v <= Y1):
                lines.add((F(1), F(0), v) if key[0] == 'v' else (F(0), F(1), v))
        for vs, d in self.polys:
            n = len(vs)
            for i in range(n):
                P, R = vs[i], vs[(i + 1) % n]
                a, b = R[1] - P[1], P[0] - R[0]
                lines.add((a, b, a * P[0] + b * P[1]))
                bps.add(P)
        self.lines = sorted(lines)
        self.bps = sorted(bps)


def point_mass(loc, x, y, u, fr=None):
    """Exact mu of the closed square centred (x, y) at angle u (any number type)."""
    c, s, verts, normals = fr or frame(u)
    m = 0
    for (A, B, w) in loc.segs:
        d = (B[0] - A[0], B[1] - A[1])
        t0, t1 = 0, 1
        empty = False
        for n in normals:
            num = HALF - (n[0] * (A[0] - x) + n[1] * (A[1] - y))
            den = n[0] * d[0] + n[1] * d[1]
            if den == 0:
                if num < 0:
                    empty = True; break
            elif den > 0:
                q = num / den
                if q < t1: t1 = q
            else:
                q = num / den
                if q > t0: t0 = q
            if t1 <= t0:
                empty = True; break
        if not empty:
            m = m + w * (t1 - t0)
    for (px, py, w) in loc.pts:
        if all(n[0] * (px - x) + n[1] * (py - y) <= HALF for n in normals):
            m = m + w
    return m + poly_mass(loc, x, y, u, (c, s, verts, normals))


def poly_mass(loc, x, y, u, fr=None):
    """The polygon part of mu(Q) alone (along an edge of the arrangement the segment part is affine, so the
    second difference of mu equals that of this term)."""
    c, s, verts, normals = fr or frame(u)
    m = 0
    for vs, dens in loc.polys:
        poly = [(x + vx, y + vy) for vx, vy in verts]
        k = len(vs)
        for i in range(k):
            P, R = vs[i], vs[(i + 1) % k]
            a, b = R[1] - P[1], P[0] - R[0]
            poly = clip(poly, a, b, a * P[0] + b * P[1])
            if not poly:
                break
        if len(poly) >= 3:
            m = m + dens * area(poly)
    return m


def norm(l):
    a, b, k = l
    d = a if a != 0 else b
    d = abs(d)
    return (a / d, b / d, k / d)


def box_min(loc, side, u, x0, x1, y0, y1, keep=False):
    """Min over admissible centres in the box.  side = container side.  Returns (value, point, kind) or None;
    with keep=True also the list of all candidates [(value, point, kind)]."""
    fr = frame(u)
    c, s, verts, normals = fr
    lo = (abs(c) + abs(s)) / 2
    hi = side - lo
    X0 = x0 if x0 >= lo else lo
    X1 = x1 if x1 <= hi else hi
    Y0 = y0 if y0 >= lo else lo
    Y1 = y1 if y1 <= hi else hi
    if X0 > X1 or Y0 > Y1:
        return None
    corners = [(X0, Y0), (X1, Y0), (X1, Y1), (X0, Y1)]
    region = [(1, 0, X0), (1, 0, X1), (0, 1, Y0), (0, 1, Y1)]
    cand = set()
    for (a, b, k) in loc.lines:
        for vx, vy in verts:
            cand.add(norm((a, b, k - a * vx - b * vy)))
    for P in loc.bps:
        for n in normals:
            cand.add(norm((n[0], n[1], n[0] * P[0] + n[1] * P[1] - HALF)))
    L = list(region)
    for l in sorted(cand, key=repr):          # deterministic order (records are reproducible)
        vals = [l[0] * q[0] + l[1] * q[1] - l[2] for q in corners]
        if min(vals) < 0 and max(vals) > 0:
            L.append(l)
    inb = lambda p: X0 <= p[0] <= X1 and Y0 <= p[1] <= Y1
    on = defaultdict(list)
    for i in range(len(L)):
        a1, b1, k1 = L[i]
        for j in range(i + 1, len(L)):
            a2, b2, k2 = L[j]
            det = a1 * b2 - a2 * b1
            if det == 0:
                continue
            p = ((k1 * b2 - k2 * b1) / det, (a1 * k2 - a2 * k1) / det)
            if inb(p):
                on[i].append(p); on[j].append(p)
    vals = {}
    def f(p):
        if p not in vals:
            vals[p] = point_mass(loc, p[0], p[1], u, fr)
        return vals[p]
    out = []
    pts = set()
    for P in on.values():
        pts.update(P)
    for p in sorted(pts, key=repr):
        out.append((f(p), p, 'vertex'))
    for i, P in on.items():
        a, b, k = L[i]
        dx, dy = -b, a
        S = sorted(sorted(set(P), key=repr), key=lambda p: p[0] * dx + p[1] * dy)
        for p, q in zip(S, S[1:]):
            m = ((p[0] + q[0]) / 2, (p[1] + q[1]) / 2)
            fp, fm, fq = f(p), f(m), f(q)
            A = 2 * (fp - 2 * fm + fq)
            if A > 0:
                B = fq - fp - A
                t = -B / (2 * A)
                if t > 0 and t < 1:
                    z = (p[0] + t * (q[0] - p[0]), p[1] + t * (q[1] - p[1]))
                    out.append((fp + B * t + A * t * t, z, 'edge'))
    best = min(out, key=lambda r: r[0])
    return (best, out) if keep else best
