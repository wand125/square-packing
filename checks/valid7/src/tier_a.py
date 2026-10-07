"""Tier A: exact lower bound of mu over a pose box via the inner core polygon.

Pose: Q(c, t) = c + R_t [-1/2, 1/2]^2, u = tan(t/2), cos t = (1-u^2)/(1+u^2), sin t = 2u/(1+u^2).
Box: centre in [x0, x1] x [y0, y1], u in [u0, u1] (0 <= u0 <= u1 <= 1).

Lemma A1 (angular core).  For t in [t0, t1] with t1 - t0 < pi, let n0, n1 be unit normals at t0, t1, and let
p0 = n0/2, p1 = n1/2.  Then H(n0) ∩ H(n1) ∩ {x on the origin side of the line p0 p1} is contained in
H(n(t)) = {x : x.n(t) <= 1/2} for every t in [t0, t1].
Proof: write n(t) = l0 n0 + lm nm (nm the bisector, t between t0 and tm); with a = t - t0 in [0, h], h = (t1-t0)/2,
l0 = sin(h - a)/sin h, lm = sin a / sin h, and the chord is x.nm <= cos(h)/2.  So x.n(t) <= (l0 + lm cos h)/2
= (sin h cos a)/(2 sin h) <= 1/2.  (Symmetric for t between tm and t1; l0, lm >= 0.)
Lemma A2 (erosion).  If P = {x : a_i.x <= b_i} ⊆ A (the angular core at centre 0), then
P_B = {x : a_i.x <= b_i - h_B(a_i)} + c_mid, h_B(a) = |a_x| r_x + |a_y| r_y, is contained in c + A for every
c in the box (c_mid, half sizes r_x, r_y).  So mu(Q) >= mu(P_B) for every pose of the box.
Lemma A3 (outer hull, for a polygon of density 1 such as the Lebesgue square S).  Vertex v of the square sweeps an
arc of radius sqrt2/2 from v(t0) to v(t1); the arc lies in the triangle v(t0), v(t1), T where T solves
T.v(t0) = T.v(t1) = 1/2 (the tangents' meet).  O = conv(those 12 points) + box is a rational polygon containing every
square of the box, so area(Q ∩ S) = 1 - area(Q minus S) >= 1 - (area(O) - area(O ∩ S)).
"""
from fractions import Fraction as F
from cover import load, validate


def cs(u):
    d = 1 + u * u
    return (1 - u * u) / d, 2 * u / d


def angular_core_halfplanes(u0, u1):
    """Half-planes a.x <= b (a rational, not unit) whose intersection lies inside every R_t[-1/2,1/2]^2."""
    c0, s0 = cs(u0); c1, s1 = cs(u1)
    hp = []
    for k in range(4):
        # rotate normals by k * 90 degrees
        n0, n1 = (c0, s0), (c1, s1)
        for _ in range(k):
            n0 = (-n0[1], n0[0]); n1 = (-n1[1], n1[0])
        hp.append((n0, F(1, 2)))
        if u0 != u1:
            hp.append((n1, F(1, 2)))
            p0 = (n0[0] / 2, n0[1] / 2); p1 = (n1[0] / 2, n1[1] / 2)
            m = (n0[0] + n1[0], n0[1] + n1[1])            # normal of the chord, points away from origin
            hp.append((m, m[0] * p0[0] + m[1] * p0[1]))
    return hp


def clip_poly(poly, a, b):
    """Sutherland-Hodgman: keep a.x <= b."""
    out = []
    n = len(poly)
    for i in range(n):
        P, Q = poly[i], poly[(i + 1) % n]
        fp = a[0] * P[0] + a[1] * P[1] - b
        fq = a[0] * Q[0] + a[1] * Q[1] - b
        if fp <= 0:
            out.append(P)
        if (fp < 0 < fq) or (fq < 0 < fp):
            t = fp / (fp - fq)
            out.append((P[0] + t * (Q[0] - P[0]), P[1] + t * (Q[1] - P[1])))
    return out


