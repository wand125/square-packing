"""Float probe: min capture of a certificate over random admissible poses (not a proof)."""
import json, math, sys, random
import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'checker'))
from q3 import Q3
c = json.load(open(sys.argv[1])); N = int(sys.argv[2]) if len(sys.argv) > 2 else 200000
L = float(Q3.parse(c["L"])); r3 = math.sqrt(3)
P = [(float(Q3.parse(p["x"])), float(Q3.parse(p["y"])), float(eval(p["w"].replace('/', '/1.0/') if False else str(float(__import__('fractions').Fraction(p["w"])))))) for p in c["points"]]
rng = random.Random(1); worst = (9, None); cnt = 0
while cnt < N:
    th = rng.uniform(0, math.pi / 2); cx = rng.uniform(0, L); cy = rng.uniform(0, L * r3 / 2)
    co, si = math.cos(th), math.sin(th)
    ok = True
    for sx in (-.5, .5):
        for sy in (-.5, .5):
            x = cx + co * sx - si * sy; y = cy + si * sx + co * sy
            if y < 0 or r3 * x - y < 0 or r3 * (L - x) - y < 0: ok = False
    if not ok: continue
    cnt += 1
    cap = sum(w for px, py, w in P if abs((px - cx) * co + (py - cy) * si) <= .5 + 1e-12 and abs(-(px - cx) * si + (py - cy) * co) <= .5 + 1e-12)
    if cap < worst[0]: worst = (cap, (cx, cy, math.degrees(th)))
print("min capture", worst)
