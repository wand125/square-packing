#!/usr/bin/env python3
"""Exact check of Lemmas R1 and R2 for a rectangle container built from one closed-form family.

Container [0, a] x [0, b], a = k + d_a, b = m + d_b, with d_a and d_b in the family's interval [d0, d1].
The family JSON and the square construction are those of ../../closed-form/SPEC.md; this script uses the
functions of ../../closed-form/structure/validate_family.py (read only).

Construction (sigma(x, y) = (a - x, b - y), tau(x, y) = (a - y, x)):
  SW: the corner at d_a, the bottom wall (profile at x = 2 + d_a + n, n = 0..k-5) and its terminal line at a - 2;
  SE: the same in local coordinates with d_b and m, mapped by tau (the local bottom wall becomes the right wall);
  NE, NW: the sigma-images of SW and SE; Lebesgue measure (counted separately) on [9/5, a - 9/5] x [9/5, b - 9/5].

Checks for every (d_a, d_b) in {d0, d1}^2 and every (k, m) given:
  R2   total mass + (a - 2 alpha)(b - 2 alpha) = ab - 2S(d_a) - 2S(d_b); densities >= 0; support in the container;
       invariance under sigma
  R1a  the corner window [0, 24/5]^2 of SW equals the local model at d_a; that of SE (pulled back by tau) equals
       the local model at d_b
  R1b  on the quarter box [0, a/2 + 3/4] x [0, b/2 + 3/4] the measure equals the local model of SW at d_a
       (both walls extended periodically); likewise for SE in its local coordinates, on [0, b/2 + 3/4] x [0, a/2 + 3/4]
  R1c  the inner periods of the bottom and right walls equal the profile after integer shifts; the terminal lines
       have phase 0
  C4   for k = m and d_a = d_b, the measure equals the square construction of validate_family.build

Usage: python3 validate_rect.py family.json [--km 7x7,7x9,9x7,8x11,12x7,7x13]
"""
import argparse
from fractions import Fraction as Q
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'closed-form', 'structure'))
from validate_family import (ALPHA, WINDOW, Report, build, canonical, clip, corner, decompose,  # noqa: E402
                             difference, equal, load, mass, period, require, saving, shift, transform)

MARGIN = Q(3, 4)   # r = sqrt(2)/2 < 3/4


class Fam:
    def __init__(self, path):
        self.path = path
        self.f = load(path)
        self.profile, self.cf, self.ct = decompose(self.f)
        self.terminal = [s for s in self.profile if s[0] == 'v' and s[1] == 0]

    def corner(self, d):
        return corner(self.f, self.cf, self.ct, d)

    def S(self, d):
        return saving(self.f, self.cf, self.ct, self.profile, d)

    def local(self, d, count):
        """Local model of a corner: the corner pieces, count bottom-wall periods (x = 2 + d + n) and count left-wall
        periods (y = 2 + n, transposed)."""
        out = self.corner(d)
        out += [s for n in range(count) for s in shift(self.profile, 2+d+n)]
        out += transform([s for n in range(count) for s in shift(self.profile, 2+n)], lambda x, y: (y, x))
        return out


def wall(fam, start, count):
    """count periods of the bottom wall at x = start + n, then the terminal line."""
    return [s for n in range(count) for s in shift(fam.profile, start+n)] + shift(fam.terminal, start+count)


def build_rect(fam, k, m, da, db):
    """The global measure without the Lebesgue part."""
    a, b = k+da, m+db
    sw = fam.corner(da) + wall(fam, 2+da, k-4)
    se = transform(fam.corner(db) + wall(fam, 2+db, m-4), lambda x, y: (a-y, x))   # tau
    half = sw + se
    return half + transform(half, lambda x, y: (a-x, b-y))                          # sigma


def window(segs, X, Y):
    """[0, X) x [0, Y) (right and top ends open)."""
    tr = lambda s: transform(s, lambda x, y: (y, x))
    return clip(tr(clip(tr(segs), 0, Y, 0, X, True)), 0, X, 0, Y, True)


def to_se(segs, a):
    return transform(segs, lambda X, Y: (Y, a-X))                                    # tau^-1