def halfplanes_to_poly(hp, big):
    poly = [(-big, -big), (big, -big), (big, big), (-big, big)]
    for a, b in hp:
        poly = clip_poly(poly, a, b)
        if not poly:
            return []
    return poly


def area(poly):
    n = len(poly)
    return sum(poly[i][0] * poly[(i + 1) % n][1] - poly[(i + 1) % n][0] * poly[i][1] for i in range(n)) / 2


class Cover:
    def __init__(self, path):
        c = load(path); validate(c)
        self.s = c['s']; self.pts = c['pts']
        self.segs = [(a, b, w) for a, b, w in c['segs']]
        self.polys = [(vs, w, w / area_(vs)) for vs, w in c['polys']]
        # grid index of segments by unit cells
        self.idx = {}
        for i, (a, b, w) in enumerate(self.segs):
            for gx in range(int(min(a[0], b[0])), int(max(a[0], b[0])) + 1):
                for gy in range(int(min(a[1], b[1])), int(max(a[1], b[1])) + 1):
                    self.idx.setdefault((gx, gy), []).append(i)

    def mass_convex(self, poly, polys=True):
        """Exact mu(P) for a closed convex polygon P (vertex list, CCW or degenerate)."""
        if len(poly) < 3:
            return F(0)  # lower bound use only: a degenerate core is given mass 0 (valid lower bound)
        xs = [p[0] for p in poly]; ys = [p[1] for p in poly]
        lx, hx, ly, hy = min(xs), max(xs), min(ys), max(ys)
        edges = []
        n = len(poly)
        for i in range(n):
            P, Q = poly[i], poly[(i + 1) % n]
            a = (Q[1] - P[1], P[0] - Q[0])                    # outward normal for CCW
            edges.append((a, a[0] * P[0] + a[1] * P[1]))
        m = F(0)
        seen = set()
        for gx in range(int(lx) if lx >= 0 else int(lx) - 1, int(hx) + 1):
            for gy in range(int(ly) if ly >= 0 else int(ly) - 1, int(hy) + 1):
                for i in self.idx.get((gx, gy), ()):
                    if i in seen:
                        continue
                    seen.add(i)
                    A, B, w = self.segs[i]
                    t0, t1 = F(0), F(1)
                    d = (B[0] - A[0], B[1] - A[1])
                    for a, b in edges:                       # Cyrus-Beck on the closed polygon
                        num = b - (a[0] * A[0] + a[1] * A[1]); den = a[0] * d[0] + a[1] * d[1]
                        if den == 0:
                            if num < 0:
                                t0, t1 = F(1), F(0); break
                        elif den > 0:
                            t1 = min(t1, num / den)
                        else:
                            t0 = max(t0, num / den)
                        if t0 > t1:
                            break
                    if t1 > t0:
                        m += w * (t1 - t0)
                    # t1 == t0: a single point of the segment, measure 0
        for x, y, w in self.pts:
            if all(a[0] * x + a[1] * y <= b for a, b in edges):
                m += w
        for vs, w, dens in (self.polys if polys else ()):
            cp = list(poly)
            k = len(vs)
            for i in range(k):
                P, Q = vs[i], vs[(i + 1) % k]
                a = (Q[1] - P[1], P[0] - Q[0])
                cp = clip_poly(cp, a, a[0] * P[0] + a[1] * P[1])
                if not cp:
                    break
            if len(cp) >= 3:
                m += dens * area(cp)
        return m


def area_(vs):
    return area(vs)


