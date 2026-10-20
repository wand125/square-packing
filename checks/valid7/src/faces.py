"""Face-interior critical points (Lemma B5).  Needed when the polygon part of the cover is not a single convex
polygon piece: Lemma F2 (solver.py) then does not apply, and the minimum of mu over a face of the arrangement can be
in the interior of the face.  Written 2026-10-20 after the review that found the gap in Lemma F2.

Lemma B5 (face sweep).  Let L be the line list of tier_b2.certify for (B, (a, b)) (it contains the sides of B and
of R(u)).  Let U be the real roots in (a, b) of every pairwise determinant and every 3 x 3 determinant (concurrency)
of lines of L that are not identically zero.  On each open interval J between consecutive points of U ∪ {a, b} no two
lines become parallel and no three become concurrent (beyond those concurrent for every u), so the arrangement of L
inside B ∩ R(u) has the same combinatorial structure for all u in J: it is enumerated exactly at one rational u0 in J,
and each face F is a polygon whose vertices are p_ij(u) = L_i ∩ L_j for fixed pairs (i, j).  (The sides of R(u) are in
L, so a vertex crossing a side of R(u) is a concurrency and lies in U.)  On F, mu is one quadratic q_F(u; c) (Lemma F1).
Its coefficients follow from the values of mu at three vertices V1, V2, V3 of F and at the midpoints of the three
chords (all in cl F, where mu = q_F by continuity):
  s_ij = 4 (q(Vi) + q(Vj) - 2 q(Mij)) = d_ij^T H d_ij,   q(Vk) = q(V1) + g . d_1k + s_1k / 2   (k = 2, 3).
Where det H > 0 and tr H > 0 the unique critical point c* = V1 - H^-1 g is a strict minimum and
  q* = q(V1) - g^T H^-1 g / 2   is a lower bound of q_F on all of R^2.
So it suffices that for every u in J with det H > 0 and tr H > 0: q* >= 1, or c* is not in cl F.  (Where H is not
positive definite the minimum of q_F over cl F is on the boundary, which tier_b2 covers by its vertices and edge
critical points.)  The test is exact: signs of numerator x denominator of each rational function of u on the open
pieces between their roots, with the guards of the symbolic evaluation splitting the pieces as in
tier_b2.check_value.  The points of U, the piece ends and u = 0 are covered by the continuity of mu in (c, u) for
u != 0 and by upper semicontinuity at u = 0 (closed squares).
"""
from fractions import Fraction
from itertools import combinations
import rf
from rf import Q, Resample
import solver
from tier_b import Alg, alg_cmp
import tier_b2 as T2


def _wrap(ctx, nd):
    return rf.RF(nd[0], nd[1], ctx, reduce=False)


def _val(nd, u0):
    n, d = nd
    if isinstance(u0, Fraction):
        u0 = Q(u0.numerator, u0.denominator)
    return Fraction(int(n(u0).p), int(n(u0).q)) / Fraction(int(d(u0).p), int(d(u0).q))


def critical_u(Lp, ctx, a, b):
    """Roots in (a, b) of the pairwise and triple determinants that are not identically zero."""
    L = [tuple(_wrap(ctx, nd) for nd in l) for l in Lp]
    out = []
    n = len(L)
    for i, j in combinations(range(n), 2):
        d = L[i][0] * L[j][1] - L[j][0] * L[i][1]
        if d.n != 0:
            out += T2.roots_in(T2.sign_poly(d), a, b)
    for i, j, k in combinations(range(n), 3):
        (a1, b1, k1), (a2, b2, k2), (a3, b3, k3) = L[i], L[j], L[k]
        d = a1 * (b2 * k3 - b3 * k2) - b1 * (a2 * k3 - a3 * k2) + k1 * (a2 * b3 - a3 * b2)
        if d.n != 0:
            out += T2.roots_in(T2.sign_poly(d), a, b)
    return T2.sorted_unique(out)


