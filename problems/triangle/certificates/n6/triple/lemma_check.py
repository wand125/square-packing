"""Rigorous (mpmath interval) check of the triple lemma's main inequality.
For each separation case (S0, S1) and each sign orthant of (phi0, phi1, phi3), with the orthant's weights
(alpha, beta0, beta1), show  S <= -c * (|phi0|+|phi1|+|phi3|)  where
  S = F(phi) + p-terms,  F from derive2.py,  p-terms bounded with |a_i| <= dp, 0 <= b_i <= dp.
Bound: F(phi) <= grad.phi + 1/2 sum_ij max|H_ij| |phi_i||phi_j|  (H over the box, F(0) = 0).
Usage: python lemma_check.py PHI DP TAU"""
import sys, itertools
from mpmath import iv, mpf
import sympy as sp
PHI, DP, TAU = (iv.mpf(x) for x in sys.argv[1:4])
TAUS = sys.argv[3]
p0, p1, p3, al, be0, be1, tau = sp.symbols('phi0 phi1 phi3 alpha beta0 beta1 tau', real=True)
u = sp.sqrt(3)
FS = {"S1": u*al*sp.sin(p0-p1)/2 + be0*sp.sin(p0)/2 + be1*sp.sin(p1)/2 - tau*sp.sin(p3) + u*sp.sin(p1)/2
            - sp.sin(p0+sp.pi/6) - sp.sqrt(2)*sp.sin(p1+sp.pi/4)/2 - sp.cos(p3) - u*sp.cos(p0-p1)/2 + u/2 + 2,
      "S0": u*al*sp.sin(p0-p1)/2 + be0*sp.sin(p0)/2 + be1*sp.sin(p1)/2 - tau*sp.sin(p3)
            - sp.sin(p0+sp.pi/6) + u*sp.cos(p0)/2 - sp.cos(p3) - sp.sqrt(2)*sp.cos(p1+sp.pi/12) + 2}
PV = {"S1": p1, "S0": p0}           # the tilt appearing in the p-terms
a_pp = 1 - 1/(2*u)
W = {(1, 1): (a_pp, 0, 0), (-1, -1): (a_pp, 1, 1), (1, -1): (0, 0, 1), (-1, 1): (1, 1, 0)}
X = (p0, p1, p3)
worst = None
for case, F in FS.items():
    for s0, s1, s3 in itertools.product((1, -1), repeat=3):
        a, b0_, b1_ = W[(s0, s1)]
        Fo = F.subs({al: a, be0: b0_, be1: b1_, tau: s3 * sp.Symbol('T')})  # -T|sin phi3|
        Fo = Fo.subs(sp.Symbol('T'), sp.Rational(TAUS))
        assert sp.simplify(Fo.subs({p0: 0, p1: 0, p3: 0})) == 0
        g = [sp.diff(Fo, x).subs({p0: 0, p1: 0, p3: 0}) for x in X]
        box = {p0: iv.mpf([0, PHI.b]) * s0, p1: iv.mpf([0, PHI.b]) * s1, p3: iv.mpf([0, PHI.b]) * s3}
        MOD = [{'sin': iv.sin, 'cos': iv.cos, 'sqrt': iv.sqrt, 'pi': iv.pi}]
        Hm = [[None] * 3 for _ in range(3)]
        for i in range(3):
            for j in range(3):
                h = sp.lambdify(X, sp.diff(Fo, X[i], X[j]), modules=[{'sin': iv.sin, 'cos': iv.cos, 'sqrt': iv.sqrt, 'pi': iv.pi}])
                val = iv.mpf(h(box[p0], box[p1], box[p3])) if sp.diff(Fo, X[i], X[j]) != 0 else iv.mpf(0)
                Hm[i][j] = iv.mpf(max(abs(val.a), abs(val.b)))
        coefs = []
        for i, x in enumerate(X):
            gi = iv.mpf(sp.lambdify((), g[i], modules=MOD)()) if g[i] != 0 else iv.mpf(0)
            c = gi * (s0, s1, s3)[i] + PHI / 2 * sum(Hm[i])
            if x == PV[case]:   # (sqrt3/2)(1-cos)|a0-a1| + (sqrt3/2)|sin||b1-b0|
                c += iv.sqrt(3) / 2 * (PHI / 2 * 2 * DP) + iv.sqrt(3) / 2 * DP
            coefs.append(c)
        m = max(c.b for c in coefs)
        print(case, (s0, s1, s3), " coef upper bounds:", [float(c.b) for c in coefs])
        worst = m if worst is None else max(worst, m)
print("worst coefficient:", float(worst), "=> PROVED" if worst < 0 else "=> FAILS")
