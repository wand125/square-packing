#!/usr/bin/env python3
"""Exact checks of the root set and the coverage of one seam (SPEC.md section 5.3, steps 4 and the R5 list).

1. The R5 root list. The window of the seam check is the product grid
   x in [S - 3/4, S + n + 3/4], y in [0, 13/5] with pitch 1/10, and u = tan(theta/2) in [-13/32, 7/16] with
   pitch 1/32 (an angle range longer than 90 degrees, so every orientation occurs); with S = 5, n = 1 these are
   25 x 26 x 27 = 17,550 roots. A root may be left out only if no square in it reaches a band:
   x1 + w < S + d or x0 - w > S + n - d, where w bounds the half-width of a square in x over the root's angles.
   The half-width is w(u) = (cos t + |sin t|)/2 = (1 - u^2 + 2|u|) / (2 (1 + u^2)), a rational function of u; on
   [u0, u1] its maximum is at an end, or sqrt(2)/2 if the interval contains +-tan(pi/8); we use the rational
   upper bound 7072/10000 > sqrt(2)/2 there. The check: every listed root is a grid root, and every grid root not
   listed satisfies the exclusion exactly. (A larger list is always safe; only the left-out roots need a proof.)
2. Coverage. The roots of the records (all levels) are pieces: each lies inside a listed root, the pieces are
   pairwise interior-disjoint, and their volumes add up to the volume of the list. Hence they cover it.
   Each record line must have no uncertified leaves.

usage: seam_cover.py ROOTS_R5.json RECORD [RECORD ...] [--S 5] [--n 1] [--d 2/5]
"""
import argparse
import json
import sys
from fractions import Fraction as Q


def half_width_bound(u0, u1):
    t = Q(4142135623730950, 10**16)        # below tan(pi/8) = 0.41421356237309504...
    t_hi = Q(4142135623730951, 10**16)     # above tan(pi/8)
    if (u0 <= t_hi and u1 >= t) or (u0 <= -t and u1 >= -t_hi):
        return Q(7072, 10000)
    w = lambda u: (1 - u * u + 2 * abs(u)) / (2 * (1 + u * u))
    return max(w(u0), w(u1))


def grid(S, n):
    xs = [Q(S) - Q(3, 4) + Q(i, 10) for i in range(int((n + Q(3, 2)) * 10))]
    ys = [Q(j, 10) for j in range(26)]
    us = [Q(k, 32) for k in range(-13, 14)]
    for x in xs:
        for y in ys:
            for u in us:
                yield (x, x + Q(1, 10), y, y + Q(1, 10), u, u + Q(1, 32))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('roots'); ap.add_argument('records', nargs='+')
    ap.add_argument('--S', default='5'); ap.add_argument('--n', default='1'); ap.add_argument('--d', default='2/5')
    a = ap.parse_args()
    S, n, d = Q(a.S), Q(a.n), Q(a.d)
    listed = {tuple(Q(v) for v in r) for r in json.load(open(a.roots))}
    full = list(grid(S, n))
    ok = True
    extra = listed - set(full)
    if extra:
        ok = False; print('listed roots not on the grid:', len(extra))
    left_out = [r for r in full if r not in listed]
    unproved = [r for r in left_out
                if not (r[1] + half_width_bound(r[4], r[5]) < S + d or r[0] - half_width_bound(r[4], r[5]) > S + n - d)]
    print(f'grid {len(full)}, listed {len(listed)}, left out {len(left_out)}, left out without proof {len(unproved)}')
    ok &= not unproved
    pieces, uncert = [], 0
    for rec in a.records:
        for line in open(rec):
            row = json.loads(line)
            if 'root' not in row:
                continue
            uncert += len(row.get('uncert') or [])
            pieces.append(tuple(Q(v) for v in row['root'][:6]))
    vol = lambda r: (r[1] - r[0]) * (r[3] - r[2]) * (r[5] - r[4])
    roots = sorted(listed)
    inside = all(any(all(t[2 * i] <= p[2 * i] and p[2 * i + 1] <= t[2 * i + 1] for i in range(3)) for t in roots
                     if t[0] <= p[0] < t[1]) for p in pieces)
    ps = sorted(pieces)
    disjoint = True
    for k, p in enumerate(ps):
        for q in ps[k + 1:]:
            if q[0] >= p[1]:
                break
            if not any(p[2 * i + 1] <= q[2 * i] or q[2 * i + 1] <= p[2 * i] for i in range(3)):
                disjoint = False; break
        if not disjoint:
            break
    same = sum(map(vol, pieces)) == sum(map(vol, roots))
    print(f'pieces {len(pieces)}, uncertified leaves {uncert}, inside {inside}, disjoint {disjoint}, volume equal {same}')
    ok &= inside and disjoint and same and uncert == 0
    print('SEAM_COVER', 'OK' if ok else 'BAD')
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
