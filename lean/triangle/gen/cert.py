"""Farkas-Bernstein certificates for unit squares in an equilateral triangle (generator side).

Not part of the trusted base: every certificate produced here is re-checked by the Lean kernel.

Variables: centre (x, y) and u = tan(theta/2).  All polynomials are affine in (x, y) and
polynomial in u, with coefficients in Q(sqrt3).  An affine form is a dict {'1','x','y'} -> upoly.
"""
from itertools import product

import numpy as np
from gmpy2 import mpq
from scipy.optimize import linprog

from q3 import Q3, ZERO, ONE

S3 = Q3(0, 1)
HALF = mpq(1, 2)

# ------------------------------------------------------------------ univariate polys over Q3


def ptrim(p):
    p = list(p)
    while p and p[-1].is_zero():
        p.pop()
    return p


def padd(p, q):
    n = max(len(p), len(q))
    return ptrim([(p[i] if i < len(p) else ZERO) + (q[i] if i < len(q) else ZERO) for i in range(n)])


def pmul(p, q):
    if not p or not q:
        return []
    r = [ZERO] * (len(p) + len(q) - 1)
    for i, a in enumerate(p):
        if a.is_zero():
            continue
        for j, b in enumerate(q):
            r[i + j] = r[i + j] + a * b
    return ptrim(r)


def pscale(p, k):
    return ptrim([c * k for c in p])


def pneg(p):
    return [-c for c in p]


def ppow(p, k):
    r = [ONE]
    for _ in range(k):
        r = pmul(r, p)
    return r


def peval_f(p, u):
    r = 0.0
    for c in reversed(p):
        r = r * u + float(c)
    return r


D = [ONE, ZERO, ONE]            # 1 + u^2
C1 = [ONE, ZERO, Q3(-1)]        # 1 - u^2
S1 = [ZERO, Q3(2)]              # 2u

# ------------------------------------------------------------------ affine forms


def aff(one=(), x=(), y=()):
    return {'1': ptrim(list(one)), 'x': ptrim(list(x)), 'y': ptrim(list(y))}


def aadd(f, g):
    return {k: padd(f[k], g[k]) for k in ('1', 'x', 'y')}


def amul(p, f):
    return {k: pmul(p, f[k]) for k in ('1', 'x', 'y')}


def aneg(f):
    return {k: pneg(f[k]) for k in ('1', 'x', 'y')}


def adeg(f):
    return max(len(f[k]) for k in f) - 1


def aeval_f(f, x, y, u):
    return peval_f(f['1'], u) + peval_f(f['x'], u) * x + peval_f(f['y'], u) * y

# ------------------------------------------------------------------ geometry


def triangle_sides(L):
    """Half-planes a.q + b >= 0 of T_L = conv{(0,0),(L,0),(L/2, L sqrt3/2)}."""
    return [((ZERO, ONE), ZERO),               # y >= 0
            ((S3, Q3(-1)), ZERO),              # sqrt3 x - y >= 0
            ((-S3, Q3(-1)), S3 * L)]           # sqrt3 (L - x) - y >= 0


def admissibility(L):
    """The 12 forms H >= 0 (times D): each square vertex c + R sigma lies in T_L."""
    out = []
    for k, ((ax, ay), b) in enumerate(triangle_sides(L)):
        for sx, sy in product((-HALF, HALF), repeat=2):
            vx = padd(pscale(C1, sx), pscale(S1, -sy))     # D * (R sigma).x
            vy = padd(pscale(S1, sx), pscale(C1, sy))      # D * (R sigma).y
            one = padd(pscale(D, b), padd(pscale(vx, ax), pscale(vy, ay)))
            out.append((('adm', k, int(sx * 2), int(sy * 2)), aff(one, pscale(D, ax), pscale(D, ay))))
    return out


def gcoef(k):
    """(alpha_k(u), beta_k(u)) of G_k = -D + alpha (px - x) + beta (py - y)."""
    two_c1 = pscale(C1, 2)
    four_u = [ZERO, Q3(4)]
    return [(two_c1, four_u), (pneg(two_c1), pneg(four_u)),
            (pneg(four_u), two_c1), (four_u, pneg(two_c1))][k]


def capture_target(p, k):
    """D * (-G_k) >= 0 means the k-th side condition of 'p in Q(c, theta)'."""
    px, py = p
    al, be = gcoef(k)
    g_one = padd(pneg(D), padd(pscale(al, px), pscale(be, py)))
    g = aff(g_one, pneg(al), pneg(be))                 # G_k as an affine form in (x, y)
    return amul(D, aneg(g))


def box_forms(x0, x1, y0, y1):
    return [(('box', 'x0'), aff([-x0], [ONE])), (('box', 'x1'), aff([x1], [Q3(-1)])),
            (('box', 'y0'), aff([-y0], [], [ONE])), (('box', 'y1'), aff([y1], [], [Q3(-1)]))]

# ------------------------------------------------------------------ Bernstein-type basis


def bern(U0, U1, d, i):
    """(u - U0)^i (U1 - u)^(d-i), nonnegative on [U0, U1]."""
    return pmul(ppow([-U0, ONE], i), ppow([U1, Q3(-1)], d - i))

# ------------------------------------------------------------------ LP


