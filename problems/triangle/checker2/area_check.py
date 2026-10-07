#!/usr/bin/env python3
"""Floating-point cross-check (not a proof): for each angle on a grid, subtract the union of the
points' capture squares from the region of admissible centres and report the largest remainder.

A positive area would give a unit square in T_L that contains no certificate point.

    python area_check.py lattice_m9.json [--steps 9000]
"""
import argparse
import json
import math
from fractions import Fraction

from shapely import affinity
from shapely.geometry import Polygon, box
from shapely.ops import unary_union

R3 = math.sqrt(3)


def val(s):
    s = s.replace(' ', '').replace('+-', '-')
    if 'sqrt3' not in s:
        return float(Fraction(s))
    body = s[:s.index('sqrt3') - 1]
    k = max(body.rfind('+'), body.rfind('-'))
    if k <= 0:
        return float(Fraction(body)) * R3
    return float(Fraction(body[:k])) + float(Fraction(body[k:].lstrip('+'))) * R3


def halfplane(a1, a2, off, R=100.0):
    """{a1 x + a2 y >= off} intersected with a large square."""
    nn = math.hypot(a1, a2)
    u = (a1 / nn, a2 / nn)
    t = (-u[1], u[0])
    p = (u[0] * off / nn, u[1] * off / nn)
    return Polygon([(p[0] + t[0] * R, p[1] + t[1] * R), (p[0] - t[0] * R, p[1] - t[1] * R),
                    (p[0] - t[0] * R + u[0] * R, p[1] - t[1] * R + u[1] * R),
                    (p[0] + t[0] * R + u[0] * R, p[1] + t[1] * R + u[1] * R)])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('cert')
    ap.add_argument('--steps', type=int, default=9000)
    a = ap.parse_args()
    c = json.load(open(a.cert))
    L = val(c['L'])
    pts = [(val(p['x']), val(p['y'])) for p in c['points']]
    sides = [((0, 1), 0), ((R3, -1), 0), ((-R3, -1), R3 * L)]      # a.q + b >= 0
    unit = Polygon([(-.5, -.5), (.5, -.5), (.5, .5), (-.5, .5)])
    best, best_deg = 0.0, None
    for i in range(a.steps + 1):
        th = math.pi / 2 * i / a.steps
        ct, st = math.cos(th), math.sin(th)
        region = box(-1, -1, L + 1, L)
        for (a1, a2), b in sides:
            for sx in (-.5, .5):
                for sy in (-.5, .5):
                    vx, vy = sx * ct - sy * st, sx * st + sy * ct
                    region = region.intersection(halfplane(a1, a2, -b - (a1 * vx + a2 * vy)))
        caps = unary_union([affinity.translate(affinity.rotate(unit, math.degrees(th), origin=(0, 0)), x, y)
                            for x, y in pts])
        rest = region.difference(caps).area
        if rest > best:
            best, best_deg = rest, math.degrees(th)
    print(json.dumps(dict(certificate=a.cert, L=L, points=len(pts), angles=a.steps + 1,
                          max_uncovered_area=best, at_degrees=best_deg)))


if __name__ == '__main__':
    main()
