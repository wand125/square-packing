"""Tier B, per-candidate form, for centre boxes whose squares cannot meet a polygon of the cover (then mu is
piecewise *linear* in the centre at each fixed angle).

Lemma B3.  Fix an interval J = (a, b) not containing 0, and a centre box X = [x0,x1] x [y0,y1] such that no square
centred in X (any angle) meets a polygon of the cover.  For u in J let R(u) = X ∩ [lo, s - lo]^2 (admissible
centres, lo = (|cos t| + |sin t|)/2).  By Lemma F1, c -> mu(Q(c, t)) is continuous and affine on every face of the
arrangement A(u) of the lines (a), (b); the faces inside R(u) are convex and R(u) is compact, so
min_{R(u)} mu = min over the vertices of A(u) ∪ {sides of R(u)} that lie in R(u).
Let 𝓛 be a set of lines (with coefficients rational in u) containing every line of (a), (b) that meets X for some
u in J (a line is left out only if its value at the four corners of X has one strict sign on all of [a, b],
proved exactly), plus the eight lines bounding R(u).  Every vertex in R(u) is p_ij(u) = L_i ∩ L_j for a pair of
𝓛 with p_ij(u) ∈ R(u).  Hence it suffices that for every pair (i, j) and every u in J with p_ij(u) ∈ R(u):
mu(Q(p_ij(u), t(u))) >= 1.
Each pair's set {u ∈ J : p_ij(u) ∈ R(u)} is a finite union of intervals cut out by the real roots of nine
polynomials (eight membership tests and the determinant); on each piece the value is evaluated by symbolic
execution of point_mass (Lemma B1, guards per piece), and (N - D) D >= 0 is checked exactly on the open piece
(roots of odd multiplicity excluded, exact comparison with the algebraic ends).  Points where these conditions
change are finitely many and are covered by continuity of mu in (c, u) for u != 0 (closedness of the
inequality).
"""
from fractions import Fraction
import rf
from rf import P, Q, Resample
import solver
from tier_b import Alg, alg_cmp, root_free, strip0


def rf_const(ctx, x):
    return rf.RF(P([Q(x.numerator, x.denominator) if isinstance(x, Fraction) else Q(x)]), P([1]), ctx, reduce=False)


def sign_poly(v):
    """Polynomial with the sign of the RF v wherever its denominator is nonzero."""
    return v.n * v.d


def roots_in(p, a, b):
    """Alg roots of p in the open interval (a, b) (rationals), distinct."""
    out = []
    if p.degree() <= 0:
        return out
    if a == 0 or b == 0:
        p = strip0(p)
        if p.degree() <= 0:
            return out
    if root_free(p, a, b):
        return out
    sq = rf.squarefree(p)
    for l, r in rf.roots_open(sq, a, b):
        out.append(Alg(sq, l, r))
    return out


def sorted_unique(algs):
    res = []
    for x in sorted(algs, key=lambda z: z.l):
        res.append(x)
    # exact sort (insertion with alg_cmp), drop duplicates
    out = []
    for x in res:
        k = len(out)
        while k > 0 and alg_cmp(out[k - 1], x) > 0:
            k -= 1
        if k > 0 and alg_cmp(out[k - 1], x) == 0:
            continue
        out.insert(k, x)
    return out


def between(A, B):
    """A rational strictly between the algebraic numbers A < B."""
    for _ in range(400):
        if A.r < B.l:
            return (A.r + B.l) / 2 if A.p is not None or B.p is not None or True else None
        if A.width() >= B.width() and A.p is not None:
            A.refine()
        elif B.p is not None:
            B.refine()
        else:
            A.refine()
    raise RuntimeError('between')