def faces_at(Lp, u0):
    """Exact faces of the arrangement inside B ∩ R(u0) at the rational u0.  Lines 0..3 are B's sides x0, x1, y0, y1;
    4..7 are R's sides lo, hi (x), lo, hi (y).  A face is a list of (point, (i, j), e) in cyclic order: (i, j) the two
    lines meeting at the vertex, e the line of the edge leaving it."""
    Lq = [tuple(_val(nd, u0) for nd in l) for l in Lp]

    def meet(i, j):
        (a1, b1, k1), (a2, b2, k2) = Lq[i], Lq[j]
        det = a1 * b2 - a2 * b1
        return ((k1 * b2 - k2 * b1) / det, (a1 * k2 - a2 * k1) / det)

    poly = [(meet(0, 2), (0, 2), 2), (meet(1, 2), (1, 2), 1), (meet(1, 3), (1, 3), 3), (meet(0, 3), (0, 3), 0)]

    def side(m, p):
        a, b_, k = Lq[m]
        return a * p[0] + b_ * p[1] - k

    def cut(poly, m, keep):
        """keep = +1: the part a x + b y - k >= 0; -1: the part <= 0."""
        out = []
        n = len(poly)
        for t in range(n):
            P, lab, e = poly[t]
            R = poly[(t + 1) % n][0]
            fp, fr = keep * side(m, P), keep * side(m, R)
            if fp >= 0:
                # a vertex on the cutting line (a concurrency that holds for every u) gets m in its label
                out.append((P, lab if fp > 0 else tuple(sorted(set(lab) | {m})), e))
            if (fp > 0 and fr < 0) or (fp < 0 and fr > 0):
                tt = fp / (fp - fr)
                X = (P[0] + tt * (R[0] - P[0]), P[1] + tt * (R[1] - P[1]))
                out.append((X, (e, m), e))
        # every edge's line is a label shared by its two ends (the chord of the cut gets m); duplicate points
        # (two consecutive vertices with two common lines) are merged
        res = []
        for t in range(len(out)):
            P, lab, _ = out[t]
            R, lab2, _ = out[(t + 1) % len(out)]
            common = set(lab) & set(lab2)
            if P == R:
                if res and res[-1][0] == P:
                    continue
                lab = tuple(sorted(set(lab) | set(lab2)))
                R2, lab3, _ = out[(t + 2) % len(out)]
                common = set(lab) & set(lab3)
            assert common, 'faces.py: consecutive vertices share no line'
            res.append((P, lab, min(common)))
        return res

    for m, keep in ((4, 1), (5, -1), (6, 1), (7, -1)):
        poly = cut(poly, m, keep)
        if len(poly) < 3:
            return []
    faces = [poly]
    for m in range(8, len(Lq)):
        nxt = []
        for f in faces:
            sg = [side(m, P) for P, _, _ in f]
            if min(sg) < 0 < max(sg):
                for keep in (1, -1):
                    g = cut(f, m, keep)
                    if len(g) >= 3:
                        nxt.append(g)
            else:
                nxt.append(f)
        faces = nxt
    return faces


def _area2(V):
    return sum(V[t][0] * V[(t + 1) % len(V)][1] - V[(t + 1) % len(V)][0] * V[t][1] for t in range(len(V)))


