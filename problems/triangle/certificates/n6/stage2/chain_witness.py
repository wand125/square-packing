"""Chain witnesses for obstacle square 1 against square 3 (triangle n=6, case 1,3:0).
Square 1 (pose box B1) and square 3 (pose box B3) are known to lie in their boxes, inside T_v, disjoint.
Step 1 of n6/triple/LEMMA.md: if the foot of P (top-right corner of square 1) on square 3's inner edge has
parameter t in (0,1) for every pose pair of B1 x B3 (checked by validity_box.py), then
     d_R(P) >= cos(phi3) >= c3 := cos(DTH3)       (d_R = distance to the right side of T_v).
So square 1 cannot move right beyond the line d_R = c3 with its corner P.  A witness p near square 1's left edge
lies in the open square 1 for every pose of B1 whose corner P satisfies d_R(P) >= c3.  We prove this by
interval branch-and-bound over B1: a sub-box is dropped if d_R(P) < c3 surely (no admissible pose there), and
accepted if p is surely in the open square.  (Bottom and top are handled by the box: b1 >= 0 is not needed.)
Usage: python chain_witness.py D1 DTH1 DTH3 out.json [EPS STEP]"""
import json, math, sys
from fractions import Fraction as F
from mpmath import iv
sys.path.insert(0, "checker")
from q3 import Q3
r3 = iv.sqrt(3); Lv = iv.mpf(2) + 4 * r3 / 3
def q3s(z): return f"{z.a}" if z.b == 0 else f"{z.a}{'+' if z.b > 0 else '-'}{abs(z.b)}*sqrt3"
def main():
    D1, DTH1, DTH3 = (float(F(a)) for a in sys.argv[1:4]); outp = sys.argv[4]
    EPS = F(sys.argv[5]) if len(sys.argv) > 5 else F(1, 200); STEP = F(sys.argv[6]) if len(sys.argv) > 6 else F(1, 50)
    c3 = iv.cos(iv.mpf(DTH3)).a                      # lower bound of cos(DTH3)
    cx0 = 1 + 1 / r3 + iv.mpf(0.5); cy0 = iv.mpf(0.5)
    # the largest x of square 1's left edge midpoint allowed by d_R(P) >= c3 (float guide for placing witnesses)
    # P = c + R(phi)(1/2, 1/2); with phi = 0: P = (cx + 1/2, cy + 1/2) and d_R(P) >= c3 gives cx <= L - (2c3 + cy + 1/2)/sqrt3 - 1/2
    pts = []
    for k in range(5, 46):
        y = F(k, 50)                                   # heights 0.1 .. 0.9
        # guide: left edge x <= xmax(y) ~ L - (2 c3 + cy + 1/2)/sqrt3 - 1 ; place p at that + EPS (inside)
        for dx in (F(0), F(1, 400), F(1, 200), F(1, 100), F(1, 50)):
            xg = float((Lv - (2 * c3 + 1) / r3 - 1).b) + float(EPS) + float(dx)
            xq = F(round(xg * 10**5), 10**5)
            p = (Q3(xq), Q3(y))
            if prove(p, D1, DTH1, c3, cx0, cy0):
                pts.append({"x": q3s(p[0]), "y": q3s(p[1]), "obstacle": 1, "rule": "chain d_R(P) >= cos(DTH3)"}); break
    json.dump({"D1": sys.argv[1], "DTH1": sys.argv[2], "DTH3": sys.argv[3], "EPS": str(EPS), "points": pts}, open(outp, "w"), indent=1)
    print(len(pts), "chain witnesses proved ->", outp, [(p["x"], p["y"]) for p in pts[:3]])
def ivq(z): return iv.mpf(z.a.numerator) / z.a.denominator + iv.mpf(z.b.numerator) / z.b.denominator * r3
def prove(p, D1, DTH1, c3, cx0, cy0):
    px, py = ivq(p[0]), ivq(p[1])
    def ok(X, Y, T, depth):
        c, s = iv.cos(T), iv.sin(T)
        Px = X + c * 0.5 - s * 0.5; Py = Y + s * 0.5 + c * 0.5
        dR = (r3 * (Lv - Px) - Py) / 2
        if dR.b < c3:                                  # surely infeasible (square 1 would cut into square 3)
            return True
        # also drop sub-boxes surely outside T (bottom corners below the base)
        for a, b in ((-.5, -.5), (.5, -.5)):
            if (Y + s * a + c * b).b < 0: return True
        u = (px - X) * c + (py - Y) * s; w = -(px - X) * s + (py - Y) * c
        if abs(u).b < 0.5 and abs(w).b < 0.5:
            return True
        if depth >= 26: return False
        wid = [X.delta, Y.delta, T.delta]; j = wid.index(max(wid)); bb = [X, Y, T]; m = (bb[j].a + bb[j].b) / 2
        lo = list(bb); hi = list(bb); lo[j] = iv.mpf([bb[j].a, m]); hi[j] = iv.mpf([m, bb[j].b])
        return ok(*lo, depth + 1) and ok(*hi, depth + 1)
    return ok(cx0 + iv.mpf([-D1, D1]), cy0 + iv.mpf([-D1, D1]), iv.mpf([-DTH1, DTH1]), 0)
main()
