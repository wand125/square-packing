"""Lemma hypotheses on a localization leaf: squares 0, 1, 3 of the stored pinwheel with centre within D (max norm)
and angle within DTH of their pinwheel poses.  Checks, in mpmath interval arithmetic with subdivision:
  * corner displacement |a_i|, |b_i| <= DELTA for the bottom-left corners of squares 0, 1, tilts <= PHI;
  * t = (P - D3)·e3 in [TAU, 1 - TAU], where P = top-right corner of square 1 and D3 = lower inner corner of
    square 3 (centre-parametrised: D3 = c3 + R(theta3)(-1/2, -1/2) in square 3's own frame, see below).
Usage: python validity_box.py D DTH PHI DELTA TAU"""
import sys, itertools
from mpmath import iv, mp
D, DTH, PHI, DELTA, TAU = (iv.mpf(x) for x in sys.argv[1:6])
r3 = iv.sqrt(3)
I = lambda c, r: iv.mpf([(c - r).a, (c + r).b])
# pinwheel: square 1 centre (3/2 + 1/sqrt3, 1/2), angle 0; square 3 centre and frame
c1 = (iv.mpf(3) / 2 + 1 / r3, iv.mpf(1) / 2)
# square 3 corners (stored): V0=(3/2+7/6r3, 1/2+r3/2) [A, outer lower], V1=(1+7/6r3, 1/2+r3) [B, outer upper],
# V2=(1+2/3r3, r3) [C, inner upper], V3=(3/2+2/3r3, r3/2) [D, inner lower]
A = (iv.mpf(3) / 2 + 7 * r3 / 6, iv.mpf(1) / 2 + r3 / 2); C = (1 + 2 * r3 / 3, r3)
c3 = ((A[0] + C[0]) / 2, (A[1] + C[1]) / 2)
e3 = (-iv.mpf(1) / 2, r3 / 2)          # D -> C direction (up the right side)
f3 = (-r3 / 2, -iv.mpf(1) / 2)          # A -> D direction (inward)
# D = c3 - e3/2 + f3/2 ; offsets in the (e3, f3) frame rotated by theta3
def rot(v, t):
    c, s = iv.cos(t), iv.sin(t); return (v[0] * c - v[1] * s, v[0] * s + v[1] * c)
def t_enclosure(dx1, dy1, t1, dx3, dy3, t3):
    P = (c1[0] + dx1 + rot((iv.mpf(1) / 2, iv.mpf(1) / 2), t1)[0], c1[1] + dy1 + rot((iv.mpf(1) / 2, iv.mpf(1) / 2), t1)[1])
    E = rot(e3, t3); Fv = rot(f3, t3)
    Dp = (c3[0] + dx3 - E[0] / 2 + Fv[0] / 2, c3[1] + dy3 - E[1] / 2 + Fv[1] / 2)
    return (P[0] - Dp[0]) * E[0] + (P[1] - Dp[1]) * E[1]
N = int(sys.argv[6]) if len(sys.argv) > 6 else 3
D3 = iv.mpf(sys.argv[7]) if len(sys.argv) > 7 else D; DTH3 = iv.mpf(sys.argv[8]) if len(sys.argv) > 8 else DTH   # square 3's box
lo, hi = None, None
def parts(r):
    w = 2 * r / N
    return [iv.mpf([(-r + k * w).a, (-r + (k + 1) * w).b]) for k in range(N)]
PD, PT = parts(D), parts(DTH); PD3, PT3 = parts(D3), parts(DTH3)
for combo in itertools.product(PD, PD, PT, PD3, PD3, PT3):
    t = t_enclosure(*combo)
    lo = t.a if lo is None else min(lo, t.a); hi = t.b if hi is None else max(hi, t.b)
corner = D + DTH * iv.sqrt(2) / 2   # |corner - corner*| <= |dc|_inf + |R(dt)o - o|_inf, o = (-1/2,-1/2), |o| = 1/sqrt2
ok_t = lo >= TAU.b and hi <= 1 - TAU.b
ok_c = corner.b <= DELTA.a and max(DTH.b, DTH3.b) <= PHI.a
print(f"sq0,1: D={sys.argv[1]} DTH={sys.argv[2]}; sq3: D={float(D3.b):.4f} DTH={float(DTH3.b):.4f}: t in [{float(lo):.4f}, {float(hi):.4f}] (need [{sys.argv[5]}, 1-{sys.argv[5]}]): {ok_t}; "
      f"corner shift <= {float(corner.b):.4f} (<= {sys.argv[4]}): {ok_c}  => {'HYPOTHESES HOLD' if ok_t and ok_c else 'FAIL'}")
