"""Second check of the obstacle points of the n = 6 certificates (item 2-g).

Claim for each obstacle point p of a certificate: there is an obstacle square k of that stage such that p lies in
the OPEN square Q_k for every pose of k in its box B_k = {|c - c_k*|_inf <= D, |t - t_k*| <= DTH} that is
admissible (Q_k inside T_v).  For the chain witnesses of case 1,3:0 the pose of square 1 may in addition be
restricted by d_R(P) >= cos(DTH3), P = top-right corner of square 1; this restriction is only tried when the plain
claim fails, and the points that need it are counted.  (Its premise, Step 1 of the triple lemma with t in (0, 1)
on B1 x B3, is checked separately in validity.py.)

Pinwheel poses c_k*, t_k* are recomputed from the corner list in certificates/n6/n6_packing.json.
Proof method: interval branch and bound over (c_x, c_y, t) with outward-rounded float intervals (ival.py).
A sub-box is closed if p is surely inside the open square (both |(p-c).e_i| < 1/2), or the pose is surely not
admissible (some corner surely outside a side of T_v), or (chain) d_R(P) < cos(DTH3) surely.  This does not use
the witness constructions (inner grid, wall or chain rules) at all.
"""
import argparse
import json
import os
import math
import sys
import time
from fractions import Fraction
from multiprocessing import Pool

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from q3 import Q3  # noqa: E402
import ival  # noqa: E402
from ival import I  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
N6 = os.environ.get('N6_CERTS', os.path.join(os.path.dirname(os.path.dirname(HERE)), 'certificates', 'n6'))
SQ3 = ival.I(1.7320508075688772, ival.up(1.7320508075688772))  # contains sqrt3
assert 1.7320508075688772 ** 2 < 3 < ival.up(1.7320508075688772) ** 2


def qI(q):
    """interval enclosing an exact Q3 value."""
    a = I(ival.down(float(q.a)), ival.up(float(q.a)))
    if q.b == 0:
        return a
    return a + I(ival.down(float(q.b)), ival.up(float(q.b))) * SQ3


def fI(fr):
    f = float(fr)
    return I(ival.down(f), ival.up(f))


def pinwheel():
    d = json.load(open(os.path.join(N6, 'n6_packing.json')))
    out = []
    for sq in d['squares']:
        P = [(Q3.parse(x), Q3.parse(y)) for x, y in sq]
        cx = (P[0][0] + P[1][0] + P[2][0] + P[3][0]) * Fraction(1, 4)
        cy = (P[0][1] + P[1][1] + P[2][1] + P[3][1]) * Fraction(1, 4)
        # exact checks: unit square (edges of length 1, right angles)
        for i in range(4):
            ax, ay = P[(i + 1) % 4][0] - P[i][0], P[(i + 1) % 4][1] - P[i][1]
            bx, by = P[(i + 2) % 4][0] - P[(i + 1) % 4][0], P[(i + 2) % 4][1] - P[(i + 1) % 4][1]
            assert (ax * ax + ay * ay - 1).is_zero() and (ax * bx + ay * by).is_zero()
        ex, ey = P[1][0] - P[0][0], P[1][1] - P[0][1]
        t = math.atan2(float(ey.a) + float(ey.b) * math.sqrt(3), float(ex.a) + float(ex.b) * math.sqrt(3))
        t = t % (math.pi / 2)
        k = round(t / (math.pi / 6))
        assert abs(t - k * math.pi / 6) < 1e-12
        # exact: edge direction equals (cos k pi/6, sin k pi/6) up to a quarter turn
        out.append({'c': (cx, cy), 'k6': k % 3})
    return out


def theta_star(k6):
    # k6 * pi/6 as an interval
    return I(ival.down(k6 * ival.PI_LO / 6), ival.up(k6 * ival.PI_HI / 6)) if k6 else I(0.0)


class Ctx:
    def __init__(self, L, sq, D, DTH, chain_c3=None):
        self.L = qI(L)
        self.cx = qI(sq['c'][0])
        self.cy = qI(sq['c'][1])
        self.t0 = theta_star(sq['k6'])
        self.D = fI(D)
        self.DTH = fI(DTH)
        self.c3 = None if chain_c3 is None else ival.cos(fI(chain_c3))


HALF = 0.5


def surely_in(px, py, cx, cy, t):
    c, s = ival.cos(t), ival.sin(t)
    dx, dy = px - cx, py - cy
    a = dx * c + dy * s
    b = dy * c - dx * s
    return a.abs().hi < HALF and b.abs().hi < HALF


