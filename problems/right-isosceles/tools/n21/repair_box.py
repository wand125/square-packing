"""Monotone repair of the degenerate poses at theta = 0: for every quarter pose of screen_box.py whose provable count is
below `need`, add weight to points that are provably inside there (interior or robust edge points), by a small LP that
minimises the added weight (D1 orbits get the same addition).  Weights only grow, so every other capture stays.
Usage: python3 n21/repair_box.py cert.json out.json [need=1] [G=8] [slab_step=64] [den=2520]"""
import json, sys, os, math
from fractions import Fraction as F
import numpy as np
from scipy.optimize import linprog
here = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.dirname(here))
import lp_points as LPP
src, dst = sys.argv[1], sys.argv[2]
need = float(sys.argv[3]) if len(sys.argv) > 3 else 1.0
G = int(sys.argv[4]) if len(sys.argv) > 4 else 8; SS = int(sys.argv[5]) if len(sys.argv) > 5 else 64
den = int(sys.argv[6]) if len(sys.argv) > 6 else 2520
c = json.load(open(src)); L = float(F(c['L']))
P = np.array([(float(F(p['x'])), float(F(p['y']))) for p in c['points']]); W = np.array([float(F(p['w'])) for p in c['points']])
key = {(p['x'], p['y']): i for i, p in enumerate(c['points'])}
mir = np.array([key[(p['y'], p['x'])] for p in c['points']])
orb = np.minimum(np.arange(len(P)), mir); ou, oinv = np.unique(orb, return_inverse=True)
pairs = [tuple(p) for p in c.get('pairs', [])]
E = 1e-9
def row(Cx, Cy, sx, sy):
    x0, y0 = Cx - .5, Cy - .5
    m = (P[:, 0] >= x0 - E) & (P[:, 0] <= x0 + 1 + E) & (P[:, 1] >= y0 - E) & (P[:, 1] <= y0 + 1 + E)
    rob = []
    for i in np.nonzero(m)[0]:
        x, y = P[i]
        onL, onR, onB, onT = abs(x - x0) < E, abs(x - x0 - 1) < E, abs(y - y0) < E, abs(y - y0 - 1) < E
        ok = True
        if onL: ok &= (sx < 0 and y > Cy + E)
        if onR: ok &= (sx > 0 and y < Cy - E)
        if onB: ok &= (sy < 0 and x < Cx - E)
        if onT: ok &= (sy > 0 and x > Cx + E)
        if ok: rob.append(i)
    tot = W[rob].sum() if rob else 0.0
    used = set(rob)
    for i, j in pairs:
        if i in used or j in used: continue
        (xi, yi), (xj, yj) = P[i], P[j]
        h = abs(yi - yj) < E and abs(abs(xi - xj) - 1) < E and abs(min(xi, xj) - x0) < E and y0 + E < yi < y0 + 1 - E
        v = abs(xi - xj) < E and abs(abs(yi - yj) - 1) < E and abs(min(yi, yj) - y0) < E and x0 + E < xi < x0 + 1 - E
        if h or v:
            tot += min(W[i], W[j]); used |= {i, j}
    return tot, rob
adm = lambda cx, cy: LPP.admissible(L, cx, cy, 0.0, tol=1e-9)
cent = set()
for a in range(int(L * G) + 1):
    for b in range(int(L * G) + 1): cent.add((a / G, b / G))
    for t in range(int(L * SS) + 1): cent.add((a / G, t / SS)); cent.add((t / SS, a / G))
rows = []
for cx, cy in sorted(cent):
    if not adm(cx, cy) or cx < .5 + 1e-6 or cy < .5 + 1e-6 or cx + cy > L - 1 - 1e-6: continue
    for sx in (-1, 1):
        for sy in (-1, 1):
            if not adm(cx + sx * 1e-6, cy + sy * 1e-6): continue
            tot, rob = row(cx, cy, sx, sy)
            if tot < need + 1e-6: rows.append((need + 1e-6 - tot, rob, (cx, cy, sx, sy)))
print(f"rows below need {need}: {len(rows)}")
if rows:
    no = len(ou); mult = np.bincount(oinv, minlength=no).astype(float)
    A = np.zeros((len(rows), no)); b = np.zeros(len(rows))
    for r, (d, rob, _) in enumerate(rows):
        for i in rob: A[r, oinv[i]] += 1.0
        b[r] = d
    res = linprog(mult, A_ub=-A, b_ub=-b, bounds=(0, None), method='highs')
    assert res.status == 0, res.message
    add = res.x
    print(f"added weight {res.fun:.6f} on {int((add > 1e-12).sum())} orbits")
    for k, p in enumerate(c['points']):
        a = add[oinv[k]]
        if a > 1e-12:
            p['w'] = str(F(p['w']) + F(math.ceil(a * den + 1e-6), den))
tot = sum(F(p['w']) for p in c['points'])
print(f"total {tot} = {float(tot):.6f}")
json.dump(c, open(dst, 'w'), indent=1)
