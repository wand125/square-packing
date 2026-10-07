#!/usr/bin/env python3
"""Rebuild only the FAILED leaves of a tree (tree.py output) with more depth / more linear
splits, and splice the new subtrees in place.  Everything else is kept as is."""
import argparse
import json
import sys
import time
from pathlib import Path

import tree as T
from cert import Q3, aneg


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('tree_json')
    ap.add_argument('cert')
    ap.add_argument('--out', required=True)
    ap.add_argument('--extra-depth', type=int, default=8)
    ap.add_argument('--max-lin', type=int, default=8)
    a = ap.parse_args()
    d = json.loads(Path(a.tree_json).read_text())
    L, pts = T.load(a.cert)
    b = T.Builder(L, pts, max_depth=10 ** 6)
    src = Path(T.__file__).read_text()
    T.MAX_LIN = a.max_lin
    fixed = failed = 0
    t0 = time.time()

    def lin_forms(path):
        return tuple(path)

    def rec(n, box, U, lins, depth):
        nonlocal fixed, failed
        if 'leaf' in n:
            if n['leaf'] != 'FAILED':
                return n
            b.max_depth = depth + a.extra_depth
            new = b.build(box, U[0], U[1], lins, depth)
            bad = count_failed(new)
            if bad:
                failed += bad
            else:
                fixed += 1
            print(json.dumps(dict(fixed=fixed, failed=failed, seconds=round(time.time() - t0))), flush=True)
            return new
        s = n['split']
        if s == 'lin':
            f = parse_aff(n['form'])
            n['form'] = f
            n['pos'] = rec(n['pos'], box, U, lins + (f,), depth + 1)
            n['neg'] = rec(n['neg'], box, U, lins + (aneg(f),), depth + 1)
            return n
        m = Q3.parse(n['at'])
        n['at'] = m
        x0, x1, y0, y1 = box
        if s == 'x':
            n['lo'] = rec(n['lo'], (x0, m, y0, y1), U, lins, depth + 1)
            n['hi'] = rec(n['hi'], (m, x1, y0, y1), U, lins, depth + 1)
        elif s == 'y':
            n['lo'] = rec(n['lo'], (x0, x1, y0, m), U, lins, depth + 1)
            n['hi'] = rec(n['hi'], (x0, x1, m, y1), U, lins, depth + 1)
        else:
            n['lo'] = rec(n['lo'], box, (U[0], m), lins, depth + 1)
            n['hi'] = rec(n['hi'], box, (m, U[1]), lins, depth + 1)
        return n

    for r in d['roots']:
        U = tuple(Q3.parse(x) for x in r['u'])
        r['tree'] = rec(r['tree'], T.root_box(L), U, (), 0)
    Path(a.out).write_text(json.dumps(d, default=str))
    print(json.dumps(dict(fixed=fixed, still_failed=failed)))
    return 0 if failed == 0 else 1


def parse_aff(f):
    return {k: [Q3.parse(c) for c in f[k]] for k in ('1', 'x', 'y')}


def count_failed(n):
    if 'leaf' in n:
        return 1 if n['leaf'] == 'FAILED' else 0
    return sum(count_failed(n[k]) for k in ('lo', 'hi', 'pos', 'neg') if k in n)


if __name__ == '__main__':
    sys.exit(main())