def nonneg_open(p, A, B):
    """Exact: p >= 0 on the open interval (A, B), A < B algebraic or rational."""
    if p == 0:
        return True
    lo, hi = A.l, B.r
    c, facs = p.factor_squarefree()
    odd = P([1])
    for q, k in facs:
        if k % 2 == 1:
            odd = odd * q
    # odd-multiplicity roots strictly inside (A, B) make p change sign there
    if odd.degree() > 0:
        for l, r in rf.isolate(odd, lo, hi):
            R = Alg(rf.squarefree(odd), l, r)
            if odd(r) == 0:
                R = Alg.rat(r)
            if alg_cmp(A, R) < 0 and alg_cmp(R, B) < 0:
                return False
    s = between(A, B)
    return p(s) >= 0


def certify(loc, side, box, a, b, stats=None, max_runs=2000):
    """Per-candidate Tier B on (a, b), 0 <= a < b or a < b <= 0.  Vertices per pair (Lemma B3); if a square of the
    box can meet a polygon, also the edge criticals line by line (Lemma B4).  Point masses are not supported
    (with them mu is not continuous in the centre, and the edge second difference below would be wrong)."""
    assert not loc.pts, 'Tier B does not support point masses'
    a, b = Q(a), Q(b)
    pos = a >= 0
    assert pos or b <= 0
    x0, x1, y0, y1 = box
    sm = (a + b) / 2
    ctx = rf.Ctx(Fraction(int(sm.p), int(sm.q)))
    u = ctx.var()
    c, s, verts, normals = solver.frame(u)
    lo = (c + s) / 2 if pos else (c - s) / 2         # |cos| + |sin| with cos > 0 for |u| <= 1/2
    hi = side - lo
    corners = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    # all candidate lines, as RF triples (a, b, k): a x + b y = k
    cand = []
    for (la, lb, lk) in loc.lines:
        for vx, vy in verts:
            cand.append((rf_const(ctx, la), rf_const(ctx, lb), lk - la * vx - lb * vy))
    for Pt in loc.bps:
        for n in normals:
            cand.append((n[0], n[1], n[0] * Pt[0] + n[1] * Pt[1] - Fraction(1, 2)))
    L = [(rf_const(ctx, 1), rf_const(ctx, 0), rf_const(ctx, x0)), (rf_const(ctx, 1), rf_const(ctx, 0), rf_const(ctx, x1)),
         (rf_const(ctx, 0), rf_const(ctx, 1), rf_const(ctx, y0)), (rf_const(ctx, 0), rf_const(ctx, 1), rf_const(ctx, y1)),
         (rf_const(ctx, 1), rf_const(ctx, 0), lo), (rf_const(ctx, 1), rf_const(ctx, 0), hi),
         (rf_const(ctx, 0), rf_const(ctx, 1), lo), (rf_const(ctx, 0), rf_const(ctx, 1), hi)]
    seen = set()
    dropped = 0
    for l in cand:
        key = (hash(l[0]), hash(l[1]), hash(l[2]))
        if key in seen:
            continue
        seen.add(key)
        vals = [l[0] * q[0] + l[1] * q[1] - l[2] for q in corners]
        sg = [sign_poly(v) for v in vals]
        # exclude only if all four have the same strict sign on the whole closed [a, b]
        def strict_sign(p):
            if p == 0:
                return 0
            if not root_free(p, a, b):
                return 0
            v = p(a)
            return 1 if v > 0 else -1
        ss = [strict_sign(p) for p in sg]
        if all(x == 1 for x in ss) or all(x == -1 for x in ss):
            dropped += 1
            continue
        L.append(l)
    A0, B0 = Alg.rat(a), Alg.rat(b)
    npairs = nvals = 0
    for i in range(len(L)):
        a1, b1, k1 = L[i]
        for j in range(i + 1, len(L)):
            a2, b2, k2 = L[j]
            det = a1 * b2 - a2 * b1
            if det == 0:
                continue
            px = (k1 * b2 - k2 * b1) / det
            py = (a1 * k2 - a2 * k1) / det
            conds = [px - x0, x1 - px, py - y0, y1 - py, px - lo, hi - px, py - lo, hi - py]
            polys = [sign_poly(v) for v in conds]
            # quick reject: some condition strictly negative on all of [a, b]
            reject = False
            for p in polys:
                if p != 0 and root_free(p, a, b) and p(a) < 0:
                    reject = True; break
            if reject:
                continue
            npairs += 1
            brk = []
            for p in polys + [sign_poly(det)]:
                brk += roots_in(p, a, b)
            brk = [A0] + sorted_unique(brk) + [B0]
            for A, B in zip(brk, brk[1:]):
                smp = between(A, B)
                ok_in = all(p(smp) >= 0 for p in polys)
                if not ok_in:
                    continue
                ok, where = check_value(loc, (px, py), A, B, smp)
                if not ok:
                    return {'ok': False, 'why': 'value', 'pair': (i, j), 'at': str(smp),
                            'pose': witness(loc, (px, py), where)}
                nvals += 1
    res = {'ok': True, 'lines': len(L), 'dropped': dropped, 'pairs': npairs, 'values': nvals}
    if loc.polys:
        from tier_b import chain
        Lp = [tuple((v.n, v.d) for v in l) for l in L]
        nruns = 0
        for i in range(len(L)):
            r = chain(edge_runner(loc, side, box, Lp, i, pos), a, b, max_runs=max_runs)
            nruns += len(r.get('runs', []))
            if not r['ok']:
                return {'ok': False, 'why': 'edge:' + r['why'], 'line': i, 'at': r.get('at')}
        res['edge_runs'] = nruns
    return res


