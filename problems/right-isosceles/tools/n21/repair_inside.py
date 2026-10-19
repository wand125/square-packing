"""Monotone repair at listed degenerate poses: make the weight strictly inside the square >= need at each pose
[cx, cy, theta] of the given lists (from wall_screen.py / inner_screen.py), adding weight only, the same on D1 orbits,
by a small LP minimising the added weight.  Usage: python3 n21/repair_inside.py cert.json out.json need den list.json..."""
import json, sys, math
from fractions import Fraction as F
import numpy as np
from scipy.optimize import linprog
c = json.load(open(sys.argv[1])); need = float(sys.argv[3]); den = int(sys.argv[4])
poses = [p[:3] for f in sys.argv[5:] for p in json.load(open(f))]
P = np.array([(float(F(p['x'])), float(F(p['y']))) for p in c['points']]); W = np.array([float(F(p['w'])) for p in c['points']])
key = {(p['x'], p['y']): i for i, p in enumerate(c['points'])}
mir = np.array([key[(p['y'], p['x'])] for p in c['points']])
orb = np.minimum(np.arange(len(P)), mir); ou, oinv = np.unique(orb, return_inverse=True)
A, b = [], []
for cx, cy, th in poses:
    ca, sa = math.cos(th), math.sin(th); dx, dy = P[:, 0] - cx, P[:, 1] - cy
    inn = np.maximum(np.abs(ca * dx + sa * dy), np.abs(-sa * dx + ca * dy)) < .5 - 1e-7
    d = need + 1e-6 - W[inn].sum()
    if d <= 0: continue
    row = np.zeros(len(ou)); np.add.at(row, oinv[inn], 1.0); A.append(row); b.append(d)
print(f"poses {len(poses)}, rows below need {len(A)}")
if A:
    res = linprog(np.bincount(oinv).astype(float), A_ub=-np.array(A), b_ub=-np.array(b), bounds=(0, None), method='highs')
    assert res.status == 0, res.message
    print(f"added weight {res.fun:.6f} on {int((res.x > 1e-12).sum())} orbits")
    for k, p in enumerate(c['points']):
        a = res.x[oinv[k]]
        if a > 1e-12: p['w'] = str(F(p['w']) + F(math.ceil(a * den + 1e-6), den))
tot = sum(F(p['w']) for p in c['points']); print(f"total {float(tot):.6f}")
json.dump(c, open(sys.argv[2], 'w'), indent=1)