def check_face(loc, Lp, face, A, B, u0):
    """Lemma B5 on one face over the open interval (A, B).  Returns (ok, info)."""
    labs = [lab for _, lab, _ in face]
    pts = [P for P, _, _ in face]
    best, tri = 0, None
    n = len(pts)
    for i, j, k in combinations(range(n), 3):
        ar = abs(_area2([pts[i], pts[j], pts[k]]))
        if ar > best:
            best, tri = ar, (i, j, k)
    if tri is None:
        return True, 'flat'
    edges = sorted({e for _, _, e in face if e is not None})
    centre = (sum(p[0] for p in pts) / n, sum(p[1] for p in pts) / n)
    inside = {}
    for m in edges:
        a_, b_, k_ = (_val(nd, u0) for nd in Lp[m])
        v = a_ * centre[0] + b_ * centre[1] - k_
        inside[m] = 1 if v > 0 else -1
    pieces = [(A, B, T2.between(A, B))]
    while pieces:
        A1, B1, s1 = pieces.pop()
        for attempt in range(60):
            try:
                ctx = rf.Ctx(Fraction(int(s1.p), int(s1.q)))
                u = ctx.var()
                fr = solver.frame(u)

                def vert(lab):
                    # any two non-parallel lines of the label define the vertex on all of J
                    for i, j in combinations(lab, 2):
                        a1, b1, k1 = (_wrap(ctx, nd) for nd in Lp[i])
                        a2, b2, k2 = (_wrap(ctx, nd) for nd in Lp[j])
                        det = a1 * b2 - a2 * b1
                        if not (det.n == 0 if isinstance(det, rf.RF) else det == 0):
                            return ((k1 * b2 - k2 * b1) / det, (a1 * k2 - a2 * k1) / det)
                    raise AssertionError('faces.py: degenerate vertex label')

                V = [vert(labs[t]) for t in tri]
                M = lambda p, q: ((p[0] + q[0]) / 2, (p[1] + q[1]) / 2)
                q = [solver.point_mass(loc, v[0], v[1], u, fr) for v in V]
                m12, m13, m23 = (solver.point_mass(loc, *M(V[i], V[j]), u, fr) for i, j in ((0, 1), (0, 2), (1, 2)))
                d12 = (V[1][0] - V[0][0], V[1][1] - V[0][1])
                d13 = (V[2][0] - V[0][0], V[2][1] - V[0][1])
                d23 = (V[2][0] - V[1][0], V[2][1] - V[1][1])
                s12 = 4 * (q[0] + q[1] - 2 * m12)
                s13 = 4 * (q[0] + q[2] - 2 * m13)
                s23 = 4 * (q[1] + q[2] - 2 * m23)
                # d^T H d = s for the three chords (Cramer)
                rows = [(d[0] * d[0], 2 * d[0] * d[1], d[1] * d[1], s) for d, s in ((d12, s12), (d13, s13), (d23, s23))]

                def det3(r):
                    return (r[0][0] * (r[1][1] * r[2][2] - r[1][2] * r[2][1])
                            - r[0][1] * (r[1][0] * r[2][2] - r[1][2] * r[2][0])
                            + r[0][2] * (r[1][0] * r[2][1] - r[1][1] * r[2][0]))

                Dm = det3([r[:3] for r in rows])
                h = []
                for col in range(3):
                    mm = [list(r[:3]) for r in rows]
                    for t in range(3):
                        mm[t][col] = rows[t][3]
                    h.append(det3(mm) / Dm)
                h11, h12, h22 = h
                # gradient at V1: g . d12 = q2 - q1 - s12/2, g . d13 = q3 - q1 - s13/2
                r1 = q[1] - q[0] - s12 / 2
                r2 = q[2] - q[0] - s13 / 2
                dd = d12[0] * d13[1] - d12[1] * d13[0]
                gx = (r1 * d13[1] - r2 * d12[1]) / dd
                gy = (d12[0] * r2 - d13[0] * r1) / dd
                detH = h11 * h22 - h12 * h12
                trH = h11 + h22
                break
            except Resample:
                s1 = T2.between(Alg.rat(s1), B1) if attempt % 2 else T2.between(A1, Alg.rat(s1))
        else:
            return False, ('resample', str(s1))
        brk = []
        for gpol in ctx.guards.values():
            brk += T2.roots_in_alg(gpol, A1, B1)
        brk = T2.sorted_unique(brk)
        if brk:
            ends = [A1] + brk + [B1]
            for X, Y in zip(ends, ends[1:]):
                pieces.append((X, Y, T2.between(X, Y)))
            continue
        if (isinstance(detH, rf.RF) and detH.n == 0) or (not isinstance(detH, rf.RF) and detH == 0):
            continue                         # H singular on the piece: no strict interior minimum

        def rfc(x):
            return x if isinstance(x, rf.RF) else T2.rf_const(ctx, Fraction(x))

        detH, trH = rfc(detH), rfc(trH)
        qstar = q[0] - (h22 * gx * gx - 2 * h12 * gx * gy + h11 * gy * gy) / (2 * detH)
        val = rfc(qstar - 1)
        cx = rfc(V[0][0] - (h22 * gx - h12 * gy) / detH)
        cy = rfc(V[0][1] - (h11 * gy - h12 * gx) / detH)
        conds = []
        for m in edges:
            a_, b_, k_ = (_wrap(ctx, nd) for nd in Lp[m])
            conds.append(rfc(inside[m] * (a_ * cx + b_ * cy - k_)))
        polys = [T2.sign_poly(detH), T2.sign_poly(trH), T2.sign_poly(val)] + [T2.sign_poly(c) for c in conds]
        cut_pts = []
        for p in polys:
            if p != 0:
                cut_pts += T2.roots_in_alg(p, A1, B1)
        ends = [A1] + T2.sorted_unique(cut_pts) + [B1]
        for X, Y in zip(ends, ends[1:]):
            t = T2.between(X, Y)
            sd, st, sv = (p(t) for p in polys[:3])
            if sd > 0 and st > 0 and sv < 0 and all(p(t) >= 0 for p in polys[3:]):
                uq = Fraction(int(t.p), int(t.q))
                xq = Fraction(int((cx.n(t) / cx.d(t)).p), int((cx.n(t) / cx.d(t)).q))
                yq = Fraction(int((cy.n(t) / cy.d(t)).p), int((cy.n(t) / cy.d(t)).q))
                mass = solver.point_mass(loc, xq, yq, uq)
                return False, {'why': 'face interior', 'face': labs, 'u': str(uq), 'x': str(xq), 'y': str(yq),
                               'mass': str(mass), 'mass_float': float(mass)}
    return True, None


def face_check(loc, Lp, a, b):
    """Lemma B5 over (a, b): sweep the critical u, enumerate the faces at a sample of each interval, check each."""
    assert not loc.pts, 'faces.py: point masses are not supported'
    sm = (a + b) / 2
    ctx = rf.Ctx(Fraction(int(sm.p), int(sm.q)))
    U = critical_u(Lp, ctx, a, b)
    ends = [Alg.rat(a)] + U + [Alg.rat(b)]
    nf = 0
    for A, B in zip(ends, ends[1:]):
        u0 = T2.between(A, B)
        u0f = Fraction(int(u0.p), int(u0.q))
        for f in faces_at(Lp, u0f):
            nf += 1
            ok, info = check_face(loc, Lp, f, A, B, u0)
            if not ok:
                return {'ok': False, 'why': 'face', 'info': info, 'intervals': len(ends) - 1, 'faces': nf}
    return {'ok': True, 'intervals': len(ends) - 1, 'faces': nf}
