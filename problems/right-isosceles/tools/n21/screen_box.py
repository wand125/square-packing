"""Float screen of the degenerate poses at theta = 0 on a 1/G grid of centres (crossings) and on slabs: for each quarter
box (signs of dx, dy, theta >= 0) count what the checker can prove (the rule of lp_repair.box_row: interior points,
edge points that stay inside on the quarter box, chord pairs of the certificate with one end on each opposite edge,
counted with min weight, no point twice).  Prints the quarter poses with count < 1.
Usage: python3 n21/screen_box.py cert.json [G=8] [slab_step=64]"""
import json, sys, os
from fractions import Fraction as F
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import lp_points as LPP
c = json.load(open(sys.argv[1])); G = int(sys.argv[2]) if len(sys.argv) > 2 else 8
SS = int(sys.argv[3]) if len(sys.argv) > 3 else 64
L = float(F(c['L'])) if '/' in c['L'] or c['L'].isdigit() else float(eval(c['L']))
P = np.array([(float(F(p['x'])), float(F(p['y']))) for p in c['points']]); W = np.array([float(F(p['w'])) for p in c['points']])
pairs = [tuple(p) for p in c.get('pairs', [])]
E = 1e-9
def count(Cx, Cy, sx, sy):
    x0, y0 = Cx - .5, Cy - .5
    m = (P[:, 0] >= x0 - E) & (P[:, 0] <= x0 + 1 + E) & (P[:, 1] >= y0 - E) & (P[:, 1] <= y0 + 1 + E)
    rob = set()
    for i in np.nonzero(m)[0]:
        x, y = P[i]
        onL, onR, onB, onT = abs(x - x0) < E, abs(x - x0 - 1) < E, abs(y - y0) < E, abs(y - y0 - 1) < E
        if not (onL or onR or onB or onT):
            rob.add(i); continue
        ok = True
        if onL: ok &= (sx < 0 and y > Cy + E)
        if onR: ok &= (sx > 0 and y < Cy - E)
        if onB: ok &= (sy < 0 and x < Cx - E)
        if onT: ok &= (sy > 0 and x > Cx + E)
        if ok: rob.add(i)
    tot = W[list(rob)].sum() if rob else 0.0
    used = set(rob)
    for i, j in pairs:
        if i in used or j in used: continue
        (xi, yi), (xj, yj) = P[i], P[j]
        if abs(yi - yj) < E and abs(abs(xi - xj) - 1) < E and abs(min(xi, xj) - x0) < E and y0 + E < yi < y0 + 1 - E:
            pass
        elif abs(xi - xj) < E and abs(abs(yi - yj) - 1) < E and abs(min(yi, yj) - y0) < E and x0 + E < xi < x0 + 1 - E:
            pass
        else:
            continue
        tot += min(W[i], W[j]); used |= {i, j}
    return tot
adm = lambda cx, cy: LPP.admissible(L, cx, cy, 0.0, tol=1e-9)
bad = []
cent = set()
for a in range(int(L * G) + 1):
    for b in range(int(L * G) + 1):
        cent.add((a / G, b / G))                  # crossings
for a in range(int(L * G) + 1):
    for t in range(int(L * SS) + 1):
        cent.add((a / G, t / SS)); cent.add((t / SS, a / G))   # slabs
for cx, cy in sorted(cent):
    if not adm(cx, cy): continue
    if cx < .5 + 1e-6 or cy < .5 + 1e-6 or cx + cy > L - 1 - 1e-6: continue   # touches a side: --slices handles it
    for sx in (-1, 1):
        for sy in (-1, 1):
            if not adm(cx + sx * 1e-6, cy + sy * 1e-6): continue
            v = count(cx, cy, sx, sy)
            if v < 1 - 1e-9: bad.append((round(v, 4), cx, cy, sx, sy))
bad.sort()
print(f"{sys.argv[1]}: quarter poses with provable count < 1: {len(bad)}")
for r in bad[:int(os.environ.get("SHOW", 15))]: print(' ', r)
