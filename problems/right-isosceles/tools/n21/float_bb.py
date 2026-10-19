"""Float branch-and-bound over pose space for a squintan certificate (right isosceles container T_L, angles in
[0, pi/4] when the certificate is D1-symmetric, else [0, pi/2]; adapted from tri_container/n6/stage2/float_bb.py): finds poses that are
admissible, not excluded, contain no obstacle point, and capture < 1.  Breadth-first, vectorised.
A box is dropped when every pose in it is: inadmissible, or exempt (some witness surely inside), or inside an
exclusion box, or surely captures >= 1.  At each level the centre pose of every live box is evaluated; deficit
centres are recorded as seeds.  Output: JSON list of [cx, cy, theta] seeds (one per box, deduplicated on a grid).
Usage: python float_bb.py cert.json out_seeds.json [max_level] [max_boxes] [margin]"""
import json, math, sys
from fractions import Fraction as F
import numpy as np
sys.path.insert(0, __import__("os").path.join(__import__("os").path.dirname(__import__("os").path.abspath(__file__)), "checker"))
from q2 import Q2 as Q3
c = json.load(open(sys.argv[1])); out = sys.argv[2]
MAXL = int(sys.argv[3]) if len(sys.argv) > 3 else 26; MAXB = int(sys.argv[4]) if len(sys.argv) > 4 else 3_000_000
MG = float(sys.argv[5]) if len(sys.argv) > 5 else 0.0   # report centres whose capture with this margin is < 1
L = float(Q3.parse(c["L"])); r2 = math.sqrt(2)
HYP = c.get("frame") == "hyp"; H = L * r2     # hypotenuse frame: T = {y >= 0, y <= x, y <= H - x}
P = np.array([(float(Q3.parse(p["x"])), float(Q3.parse(p["y"]))) for p in c["points"]]); W = np.array([float(F(p["w"])) for p in c["points"]])
O = np.array([(float(Q3.parse(p["x"])), float(Q3.parse(p["y"]))) for p in c.get("obstacle_points", [])]).reshape(-1, 2)
EX = np.array([[float(Q3.parse(v)) for v in (e["x"][0], e["x"][1], e["y"][0], e["y"][1], e["u"][0], e["u"][1])] for e in c.get("exclusions", [])]).reshape(-1, 6)
TEX = np.stack([EX[:, 0], EX[:, 1], EX[:, 2], EX[:, 3], 2 * np.arctan(EX[:, 4]), 2 * np.arctan(EX[:, 5])], 1) if len(EX) else EX
# boxes: columns x0 x1 y0 y1 t0 t1
B = np.array([[0, H if HYP else L, 0, H / 2 if HYP else L, 0, math.pi / 4 if c.get("symmetry") == "D1" else math.pi / 2]])
SG = np.array([(-.5, -.5), (.5, -.5), (.5, .5), (-.5, .5)])
seeds = {}
CH = 20000   # boxes per chunk


def local(Q, cx, cy, th):
    """local coords of points Q (m,2) for poses (k,) -> a, b of shape (k, m)"""
    co, si = np.cos(th)[:, None], np.sin(th)[:, None]
    dx = Q[None, :, 0] - cx[:, None]; dy = Q[None, :, 1] - cy[:, None]
    return dx * co + dy * si, -dx * si + dy * co