def hull(pts):
    pts = sorted(set(pts))
    if len(pts) < 3:
        return pts
    cross = lambda o, a, b: (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lo, up = [], []
    for p in pts:
        while len(lo) >= 2 and cross(lo[-2], lo[-1], p) <= 0: lo.pop()
        lo.append(p)
    for p in reversed(pts):
        while len(up) >= 2 and cross(up[-2], up[-1], p) <= 0: up.pop()
        up.append(p)
    return lo[:-1] + up[:-1]


def outer_hull(u0, u1, cx, cy, rx, ry):
    c0, s0 = cs(u0); c1, s1 = cs(u1)
    pts = []
    for (ex, ey) in [(1, 1), (-1, 1), (-1, -1), (1, -1)]:
        v0 = ((c0 * ex - s0 * ey) / 2, (s0 * ex + c0 * ey) / 2)
        v1 = ((c1 * ex - s1 * ey) / 2, (s1 * ex + c1 * ey) / 2)
        pts += [v0, v1]
        det = v0[0] * v1[1] - v0[1] * v1[0]
        if det != 0:   # T with T.v0 = T.v1 = 1/2
            h = F(1, 2)
            pts.append(((h * v1[1] - v0[1] * h) / det, (v0[0] * h - h * v1[0]) / det))
    return hull([(p[0] + cx + sx * rx, p[1] + cy + sy * ry) for p in pts for sx in (-1, 1) for sy in (-1, 1)])


def clip_to(poly, vs):
    k = len(vs)
    for i in range(k):
        P, Q = vs[i], vs[(i + 1) % k]
        a = (Q[1] - P[1], P[0] - Q[0])
        poly = clip_poly(poly, a, a[0] * P[0] + a[1] * P[1])
        if not poly:
            return []
    return poly


def wmin(u0, u1):
    """min over t in [t0, t1] (inside (-pi/2, pi/2)) of the width |cos t| + |sin t| of the rotated square.
    The width is concave on [-pi/2, 0] and on [0, pi/2] and equals 1 at t = 0: the minimum is at an end of
    the interval, or 1 if the interval contains 0."""
    if u0 <= 0 <= u1:
        return F(1)
    return min(abs(cs(u0)[0]) + abs(cs(u0)[1]), abs(cs(u1)[0]) + abs(cs(u1)[1]))


def core_bound(cov, x0, x1, y0, y1, u0, u1):
    """Lower bound of mu(Q) over admissible poses of the box; None if the box has no admissible pose."""
    lo = wmin(u0, u1) / 2; hi = cov.s - lo
    x0, x1, y0, y1 = max(x0, lo), min(x1, hi), max(y0, lo), min(y1, hi)
    if x0 > x1 or y0 > y1:
        return None
    cx, cy, rx, ry = (x0 + x1) / 2, (y0 + y1) / 2, (x1 - x0) / 2, (y1 - y0) / 2
    hp = [(a, b - abs(a[0]) * rx - abs(a[1]) * ry) for a, b in angular_core_halfplanes(u0, u1)]
    poly = halfplanes_to_poly(hp, F(2))
    poly = [(p[0] + cx, p[1] + cy) for p in poly]
    if len(poly) >= 3 and area(poly) < 0:
        poly.reverse()
    m = cov.mass_convex(poly, polys=False)
    O = outer_hull(u0, u1, cx, cy, rx, ry)
    for vs, w, dens in cov.polys:
        inner = clip_to(list(poly), vs) if len(poly) >= 3 else []
        a_in = area(inner) if len(inner) >= 3 else F(0)
        oc = clip_to(list(O), vs)
        a_out = 1 - (area(O) - (area(oc) if len(oc) >= 3 else 0))
        m += dens * max(a_in, a_out)
    return m


if __name__ == '__main__':
    import sys, time
    cov = Cover(sys.argv[1])
    t = time.time()
    # exact single poses (box of size 0)
    for (x, y, u) in [(F(3), F(1, 2), F(0)), (F(7, 2), F(7, 2), F(0)), (F(3), F(51, 100), F(1, 1000)),
                      (F(7, 2), F(7, 2), F(1, 3)), (F(1, 2), F(1, 2), F(0))]:
        print('pose', x, y, u, float(core_bound(cov, x, x, y, y, u, u)))
    print('box', float(core_bound(cov, F(2), F(21, 10), F(2), F(21, 10), F(1, 5), F(1, 5) + F(1, 64))))
    print('time', time.time() - t)
