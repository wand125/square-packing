"""Exact random soundness probe: random rational admissible poses; exact capture of the certificate."""
import json, sys, random, os
from fractions import Fraction as F
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'checker'))
from q3 import Q3
c = json.load(open(sys.argv[1])); N = int(sys.argv[2])
L = Q3.parse(c["L"]); s3 = Q3(0, 1)
P = [(Q3.parse(p["x"]), Q3.parse(p["y"]), F(p["w"])) for p in c["points"]]
rng = random.Random(7); got = 0; tries = 0; worst = None
while got < N:
    tries += 1
    u = F(rng.randrange(0, 10**6), 10**6)
    co, si = (1 - u * u) / (1 + u * u), 2 * u / (1 + u * u)
    cx = F(rng.randrange(0, 5 * 10**5), 10**5); cy = F(rng.randrange(0, 4 * 10**5), 10**5)
    ok = True
    for sx in (F(-1, 2), F(1, 2)):
        for sy in (F(-1, 2), F(1, 2)):
            x = Q3(cx + co * sx - si * sy); y = Q3(cy + si * sx + co * sy)
            if y.sign() < 0 or (s3 * x - y).sign() < 0 or (s3 * (L - x) - y).sign() < 0:
                ok = False
    if not ok:
        continue
    got += 1
    cap = F(0)
    for px, py, w in P:
        a = (px - cx) * co + (py - cy) * si; b = -(px - cx) * si + (py - cy) * co
        if (Q3(F(1, 2)) - a).sign() >= 0 and (Q3(F(1, 2)) + a).sign() >= 0 and (Q3(F(1, 2)) - b).sign() >= 0 and (Q3(F(1, 2)) + b).sign() >= 0:
            cap += w
    if worst is None or cap < worst[0]:
        worst = (cap, (cx, cy, u))
print(f"{got} admissible poses of {tries}; min exact capture {worst[0]} at {worst[1]}")