for lev in range(MAXL + 1):
    if not len(B): break
    cx = (B[:, 0] + B[:, 1]) / 2; cy = (B[:, 2] + B[:, 3]) / 2; th = (B[:, 4] + B[:, 5]) / 2
    rc = np.hypot(B[:, 1] - B[:, 0], B[:, 3] - B[:, 2]) / 2; dt = (B[:, 5] - B[:, 4]) / 2
    # admissibility: corners of mid pose; a corner moves by <= rc + dt*sqrt(1/2)
    rr = rc + dt * math.sqrt(.5)
    co, si = np.cos(th), np.sin(th)
    worst = np.full(len(B), np.inf); best = np.full(len(B), np.inf)
    for sx, sy in SG:
        x = cx + co * sx - si * sy; y = cy + si * sx + co * sy
        g = np.minimum(np.minimum(y, (x - y) / r2), (H - x - y) / r2) if HYP else np.minimum(np.minimum(y, x), (L - x - y) / r2)
        worst = np.minimum(worst, g)
    keep = worst >= -rr - 1e-12                      # possibly admissible somewhere in the box
    sure_adm_c = worst >= 0                          # the centre pose itself is admissible
    # exclusion: box inside some exclusion box
    inex = np.zeros(len(B), bool)
    for e in TEX:
        inex |= (B[:, 0] >= e[0]) & (B[:, 1] <= e[1]) & (B[:, 2] >= e[2]) & (B[:, 3] <= e[3]) & (B[:, 4] >= e[4]) & (B[:, 5] <= e[5])
    # centre excluded?
    cex = np.zeros(len(B), bool)
    for e in TEX:
        cex |= (cx >= e[0]) & (cx <= e[1]) & (cy >= e[2]) & (cy <= e[3]) & (th >= e[4]) & (th <= e[5])
    # points: distance moved <= rc + dt*|p - c|  (bound |p - c| by its centre value + rc)
    # in chunks of boxes: the (boxes x points) arrays of one level can exceed a memory cap of a few GB
    sure = np.zeros(len(B)); capc = np.zeros(len(B))
    exempt_all = np.zeros(len(B), bool); exempt_c = np.zeros(len(B), bool)
    for c0 in range(0, len(B), CH):
        sl = slice(c0, c0 + CH)
        a, b = local(P, cx[sl], cy[sl], th[sl])
        dist = np.hypot(P[None, :, 0] - cx[sl, None], P[None, :, 1] - cy[sl, None])
        mv = rc[sl, None] + dt[sl, None] * (dist + rc[sl, None])
        m = np.maximum(np.abs(a), np.abs(b))
        sure[sl] = ((m <= .5 - MG - mv) * W[None, :]).sum(1)
        capc[sl] = ((m <= .5 - MG + 1e-12) * W[None, :]).sum(1)
        del a, b, dist, mv, m
        if len(O):
            ao, bo = local(O, cx[sl], cy[sl], th[sl])
            disto = np.hypot(O[None, :, 0] - cx[sl, None], O[None, :, 1] - cy[sl, None])
            mo = np.maximum(np.abs(ao), np.abs(bo)); mvo = rc[sl, None] + dt[sl, None] * (disto + rc[sl, None])
            exempt_all[sl] = (mo <= .5 - mvo).any(1); exempt_c[sl] = (mo <= .5 - 1e-9).any(1)
    deficit = keep & sure_adm_c & ~cex & ~exempt_c & (capc < 1 - 1e-9)
    for i in np.nonzero(deficit)[0]:
        k = (round(cx[i], 3), round(cy[i], 3), round(th[i], 3))
        if k not in seeds: seeds[k] = [float(cx[i]), float(cy[i]), float(th[i])]
    live = keep & ~inex & ~exempt_all & (sure < 1 - 1e-12) & ~deficit
    B = B[live]
    print(f"level {lev}: live {len(B)}, seeds {len(seeds)}", flush=True)
    if len(B) > MAXB:
        rng = np.random.default_rng(lev); B = B[rng.choice(len(B), MAXB, replace=False)]
        print("  (sampled down)", flush=True)
    # split along the widest side (angle weighted by 1)
    wx = B[:, 1] - B[:, 0]; wy = B[:, 3] - B[:, 2]; wt = (B[:, 5] - B[:, 4]) * 1.0
    ax = np.argmax(np.stack([wx, wy, wt], 1), 1)
    lo = B.copy(); hi = B.copy()
    for k, (i0, i1) in enumerate(((0, 1), (2, 3), (4, 5))):
        s = ax == k; mid = (B[s, i0] + B[s, i1]) / 2
        lo[s, i1] = mid; hi[s, i0] = mid
    B = np.concatenate([lo, hi])
json.dump(list(seeds.values()), open(out, "w"))
print("seeds", len(seeds), "->", out)