def check_case(rep, fam, k, m, da, db):
    a, b = k+da, m+db
    tag = f'k={k}, m={m}, d_a={da}, d_b={db}'
    ss = build_rect(fam, k, m, da, db)

    def total():
        neg = next((s for s in canonical(ss) if s[-1] < 0), None)
        require(neg is None, f'negative density {neg}')
        lhs = mass(ss) + (a-2*ALPHA)*(b-2*ALPHA)
        rhs = a*b - 2*fam.S(da) - 2*fam.S(db)
        require(lhs == rhs, f'total {lhs} != ab - 2S(d_a) - 2S(d_b) = {rhs}')
        equal(ss, clip(ss, 0, a, 0, b), 'support in the container')
        equal(ss, transform(ss, lambda x, y: (a-x, b-y)), 'sigma invariance')
        return f'total = ab - 2*{fam.S(da)} - 2*{fam.S(db)}'
    rep.check(f'R2 {tag}', total)

    def windows():
        require(a-ALPHA >= WINDOW and b-ALPHA >= WINDOW, 'the edge of U lies outside the window')
        equal(window(ss, WINDOW, WINDOW), window(fam.local(da, 4), WINDOW, WINDOW), 'SW window')
        equal(window(to_se(ss, a), WINDOW, WINDOW), window(fam.local(db, 4), WINDOW, WINDOW), 'SE window')
    rep.check(f'R1a {tag} corner windows [0,24/5]^2', windows)

    def quarter():
        box = lambda s, X, Y: clip(s, 0, X, 0, Y)
        X, Y = a/2+MARGIN, b/2+MARGIN
        equal(box(ss, X, Y), box(fam.local(da, max(k, m)), X, Y), 'SW quarter')
        X, Y = b/2+MARGIN, a/2+MARGIN   # SE local coordinates: x along the right wall (length b), y along the bottom (a)
        equal(box(to_se(ss, a), X, Y), box(fam.local(db, max(k, m)), X, Y), 'SE quarter')
    rep.check(f'R1b {tag} quarter boxes: global = local', quarter)

    def walls():
        for segs, d, n_per, label in ((ss, da, k-4, 'bottom'), (to_se(ss, a), db, m-4, 'right')):
            for n in range(1, n_per):
                equal(period(segs, 2+d+n), fam.profile, f'{label} wall period n={n}')
        # Terminal lines: after removing the four corners, the vertical line x = a - R (bottom) and y = b - R (right)
        # is the profile's phase 0 line.
        corners = fam.corner(da) + transform(fam.corner(db), lambda x, y: (a-y, x))
        corners += transform(corners, lambda x, y: (a-x, b-y))
        walls_only = difference(ss, corners)
        got = [s for s in clip(walls_only, a-2, a-2, 0, ALPHA) if s[0] == 'v']
        equal(shift(got, -(a-2)), fam.terminal, 'bottom wall terminal line')
        got = [s for s in clip(to_se(walls_only, a), b-2, b-2, 0, ALPHA) if s[0] == 'v']
        equal(shift(got, -(b-2)), fam.terminal, 'right wall terminal line')
    rep.check(f'R1c {tag} wall shifts and terminal lines', walls)

    if k == m and da == db:
        def c4():
            equal(ss, build(fam.f, fam.profile, fam.cf, fam.ct, da, k), 'agreement with the square construction')
        rep.check(f'C4 {tag} equals the square construction', c4)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('family')
    p.add_argument('--km', default='7x7,7x9,9x7,8x11,12x7,7x13,8x8,10x14', help='(k, m) pairs, e.g. 7x7,7x9')
    args = p.parse_args(argv)
    rep = Report()
    fam = Fam(args.family)
    for k, m in (tuple(int(v) for v in s.split('x')) for s in args.km.split(',')):
        require(k >= 7 and m >= 7, 'k, m >= 7')
        for da in sorted({fam.f['d0'], fam.f['d1']}):
            for db in sorted({fam.f['d0'], fam.f['d1']}):
                check_case(rep, fam, k, m, da, db)
    for d in (fam.f['d0'], fam.f['d1']):
        s = fam.S(d)
        ok = s > Q(3, 4)
        rep.ok &= ok
        print(f'S({d}) = {s} = {float(s):.6f}; S > 3/4: {ok}')
    print('VALIDATE_RECT OK' if rep.ok else 'VALIDATE_RECT FAILED')
    return 0 if rep.ok else 1


if __name__ == '__main__':
    sys.exit(main())
