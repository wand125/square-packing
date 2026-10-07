"""Second check of the triple lemma inequality (M) (n6/triple/LEMMA.md, item 2-a).

S is derived here from the definitions in LEMMA.md (not from derive2.py):
  v = 2 + 4/sqrt3, d_L(X) = (sqrt3 x - y)/2, d_R(X) = (sqrt3 (v - x) - y)/2,
  Q_i = Q_i* + (a_i, b_i), Q_0* = (1/sqrt3, 0), Q_1* = (1 + 1/sqrt3, 0), e_i = (cos p_i, sin p_i), f_i = (-sin p_i, cos p_i),
  P = Q_1 + e_1 + f_1,
  g_L = d_L(Q_0 + f_0),  g_R = d_R(P) - cos p3 - tau |sin p3|,  g_b,i = b_i + beta_i sin p_i,
  S1: g_sep = e_1.Q_1 - e_1.(alpha (Q_0 + e_0 + f_0) + (1 - alpha)(Q_0 + e_0)),
  S0: g_sep = alpha e_0.(Q_1 + f_1) + (1 - alpha) e_0.Q_1 - e_0.Q_0 - 1,
  S = g_L + g_R + (sqrt3/2) g_sep + (g_b,0 + g_b,1)/2,
with (alpha, beta_0, beta_1) chosen by the orthant of (p0, p1) as in the LEMMA table.

Claim (M): on |p_i| <= Phi, |a_i| <= delta, 0 <= b_i <= delta, for both cases and all 8 orthants of (p0, p1, p3),
  S <= -c (|p0| + |p1| + |p3|) for an explicit c > 0.

Proof by computer (mpmath interval arithmetic, outward rounded):
 * p3 enters only through T3 = 1 - cos p3 - tau |sin p3| (checked symbolically: dS/dp3 has no other term), and
   T3 <= -c3 |p3| with c3 = tau sin(Phi)/Phi - Phi/2 (1 - cos x <= x^2/2, sin is concave on [0, Phi]).
 * S - T3 is affine in (a, b): S - T3 = F(p0, p1) + sum k_v(p0, p1) v over v in {a0, a1, b0, b1}.  Its max over the
   (a, b) box is F + sum_a delta |k_a| + sum_b delta max(k_b, 0).
 * G(p) := that max must be <= -c01 (|p0| + |p1|) on the orthant box [0, Phi]^2 (signs folded).  Branch and bound:
   - a sub-box not touching p = 0: interval value of G + c01 (|p0| + |p1|) < 0;
   - the sub-box [0, r]^2 at the origin: F(p) <= grad F(0).p + (1/2) sum_jl sup|F_jl| |p_j| |p_l| and
     |k(p)| <= sum_j sup|k_j| |p_j| (k(0) = 0 is checked exactly), which gives a linear bound in |p_j|.
"""
import argparse
import json
import time

import sympy as sp
from mpmath import iv, mp

mp.prec = 80
iv.prec = 80

p0, p1, p3, a0, a1, b0, b1 = sp.symbols('p0 p1 p3 a0 a1 b0 b1', real=True)
al, be0, be1, tau = sp.symbols('alpha beta0 beta1 tau', real=True)
r3 = sp.sqrt(3)
v = 2 + 4 / r3


def dL(X):
    return (r3 * X[0] - X[1]) / 2


def dR(X):
    return (r3 * (v - X[0]) - X[1]) / 2


def vec(x, y):
    return sp.Matrix([x, y])


e0, f0 = vec(sp.cos(p0), sp.sin(p0)), vec(-sp.sin(p0), sp.cos(p0))
e1, f1 = vec(sp.cos(p1), sp.sin(p1)), vec(-sp.sin(p1), sp.cos(p1))
Q0 = vec(1 / r3 + a0, b0)
Q1 = vec(1 + 1 / r3 + a1, b1)
P = Q1 + e1 + f1
s3abs = sp.Symbol('s3abs', nonnegative=True)      # stands for |sin p3|


