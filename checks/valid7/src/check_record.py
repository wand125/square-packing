"""Re-check a run record of run_all.py, independently of its control flow.

1. The roots tile [0, s]^2 x [U0, U1] (centre boxes x u-intervals), each exactly once, U0 <= -tan(pi/8)... we
   require U0 <= -1/2 and U1 >= 1/2, so the u-range covers more than one period of the square (pi/2).
2. Per root: no uncertified box, no counterexample; the leaves tile the root (exact recursive bisection check:
   every leaf box is obtained by halving).
3. Leaf kinds: EMPTY leaves have no admissible centre (exact: the centre box misses [w/2, s - w/2]^2 where
   w = min width over the u-range); TIERB leaves have a u-range not containing 0 in its interior and their
   components chain from the left end to the right end (each component's left end <= previous right end as
   rational bounds of isolating intervals, first starts at u0, last ends at u1).
Optional --recheck N / --recheck-b N: re-certify N random CORE / TIERB2 leaves (sample drawn with --seed, default a
fresh random seed that is printed).
"""
import sys, json, random, argparse
from fractions import Fraction as F
from tier_a import Cover, wmin, core_bound


def tiles(box, leaves):
    """Exact: the leaf boxes are a bisection partition of box."""
    stack = [(box, leaves)]
    while stack:
        b, L = stack.pop()
        if len(L) == 1 and L[0] == b:
            continue
        if not L:
            return False
        done = False
        for k in (4, 0, 2):            # u, x, y
            m = (b[k] + b[k + 1]) / 2
            lo = [l for l in L if l[k + 1] <= m]
            hi = [l for l in L if l[k] >= m]
            if len(lo) + len(hi) == len(L) and lo and hi:
                b1 = list(b); b1[k + 1] = m
                b2 = list(b); b2[k] = m
                stack += [(tuple(b1), lo), (tuple(b2), hi)]
                done = True
                break
        if not done:
            return False
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('cover')
    ap.add_argument('records', nargs='+', help='one or more record files; together they must tile the domain')
    ap.add_argument('--recheck', type=int, default=0)
    ap.add_argument('--recheck-b', type=int, default=0, help='re-run Tier B on N random TIERB2 leaves')
    ap.add_argument('--seed', type=int, default=None,
                    help='seed of the random leaf samples (default: a fresh random seed, printed; rerun with it to repeat)')
    ap.add_argument('--partial', action='store_true', help='skip the global tiling of the domain')
    ap.add_argument('--claim', choices=['valid', 'tilt'], default='valid',
                    help="valid: centres [0,s]^2, u in [-1/2,1/2] (every angle, Valid7); tilt: centres [0,s/2]^2, "
                         "u from 0 to at least sqrt2-1 (0 < theta <= 45 degrees, e.g. ValidTilt9)")
    a = ap.parse_args()
    cov = Cover(a.cover); s = cov.s
    roots = []; bad = []; kinds = {}; core = []; tb2 = []
    import itertools
    for line in itertools.chain.from_iterable(open(f) for f in a.records):
        r = json.loads(line)
        if 'header' in r:
            continue
        box = tuple(F(v) for v in r['root'])
        roots.append(box)
        if r['uncert'] or r['cex']:
            bad.append((box, 'uncert/cex')); continue
        L = []
        for b, k, info in r['leaves']:
            b = tuple(F(v) for v in b)
            L.append(b); kinds[k] = kinds.get(k, 0) + 1
            x0, x1, y0, y1, u0, u1 = b
            if k == 'EMPTY':
                lo = wmin(u0, u1) / 2
                if not (x1 < lo or x0 > s - lo or y1 < lo or y0 > s - lo):
                    bad.append((b, 'EMPTY has admissible centres'))
            elif k == 'TIERB':
                if u0 < 0 < u1:
                    bad.append((b, 'TIERB contains u=0'))
                prev = u0
                for j, (smp, Lb, Rb) in enumerate(info):
                    Ll, Lr = F(Lb[0]), F(Lb[1]); Rl, Rr = F(Rb[0]), F(Rb[1])
                    if j == 0 and not (Ll == Lr == u0):
                        bad.append((b, 'TIERB first component')); break
                    if j > 0 and not (Ll <= prev):
                        bad.append((b, 'TIERB chain gap')); break
                    if not (Ll <= F(smp) <= Rr):
                        bad.append((b, 'TIERB sample')); break
                    prev = Rr
                if info and not (F(info[-1][2][0]) == F(info[-1][2][1]) == u1):
                    bad.append((b, 'TIERB last component'))
            elif k == 'TIERB2':
                tb2.append(b)
                if u0 < 0 < u1:
                    bad.append((b, 'TIERB2 contains u=0'))
            elif k == 'CORE':
                core.append(b)
            else:
                bad.append((b, 'unknown kind ' + k))
        if not tiles(box, L):
            bad.append((box, 'leaves do not tile the root'))
    # roots tile the domain
    if not a.partial:
        U0 = min(b[4] for b in roots); U1 = max(b[5] for b in roots)
        if a.claim == 'valid':
            CX = s
            if not (U0 <= F(-1, 2) and U1 >= F(1, 2)):
                bad.append(('domain', 'u-range'))
        else:
            CX = s / 2
            if not (U0 == 0 and U1 * U1 + 2 * U1 >= 1):       # u1 >= sqrt2 - 1, i.e. theta up to 45 degrees
                bad.append(('domain', 'u-range'))
        # the roots are exactly the product of three interval partitions: [0,s] (x), [0,s] (y), [U0,U1] (u)
        def partition(ivs, lo, hi):
            ivs = sorted(ivs)
            return bool(ivs) and ivs[0][0] == lo and ivs[-1][1] == hi and \
                all(p[1] == q[0] for p, q in zip(ivs, ivs[1:])) and all(p[0] < p[1] for p in ivs)
        X = {(b[0], b[1]) for b in roots}; Y = {(b[2], b[3]) for b in roots}; U = {(b[4], b[5]) for b in roots}
        if not (partition(X, 0, CX) and partition(Y, 0, CX) and partition(U, U0, U1)):
            bad.append(('domain', 'root intervals are not partitions'))
        prod = {(x[0], x[1], y[0], y[1], u[0], u[1]) for x in X for y in Y for u in U}
        if prod != set(roots) or len(set(roots)) != len(roots):
            bad.append(('domain', 'roots are not exactly the product grid'))
        if any(b[4] < 0 < b[5] for b in roots):
            bad.append(('domain', 'a root contains u = 0 inside'))
    if a.seed is None:
        import secrets
        a.seed = secrets.randbits(63)
    if a.recheck or a.recheck_b:
        print('recheck seed', a.seed)
    rng = random.Random(a.seed)
    if a.recheck:
        for b in rng.sample(core, min(a.recheck, len(core))):
            if not (core_bound(cov, *b) >= 1):
                bad.append((b, 'CORE recheck failed'))
    if a.recheck_b:
        import solver, tier_b2
        from rf import Q
        for b in rng.sample(tb2, min(a.recheck_b, len(tb2))):
            loc = solver.Local(cov, *b[:4])
            r = tier_b2.certify(loc, cov.s, b[:4], Q(b[4].numerator, b[4].denominator),
                                Q(b[5].numerator, b[5].denominator))
            if not r['ok']:
                bad.append((b, 'TIERB2 recheck failed'))
    print('claim', a.claim, 'roots', len(roots), 'leaf kinds', kinds)
    for x in bad[:20]:
        print('BAD', x)
    print('RECORD OK' if not bad else f'RECORD BAD ({len(bad)})')


if __name__ == '__main__':
    main()