def edge_runner(loc, side, box, Lp, i, pos):
    """Lemma B4.  The 1-D critical points on line i: its breakpoints are its intersections with the other lines
    of the (superset) list that lie in R(u); between consecutive ones mu is a single quadratic along the line
    (Lemma F1), fitted exactly from three values.  Returns the critical values (A > 0, 0 < t < 1)."""
    x0, x1, y0, y1 = box

    def run(u):
        ctx = u.c
        mk = lambda nd: rf.RF(nd[0], nd[1], ctx, reduce=False)
        L = [tuple(mk(nd) for nd in l) for l in Lp]
        fr = solver.frame(u)
        c, s_, _, _ = fr
        lo = (c + s_) / 2 if pos else (c - s_) / 2
        hi = side - lo
        a1, b1, k1 = L[i]
        pts = []
        for j in range(len(L)):
            if j == i:
                continue
            a2, b2, k2 = L[j]
            det = a1 * b2 - a2 * b1
            if det == 0:
                continue
            px = (k1 * b2 - k2 * b1) / det
            py = (a1 * k2 - a2 * k1) / det
            if x0 <= px <= x1 and y0 <= py <= y1 and lo <= px <= hi and lo <= py <= hi:
                pts.append((px, py))
        dx, dy = -b1, a1
        pts = sorted(pts, key=lambda p: p[0] * dx + p[1] * dy)
        out = []
        cache, gcache = {}, {}
        def f(p):
            key = (hash(p[0]), hash(p[1]))
            if key not in cache:
                cache[key] = solver.point_mass(loc, p[0], p[1], u, fr)
            return cache[key]
        def g(p):
            key = (hash(p[0]), hash(p[1]))
            if key not in gcache:
                gcache[key] = solver.poly_mass(loc, p[0], p[1], u, fr)
            return gcache[key]
        for p, q in zip(pts, pts[1:]):
            if p[0] == q[0] and p[1] == q[1]:
                continue
            m = ((p[0] + q[0]) / 2, (p[1] + q[1]) / 2)
            # second difference from the polygon term alone (the segment term is affine on the sub-edge)
            A = 2 * (g(p) - 2 * g(m) + g(q))
            if A > 0:
                fp, fq = f(p), f(q)
                B = fq - fp - A
                t = -B / (2 * A)
                if t > 0 and t < 1:
                    out.append((fp + B * t + A * t * t, ('edge', i)))
        return out
    return run