def S_expr(case):
    gL = dL(Q0 + f0)
    gR = dR(P) - sp.cos(p3) - tau * s3abs
    gb = (b0 + be0 * sp.sin(p0)) + (b1 + be1 * sp.sin(p1))
    if case == 'S1':
        X = al * (Q0 + e0 + f0) + (1 - al) * (Q0 + e0)
        gsep = (e1.T * Q1)[0] - (e1.T * X)[0]
    else:
        gsep = al * (e0.T * (Q1 + f1))[0] + (1 - al) * (e0.T * Q1)[0] - (e0.T * Q0)[0] - 1
    return sp.expand(gL + gR + r3 / 2 * gsep + gb / 2)


T = 1 - 1 / (2 * r3)
ORTHANTS = {(1, 1): (T, 0, 0), (-1, -1): (T, 1, 1), (1, -1): (0, 0, 1), (-1, 1): (1, 1, 0)}


def to_iv(e, env):
    """Rigorous interval evaluation of a sympy expression."""
    if e.is_Symbol:
        return env[e]
    if e.is_Rational:
        return iv.mpf(int(e.p)) / iv.mpf(int(e.q))
    if e.is_Add:
        r = iv.mpf(0)
        for t in e.args:
            r = r + to_iv(t, env)
        return r
    if e.is_Mul:
        r = iv.mpf(1)
        for t in e.args:
            r = r * to_iv(t, env)
        return r
    if e.is_Pow:
        b, ex = e.args
        if ex == sp.Rational(1, 2):
            return iv.sqrt(to_iv(b, env))
        if ex == -sp.Rational(1, 2):
            return 1 / iv.sqrt(to_iv(b, env))
        if ex.is_Integer:
            base = to_iv(b, env)
            n = int(ex)
            if n >= 0:
                r = iv.mpf(1)
                for _ in range(n):
                    r = r * base
                return r
            r = iv.mpf(1)
            for _ in range(-n):
                r = r * base
            return 1 / r
    if isinstance(e, sp.cos):
        return iv.cos(to_iv(e.args[0], env))
    if isinstance(e, sp.sin):
        return iv.sin(to_iv(e.args[0], env))
    raise ValueError(f'cannot evaluate {e!r} ({type(e)})')


def iabs(x):
    lo, hi = x.a, x.b
    if lo >= 0:
        return x
    if hi <= 0:
        return -x
    return iv.mpf([0, max(-lo, hi)])


def imax0(x):
    return iv.mpf([max(x.a, 0), max(x.b, 0)])


