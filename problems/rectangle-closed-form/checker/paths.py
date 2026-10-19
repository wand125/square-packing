#!/usr/bin/env python3
"""Paths between intervals, E, r, k0 and where Theorem B improves on the area bound (SPEC.md section 5).

Input: data/edges.json (30 seams with their e, and 4 adjacent pairs with identical profiles, e = 0) and
../closed-form/intervals.json (the 34 intervals and their certified lines S_J(delta) = alpha delta + beta).
For every pair of intervals (J_a, J_b), a <= b, and every number of seams r, the least E over paths with at
most r seams (the frontier); k0(r) = max(7, 6 + 3r). The path of least E overall is reported with its r and k0.
Usefulness: g = 2 S_a(delta_a) + 2 S_b(delta_b) - 4E over the closed box J_a x J_b (S is affine, so the extreme
values are at the corners): 'all' if g > 0 at every corner, 'part' if at some, 'none' otherwise.
Output: data/paths.json and a summary. Exact rationals throughout.

usage: paths.py [--edges data/edges.json] [--intervals ../closed-form/intervals.json] [--out data/paths.json]
"""
import argparse
import heapq
import json
import os
from collections import Counter
from fractions import Fraction as Q

HERE = os.path.dirname(os.path.abspath(__file__))


def k0(r):
    return max(7, 6 + 3 * r)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--edges', default=os.path.join(HERE, '..', 'data', 'edges.json'))
    ap.add_argument('--intervals', default=os.path.join(HERE, '..', '..', 'closed-form', 'intervals.json'))
    ap.add_argument('--out', default=os.path.join(HERE, '..', 'data', 'paths.json'))
    a = ap.parse_args()
    iv = json.load(open(a.intervals))
    iv = iv.get('intervals', iv) if isinstance(iv, dict) else iv
    N = len(iv)
    line = {i + 1: (Q(r['certified_line']['alpha']), Q(r['certified_line']['beta']), Q(r['d0']), Q(r['d1']))
            for i, r in enumerate(iv)}
    adj = {i: [] for i in range(1, N + 1)}
    for e in json.load(open(a.edges))['edges']:
        w, s = Q(e['e']), 1 if e['kind'] == 'seam' else 0
        assert (s == 1) == (w > 0), e
        adj[e['a']].append((e['b'], w, s)); adj[e['b']].append((e['a'], w, s))

    def frontier(src):
        best = {(src, 0): Q(0)}
        pq = [(Q(0), 0, src)]
        while pq:
            e, r, u = heapq.heappop(pq)
            if best.get((u, r)) != e:
                continue
            for v, w, s in adj[u]:
                ne, nr = e + w, r + s
                if any(rr <= nr and ee <= ne for (vv, rr), ee in best.items() if vv == v):
                    continue
                best[(v, nr)] = ne
                heapq.heappush(pq, (ne, nr, v))
        out = {}
        for (v, r), e in sorted(best.items(), key=lambda t: (t[0][0], t[0][1])):
            pts = out.setdefault(v, [])
            if not pts or e < Q(pts[-1]['E']):
                pts.append({'r': r, 'k0': k0(r), 'E': str(e)})
        return out

    def ends(i):
        al, be, d0, d1 = line[i]
        return [al * d0 + be, al * d1 + be]

    rows = []
    for i in range(1, N + 1):
        fr = frontier(i)
        assert len(fr) == N, f'graph not connected from interval {i}'
        for j in range(i, N + 1):
            last = fr[j][-1]
            E = Q(last['E'])
            g = [2 * x + 2 * y - 4 * E for x in ends(i) for y in ends(j)]
            rows.append({'a': i, 'b': j, 'E': last['E'], 'r': last['r'], 'k0': last['k0'],
                         'useful': 'all' if min(g) > 0 else 'part' if max(g) > 0 else 'none',
                         'net_min': str(min(g)), 'net_max': str(max(g)), 'frontier': fr[j]})
    json.dump(rows, open(a.out, 'w'), indent=1)
    for same in (True, False):
        sel = [o for o in rows if (o['a'] == o['b']) == same]
        c = Counter(o['useful'] for o in sel)
        print('same interval' if same else 'different intervals', len(sel), dict(c),
              'largest k0 among useful', max(o['k0'] for o in sel if o['useful'] != 'none'))
    m = max(rows, key=lambda o: Q(o['E']))
    print('largest E', m['E'], f'({float(Q(m["E"])):.6f})', 'for intervals', m['a'], m['b'], 'r', m['r'], 'k0', m['k0'])
    print('largest number of frontier steps', max(len(o['frontier']) for o in rows))
    print('PATHS OK')


if __name__ == '__main__':
    main()
