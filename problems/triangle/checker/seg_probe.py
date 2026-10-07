#!/usr/bin/env python3
"""Float sanity probe (NOT a proof): minimum capture of a certificate over random poses.

For random admissible poses Q(c, theta) in T_L it evaluates

    capture(Q) = sum of w_i over points p_i in Q  +  sum over segments of rho * |Q cap segment|

and reports the minimum found, after a local refinement of the worst poses.  Chord pairs
and threshold features are ignored (they only add to the exact checker's capture).

Usage:
    python seg_probe.py cert.json [--samples 200000] [--seed 1] [--refine 20] [--tol 1e-9]
"""
from __future__ import annotations

import argparse
import json
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from check import load_certificate  # noqa: E402

H = math.sqrt(3) / 2


def admissible(L, cx, cy, th, tol=0.0):
    co, si = math.cos(th), math.sin(th)
    for sx in (0.5, -0.5):
        for sy in (0.5, -0.5):
            vx = cx + co * sx - si * sy
            vy = cy + si * sx + co * sy
            if vy < -tol or H * vx + 0.5 * vy > H * L + tol or -H * vx + 0.5 * vy > tol:
                return False
    return True


def seg_length(p, d, cx, cy, th):
    """|Q(c, theta) cap {p + t d : t in [0, 1]}| by clipping against the two slabs."""
    lo, hi = 0.0, 1.0
    for ax, ay in ((math.cos(th), math.sin(th)), (-math.sin(th), math.cos(th))):
        m = d[0] * ax + d[1] * ay
        n = (p[0] - cx) * ax + (p[1] - cy) * ay
        if abs(m) < 1e-15:
            if abs(n) > 0.5:
                return 0.0
            continue
        t1, t2 = (-0.5 - n) / m, (0.5 - n) / m
        lo, hi = max(lo, min(t1, t2)), min(hi, max(t1, t2))
        if hi <= lo:
            return 0.0
    return (hi - lo) * math.hypot(d[0], d[1])


def capture(pts, segs, cx, cy, th, tol):
    co, si = math.cos(th), math.sin(th)
    tot = 0.0
    for x, y, w in pts:
        dx, dy = x - cx, y - cy
        if abs(dx * co + dy * si) <= 0.5 + tol and abs(-dx * si + dy * co) <= 0.5 + tol:
            tot += w
    for p, d, rho in segs:
        if rho:
            tot += rho * seg_length(p, d, cx, cy, th)
    return tot


def probe(cert, samples=200000, seed=1, refine=20, tol=1e-9):
    _, L, _, points, _, _, segments = load_certificate(cert)
    Lf = float(L)
    pts = [(float(x), float(y), float(w)) for x, y, w in points]
    segs = [((float(p[0]), float(p[1])), (float(q[0] - p[0]), float(q[1] - p[1])), float(rho))
            for p, q, rho in segments]
    rng = random.Random(seed)
    worst = []
    hits = 0
    for _ in range(samples):
        th = rng.uniform(0, math.pi / 2)
        cx, cy = rng.uniform(0, Lf), rng.uniform(0, Lf * H)
        if not admissible(Lf, cx, cy, th):
            continue
        hits += 1
        worst.append((capture(pts, segs, cx, cy, th, tol), cx, cy, th))
        if len(worst) > 4 * refine:
            worst.sort()
            del worst[refine:]
    worst.sort()
    best = list(worst[:refine])
    # local refinement: random walk with shrinking steps, staying admissible
    for i, (v, cx, cy, th) in enumerate(best):
        step = 0.05
        while step > 1e-7:
            improved = False
            for _ in range(30):
                nx, ny = cx + rng.gauss(0, step), cy + rng.gauss(0, step)
                nt = th + rng.gauss(0, step)
                if not admissible(Lf, nx, ny, nt):
                    continue
                nv = capture(pts, segs, nx, ny, nt, tol)
                if nv < v:
                    v, cx, cy, th, improved = nv, nx, ny, nt, True
            if not improved:
                step /= 2
        best[i] = (v, cx, cy, th)
    best.sort()
    out = {"L": str(L), "points": len(pts), "segments": len(segs), "admissible_samples": hits}
    if best:
        v, cx, cy, th = best[0]
        out.update(min_capture=v, argmin={"cx": cx, "cy": cy, "theta": th,
                                          "theta_deg": math.degrees(th) % 90})
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cert")
    ap.add_argument("--samples", type=int, default=200000)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--refine", type=int, default=20, help="number of worst poses refined locally")
    ap.add_argument("--tol", type=float, default=1e-9, help="float tolerance for point capture")
    a = ap.parse_args(argv)
    print(json.dumps(probe(a.cert, a.samples, a.seed, a.refine, a.tol), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