def check_value(loc, pt, A, B, smp):
    """mu(Q(p(u), u)) >= 1 on the open piece (A, B), p = pt (RF coordinates), by symbolic execution of point_mass
    at a sample (Lemma B1); pieces with guard roots inside are split at those roots and redone."""
    px0, py0 = pt
    pieces = [(A, B, smp)]
    while pieces:
        A1, B1, s1 = pieces.pop()
        for attempt in range(60):
            try:
                ctx = rf.Ctx(Fraction(int(s1.p), int(s1.q)))
                u = ctx.var()
                px = rf.RF(px0.n, px0.d, ctx, reduce=False)
                py = rf.RF(py0.n, py0.d, ctx, reduce=False)
                v = solver.point_mass(loc, px, py, u)
                if not isinstance(v, rf.RF):
                    v = rf_const(ctx, v)
                break
            except Resample:
                s1 = between(Alg.rat(s1), B1) if attempt % 2 else between(A1, Alg.rat(s1))
        else:
            return False, s1
        brk = []
        for g in ctx.guards.values():
            brk += roots_in_alg(g, A1, B1)
        brk = sorted_unique(brk)
        if brk:
            ends = [A1] + brk + [B1]
            for X, Y in zip(ends, ends[1:]):
                pieces.append((X, Y, between(X, Y)))
            continue
        pol = (v.n - v.d) * v.d
        if not nonneg_open(pol, A1, B1):
            return False, (A1, B1, s1, pol)
    return True, None


def witness(loc, pt, where):
    """A concrete pose where the failing value is below 1, with its exact mass (or None if none is found among
    a few rational samples of the piece; then the failure may be a tight value at an end of the piece)."""
    if not isinstance(where, tuple):
        return None
    A1, B1, s1, pol = where
    px0, py0 = pt
    cands = [s1]
    lo, hi = A1.r if A1.p is not None else A1.l, B1.l if B1.p is not None else B1.r
    pts = [lo, hi]
    sq = rf.squarefree(pol)
    for l, r in rf.isolate(sq, lo, hi):
        R = Alg(sq, l, r)
        for _ in range(40):
            R.refine()
        pts += [R.l, R.r]
    pts = sorted(set(pts))
    for p_, q_ in zip(pts, pts[1:]):
        cands.append((p_ + q_) / 2)
    for t in cands:
        if not (alg_cmp(A1, Alg.rat(t)) < 0 and alg_cmp(Alg.rat(t), B1) < 0):
            continue
        if pol(t) < 0:
            u = Fraction(int(t.p), int(t.q))
            x = Fraction(int((px0.n(t) / px0.d(t)).p), int((px0.n(t) / px0.d(t)).q))
            y = Fraction(int((py0.n(t) / py0.d(t)).p), int((py0.n(t) / py0.d(t)).q))
            m = solver.point_mass(loc, x, y, u)
            return {'u': str(u), 'x': str(x), 'y': str(y), 'mass': str(m), 'mass_float': float(m)}
    return None


def roots_in_alg(g, A, B):
    """Alg roots of g strictly between the algebraic numbers A < B."""
    lo, hi = A.l, B.r
    out = []
    for r in roots_in(g, lo, hi):
        if alg_cmp(A, r) < 0 and alg_cmp(r, B) < 0:
            out.append(r)
    # a root exactly at a rational end lo/hi is not inside (A, B) unless A, B are irrational; check them too
    for x in (lo, hi):
        if g != 0 and g(x) == 0:
            R = Alg.rat(x)
            if alg_cmp(A, R) < 0 and alg_cmp(R, B) < 0:
                out.append(R)
    return out


if __name__ == '__main__':
    import sys, time
    from tier_a import Cover
    cov = Cover(sys.argv[1])
    box = tuple(Fraction(v) for v in sys.argv[2:6])
    a, b = Fraction(sys.argv[6]), Fraction(sys.argv[7])
    loc = solver.Local(cov, *box)
    t = time.time()
    r = certify(loc, cov.s, box, Q(a.numerator, a.denominator), Q(b.numerator, b.denominator))
    print(r, f'{time.time() - t:.1f}s')