def columns(forms, U0, U1, dmax):
    """Columns of the certificate LP: every (form, basis index) with product degree <= dmax,
    plus the free nonnegative term mu(u) (on '1')."""
    cols = []
    for tag, f in forms:
        d = dmax - max(adeg(f), 0)
        if d < 0:
            continue
        for i in range(d + 1):
            cols.append((tag, d, i, amul(bern(U0, U1, d, i), f)))
    for i in range(dmax + 1):
        cols.append((('mu',), dmax, i, aff(bern(U0, U1, dmax, i))))
    return cols


def vec(f, dmax):
    v = []
    for k in ('1', 'x', 'y'):
        p = f[k]
        v += [p[i] if i < len(p) else ZERO for i in range(dmax + 1)]
    return v


def shift(p, U0, w):
    """p(U0 + w t) as a polynomial in t.  A linear change of variable keeps every identity, so the
    coefficients are compared in t: on a narrow bin the monomial basis in u is badly conditioned."""
    r = []
    lin = [U0, w]
    for c in reversed(p):
        r = padd(pmul(r, lin), [c])
    return r


def tvec(f, dmax, U0, w):
    return vec({k: shift(f[k], U0, w) for k in ('1', 'x', 'y')}, dmax)


def solve(target, forms, U0, U1, dmax=4):
    """Find nonnegative coefficients with sum coef * column == target exactly.
    Returns a list of (tag, d, i, coef) or None."""
    cols = columns(forms, U0, U1, dmax)
    w = U1 - U0
    if w.is_zero():
        w = ONE
    A = [tvec(c[3], dmax, U0, w) for c in cols]
    b = tvec(target, dmax, U0, w)
    m, n = len(b), len(cols)
    Af = np.array([[float(A[j][r]) for j in range(n)] for r in range(m)])
    bf = np.array([float(x) for x in b])
    cscale = np.maximum(np.abs(Af).max(axis=0), 1e-300)
    Af = Af / cscale[None, :]
    scale = np.maximum(np.abs(Af).max(axis=1), 1e-300)
    res = linprog(np.zeros(n), A_eq=Af / scale[:, None], b_eq=bf / scale, bounds=[(0, None)] * n,
                  method='highs')
    if res.status == 2:
        return None
    if res.status != 0:
        sol = exact_feasible([[A[j][r] for j in range(n)] for r in range(m)], b)
        if sol is None:
            return None
        return [(cols[j][0], cols[j][1], cols[j][2], sol[j]) for j in range(n) if not sol[j].is_zero()]
    support = [j for j in range(n) if res.x[j] > 1e-9 * max(1.0, float(np.max(res.x)))]
    sol = exact_feasible([[A[j][r] for j in support] for r in range(m)], b)
    if sol is None:
        sol_full = exact_feasible([[A[j][r] for j in range(n)] for r in range(m)], b)
        if sol_full is None:
            return None
        support = list(range(n))
        sol = sol_full
    return [(cols[j][0], cols[j][1], cols[j][2], sol[k]) for k, j in enumerate(support) if not sol[k].is_zero()]


def exact_feasible(A, b):
    """x >= 0 with A x = b over Q(sqrt3): phase-1 simplex with Bland's rule.  None if infeasible."""
    m = len(b)
    n = len(A[0]) if m else 0
    rows = []
    for r in range(m):
        row = list(A[r])
        rhs = b[r]
        if rhs.sign() < 0:
            row = [-a for a in row]
            rhs = -rhs
        rows.append(row + [ONE if k == r else ZERO for k in range(m)] + [rhs])
    basis = [n + r for r in range(m)]
    N = n + m
    # objective: minimise sum of artificials -> reduced costs
    def reduced():
        z = [ZERO] * (N + 1)
        for r in range(m):
            if basis[r] >= n:
                for j in range(N + 1):
                    z[j] = z[j] + rows[r][j]
        return z   # maximise sum over non-artificial = reduce artificials
    for _ in range(200000):
        z = reduced()
        enter = next((j for j in range(n) if z[j].sign() > 0 and j not in basis), None)
        if enter is None:
            break
        leave, best = None, None
        for r in range(m):
            a = rows[r][enter]
            if a.sign() > 0:
                ratio = rows[r][N] / a
                if best is None or (ratio - best).sign() < 0 or ((ratio - best).is_zero() and basis[r] < basis[leave]):
                    leave, best = r, ratio
        if leave is None:
            return None
        piv = rows[leave][enter]
        rows[leave] = [v / piv for v in rows[leave]]
        for r in range(m):
            if r != leave and not rows[r][enter].is_zero():
                f = rows[r][enter]
                rows[r] = [rows[r][j] - f * rows[leave][j] for j in range(N + 1)]
        basis[leave] = enter
    if any(basis[r] >= n and not rows[r][N].is_zero() for r in range(m)):
        return None
    x = [ZERO] * n
    for r in range(m):
        if basis[r] < n:
            x[basis[r]] = rows[r][N]
    if any(v.sign() < 0 for v in x):
        return None
    return x


def check_identity(target, forms, U0, U1, cert, dmax=4):
    """Recompute sum coef * basis * form and compare with the target (sanity, exact)."""
    fmap = dict(forms)
    acc = aff()
    for tag, d, i, c in cert:
        base = aff(bern(U0, U1, d, i)) if tag == ('mu',) else amul(bern(U0, U1, d, i), fmap[tag])
        acc = aadd(acc, {k: pscale(base[k], c) for k in base})
    return all(ptrim(padd(acc[k], pneg(target[k]))) == [] for k in ('1', 'x', 'y')) and all(c.sign() >= 0 for *_, c in cert)
