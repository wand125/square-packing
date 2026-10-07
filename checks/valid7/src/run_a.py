"""Adaptive driver for Tier A over a region of (centre x, centre y, u).  Leaves are written as JSON lines."""
import sys, json, time, argparse
from fractions import Fraction as F
from multiprocessing import Pool
from tier_a import Cover, core_bound

COV = None


def init(path):
    global COV
    COV = Cover(path)


def solve_root(args):
    box, maxdepth = args
    t = time.time()
    leaves, uncert, cex = [], [], []
    stack = [(box, 0)]
    while stack:
        (x0, x1, y0, y1, u0, u1), d = stack.pop()
        b = core_bound(COV, x0, x1, y0, y1, u0, u1)
        if b is None:
            leaves.append(((x0, x1, y0, y1, u0, u1), 'EMPTY')); continue
        if b >= 1:
            leaves.append(((x0, x1, y0, y1, u0, u1), 'CORE')); continue
        # exact mass at the middle pose: a counterexample check
        xm, ym, um = (x0 + x1) / 2, (y0 + y1) / 2, (u0 + u1) / 2
        e = core_bound(COV, xm, xm, ym, ym, um, um)
        if e is not None and e < 1:
            cex.append((xm, ym, um, e)); continue
        if d >= maxdepth:
            uncert.append(((x0, x1, y0, y1, u0, u1), float(b))); continue
        wx, wy, wu = x1 - x0, y1 - y0, (u1 - u0) * F(14, 10)
        if wu >= wx and wu >= wy:
            stack += [((x0, x1, y0, y1, u0, um), d + 1), ((x0, x1, y0, y1, um, u1), d + 1)]
        elif wx >= wy:
            stack += [((x0, xm, y0, y1, u0, u1), d + 1), ((xm, x1, y0, y1, u0, u1), d + 1)]
        else:
            stack += [((x0, x1, y0, ym, u0, u1), d + 1), ((x0, x1, ym, y1, u0, u1), d + 1)]
    return box, leaves, uncert, cex, time.time() - t


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('cover')
    ap.add_argument('--centers', nargs=4, default=None)
    ap.add_argument('--u', nargs=2, default=['-1/2', '1/2'])
    ap.add_argument('--pitch', default='1/10')
    ap.add_argument('--ubins', type=int, default=16)
    ap.add_argument('--depth', type=int, default=24)
    ap.add_argument('--nproc', type=int, default=1)
    ap.add_argument('--record', default=None)
    a = ap.parse_args()
    cov = Cover(a.cover)
    X0, X1, Y0, Y1 = map(F, a.centers) if a.centers else (F(0), cov.s, F(0), cov.s)
    U0, U1 = map(F, a.u); p = F(a.pitch)
    roots = []
    x = X0
    while x < X1:
        y = Y0
        while y < Y1:
            for k in range(a.ubins):
                roots.append(((x, min(x + p, X1), y, min(y + p, Y1),
                               U0 + (U1 - U0) * k / a.ubins, U0 + (U1 - U0) * (k + 1) / a.ubins), a.depth))
            y += p
        x += p
    out = open(a.record, 'w') if a.record else None
    tot = {'EMPTY': 0, 'CORE': 0}; nunc = ncex = 0; cpu = 0
    with Pool(a.nproc, init, (a.cover,)) as pool:
        for box, leaves, unc, cex, dt in pool.imap_unordered(solve_root, roots, chunksize=4):
            cpu += dt
            for _, k in leaves: tot[k] += 1
            nunc += len(unc); ncex += len(cex)
            if out:
                out.write(json.dumps({'root': [str(v) for v in box], 'cpu': round(dt, 3),
                                      'leaves': [[[str(v) for v in b], k] for b, k in leaves],
                                      'uncert': [[[str(v) for v in b], m] for b, m in unc],
                                      'cex': [[str(v) for v in c] for c in cex]}) + '\n')
            for c in cex:
                print('COUNTEREXAMPLE', [str(v) for v in c], flush=True)
    print(f'roots {len(roots)} leaves {tot} uncertified {nunc} counterexamples {ncex} cpu {cpu:.1f}s')


if __name__ == '__main__':
    main()
