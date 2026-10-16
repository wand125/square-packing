#!/usr/bin/env python3
"""Rectangle version of Evan Daniel's k2m4 measure: build mu_{A,B} and check its reduction to the 9-box, exactly.

Inputs (from evand/square-packing, certificates/k2m4, commit 2eb15455; read only as data, no code is used):
  K4_k008_family.txt  (sha256 a66668d9d414ad1cf78b19826ce592c540c9033a0234a06b207eb776b3e8ff0f)
  K4_k008_box9.txt    (sha256 4151d7c4059d5dcf56130c9373e6b5b60635e1a4250f46562d7ecc4d64a27801)

mu_{A,B} for integers A, B >= 8:
  corners: the corner pieces of the family at the four corners, by (x, y), (A - x, y), (x, B - y), (A - x, B - y);
  walls:   the period-1 profile along the bottom (length A), right (B), top (A) and left (B) walls, at positions
           j + p along the wall (j = R, ..., L - R, j + p <= L - R), with wall coordinates (s, d) mapped by
           bottom (s, d) -> (s, d), right -> (A - d, s), top -> (A - s, B - d), left -> (d, B - s);
  Lebesgue measure of density 1 on [a, A - a] x [a, B - a], a = 14/5.

Checks:
  (0) every mass in the family is non-negative;
  (1) for A = B = 9 the measure equals the box cover K4_k008_box9.txt (density on every 1/5-grid cell, and the
      Lebesgue rectangle);
  (2) total mass = AB - 4D (D from the family header) and AB - 4D < AB - 4;
  (3) localisation (Lemma R6): for every 2 x 2 window W = [x0, x0 + 2) x [y0, y0 + 2) on the 1/5 grid inside
      [0, A] x [0, B] (an end of W is closed exactly when it lies on the container wall), with the integer shift
      (s, t) given by shift(), mu_{A,B} restricted to W equals mu_9 restricted to W + (s, t), translated back
      (cell densities and the Lebesgue part).
      The axis-parallel bounding box of a unit square has side <= sqrt 2 < 9/5, so it lies in such a window
      (x0 = its left edge rounded down to the 1/5 grid, capped at A - 2), and its mass depends only on the
      measure in the window.

Usage: python3 k2m4_rect_check.py K4_k008_family.txt K4_k008_box9.txt --ab 8x8,8x9,9x8,8x13,11x14
"""
import argparse
import hashlib
from collections import defaultdict
from fractions import Fraction as F
import math

R, K9 = 3, 9
G = F(1, 5)


def read_family(path):
    prof, corner, a, D = [], [], None, None
    for ln in open(path):
        if ln.startswith('#'):
            if 'with a =' in ln:
                a = F(ln.split('a =')[1].split(';')[0].strip())
            if ln.startswith('# D ='):
                D = F(ln.split('=')[1].split()[0])
            continue
        t = ln.split()
        if not t:
            continue
        rec = (t[0],) + tuple(F(v) for v in t[1:])
        (prof if t[0] in 'hv' else corner).append(rec)
    return a, D, prof, corner


def build(fam, A, B):
    """mu_{A,B} as a list of segments [((x0, y0), (x1, y1), mass)] and the Lebesgue rectangle."""
    a, D, prof, corner = fam
    segs = []
    for o, p, t0, t1, ms in corner:
        for f in (lambda x, y: (x, y), lambda x, y: (A - x, y), lambda x, y: (x, B - y), lambda x, y: (A - x, B - y)):
            segs.append(((f(t0, p), f(t1, p)) if o == 'H' else (f(p, t0), f(p, t1))) + (ms,))
    walls = [(A, lambda s, d: (s, d)), (B, lambda s, d: (A - d, s)),
             (A, lambda s, d: (A - s, B - d)), (B, lambda s, d: (d, B - s))]
    for L, f in walls:
        for j in range(R, L - R + 1):
            for e in prof:
                if e[0] == 'h':
                    _, d, p0, p1, ms = e
                    if j + p1 > L - R:
                        continue
                    segs.append((f(j + p0, d), f(j + p1, d), ms))
                else:
                    _, p, d0, d1, ms = e
                    if j + p > L - R:
                        continue
                    segs.append((f(j + p, d0), f(j + p, d1), ms))
    return segs, (a, A - a, a, B - a)


def cells(segs):
    """Density on each 1/5-grid cell {('h', y, i) or ('v', x, i): density}; the cell starts at i/5."""
    out = defaultdict(F)
    for (x0, y0), (x1, y1), ms in segs:
        if y0 == y1:
            lo, hi, key, c = min(x0, x1), max(x0, x1), 'h', y0
        else:
            assert x0 == x1
            lo, hi, key, c = min(y0, y1), max(y0, y1), 'v', x0
        assert (lo / G).denominator == 1 and (hi / G).denominator == 1 and (c / G).denominator == 1
        dens = ms / (hi - lo)
        for i in range(int(lo / G), int(hi / G)):
            out[(key, c, i)] += dens
    return {k: v for k, v in out.items() if v != 0}


def read_box(path):
    tok = []
    for ln in open(path):
        tok += ln.split('#', 1)[0].split()
    it = iter(tok)
    assert next(it) == 'mixed' and next(it) == '1'
    sn, sd = int(next(it)), int(next(it)); Dd = int(next(it)); Wd = int(next(it))
    assert F(sn, sd) == K9 and int(next(it)) == 0
    segs = []
    for _ in range(int(next(it))):
        X0, Y0, X1, Y1, wm = (int(next(it)) for _ in range(5))
        segs.append(((F(X0, Dd), F(Y0, Dd)), (F(X1, Dd), F(Y1, Dd)), F(wm, Wd)))
    assert int(next(it)) == 1
    kk = int(next(it)); wm = F(int(next(it)), Wd)
    V = [(F(int(next(it)), Dd), F(int(next(it)), Dd)) for _ in range(kk)]
    xs, ys = sorted({v[0] for v in V}), sorted({v[1] for v in V})
    assert len(V) == 4 and len(xs) == 2 and len(ys) == 2 and wm == (xs[1] - xs[0]) * (ys[1] - ys[0])
    return segs, (xs[0], xs[1], ys[0], ys[1])


