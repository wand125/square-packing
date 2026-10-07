# Rigorous check of the n=2 lemma on theta in [0, pi/12]:
#   g(theta) = 1/2 - (+/-)(V - G).e  >= 0  for the 3 vertices V of the admissible-centre triangle D_theta
#   and both square axes e1, e2 and both signs (12 functions).
# Exact values of g(0), g'(0) via sympy; interval arithmetic (mpmath.iv) for the rest:
#   on [0, d]:    g >= g(0) + g'(0) t - M t^2 / 2, with M an interval bound of |g''| on [0, d]
#   on [d, pi/12]: interval enclosure of g on a subdivision, lower end > 0.
import sympy as sp
from mpmath import iv, mp
mp.dps = 40; iv.dps = 40
th = sp.symbols('theta', real=True)
r3 = sp.sqrt(3); v = 2 + 2/r3; r = v/(2*r3)
c, s = sp.cos(th), sp.sin(th)
h0 = (c + s)/2
h1 = (sp.cos(sp.pi/6 - th) + sp.sin(sp.pi/6 - th))/2
h2 = (sp.cos(sp.pi/6 + th) + sp.sin(sp.pi/6 + th))/2
a0, a1, a2 = r - h0, r - h1, r - h2
V = {'V01': ((2*a1 + a0)/r3, -a0), 'V02': (-(2*a2 + a0)/r3, -a0), 'V12': ((a1 - a2)/r3, a1 + a2)}
E = {'e1': (c, s), 'e2': (-s, c)}
from sympy.printing.str import StrPrinter
class P(StrPrinter):
    def _print_Rational(self, e): return f"(iv.mpf({e.p})/iv.mpf({e.q}))"
    def _print_Integer(self, e): return f"iv.mpf({e.p})"
    def _print_Pi(self, e): return "iv.pi"
def ivfun(expr):
    code = P().doprint(expr)
    ns = {'iv': iv, 'sqrt': iv.sqrt, 'sin': iv.sin, 'cos': iv.cos}
    return lambda t: eval(code, dict(ns, theta=t))
D = sp.Rational(1, 100)          # local window [0, D] (radians)
N = 400                          # subdivision of [D, pi/12]
allok = True
for vn, (x, y) in V.items():
    for en, (ex, ey) in E.items():
        for sg in (1, -1):
            g = sp.Rational(1, 2) - sg*(x*ex + y*ey)
            g0 = sp.nsimplify(sp.simplify(g.subs(th, 0)))
            g1 = sp.simplify(sp.diff(g, th).subs(th, 0))
            f = ivfun(g)
            f2 = ivfun(sp.diff(g, th, 2))
            Dv = iv.mpf(1)/100
            M = abs(f2(iv.mpf([0, Dv])))
            M = iv.mpf(M.b)
            # local: g0 >= 0 exact; need g0 + g1 t - M t^2/2 >= 0 on [0, D]
            if g0 < 0:
                ok_loc = False
            elif g0 == 0:
                ok_loc = (ivfun(g1)(iv.mpf(0)) - M*Dv/2).a > 0   # g >= t*(g'(0) - M t/2) >= 0
            else:
                lo = ivfun(g0)(iv.mpf(0)) - abs(ivfun(g1)(iv.mpf(0)))*Dv - M*Dv*Dv/2
                ok_loc = lo.a > 0
            # global on [D, pi/12]
            pi12 = iv.pi/12
            mn = None; ok_glob = True
            for i in range(N):
                t = Dv + (pi12 - Dv)*iv.mpf([i, i + 1])/N
                val = f(t)
                mn = val.a if mn is None else min(mn, val.a)
                if not val.a > 0: ok_glob = False
            print(f"{vn} {en} {'+' if sg > 0 else '-'}: g(0)={g0} g'(0)={g1} (~{float(g1):.4f}) "
                  f"|g''|<={float(M.b):.3f} local={'ok' if ok_loc else 'FAIL'} "
                  f"min_enclosure[D,pi/12]={float(mn):.4e} global={'ok' if ok_glob else 'FAIL'}")
            allok &= ok_loc and ok_glob
print("ALL OK" if allok else "SOME FAIL")
