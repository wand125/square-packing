#!/usr/bin/env python3
"""Exact random probe, independent of the sweep: draw random admissible poses with rational
u = tan(t/2) and rational-plus-sqrt3 centres, and count the captured weight exactly.

It cannot prove anything; it can only find a counterexample.  It also checks the D3 invariance
of the weighted point set exactly (reported, not used by the sweep).

    python probe.py cert.json [--poses 20000] [--seed 1]
"""
import argparse
import json
import random
import sys

from gmpy2 import mpq

from q3 import Q3
from sweep import load, HALF

S3 = Q3(0, 1)


def pose_ok(L, c, ct, st):
    for sx in (-HALF, HALF):
        for sy in (-HALF, HALF):
            x = c[0] + ct * sx - st * sy
            y = c[1] + st * sx + ct * sy
            if y.sign() < 0 or (S3 * x + y - S3 * L).sign() > 0 or (y - S3 * x).sign() > 0:
                return False
    return True


def captured(pts, c, ct, st):
    w = mpq(0)
    for px, py, pw in pts:
        dx, dy = px - c[0], py - c[1]
        a = dx * ct + dy * st
        b = -dx * st + dy * ct
        if (HALF - a).sign() >= 0 and (HALF + a).sign() >= 0 and (HALF - b).sign() >= 0 and (HALF + b).sign() >= 0:
            w += pw
    return w


def d3_invariant(L, pts):
    """Rotation by 2pi/3 about the centroid and the reflection x -> L - x preserve the weights."""
    G = (L / 2, L * S3 / 6)
    c, s = Q3(mpq(-1, 2)), Q3(0, HALF)          # cos, sin of 2pi/3
    bag = {}
    for x, y, w in pts:
        bag[(x, y)] = bag.get((x, y), 0) + w
    def rot(p):
        dx, dy = p[0] - G[0], p[1] - G[1]
        return (G[0] + c * dx - s * dy, G[1] + s * dx + c * dy)
    def ref(p):
        return (L - p[0], p[1])
    for f in (rot, ref):
        img = {}
        for p, w in bag.items():
            q = f(p)
            img[q] = img.get(q, 0) + w
        if img != bag:
            return False
    return True


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('cert')
    ap.add_argument('--poses', type=int, default=20000)
    ap.add_argument('--seed', type=int, default=1)
    a = ap.parse_args(argv)
    _, L, pts, sha = load(a.cert)
    rng = random.Random(a.seed)
    Lf = float(L)
    best, tried, found = None, 0, 0
    while found < a.poses:
        tried += 1
        u = mpq(rng.randint(0, 10**6), 10**6)
        uq = Q3(u)
        D = 1 + uq * uq
        ct, st = (1 - uq * uq) / D, (2 * uq) / D
        cx = Q3(mpq(rng.randint(0, 10**6), 10**6) * mpq(str(Lf)))
        cy = Q3(mpq(rng.randint(0, 10**6), 10**6) * mpq(str(Lf * 0.8660254)))
        # bias half the draws towards the boundary, where the tight poses are
        if found % 2:
            k = rng.random()
            cy = Q3(mpq(rng.randint(0, 10**4), 10**6) + mpq(1, 2) * (1 if k < .5 else 0))
        if not pose_ok(L, (cx, cy), ct, st):
            continue
        found += 1
        w = captured(pts, (cx, cy), ct, st)
        best = w if best is None or w < best else best
    print(json.dumps(dict(certificate=a.cert, sha256=sha, admissible_poses=found, draws=tried,
                          min_captured_weight=str(best), d3_invariant=d3_invariant(L, pts))))
    return 0 if best >= 1 else 1


if __name__ == '__main__':
    sys.exit(main())
