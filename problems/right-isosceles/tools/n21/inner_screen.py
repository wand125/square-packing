"""Float screen of degenerate interior poses at the special angles theta = atan(b/a), 0 < b <= a, a^2 + b^2 <= R^2:
centres where one point lies on a u-edge and another on a v-edge; lists admissible ones with >= 3 points on edges and
weight strictly inside < need.  Usage: OMP_NUM_THREADS=1 python3 n21/inner_screen.py cert.json [R=8] [need=1] [out.json]"""
import json, sys, math
from fractions import Fraction as F
import numpy as np
c = json.load(open(sys.argv[1])); R = int(sys.argv[2]) if len(sys.argv) > 2 else 8
need = float(sys.argv[3]) if len(sys.argv) > 3 else 1.0
L = float(F(c['L']))
P = np.array([(float(F(p['x'])), float(F(p['y']))) for p in c['points']]); W = np.array([float(F(p['w'])) for p in c['points']])
angs = sorted({math.atan2(b, a) for a in range(1, R + 1) for b in range(1, a + 1) if a * a + b * b <= R * R})
dist = np.hypot(P[:, None, 0] - P[None, :, 0], P[:, None, 1] - P[None, :, 1])
I, J = np.nonzero((dist < math.sqrt(2) + 1e-9) & ~np.eye(len(P), dtype=bool))
CORN = ((-.5, -.5), (.5, -.5), (.5, .5), (-.5, .5))
out = {}
for th in angs:
    ca, sa = math.cos(th), math.sin(th)
    pu = ca * P[:, 0] + sa * P[:, 1]; pv = -sa * P[:, 0] + ca * P[:, 1]
    for s1 in (-.5, .5):
        for s2 in (-.5, .5):
            cu, cv = pu[I] - s1, pv[J] - s2
            cx, cy = ca * cu - sa * cv, sa * cu + ca * cv
            ok = np.ones(len(cx), bool)
            for a, b in CORN:
                x = cx + ca * a - sa * b; y = cy + sa * a + ca * b
                ok &= (x >= -1e-9) & (y >= -1e-9) & (x + y <= L + 1e-9)
            idx = np.nonzero(ok)[0]
            for k in range(0, len(idx), 2000):
                sl = idx[k:k + 2000]
                m = np.maximum(np.abs(pu[None, :] - cu[sl, None]), np.abs(pv[None, :] - cv[sl, None]))
                ne = (np.abs(m - .5) < 1e-7).sum(1); inn = (m < .5 - 1e-7) @ W
                for t in np.nonzero((ne >= 3) & (inn < need - 1e-9))[0]:
                    q = sl[t]; key = (round(cx[q], 7), round(cy[q], 7), round(th, 9))
                    out[key] = (float(inn[t]), int(ne[t]))
bad = sorted(out.items(), key=lambda kv: kv[1][0])
print(f"{sys.argv[1]}: angles {len(angs)}, interior vertices with >= 3 edge points and inside < {need}: {len(bad)}")
for (cx, cy, th), (inn, ne) in bad[:20]:
    print(f"  inside {inn:.4f} edges {ne}  c=({cx}, {cy}) th={math.degrees(th):.4f}")
if len(sys.argv) > 4:
    json.dump([[cx, cy, th, v[0]] for (cx, cy, th), v in bad], open(sys.argv[4], 'w'))
