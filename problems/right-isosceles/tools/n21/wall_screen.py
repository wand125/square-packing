"""Float screen of degenerate wall poses: at the special angles theta = atan(b/a) (a^2 + b^2 <= R^2), centres where a
corner of the square touches a side of the triangle and a certificate point lies on an edge (the vertices of the
admissible region with the point lines).  Lists the admissible ones where >= 2 points lie on edges and the weight
strictly inside is < need (the checker then needs one fixed point set over a box around a pose where edge points flip).
Usage: OMP_NUM_THREADS=1 python3 n21/wall_screen.py cert.json [R=8] [need=1] [out.json]"""
import json, sys, math
from fractions import Fraction as F
import numpy as np
c = json.load(open(sys.argv[1])); R = int(sys.argv[2]) if len(sys.argv) > 2 else 8
need = float(sys.argv[3]) if len(sys.argv) > 3 else 1.0
L = float(F(c['L']))
P = np.array([(float(F(p['x'])), float(F(p['y']))) for p in c['points']]); W = np.array([float(F(p['w'])) for p in c['points']])
angs = sorted({math.atan2(b, a) for a in range(1, R + 1) for b in range(1, a + 1) if a * a + b * b <= R * R})
sides = [((-1.0, 0.0), 0.0), ((0.0, -1.0), 0.0), ((1 / math.sqrt(2), 1 / math.sqrt(2)), L / math.sqrt(2))]   # n.x <= b
CORN = ((-.5, -.5), (.5, -.5), (.5, .5), (-.5, .5))
out = {}
for th in angs:
    ca, sa = math.cos(th), math.sin(th)
    e_u, e_v = np.array([ca, sa]), np.array([-sa, ca])
    pu, pv = P @ e_u, P @ e_v
    for n, b in sides:
        n = np.array(n)
        # the corner that is extreme in direction n: h = max over corners of n.(R corner)
        hs = [n @ (a * e_u + bb * e_v) for a, bb in CORN]; h = max(hs)
        # wall line: n.c = b - h ; point line: e.(p - c) = s  ->  e.c = e.p - s, e = e_u or e_v, s = +-1/2
        for e, pe in ((e_u, pu), (e_v, pv)):
            M = np.array([n, e])
            if abs(np.linalg.det(M)) < 1e-9: continue
            Mi = np.linalg.inv(M)
            for s in (-.5, .5):
                rhs = np.stack([np.full(len(P), b - h), pe - s], 1)
                C = rhs @ Mi.T
                for cx, cy in C:
                    cu, cv = ca * cx + sa * cy, -sa * cx + ca * cy
                    ok = all((x >= -1e-9) and (y >= -1e-9) and (x + y <= L + 1e-9) for x, y in
                             ((cx + ca * a - sa * bb, cy + sa * a + ca * bb) for a, bb in CORN))
                    if not ok: continue
                    m = np.maximum(np.abs(pu - cu), np.abs(pv - cv))
                    edge = np.abs(m - .5) < 1e-7
                    if edge.sum() < 2: continue
                    inn = W[m < .5 - 1e-7].sum()
                    if inn < need - 1e-9:
                        k = (round(cx, 7), round(cy, 7), round(th, 9))
                        out[k] = (float(inn), int(edge.sum()), float(W[edge].sum()))
bad = sorted(out.items(), key=lambda kv: kv[1][0])
print(f"{sys.argv[1]}: angles {len(angs)}, wall vertices with >= 2 edge points and inside < {need}: {len(bad)}")
for (cx, cy, th), (inn, ne, we) in bad[:20]:
    print(f"  inside {inn:.4f} edges {ne} ({we:.3f})  c=({cx}, {cy}) th={math.degrees(th):.4f}")
if len(sys.argv) > 4:
    json.dump([[cx, cy, th, v[0]] for (cx, cy, th), v in bad], open(sys.argv[4], 'w'))
