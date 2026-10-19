#!/usr/bin/env python3
"""Exact checks of a seam family: structure, the band condition of Lemma R5, and domination of earlier levels.

A seam family (SPEC.md section 5) has all its segments in F, as rows [x1, y1, x2, y2, mass]. We turn the rows
into piecewise-constant line densities and compare them pointwise, in exact rationals, with the periodic wall
of the profile P (left) or P' (right) of the two interval families:
  structure:  on [S - 3, S) the seam measure equals the P-wall, on [S + n, S + n + 3) it equals the P'-wall
              (the vertical line x = S + n belongs to P');
  left band:  on the open half-plane x < S + d the seam measure is >= the P-wall;
  right band: on the open half-plane x > S + n - d the seam measure is >= the P'-wall.
Pointwise domination of line densities implies mu_seam(Q) >= mu_P(Q) for every Q inside the half-plane,
whatever the split of segments into pieces. With --dominates OLD..., also check that the family dominates
each earlier-level family pointwise everywhere, with all other fields (d0, d1, UA, T, V, U) equal.

The profiles are taken from the interval families with decompose() of
../../closed-form/structure/validate_family.py (read only).

usage: seam_exact.py SEAM.json FA.json FB.json [--d 2/5] [--dominates OLD.json ...]
"""
import argparse
import json
import os
import sys
from collections import defaultdict
from fractions import Fraction as Q

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'closed-form', 'structure'))
from validate_family import decompose, load, shift  # noqa: E402


def lines(segs):
    out = defaultdict(list)
    for k, c, lo, hi, r in segs:
        if hi > lo and r != 0:
            out[(k, Q(c))].append((Q(lo), Q(hi), Q(r)))
    return out


def family_segments(fam):
    out = []
    for x1, y1, x2, y2, m in fam['F']:
        x1, y1, x2, y2, m = map(Q, (x1, y1, x2, y2, m))
        if y1 == y2:
            lo, hi = min(x1, x2), max(x1, x2)
            out.append(('h', y1, lo, hi, m / (hi - lo)))
        else:
            if x1 != x2:
                raise SystemExit('segment not axis-parallel')
            lo, hi = min(y1, y2), max(y1, y2)
            out.append(('v', x1, lo, hi, m / (hi - lo)))
    return out


def density(ivs, a, b):
    return sum((r for lo, hi, r in ivs if lo <= a and b <= hi), Q(0))


def compare(new, ref, xlo, xhi, lo_open, hi_open, mode):
    """Compare line densities on x in <xlo, xhi> (open ends as given). mode 'eq' or 'ge'. Returns violations."""
    bad = 0
    for k, c in set(new) | set(ref):
        s, r = new.get((k, c), []), ref.get((k, c), [])
        if k == 'v':
            if c < xlo or c > xhi or (lo_open and c == xlo) or (hi_open and c == xhi):
                continue
            cuts = sorted({p for lo, hi, _ in s + r for p in (lo, hi)})
        else:
            cuts = sorted({p for lo, hi, _ in s + r for p in (lo, hi) if xlo <= p <= xhi} | {xlo, xhi})
        for a, b in zip(cuts, cuts[1:]):
            if k == 'h' and (a < xlo or b > xhi):
                continue
            ds, dr = density(s, a, b), density(r, a, b)
            if (mode == 'eq' and ds != dr) or (mode == 'ge' and ds < dr):
                bad += 1
                if bad <= 5:
                    print(f'  violation {mode}: {k}={c} on [{a}, {b}]: seam {float(ds):.9g} < ref {float(dr):.9g}')
    return bad


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('seam'); ap.add_argument('fa'); ap.add_argument('fb')
    ap.add_argument('--d', default='2/5')
    ap.add_argument('--dominates', nargs='*', default=[])
    a = ap.parse_args()
    fam = json.load(open(a.seam))
    sm = fam['seam']
    S, n, d = Q(sm['S']), int(sm['n']), Q(a.d)
    pa, pb = decompose(load(a.fa))[0], decompose(load(a.fb))[0]
    A = lines([s for j in range(-4, n + 4) for s in shift(pa, S + j)])
    B = lines([s for j in range(-4, n + 4) for s in shift(pb, S + j)])
    L = lines(family_segments(fam))
    res = {
        'structure left [S-3, S)': compare(L, A, S - 3, S, False, True, 'eq'),
        'structure right [S+n, S+n+3)': compare(L, B, S + n, S + n + 3, False, True, 'eq'),
        'band left x < S+d': compare(L, A, S - 3, S + d, False, True, 'ge'),
        'band right x > S+n-d': compare(L, B, S + n - d, S + n + 3, True, True, 'ge'),
    }
    for p in a.dominates:
        old = json.load(open(p))
        v = compare(L, lines(family_segments(old)), Q(-100), Q(100), False, False, 'ge')
        same = all(fam.get(k) == old.get(k) for k in ('d0', 'd1', 'UA', 'T', 'V', 'U'))
        res[f'dominates {os.path.basename(os.path.dirname(os.path.abspath(p)))}/{os.path.basename(p)}'] = v + (0 if same else 1)
    for k, v in res.items():
        print(f'{k}: {"OK" if v == 0 else f"BAD {v}"}')
    ok = not any(res.values())
    print('extra mass e =', sm['extra'], '| SEAM_EXACT', 'OK' if ok else 'BAD')
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
