"""Exact angular sweep inside a small window of centres and a short u-range [0, E] (used with cellgrid.py).

Claim checked: for every u in [0, E] and every centre c in the closed window W = [x0, x1] x [y0, y1] with Q(c, t(u))
inside T_L and not exempt (pose in a closed exclusion box whose u-range contains [0, E]), the captured weight from
`points` is >= 1.  cellgrid.py covers the same certificate outside W for u in [0, E] (W is passed there as an extra
exempt box), and everything for u >= E.

Method: the line-arrangement sweep of ../sweep.py (exact Q(sqrt3) arithmetic, critical angles = real roots of the
pair and triple determinants, closure by upper semicontinuity).  This version requires that no event polynomial
vanishes in (0, E] (proved by the coefficient test below); then the arrangement has one combinatorial type on
(0, E] and one rational sample checks it.
Two reductions make it local:
 * A line (half-plane A x + B y <= C, polynomials in u) whose slack C - A x - B y has a constant strict sign on the
   4 corners of W for all u in [0, E] is dropped.  The sign is proved by |g_0| > sum_{j>=1} |g_j| E^j for the
   polynomial g(u) at each corner (exact).  The slack is linear in the centre, so the sign is then constant on W.
   A capturer (point, or exclusion box with weight 10) with a line of constant negative sign never captures in W
   and is dropped; one with all lines of positive sign always captures and adds a constant weight.
 * A root of an event polynomial in (0, E] is excluded by the same coefficient test, applied to the rational
   norm of the polynomial after removing the factor u^k.
Closure: a fixed point of W (mid x, just below y1) is proved strictly admissible for every u in [0, E] by the
same coefficient test, so W n D_u has non-empty interior for every u in [0, E].  Hence every admissible,
non-exempt centre of W at any u in [0, E] is a limit of points of open cells at generic u in (0, E), and the
captured weight, being upper semicontinuous, keeps the bound >= 1 there.
"""
import argparse
import hashlib
import json
import os
import sys
import time
from fractions import Fraction
from itertools import combinations

from gmpy2 import mpq

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import sweep as S  # noqa: E402
from q3 import Q3, ZERO, ONE  # noqa: E402

HALF = mpq(1, 2)


def qabs(q):
    return q if q.sign() >= 0 else -q


def const_sign(p, E):
    """+1 / -1 if the Q3 polynomial p has that strict sign on [0, E]; 0 if not proved."""
    if not p:
        return 0
    g0 = p[0]
    if g0.is_zero():
        return 0
    tail = ZERO
    Ek = Q3(1)
    for c in p[1:]:
        Ek = Ek * E
        tail = tail + qabs(c) * Ek
    if (qabs(g0) - tail).sign() > 0:
        return g0.sign()
    return 0


def no_root_in(r, E):
    """True if the rational polynomial r (list, low degree first) has no root in (0, E]."""
    r = list(r)
    while r and r[0] == 0:
        r.pop(0)
    while r and r[-1] == 0:
        r.pop()
    if len(r) <= 1:
        return True
    tail = sum(abs(c) * E ** (j + 1) for j, c in enumerate(r[1:]))
    return abs(r[0]) > tail