def check(Phi, delta, tauv, case, orth, c01, r0, max_boxes=200000):
    s0, s1 = orth
    A, B0, B1 = ORTHANTS[orth]
    S = S_expr(case).subs({al: A, be0: B0, be1: B1, tau: tauv})
    # separate p3 part
    T3 = -sp.cos(p3) - tauv * s3abs + 1
    rest = sp.expand(S - T3)
    assert not rest.has(p3) and not rest.has(s3abs), 'p3 enters S outside T3'
    # affine in a, b
    ks = {vv: sp.diff(rest, vv) for vv in (a0, a1, b0, b1)}
    for vv, k in ks.items():
        assert not any(k.has(w) for w in (a0, a1, b0, b1)), 'not affine'
    F = sp.expand(rest.subs({a0: 0, a1: 0, b0: 0, b1: 0}))
    # fold signs: p_i = s_i q_i with q_i in [0, Phi]
    q0, q1 = sp.symbols('q0 q1', nonnegative=True)
    sub = {p0: s0 * q0, p1: s1 * q1}
    Fq = F.subs(sub)
    kq = {vv: k.subs(sub) for vv, k in ks.items()}
    # exact zero at the origin
    assert sp.simplify(Fq.subs({q0: 0, q1: 0})) == 0
    for k in kq.values():
        assert sp.simplify(k.subs({q0: 0, q1: 0})) == 0
    dlt = iv.mpf(delta)

    def G(env):
        g = to_iv(Fq, env)
        for vv in (a0, a1):
            g = g + dlt * iabs(to_iv(kq[vv], env))
        for vv in (b0, b1):
            g = g + dlt * imax0(to_iv(kq[vv], env))
        return g
    # origin box bound
    grad = [sp.diff(Fq, q) for q in (q0, q1)]
    hess = [[sp.diff(Fq, x, y) for y in (q0, q1)] for x in (q0, q1)]
    kgrad = {vv: [sp.diff(k, q) for q in (q0, q1)] for vv, k in kq.items()}
    r = iv.mpf(r0)
    env0 = {q0: iv.mpf([0, r0]), q1: iv.mpf([0, r0])}
    zero = {q0: iv.mpf(0), q1: iv.mpf(0)}
    coef = []
    for j in range(2):
        cj = to_iv(grad[j], zero)
        for l in range(2):
            cj = cj + iv.mpf(0.5) * iabs(to_iv(hess[j][l], env0)) * r
        for vv in (a0, a1, b0, b1):
            cj = cj + dlt * iabs(to_iv(kgrad[vv][j], env0))
        coef.append(cj)
    origin_ok = all(cj.b < -c01 for cj in coef)
    # branch and bound on [0, Phi]^2 minus [0, r0]^2
    Ph = float(Phi)
    stack = [((0.0, Ph), (0.0, Ph))]
    boxes = 0
    worst = None
    while stack:
        (x0, x1), (y0, y1) = stack.pop()
        if x1 <= r0 and y1 <= r0:
            continue               # inside the origin box
        boxes += 1
        if boxes > max_boxes:
            return dict(ok=False, reason='box limit')
        env = {q0: iv.mpf([x0, x1]), q1: iv.mpf([y0, y1])}
        val = G(env) + iv.mpf(c01) * (env[q0] + env[q1])
        if val.b < 0:
            worst = val.b if worst is None else max(worst, val.b)
            continue
        if max(x1 - x0, y1 - y0) < 1e-7:
            return dict(ok=False, reason=f'stuck at {x0},{y0}')
        if x1 - x0 >= y1 - y0:
            m = (x0 + x1) / 2
            stack += [((x0, m), (y0, y1)), ((m, x1), (y0, y1))]
        else:
            m = (y0 + y1) / 2
            stack += [((x0, x1), (y0, m)), ((x0, x1), (m, y1))]
    return dict(ok=origin_ok, origin_coef=[float(c.b) for c in coef], boxes=boxes, worst_rest=float(worst))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--params', default='1/10,3/25,3/50;1/20,7/100,3/100;1/10,1/10,2/25')
    ap.add_argument('--c', default='1/1000', help='c01 to prove for the (p0, p1) part')
    ap.add_argument('--r0', type=float, default=0.01)
    ap.add_argument('--out')
    a = ap.parse_args()
    t0 = time.time()
    out = []
    for trip in a.params.split(';'):
        Phi, dl, tv = [sp.Rational(x) for x in trip.split(',')]
        c01 = float(sp.Rational(a.c))
        # c3 = tau sin(Phi)/Phi - Phi/2 (rigorous)
        PhiI = iv.mpf(int(Phi.p)) / int(Phi.q)
        c3 = (iv.mpf(int(tv.p)) / int(tv.q)) * iv.sin(PhiI) / PhiI - PhiI / 2
        rows = []
        for case in ('S1', 'S0'):
            for orth in ORTHANTS:
                res = check(Phi, iv.mpf(int(dl.p)) / int(dl.q), tv, case, orth, c01, a.r0)
                rows.append(dict(case=case, orthant=list(orth), **res))
        ok = all(rw['ok'] for rw in rows) and c3.a > 0
        out.append(dict(Phi=str(Phi), delta=str(dl), tau=str(tv), c3_lower=float(c3.a), c01=a.c, ok=ok, rows=rows))
        print(json.dumps(out[-1]))
    res = dict(results=out, seconds=round(time.time() - t0, 1), status='verified' if all(o['ok'] for o in out) else 'failed')
    if a.out:
        open(a.out, 'w').write(json.dumps(res, indent=1) + '\n')
    print(res['status'], res['seconds'])


if __name__ == '__main__':
    main()
