"""Wall witnesses, general form (edge or corner contact).  Obstacle k, a side W of T with inward unit normal n_W,
and an exact direction u with u.n_W > 0.  Witness p = w + (1 - EPS) u for a point w on W.
Claim: for every admissible pose of square k in its box, p is in the open square.
Proof: let E1 be the edge of the square facing W along u, q1 the point of the line p - lam u on E1's line.
  (a) interval: p is strictly on the inner side of E1 and strictly inside the two lateral edges, and the opposite
      edge E2 is crossed: lam1 = (p - E1).n1 / (u.n1) > 0 with n1 the inward normal of E1;
  (b) interval: q1 = p - lam1 u lies on the segment E1 (lateral coordinate in [-1/2, 1/2]);
  (c) analytic: q1 is a point of the closed square, hence in T (admissible pose), so (q1 - w).n_W >= 0, i.e.
      lam1 <= (1 - EPS) (u.n_W)/(u.n_W) = 1 - EPS; the chord from q1 along u has length 1/(u.n1) >= 1, so the far
      edge is at parameter lam1 - 1/(u.n1) <= -EPS < 0 behind... i.e. p lies strictly between E1 and E2.
So (a)+(b) over the pose box (no admissibility needed) prove the claim.
Usage: python wall_witness2.py CASE D DTH out.json [EPS STEP]"""
import json, math, sys
from fractions import Fraction as F
from mpmath import iv
sys.path.insert(0, "checker")
from q3 import Q3
S3 = Q3(0, 1); H = F(1, 2)
def q3s(z): return f"{z.a}" if z.b == 0 else f"{z.a}{'+' if z.b > 0 else '-'}{abs(z.b)}*sqrt3"
d = json.load(open("certificates/n6/n6_packing.json")); LQ = Q3.parse(d["L"])
SQ = [[(Q3.parse(x), Q3.parse(y)) for x, y in s] for s in d["squares"]]
r3 = iv.sqrt(3)
SIDES = {"base": ((Q3(0), Q3(0)), (Q3(0), Q3(1)), (Q3(1), Q3(0))),
         "left": ((Q3(0), Q3(0)), (S3 / 2, Q3(F(-1, 2))), (Q3(H), S3 / 2)),
         "right": ((LQ, Q3(0)), (-S3 / 2, Q3(F(-1, 2))), (Q3(F(-1, 2)), S3 / 2))}
def ivq(z): return iv.mpf(z.a.numerator) / z.a.denominator + iv.mpf(z.b.numerator) / z.b.denominator * r3
def dist(side, p):
    o, n, _ = SIDES[side]; return (p[0] - o[0]) * n[0] + (p[1] - o[1]) * n[1]
SG = [(-.5, -.5), (.5, -.5), (.5, .5), (-.5, .5)]
def pose0(k):
    V = SQ[k]; cx = sum((v[0] for v in V), Q3(0)) * F(1, 4); cy = sum((v[1] for v in V), Q3(0)) * F(1, 4)
    return cx, cy, math.atan2(float(V[1][1] - V[0][1]), float(V[1][0] - V[0][0]))
def prove(k, u, p, D, DTH):
    cx, cy, th = pose0(k)
    ux, uy = ivq(u[0]), ivq(u[1]); px, py = ivq(p[0]), ivq(p[1])
    # local edge normals in the square frame: +-e, +-f; E1 = the edge whose inward normal has the largest u-component
    th0 = th
    cands = [(1, 0), (-1, 0), (0, 1), (0, -1)]       # inward normal of edge = -outward; outward (a,b) in frame
    def frame_vec(a, b, t): return (a * math.cos(t) - b * math.sin(t), a * math.sin(t) + b * math.cos(t))
    # inward normal n1 of E1 (pointing into the square) should align with u
    best = max(cands, key=lambda ab: frame_vec(ab[0], ab[1], th0)[0] * float(u[0]) + frame_vec(ab[0], ab[1], th0)[1] * float(u[1]))
    a1, b1 = best                                     # n1 = R(t)(a1, b1); E1 is at offset -1/2 along n1 from the centre
    la, lb = -b1, a1                                  # lateral direction
    def ok(X, Y, T, depth):
        c, s = iv.cos(T), iv.sin(T)
        n1 = (c * a1 - s * b1, s * a1 + c * b1); lat = (c * la - s * lb, s * la + c * lb)
        rel = (px - X, py - Y)
        dn = rel[0] * n1[0] + rel[1] * n1[1]          # coordinate of p along n1 (E1 at -1/2, E2 at +1/2)
        dl = rel[0] * lat[0] + rel[1] * lat[1]
        un = ux * n1[0] + uy * n1[1]; ul = ux * lat[0] + uy * lat[1]
        lam1 = (dn + iv.mpf(0.5)) / un                # distance back along u to E1's line
        ql = dl - lam1 * ul                           # lateral coordinate of q1
        # dn < 1/2 (p before the far edge) is the analytic step (c); only the near side is checked here
        if (dn.a > -0.5 and abs(dl).b < 0.5 and un.a > 0 and abs(ql).b <= 0.5):
            return True
        if depth >= 12: return False
        wid = [X.delta, Y.delta, T.delta]; j = wid.index(max(wid)); bb = [X, Y, T]; m = (bb[j].a + bb[j].b) / 2
        lo = list(bb); hi = list(bb); lo[j] = iv.mpf([bb[j].a, m]); hi[j] = iv.mpf([m, bb[j].b])
        return ok(*lo, depth + 1) and ok(*hi, depth + 1)
    return ok(ivq(cx) + iv.mpf([-D, D]), ivq(cy) + iv.mpf([-D, D]), iv.mpf(th) + iv.mpf([-DTH, DTH]), 0)