def surely_out(ctx, cx, cy, t):
    c, s = ival.cos(t), ival.sin(t)
    L = ctx.L
    for sx, sy in ((HALF, HALF), (HALF, -HALF), (-HALF, HALF), (-HALF, -HALF)):
        vx = cx + c * sx - s * sy
        vy = cy + s * sx + c * sy
        if (-vy).lo > 0:
            return True
        if (vy - SQ3 * vx).lo > 0:                     # left side: sqrt3 x - y >= 0
            return True
        if (vy - SQ3 * (L - vx)).lo > 0:               # right side
            return True
    if ctx.c3 is not None:
        Px = cx + c * HALF - s * HALF
        Py = cy + s * HALF + c * HALF
        dR = (SQ3 * (L - Px) - Py) * 0.5
        if dR.hi < ctx.c3.lo:
            return True
    return False


def prove(px, py, ctx, max_nodes=200000):
    box0 = (I(ctx.cx.lo - ctx.D.hi, ctx.cx.hi + ctx.D.hi), I(ctx.cy.lo - ctx.D.hi, ctx.cy.hi + ctx.D.hi),
            I((ctx.t0 - ctx.DTH).lo, (ctx.t0 + ctx.DTH).hi))
    # the pose box is outward-rounded: it contains B_k
    box0 = (I(ival.down(box0[0].lo), ival.up(box0[0].hi)), I(ival.down(box0[1].lo), ival.up(box0[1].hi)), box0[2])
    stack = [box0]
    nodes = 0
    while stack:
        X, Y, T = stack.pop()
        nodes += 1
        if nodes > max_nodes:
            return False, nodes
        if surely_in(px, py, X, Y, T):
            continue
        if surely_out(ctx, X, Y, T):
            continue
        w = [X.hi - X.lo, Y.hi - Y.lo, (T.hi - T.lo) * 0.8]
        if max(w) < 1e-9:
            return False, nodes
        k = w.index(max(w))
        parts = list((X, Y, T))
        m = parts[k].mid()
        a, b = list(parts), list(parts)
        a[k] = I(parts[k].lo, m)
        b[k] = I(m, parts[k].hi)
        stack.append(tuple(a))
        stack.append(tuple(b))
    return True, nodes


_G = {}


def _job(args):
    idx, px, py = args
    pxI, pyI = qI(px), qI(py)
    for name, ctx in _G['ctxs']:
        ok, n = prove(pxI, pyI, ctx)
        if ok:
            return idx, name, n
    for name, ctx in _G['chain']:
        ok, n = prove(pxI, pyI, ctx)
        if ok:
            return idx, name, n
    return idx, None, 0


def _init(ctxs, chain):
    _G['ctxs'] = ctxs
    _G['chain'] = chain


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('cert')
    ap.add_argument('--obstacles', required=True, help='comma list of square labels')
    ap.add_argument('--D', required=True)
    ap.add_argument('--DTH', required=True)
    ap.add_argument('--chain', help='label:DTH3 of the square that may use the chain restriction, e.g. 1:3/250')
    ap.add_argument('--jobs', type=int, default=4)
    ap.add_argument('--out')
    a = ap.parse_args()
    t0 = time.time()
    c = json.load(open(a.cert))
    L = Q3.parse(c['L'])
    pw = pinwheel()
    D, DTH = Fraction(a.D), Fraction(a.DTH)
    ctxs = [(int(k), Ctx(L, pw[int(k)], D, DTH)) for k in a.obstacles.split(',')]
    chain = []
    if a.chain:
        k, d3 = a.chain.split(':')
        chain = [(f'{k}+chain', Ctx(L, pw[int(k)], D, DTH, Fraction(d3)))]
    pts = [(i, Q3.parse(p['x']), Q3.parse(p['y'])) for i, p in enumerate(c['obstacle_points'])]
    with Pool(a.jobs, initializer=_init, initargs=(ctxs, chain)) as pool:
        res = pool.map(_job, pts, chunksize=4)
    by = {}
    bad = []
    for i, name, n in res:
        if name is None:
            bad.append(i)
        else:
            by[str(name)] = by.get(str(name), 0) + 1
    out = {'cert': os.path.basename(a.cert), 'obstacle_points': len(pts), 'proved_by_square': by,
           'unproved': bad[:50], 'unproved_count': len(bad), 'max_nodes': max(n for _, _, n in res),
           'D': a.D, 'DTH': a.DTH, 'chain': a.chain,
           'status': 'verified' if not bad else 'failed', 'seconds': round(time.time() - t0, 1)}
    js = json.dumps(out, indent=1)
    print(js)
    if a.out:
        open(a.out, 'w').write(js + '\n')


if __name__ == '__main__':
    main()