def window(cm, x0, y0, cx, cy):
    """Cells in the window [x0, x0+2) x [y0, y0+2), relative to its lower-left corner. If cx (cy) is true, the far end
    on that axis is closed too (the window ends on the container wall).

    The bounding box of a unit square has side <= sqrt 2 < 9/5, so with x0 = its left edge rounded down to the 1/5
    grid it lies in [x0, x0+2). If x0 + 2 > L, take x0 = L - 2; the box lies in the container, hence in [L - 2, L]."""
    out = {}
    inx = (lambda c: x0 <= c <= x0 + 2) if cx else (lambda c: x0 <= c < x0 + 2)
    iny = (lambda c: y0 <= c <= y0 + 2) if cy else (lambda c: y0 <= c < y0 + 2)
    for (key, c, i), v in cm.items():
        lo = i * G
        if key == 'h':
            if iny(c) and x0 <= lo and lo + G <= x0 + 2:
                out[(key, c - y0, lo - x0)] = v
        else:
            if inx(c) and y0 <= lo and lo + G <= y0 + 2:
                out[(key, c - x0, lo - y0)] = v
    return out


def leb_window(leb, x0, y0):
    lx0, lx1, ly0, ly1 = leb
    cx = (max(lx0, x0) - x0, min(lx1, x0 + 2) - x0)
    cy = (max(ly0, y0) - y0, min(ly1, y0 + 2) - y0)
    if cx[0] >= cx[1] or cy[0] >= cy[1]:
        return None
    return cx + cy


def shift(z0, L):
    """Integer shift along one axis for the window starting at z0. Windows at the start of the axis stay; windows at
    the end are aligned with the end of the 9-box; middle windows go to the middle of the 9-box.

    Corner mass lies on the line z = R (and L - R) between corner and wall, so a middle window must not be moved
    onto the line z = R of the 9-box: if z0 is not an integer then z0 + s is in (3, 4); if it is, z0 + s = 4
    (the window [4, 6) contains neither z = 3 nor z = 6)."""
    if z0 <= R:
        return 0
    if z0 + 2 > L - R:
        return K9 - L
    return (R if z0 != math.floor(z0) else R + 1) - math.floor(z0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('family'); ap.add_argument('box9')
    ap.add_argument('--ab', default='8x8,8x9,9x8,9x9,8x10,10x8,8x13,13x8,9x12,10x11,11x14,12x15,15x8,14x14')
    args = ap.parse_args()
    for p in (args.family, args.box9):
        print(f'{p}: sha256 {hashlib.sha256(open(p, "rb").read()).hexdigest()}')
    fam = read_family(args.family)
    a, D = fam[0], fam[1]
    ok = True
    # (0) non-negativity (needed to compare masses)
    nonneg = all(e[-1] >= 0 for e in fam[2] + fam[3])
    print(f'(0) all masses in the family are non-negative: {nonneg} ({len(fam[2]) + len(fam[3])} pieces)')
    ok &= nonneg
    # (1) agreement with the box file at 9 x 9
    s9, l9 = build(fam, K9, K9)
    fs, fl = read_box(args.box9)
    c9 = cells(s9)
    same = c9 == cells(fs) and l9 == fl
    print(f'(1) mu_9,9 vs K4_k008_box9.txt: {len(c9)} cells, equal: {same}, Lebesgue {l9}')
    ok &= same
    for ab in args.ab.split(','):
        A, B = (int(v) for v in ab.split('x'))
        assert A >= 2 * R + 2 and B >= 2 * R + 2
        segs, leb = build(fam, A, B)
        cm = cells(segs)
        total = sum(ms for *_, ms in segs) + (leb[1] - leb[0]) * (leb[3] - leb[2])
        tot_ok = total == A * B - 4 * D and total < A * B - 4
        # (3) localisation, window by window
        nwin, bad = 0, []
        for ix in range(0, int((A - 2) / G) + 1):
            x0 = ix * G
            s = shift(x0, A)
            for iy in range(0, int((B - 2) / G) + 1):
                y0 = iy * G
                t = shift(y0, B)
                nwin += 1
                if not (0 <= x0 + s and x0 + s + 2 <= K9 and 0 <= y0 + t and y0 + t + 2 <= K9):
                    bad.append((x0, y0, 'outside')); continue
                cx, cy = x0 + 2 == A, y0 + 2 == B
                if window(cm, x0, y0, cx, cy) != window(c9, x0 + s, y0 + t, cx, cy) or \
                        leb_window(leb, x0, y0) != leb_window(l9, x0 + s, y0 + t):
                    bad.append((x0, y0, s, t))
        print(f'{A}x{B}: total {total} (= AB - 4D and < AB - 4: {tot_ok}), windows {nwin}, mismatched windows {len(bad)}'
              + (f' (e.g. {bad[:3]})' if bad else ''))
        ok &= tot_ok and not bad
    print(f'D = {D} = {float(D):.6f}, 4D = {float(4 * D):.6f} > 4: {4 * D > 4}')
    ok &= 4 * D > 4
    print('K2M4_RECT', 'OK' if ok else 'FAILED')
    return 0 if ok else 1


if __name__ == '__main__':
    raise SystemExit(main())