def candidates(k, EPS, STEP):
    """for each side touched by square k (corner or edge), u in {inward normal, edge directions with u.n > 0}"""
    cx, cy, th = pose0(k); V = SQ[k]
    out = []
    for side, (o, n, e) in SIDES.items():
        if not any(dist(side, c) == Q3(0) for c in V): continue
        us = [n]
        for ab in ((1, 0), (0, 1), (-1, 0), (0, -1)):
            deg = round(math.degrees(th)) % 360
            tr = {0: (Q3(1), Q3(0)), 30: (S3 / 2, Q3(H)), 60: (Q3(H), S3 / 2), 90: (Q3(0), Q3(1)), 120: (Q3(-H), S3 / 2),
                  150: (-S3 / 2, Q3(H)), 180: (Q3(-1), Q3(0)), 210: (-S3 / 2, Q3(-H)), 240: (Q3(-H), -S3 / 2),
                  270: (Q3(0), Q3(-1)), 300: (Q3(H), -S3 / 2), 330: (S3 / 2, Q3(-H))}[deg]
            v = (tr[0] * ab[0] - tr[1] * ab[1], tr[1] * ab[0] + tr[0] * ab[1])
            if float(v[0] * n[0] + v[1] * n[1]) > 0.3 and all(v != w for w in us): us.append(v)
        # wall points: project the square's corners on the side, scan between
        ts = [float((c[0] - o[0]) * e[0] + (c[1] - o[1]) * e[1]) for c in V]
        for u in us:
            un = u[0] * n[0] + u[1] * n[1]                       # p = w + (1-EPS) u / (u.n) so that d_W(p) = 1 - EPS... no:
            # keep |p - w| = (1 - EPS) along u (chord length >= 1 along u)
            lo, hi = min(ts) - 1, max(ts) + 1
            t = F(math.floor(lo / float(STEP))) * STEP
            while t <= hi:
                w = (o[0] + e[0] * Q3(t), o[1] + e[1] * Q3(t))
                p = (w[0] + u[0] * Q3(1 - EPS), w[1] + u[1] * Q3(1 - EPS))
                out.append((side, u, p)); t += STEP
    return out
if __name__ == "__main__":
    case, D, DTH, outp = sys.argv[1], float(F(sys.argv[2])), float(F(sys.argv[3])), sys.argv[4]
    EPS = F(sys.argv[5]) if len(sys.argv) > 5 else F(3, 10000); STEP = F(sys.argv[6]) if len(sys.argv) > 6 else F(1, 100)
    obs = [int(t) for t in case.split(":")[0].split(",")]
    res = []
    for k in obs:
        for side, u, p in candidates(k, EPS, STEP):
            if prove(k, u, p, D, DTH):
                res.append({"x": q3s(p[0]), "y": q3s(p[1]), "obstacle": k, "side": side, "u": [q3s(u[0]), q3s(u[1])]})
    json.dump({"case": case, "D": sys.argv[2], "DTH": sys.argv[3], "EPS": str(EPS), "points": res}, open(outp, "w"), indent=1)
    from collections import Counter
    print(case, len(res), "proved", Counter((r["obstacle"], r["side"], tuple(r["u"])) for r in res))
