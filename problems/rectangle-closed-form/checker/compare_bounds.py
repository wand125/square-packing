#!/usr/bin/env python3
"""Compare Theorems A and B with the area bound and with Karakus's bound, pair by pair, in exact rationals.

For intervals J_a, J_b (numbers as in ../closed-form/intervals.json) and E = E(J_a, J_b) from data/paths.json,
our bound is nu(a, b) <= ab - G with G(da, db) = 2 S_a(da) + 2 S_b(db) - 4E, S the certified line of the interval.
Karakus's bound, read for the container a x b itself (apply it to a' x b' with a' > a, b' > b and let a' -> a),
is nu(a, b) <= ab - max(da, db) for da, db in [0, 1) (the right limit of t + 1 - ceil(t) is the fractional part).
G is affine and max(da, db) is convex, so G - max(da, db) is concave on J_a x J_b and its minimum is at a corner;
its maximum is at a corner too, because the line da = db meets J_a x J_b only at corners (the intervals are
disjoint or equal). We report, per pair, whether our bound is stronger on the whole rectangle (min > 0), on a
part of it, or nowhere (max <= 0), for the area bound (G > 0) and for Karakus (G > max(da, db)).

usage: compare_bounds.py [--paths data/paths.json] [--intervals ../closed-form/intervals.json] [--out data/compare.json]
"""
import argparse
import json
import os
from fractions import Fraction as Q

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--paths', default=os.path.join(HERE, '..', 'data', 'paths.json'))
    ap.add_argument('--intervals', default=os.path.join(HERE, '..', '..', 'closed-form', 'intervals.json'))
    ap.add_argument('--out', default=os.path.join(HERE, '..', 'data', 'compare.json'))
    args = ap.parse_args()
    iv = json.load(open(args.intervals))
    iv = iv.get('intervals', iv)
    line = {e['index']: (Q(e['certified_line']['alpha']), Q(e['certified_line']['beta'])) for e in iv}
    ends = {e['index']: (Q(e['d0']), Q(e['d1'])) for e in iv}

    def S(i, d):
        al, be = line[i]
        return al * d + be

    def kind(vals):
        return 'all' if min(vals) > 0 else ('none' if max(vals) <= 0 else 'part')

    rows, count = [], {'area': {}, 'karakus': {}}
    for p in json.load(open(args.paths)):
        a, b, E = p['a'], p['b'], Q(p['E'])
        corners = [(x, y) for x in ends[a] for y in ends[b]]
        G = [2 * S(a, x) + 2 * S(b, y) - 4 * E for x, y in corners]
        K = [g - max(x, y) for g, (x, y) in zip(G, corners)]
        r = {'a': a, 'b': b, 'E': p['E'], 'vs_area': kind(G), 'vs_karakus': kind(K),
             'karakus_margin_min': str(min(K)), 'karakus_margin_max': str(max(K))}
        rows.append(r)
        for key, k in (('area', r['vs_area']), ('karakus', r['vs_karakus'])):
            count[key][k] = count[key].get(k, 0) + 1
    json.dump(rows, open(args.out, 'w'), indent=1)
    for key in ('area', 'karakus'):
        c = count[key]
        print(f'stronger than {key}: all {c.get("all", 0)}, part {c.get("part", 0)}, none {c.get("none", 0)} '
              f'(of {len(rows)} pairs)')
    print('COMPARE OK')


if __name__ == '__main__':
    main()
