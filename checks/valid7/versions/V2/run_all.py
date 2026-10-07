"""Valid7 driver: Tier A subdivision with Tier B hand-off, over centres x u (u = tan(t/2) in [-1/2, 1/2]).

Roots: centre squares of side `pitch` covering [0, s]^2 x u-bins of [-1/2, 1/2] with 0 as a bin boundary.  Each
root is bisected (largest of x-width, y-width, 1.4 u-width) until Tier A proves it.  A box whose centre width is
<= --bwidth is handed to Tier B (u-interval open at its ends; never contains 0 inside because 0 is a bin
boundary); if Tier B fails the box is split further (centre only) down to --bmin, then reported UNCERTIFIED.
Every leaf is recorded: kind CORE / EMPTY (Tier A) or TIERB (with its components).
Poses at u = 0 itself are covered by upper semicontinuity (DESIGN.md Step 1); u = +-1/2 overlaps a full period.
"""
import sys, json, time, argparse
from fractions import Fraction as F
from multiprocessing import Pool
from tier_a import Cover, core_bound

COV = None
OPT = None


def init(path, opt):
    global COV, OPT
    COV = Cover(path); OPT = opt
    sys.setrecursionlimit(10000)


def tier_b(box):
    """B2 (per candidate, Lemma B3) when no square of the box can meet a polygon; else B1 (full trace)."""
    import solver, tier_b as tb, tier_b2 as tb2
    from rf import Q
    x0, x1, y0, y1, u0, u1 = box
    loc = solver.Local(COV, x0, x1, y0, y1)
    qa, qb = Q(u0.numerator, u0.denominator), Q(u1.numerator, u1.denominator)
    r = tb2.certify(loc, COV.s, (x0, x1, y0, y1), qa, qb, max_runs=OPT['bruns'])
    r['kind'] = 'B2'
    r.setdefault('runs', [])
    return r


