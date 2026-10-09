"""Exact random probe: random rational admissible poses (rational centre, rational u = tan(theta/2)),
exact capture with Q(sqrt2) points.  Independent of the checker's box machinery (sanity only).
Usage: python3 probe_exact.py cert.json [--trials 20000] [--seed 1]"""
import argparse, json, os, random, sys
from fractions import Fraction as F
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "checker"))
from q2 import Q2
ap = argparse.ArgumentParser(); ap.add_argument("cert"); ap.add_argument("--trials", type=int, default=20000); ap.add_argument("--seed", type=int, default=1)
a = ap.parse_args(); c = json.load(open(a.cert)); rnd = random.Random(a.seed)
L = Q2.parse(c["L"]); Lf = float(L)
pts = [(Q2.parse(p["x"]), Q2.parse(p["y"]), F(p["w"])) for p in c["points"]]
H = F(1, 2); best = None; tested = 0; D = 1000
while tested < a.trials:
    u = F(rnd.randint(0, D), D); co = (1 - u*u) / (1 + u*u); si = 2*u / (1 + u*u)
    cx = F(rnd.randint(0, int(Lf*D)), D); cy = F(rnd.randint(0, int(Lf*D)), D)
    ok = True
    for sx in (-H, H):
        for sy in (-H, H):
            x = cx + co*sx - si*sy; y = cy + si*sx + co*sy
            if x < 0 or y < 0 or not (Q2(x + y) <= L): ok = False; break
        if not ok: break
    if not ok: continue
    tested += 1
    cap = F(0)
    for px, py, w in pts:
        dx, dy = px - cx, py - cy
        if abs(float(dx*co + dy*si)) <= 0.5 + 1e-6 and abs(float(-dx*si + dy*co)) <= 0.5 + 1e-6:
            t1 = dx*co + dy*si; t2 = -dx*si + dy*co
            if t1 <= H and -t1 <= H and t2 <= H and -t2 <= H: cap += w
    if best is None or cap < best: best = cap
print(json.dumps({"cert": a.cert, "trials": tested, "min_exact_capture": str(best)}))