def line_poly_at(line, x, y):
    A, B, C = line
    return S.psub(C, S.padd(S.pscale(A, x), S.pscale(B, y)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('cert')
    ap.add_argument('--window', required=True, help='x0,x1,y0,y1 (exact strings)')
    ap.add_argument('--E', required=True, help='u-range [0, E]')
    ap.add_argument('--out')
    a = ap.parse_args()
    t0 = time.time()
    raw = open(a.cert, 'rb').read()
    cert = json.loads(raw)
    L = Q3.parse(cert['L'])
    E = mpq(Fraction(a.E))
    EQ = Q3(E)
    x0, x1, y0, y1 = [Q3.parse(s) for s in a.window.split(',')]
    corners = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    pts = [(Q3.parse(p['x']), Q3.parse(p['y']), mpq(Fraction(p['w']))) for p in cert['points']]
    if cert.get('obstacle_points'):
        raise SystemExit('obstacle points not supported here')
    # admissibility lines (from sweep.build_lines with no points)
    adm_lines, nadm = S.build_lines(L, [])
    adm = [(A, B, C) for A, B, C, _ in adm_lines]
    one = (ONE,)
    win = [((Q3(-1),), (ZERO,), (-x0,)), ((ONE,), (ZERO,), (x1,)),
           ((ZERO,), (Q3(-1),), (-y0,)), ((ZERO,), (ONE,), (y1,))]
    # capturers
    caps = []          # (weight, [lines])
    e1 = (S.C1, S.S1)
    e2 = (S.pneg(S.S1), S.C1)
    halfD = S.pscale(S.D, HALF)
    for px, py, w in pts:
        ls = []
        for ex, ey in (e1, e2):
            ep = S.padd(S.pscale(ex, px), S.pscale(ey, py))
            ls.append((ex, ey, S.padd(ep, halfD)))
            ls.append((S.pneg(ex), S.pneg(ey), S.padd(S.pneg(ep), halfD)))
        caps.append((w, ls, 'point'))
    nbox = 0
    for e in cert.get('exclusions', []):
        u0, u1 = mpq(Fraction(e['u'][0])), mpq(Fraction(e['u'][1]))
        if not (u0 <= 0 and E <= u1):
            continue
        bx0, bx1 = [Q3.parse(s) for s in e['x']]
        by0, by1 = [Q3.parse(s) for s in e['y']]
        ls = [((Q3(-1),), (ZERO,), (-bx0,)), ((ONE,), (ZERO,), (bx1,)),
              ((ZERO,), (Q3(-1),), (-by0,)), ((ZERO,), (ONE,), (by1,))]
        caps.append((mpq(10), ls, 'box'))
        nbox += 1

    def status(line):
        sg = [const_sign(line_poly_at(line, x, y), EQ) for x, y in corners]
        if all(s > 0 for s in sg):
            return 'in'
        if all(s < 0 for s in sg):
            return 'out'
        return 'cross'
    region = []
    for l in adm:
        st = status(l)
        if st == 'out':
            raise SystemExit('window entirely outside a side')
        if st == 'cross':
            region.append(l)
    region += win
    base_w = mpq(0)
    kept = []          # (weight, [line indices])
    lines = list(region)
    nreg = len(region)
    dropped_never = 0
    for w, ls, kind in caps:
        sts = [status(l) for l in ls]
        if 'out' in sts:
            dropped_never += 1
            continue
        cross = [l for l, s in zip(ls, sts) if s == 'cross']
        if not cross:
            base_w += w
            continue
        idx = []
        for l in cross:
            idx.append(len(lines))
            lines.append(l)
        kept.append((w, idx))
    # closure premise: a point of W strictly inside every admissibility line for all u in [0, E]
    mx = (x0 + x1) * HALF
    probe = (mx, y1 - (y1 - y0) * mpq(1, 1000))
    interior_ok = all(const_sign(line_poly_at(l, *probe), EQ) > 0 for l in region[:-4])
    # event polynomials
    polys = []
    n = len(lines)
    for i, j in combinations(range(n), 2):
        Ai, Bi, Ci = lines[i]
        Aj, Bj, Cj = lines[j]
        cross = S.det2(Ai, Bi, Aj, Bj)
        if cross:
            polys.append(cross)
        else:
            for m in (S.det2(Ai, Ci, Aj, Cj), S.det2(Bi, Ci, Bj, Cj)):
                if m:
                    polys.append(m)
    for i, j, k in combinations(range(n), 3):
        Ai, Bi, Ci = lines[i]
        Aj, Bj, Cj = lines[j]
        Ak, Bk, Ck = lines[k]
        d = S.padd(S.padd(S.pmul(Ai, S.det2(Bj, Cj, Bk, Ck)), S.pneg(S.pmul(Bi, S.det2(Aj, Cj, Ak, Ck)))),
                   S.pmul(Ci, S.det2(Aj, Bj, Ak, Bk)))
        if d:
            polys.append(d)
    hard = [p for p in polys if not no_root_in(S.rational_norm(p), E)]
    if hard:
        # this version handles only a root-free (0, E]; choose a smaller E
        raise SystemExit(f'{len(hard)} event polynomials may vanish in (0, E]; use a smaller E')
    samples = [S.simplest_between(Fraction(0), Fraction(E.numerator, E.denominator))]
    # check each sample: region = first nreg lines
    worst = None
    stats = dict(vertices=0, sectors=0)
    for u in samples:
        uq = Q3(mpq(u.numerator, u.denominator))
        Lv = [(S.peval(A, uq), S.peval(B, uq), S.peval(C, uq)) for A, B, C in lines]
        for i, j in combinations(range(n), 2):
            Ai, Bi, Ci = Lv[i]
            Aj, Bj, Cj = Lv[j]
            det = Ai * Bj - Aj * Bi
            if det.is_zero():
                continue
            x = (Ci * Bj - Cj * Bi) / det
            y = (Ai * Cj - Aj * Ci) / det
            sl = [None] * n
            out = False
            for k in range(nreg):
                if k in (i, j):
                    continue
                s_ = (Lv[k][2] - Lv[k][0] * x - Lv[k][1] * y).sign()
                sl[k] = s_
                if s_ < 0:
                    out = True
                    break
            if out:
                continue
            stats['vertices'] += 1
            for k in range(nreg, n):
                if k not in (i, j):
                    sl[k] = (Lv[k][2] - Lv[k][0] * x - Lv[k][1] * y).sign()
            if any(sl[k] == 0 for k in range(n) if k not in (i, j)):
                raise SystemExit(f'non-generic sample u={u}')
            ti = (-Bi, Ai)
            tj = (-Bj, Aj)
            for si in (1, -1):
                for sj in (1, -1):
                    d = (ti[0] * si + tj[0] * sj, ti[1] * si + tj[1] * sj)

                    def inside(k):
                        if k == i or k == j:
                            return (Lv[k][0] * d[0] + Lv[k][1] * d[1]).sign() < 0
                        return sl[k] > 0
                    if not all(inside(k) for k in range(nreg)):
                        continue
                    stats['sectors'] += 1
                    wsum = base_w
                    for w, idx in kept:
                        if all(inside(k) for k in idx):
                            wsum += w
                    if worst is None or wsum < worst:
                        worst = wsum
                        wpos = (str(u), float(x.a) + float(x.b) * 1.7320508075688772,
                                float(y.a) + float(y.b) * 1.7320508075688772)
    res = dict(cert_sha256=hashlib.sha256(raw).hexdigest(), window=a.window, E=a.E, points=len(pts),
               exclusion_boxes_used=nbox, region_lines=nreg, capturer_lines=n - nreg,
               capturers_kept=len(kept), capturers_never=dropped_never, constant_weight=str(base_w),
               event_polys=len(polys), polys_with_possible_root=len(hard),
               samples=len(samples), interior_ok=interior_ok, **stats,
               min_weight=str(worst), min_at=wpos if worst is not None else None,
               status='verified' if (worst is not None and worst >= 1 and interior_ok) else 'failed',
               seconds=round(time.time() - t0, 1))
    js = json.dumps(res, indent=1)
    print(js)
    if a.out:
        open(a.out, 'w').write(js + '\n')


if __name__ == '__main__':
    main()