def solve_root(box):
    t = time.time()
    leaves, uncert, cex = [], [], []
    stack = [(box, 0)]
    bw, bmin, maxdepth = OPT['bwidth'], OPT['bmin'], OPT['depth']
    while stack:
        (x0, x1, y0, y1, u0, u1), d = stack.pop()
        bx = (x0, x1, y0, y1, u0, u1)
        b = core_bound(COV, *bx)
        if b is None:
            leaves.append((bx, 'EMPTY', None)); continue
        if b >= 1:
            leaves.append((bx, 'CORE', None)); continue
        xm, ym, um = (x0 + x1) / 2, (y0 + y1) / 2, (u0 + u1) / 2
        if um != 0:
            e = core_bound(COV, xm, xm, ym, ym, um, um)
            if e is not None and e < 1:
                cex.append((xm, ym, um, e)); continue
        touches0 = (u0 == 0 or u1 == 0)
        cw = max(x1 - x0, y1 - y0)
        if touches0 and u1 - u0 > OPT['ub0']:
            # keep the slab next to u = 0 thin: split u first
            stack += [((x0, x1, y0, y1, u0, um), d + 1), ((x0, x1, y0, y1, um, u1), d + 1)]
            continue
        handoff = (touches0 and cw <= bw) or (not touches0 and max(cw, (u1 - u0) * F(14, 10)) <= OPT['amin'])
        if handoff and not OPT['tierb']:
            uncert.append((bx, 'needB:%.6f' % float(b))); continue
        if handoff:
            try:
                r = tier_b(bx)
            except Exception as ex:          # never let one box stop the run; it is not certified
                import traceback
                sys.stderr.write('TIERB-ERROR %s %r\n%s\n' % ([str(v) for v in bx], ex, traceback.format_exc()))
                r = {'ok': False, 'why': 'error:' + type(ex).__name__, 'kind': 'B2'}
            if r['ok']:
                if r['kind'] == 'B2':
                    leaves.append((bx, 'TIERB2', {k: r[k] for k in ('lines', 'dropped', 'pairs', 'values', 'edge_runs')
                                                  if k in r}))
                else:
                    leaves.append((bx, 'TIERB', [(x['s'], x['L'], x['R']) for x in r['runs']]))
                continue
            if cw <= bmin:
                w = r.get('pose')
                uncert.append((bx, 'B:' + r['why'] + ('' if not w else ' witness u=%s x=%s y=%s mass=%.9f'
                                                      % (w['u'], w['x'], w['y'], w['mass_float'])))); continue
            if x1 - x0 >= y1 - y0:
                stack += [((x0, xm, y0, y1, u0, u1), d + 1), ((xm, x1, y0, y1, u0, u1), d + 1)]
            else:
                stack += [((x0, x1, y0, ym, u0, u1), d + 1), ((x0, x1, ym, y1, u0, u1), d + 1)]
            continue
        if touches0:
            # the slab next to 0: split the centres only (Tier B takes the whole u-range later)
            if x1 - x0 >= y1 - y0:
                stack += [((x0, xm, y0, y1, u0, u1), d + 1), ((xm, x1, y0, y1, u0, u1), d + 1)]
            else:
                stack += [((x0, x1, y0, ym, u0, u1), d + 1), ((x0, x1, ym, y1, u0, u1), d + 1)]
            continue
        if d >= maxdepth:
            uncert.append((bx, 'A:%.6f' % float(b))); continue
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
    ap.add_argument('--ubins', type=int, default=16, help='bins per side of 0')
    ap.add_argument('--depth', type=int, default=40)
    ap.add_argument('--bwidth', default='1/10', help='hand a box to Tier B at this centre width')
    ap.add_argument('--bmin', default='1/640')
    ap.add_argument('--ub0', default='1/32', help='width of the u-slab next to 0 handled by Tier B')
    ap.add_argument('--amin', default='1/320', help='Tier A gives up (hands to Tier B) when centre width and 1.4 x u-width are both below this')
    ap.add_argument('--bruns', type=int, default=400)
    ap.add_argument('--no-tierb', action='store_true')
    ap.add_argument('--nproc', type=int, default=1)
    ap.add_argument('--record', required=True)
    ap.add_argument('--resume', action='store_true')
    a = ap.parse_args()
    opt = {'ub0': F(a.ub0), 'amin': F(a.amin), 'bwidth': F(a.bwidth), 'bmin': F(a.bmin), 'depth': a.depth, 'bruns': a.bruns, 'tierb': not a.no_tierb}
    cov = Cover(a.cover)
    X0, X1, Y0, Y1 = map(F, a.centers) if a.centers else (F(0), cov.s, F(0), cov.s)
    U0, U1 = map(F, a.u); p = F(a.pitch)
    cuts = sorted({U0, U1} | {U0 + (0 - U0) * k / a.ubins for k in range(a.ubins + 1) if U0 < 0}
                  | {U1 * k / a.ubins for k in range(a.ubins + 1) if U1 > 0})
    cuts = [c for c in cuts if U0 <= c <= U1]
    roots = []
    x = X0
    while x < X1:
        y = Y0
        while y < Y1:
            for lo, hi in zip(cuts, cuts[1:]):
                roots.append((x, min(x + p, X1), y, min(y + p, Y1), lo, hi))
            y += p
        x += p
    import os, hashlib
    done = set()
    if a.resume and os.path.exists(a.record):
        for line in open(a.record):
            try:
                r = json.loads(line)
            except ValueError:
                continue                      # a line cut by a preemption
            if 'root' in r:
                done.add(tuple(r['root']))
        # drop a possibly truncated last line
        good = []
        for line in open(a.record):
            try:
                json.loads(line); good.append(line)
            except ValueError:
                pass
        open(a.record, 'w').writelines(good)
        out = open(a.record, 'a')
    else:
        out = open(a.record, 'w')
        sha = {f: hashlib.sha256(open(f, 'rb').read()).hexdigest()
               for f in [a.cover] + [os.path.join(os.path.dirname(os.path.abspath(__file__)), m) for m in
                                     ('run_all.py', 'tier_a.py', 'tier_b.py', 'tier_b2.py', 'solver.py', 'rf.py',
                                      'cover.py')]}
        out.write(json.dumps({'header': {'argv': sys.argv, 'roots': len(roots), 'sha256': sha}}) + '\n')
    print(f'roots {len(roots)}, already done {len(done)}', flush=True)
    roots = [r for r in roots if tuple(str(v) for v in r) not in done]
    tot = {}; nunc = ncex = 0; cpu = 0.0
    with Pool(a.nproc, init, (a.cover, opt)) as pool:
        for box, leaves, unc, cex, dt in pool.imap_unordered(solve_root, roots, chunksize=1):
            cpu += dt
            for _, k, _ in leaves: tot[k] = tot.get(k, 0) + 1
            nunc += len(unc); ncex += len(cex)
            out.write(json.dumps({'root': [str(v) for v in box], 'cpu': round(dt, 3),
                                  'leaves': [[[str(v) for v in b], k, info] for b, k, info in leaves],
                                  'uncert': [[[str(v) for v in b], m] for b, m in unc],
                                  'cex': [[str(v) for v in c] for c in cex]}) + '\n')
            out.flush()
            for c in cex:
                print('COUNTEREXAMPLE', [str(v) for v in c], flush=True)
            for b, m in unc:
                print('UNCERTIFIED', [str(v) for v in b], m, flush=True)
    print(f'new roots {len(roots)} leaves {tot} uncertified {nunc} counterexamples {ncex} cpu {cpu:.1f}s')
    print('VERIFIED' if nunc == 0 and ncex == 0 else 'NOT VERIFIED')


if __name__ == '__main__':
    main()
