"""Point-measure LP for squintan: weights on candidate points so that every closed unit square in the
right isosceles triangle T_L = conv{(0,0), (L,0), (0,L)} captures >= 1, total weight minimal.

Floats only (guidance).  The written certificate must be checked with checker/check.py.

Candidates: exact Q(sqrt2) points from
  - the rational grid of step 1/k inside T_L (--grid k),
  - the 45-degree grid of step 1/k anchored at the hypotenuse midpoint (--grid45 k),
  - --extra "x,y;x,y;..." (Q2 strings),
closed under the reflection (x, y) -> (y, x) unless --nosym.
Poses: theta grid on [0, pi/4] (D1) or [0, pi/2) (--nosym), centre grid; then a cutting-plane loop adds
random poses whose float capture is < 1 (refined by a local search towards the worst capture).
Weights are rounded up to multiples of 1/--den, so the captures only grow.

Usage: python lp_points.py n "<L>" --out cert.json [--grid 4] [--grid45 0] [--rounds 40]
"""
import argparse, json, math, os, sys, time
from fractions import Fraction as F
import numpy as np
from scipy.optimize import linprog
from scipy.sparse import csr_matrix

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "checker"))
from q2 import Q2  # noqa: E402

S2 = Q2(0, 1)


def q2s(z):
    if z.b == 0:
        return f"{z.a}"
    return f"{z.a}{'+' if z.b > 0 else '-'}{abs(z.b)}*sqrt2"


def inside_exact(L, x, y):
    return x >= 0 and y >= 0 and x + y <= L


def candidates(L, grid, grid45, extra, nosym, shifts=0):
    pts = {}

    def add(x, y):
        if inside_exact(L, x, y):
            pts[(x.a, x.b, y.a, y.b)] = (x, y)
            if not nosym:
                pts[(y.a, y.b, x.a, x.b)] = (y, x)

    Lf = float(L)
    if grid:
        m = int(math.ceil(Lf * grid)) + 1
        h = S2 * F(1, 2)
        # the rational grid, translated by (p sqrt2/2, q sqrt2/2), 0 <= p, q <= shifts (mixed packings)
        for p in range(shifts + 1):
            for q in range(shifts + 1):
                for i in range(m):
                    for j in range(m - i):
                        add(Q2(F(i, grid)) + h * p, Q2(F(j, grid)) + h * q)
    if grid45:
        # lattice (L/2, L/2) + a e1 + b e2, e1 = (1,-1)/sqrt2, e2 = (-1,-1)/sqrt2, a, b in (1/k)Z
        h = S2 * F(1, 2)
        m = int(math.ceil(Lf * grid45)) + 2
        for a in range(-m, m + 1):
            for b in range(0, m + 1):
                A, B = F(a, grid45), F(b, grid45)
                x = L * F(1, 2) + h * (A - B)
                y = L * F(1, 2) + h * (-A - B)
                add(x, y)
    for x, y in extra:
        add(x, y)
    P = list(pts.values())
    # orbits
    index = {k: i for i, k in enumerate(pts.keys())}
    orb, orbs = [-1] * len(P), []
    for i, (x, y) in enumerate(P):
        if orb[i] >= 0:
            continue
        o = len(orbs)
        mem = [i]
        orb[i] = o
        if not nosym:
            j = index[(y.a, y.b, x.a, x.b)]
            if orb[j] < 0:
                orb[j] = o
                mem.append(j)
        orbs.append(mem)
    return P, np.array(orb), len(orbs)


def admissible(L, cx, cy, th, tol=1e-12):
    c, s = math.cos(th), math.sin(th)
    for sx in (-.5, .5):
        for sy in (-.5, .5):
            x, y = cx + c * sx - s * sy, cy + s * sx + c * sy
            if x < -tol or y < -tol or x + y > L + tol:
                return False
    return True


def cap_rows(poses, Pf, orb, norb, tol=1e-9):
    # numpy chunks instead of Python lists (memory: about 16 bytes per nonzero)
    R, C, V = [], [], []
    for r, (cx, cy, th) in enumerate(poses):
        c, s = math.cos(th), math.sin(th)
        d = Pf - np.array([cx, cy])
        hit = np.nonzero((np.abs(d[:, 0] * c + d[:, 1] * s) <= .5 + tol) & (np.abs(-d[:, 0] * s + d[:, 1] * c) <= .5 + tol))[0]
        if len(hit) == 0:
            continue
        o, cnt = np.unique(orb[hit], return_counts=True)
        R.append(np.full(len(o), r, dtype=np.int32)); C.append(o.astype(np.int32)); V.append(cnt.astype(np.float32))
    if R:
        R = np.concatenate(R); C = np.concatenate(C); V = np.concatenate(V).astype(float)
    else:
        R = C = np.zeros(0, dtype=np.int32); V = np.zeros(0)
    return csr_matrix((V, (R, C)), shape=(len(poses), norb))


def capture(pose, Pf, wpt, tol=1e-9):
    cx, cy, th = pose
    c, s = math.cos(th), math.sin(th)
    d = Pf - np.array([cx, cy])
    m = (np.abs(d[:, 0] * c + d[:, 1] * s) <= .5 + tol) & (np.abs(-d[:, 0] * s + d[:, 1] * c) <= .5 + tol)
    return wpt[m].sum()


def random_pose(L, rng, thmax):
    # half of the samples touch a wall: the centre lies on an edge of the admissible-centre triangle
    # cx >= h, cy >= h, cx + cy <= L - g (h = (c + s)/2, g = (|c + s| + |c - s|)/2), or near a vertex
    if rng.random() < 0.5:
        th = rng.uniform(0, thmax)
        c, s = math.cos(th), math.sin(th)
        h = (abs(c) + abs(s)) / 2
        g = (abs(c + s) + abs(c - s)) / 2
        m = L - g - h
        if m > h:
            V = [(h, h), (h, m), (m, h)]
            k = rng.integers(3)
            A, B = V[k], V[(k + 1) % 3]
            t = rng.random() if rng.random() < 0.7 else rng.random() * 0.02
            cx, cy = A[0] + t * (B[0] - A[0]), A[1] + t * (B[1] - A[1])
            if admissible(L, cx, cy, th):
                return (cx, cy, th)
    while True:
        th = rng.uniform(0, thmax)
        cx, cy = rng.uniform(0, L, 2)
        if admissible(L, cx, cy, th):
            return (cx, cy, th)


def refine(pose, L, Pf, wpt, rng, steps=200):
    best, bv = pose, capture(pose, Pf, wpt)
    sc = 0.05
    for t in range(steps):
        q = (best[0] + rng.normal(0, sc), best[1] + rng.normal(0, sc), best[2] + rng.normal(0, sc * 0.5))
        if not admissible(L, *q):
            continue
        v = capture(q, Pf, wpt)
        if v < bv - 1e-12 or (v <= bv + 1e-12 and rng.random() < 0.3):
            best, bv = q, v
        if t % 50 == 49:
            sc *= 0.5
    return best, bv


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("n", type=int)
    ap.add_argument("L")
    ap.add_argument("--out", required=True)
    ap.add_argument("--grid", type=int, default=4)
    ap.add_argument("--grid45", type=int, default=0)
    ap.add_argument("--extra", default="")
    ap.add_argument("--shifts", type=int, default=0, help="also the rational grid shifted by multiples of sqrt2/2")
    ap.add_argument("--nosym", action="store_true")
    ap.add_argument("--rounds", type=int, default=40)
    ap.add_argument("--samples", type=int, default=20000, help="random poses tested per round")
    ap.add_argument("--nth", type=int, default=46, help="theta grid size")
    ap.add_argument("--cstep", type=float, default=0.05, help="centre grid step")
    ap.add_argument("--den", type=int, default=2520)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--harvest", default="", help="comma separated checker outputs: sample poses inside their uncertified boxes")
    ap.add_argument("--excl", default="", help="exclusion boxes 'cx,cy,th,dc,dth;...' (floats): poses with |c - c0|_inf <= dc and |theta - th| <= dth (mod pi/2) are exempt")
    ap.add_argument("--excl-stair45", default="", help="'rows,dc,dth': exclusions around a 45-degree staircase with rows rows, rows-2, ..., standing on the hypotenuse")
    ap.add_argument("--price", type=int, default=0, help="column generation: add up to this many points per round where the dual coverage exceeds 1")
    ap.add_argument("--price-den", type=int, default=64, help="new points are snapped to the rational grid (1/den)Z^2")
    ap.add_argument("--save-cands", default="", help="write the candidate points (Q2 strings) here after each pricing round")
    ap.add_argument("--load-cands", default="", help="add the candidate points from this file (written by --save-cands)")
    ap.add_argument("--prune", type=float, default=0.0, help="drop zero-weight orbits whose reduced cost exceeds this (0: never)")
    ap.add_argument("--prune-every", type=int, default=3)
    ap.add_argument("--method", default="highs", help="scipy linprog method: highs, highs-ds or highs-ipm")
    ap.add_argument("--harvest-filter", default="", help="certificate JSON: keep only harvested poses whose capture under its weights is < 1 (keeps the LP small)")
    ap.add_argument("--save-poses", default="", help="write the constraint poses (float triples) here every round")
    ap.add_argument("--load-poses", default="", help="add constraint poses from this file (written by --save-poses)")
    ap.add_argument("--near", default="", help="'frac,dc,dth': this fraction of the random samples is drawn within dc (centre) and dth (angle) of the exclusion-box centres")
    ap.add_argument("--margin", type=float, default=0.0, help="LP constraints count a point only if it lies at least this far inside the square (robustness)")
    ap.add_argument("--harvest-n", type=int, default=3000, help="float samples per uncertified box")
    a = ap.parse_args()
    L = Q2.parse(a.L); Lf = float(L)
    extra = []
    for t in a.extra.split(";"):
        if t.strip():
            xs, ys = t.split(",")
            extra.append((Q2.parse(xs), Q2.parse(ys)))
    if a.load_cands:
        extra += [(Q2.parse(x), Q2.parse(y)) for x, y in json.load(open(a.load_cands))]
    P, orb, norb = candidates(L, a.grid, a.grid45, extra, a.nosym, a.shifts)
    Pf = np.array([(float(x), float(y)) for x, y in P])
    mult = np.bincount(orb, minlength=norb).astype(float)
    print(f"L={Lf:.6f} candidates {len(P)} orbits {norb}", flush=True)
    thmax = math.pi / 2 if a.nosym else math.pi / 4
    poses = []
    for th in np.linspace(0, thmax, a.nth, endpoint=not a.nosym):
        for cx in np.arange(0, Lf + 1e-9, a.cstep):
            for cy in np.arange(0, Lf + 1e-9, a.cstep):
                if admissible(Lf, cx, cy, th):
                    poses.append((cx, cy, th))
    print(f"initial poses {len(poses)}", flush=True)
    rng = np.random.default_rng(a.seed)
    TOL = 1e-9 - a.margin
    EX = []
    for t in a.excl.split(";"):
        if t.strip():
            EX.append(tuple(float(v) for v in t.split(",")))
    if a.excl_stair45:
        rows, dc, dth = a.excl_stair45.split(",")
        rows = int(rows); r2 = math.sqrt(2)
        for j, m in enumerate(range(rows, 0, -2)):
            h = j + 0.5
            for i in range(m):
                aa = -(m - 1) / 2 + i
                EX.append((Lf / 2 + (aa - h) / r2, Lf / 2 + (-aa - h) / r2, math.pi / 4, float(dc), float(dth)))
    if EX and not a.nosym:
        EX += [(y, x, (math.pi / 2 - th), dc, dth) for (x, y, th, dc, dth) in EX]
    print(f"exclusion boxes {len(EX)}", flush=True)

    def exempt(p):
        for (x0, y0, t0, dc, dth) in EX:
            dt = (p[2] - t0 + math.pi / 4) % (math.pi / 2) - math.pi / 4
            if abs(p[0] - x0) <= dc and abs(p[1] - y0) <= dc and abs(dt) <= dth:
                return True
        return False
    if EX:
        poses = [p for p in poses if not exempt(p)]
        print(f"poses after exclusions {len(poses)}", flush=True)
    hboxes = []
    for hf in [t for t in a.harvest.split(",") if t.strip()]:
        for b in json.load(open(hf)).get("uncertified_boxes", []):
            hboxes.append(tuple(float(Q2.parse(b[k][i])) for k in ("x", "y", "u") for i in (0, 1)))
    hpool = []
    for (x0, x1, y0, y1, u0, u1) in hboxes:
        for _ in range(a.harvest_n):
            th = 2 * math.atan(rng.uniform(u0, u1))
            p = (rng.uniform(x0, x1), rng.uniform(y0, y1), th)
            if admissible(Lf, *p) and not (EX and exempt(p)):
                hpool.append(p)
    if a.harvest_filter and hpool:
        # keep a harvested pose if it is violated under any of the given certificates
        flt = []
        for hf in a.harvest_filter.split(","):
            hc = json.load(open(hf))
            flt.append((np.array([(float(Q2.parse(p["x"])), float(Q2.parse(p["y"]))) for p in hc["points"]]),
                        np.array([float(F(p["w"])) for p in hc["points"]])))
        hpool = [p for p in hpool if any(capture(p, HP, HW) < 1 - 1e-9 for HP, HW in flt)]
    print(f"harvest boxes {len(hboxes)} poses {len(hpool)}", flush=True)
    poses += hpool
    if a.load_poses:
        lp_ = [tuple(p) for p in json.load(open(a.load_poses))]
        poses += [p for p in lp_ if not (EX and exempt(p))]
        print(f"loaded poses {len(lp_)}", flush=True)
    A = cap_rows(poses, Pf, orb, norb, tol=TOL)
    t0 = time.time()
    w = None
    for r in range(a.rounds):
        res = linprog(mult, A_ub=-A, b_ub=-np.ones(A.shape[0]), bounds=(0, None), method=a.method)
        if res.status != 0:
            print("LP failed", res.message); return 1
        w = res.x
        priced_now = 0
        if a.prune and r % a.prune_every == a.prune_every - 1:
            rc = res.lower.marginals          # reduced costs of the orbit variables
            keep = (w > 1e-9) | (rc < a.prune)
            if (~keep).sum() > 0:
                kept = np.nonzero(keep)[0]
                remap = -np.ones(norb, dtype=int); remap[kept] = np.arange(len(kept))
                sel_pts = [i for i in range(len(P)) if keep[orb[i]]]
                P = [P[i] for i in sel_pts]; orb = remap[orb[sel_pts]]; norb = len(kept)
                Pf = np.array([(float(x), float(yy)) for x, yy in P])
                mult = np.bincount(orb, minlength=norb).astype(float)
                A = cap_rows(poses, Pf, orb, norb, tol=TOL)
                print(f"  pruned to {len(P)} candidates ({norb} orbits)", flush=True)
                res = linprog(mult, A_ub=-A, b_ub=-np.ones(A.shape[0]), bounds=(0, None), method=a.method)
                w = res.x
        if a.price:
            y = -res.ineqlin.marginals
            sel = np.nonzero(y > 1e-7)[0]
            step = 1.0 / a.price_den
            xs = np.arange(0, Lf + 1e-12, step)
            X, Y = np.meshgrid(xs, xs); msk = X + Y <= Lf + 1e-12
            X, Y = X[msk], Y[msk]
            cov = np.zeros(X.shape)
            for i in sel:
                cx, cy, th = poses[i]
                imgs = [(cx, cy, th)] if a.nosym else [(cx, cy, th), (cy, cx, math.pi / 2 - th)]
                for (px, py, pt) in imgs:
                    co, si = math.cos(pt), math.sin(pt); dx = X - px; dy = Y - py
                    cov += ((np.abs(dx * co + dy * si) <= .5 + 1e-9) & (np.abs(-dx * si + dy * co) <= .5 + 1e-9)) * (y[i] / len(imgs))
            order = np.argsort(-cov)
            added = 0
            have = {(float(x), float(yy)) for x, yy in P}
            for k in order:
                if cov[k] <= 1 + 1e-6 or added >= a.price:
                    break
                xq = Q2(F(int(round(X[k] * a.price_den)), a.price_den)); yq = Q2(F(int(round(Y[k] * a.price_den)), a.price_den))
                if not inside_exact(L, xq, yq) or (float(xq), float(yq)) in have:
                    continue
                o = norb; norb += 1
                P.append((xq, yq)); have.add((float(xq), float(yq))); orb = np.append(orb, o)
                if not a.nosym and xq != yq:
                    P.append((yq, xq)); have.add((float(yq), float(xq))); orb = np.append(orb, o)
                added += 1
            priced_now = added
            if added:
                Pf = np.array([(float(x), float(yy)) for x, yy in P])
                mult = np.bincount(orb, minlength=norb).astype(float)
                A = cap_rows(poses, Pf, orb, norb, tol=TOL)
                print(f"round {r} total {res.fun:.6f} priced {added} orbits (max coverage {cov.max():.3f}), candidates {len(P)} t={time.time()-t0:.0f}s", flush=True)
                if a.save_cands:
                    json.dump([[q2s(x), q2s(yy)] for x, yy in P], open(a.save_cands, "w"))
                # the weights w still refer to the old orbits: extend them by zeros for the new ones
                w = np.concatenate([w, np.zeros(norb - len(w))])
        wpt = w[orb]
        new = []
        worst = 9.0
        nfrac, ndc, ndth = (float(v) for v in a.near.split(",")) if a.near else (0.0, 0.0, 0.0)
        for _ in range(a.samples):
            if EX and rng.random() < nfrac:
                x0, y0, t0, _, _ = EX[rng.integers(len(EX))]
                p = (x0 + rng.uniform(-ndc, ndc), y0 + rng.uniform(-ndc, ndc), t0 + rng.uniform(-ndth, ndth))
                if not a.nosym:   # fold the angle into [0, pi/4] with the reflection
                    th = p[2] % (math.pi / 2)
                    p = (p[0], p[1], th) if th <= math.pi / 4 else (p[1], p[0], math.pi / 2 - th)
                if not admissible(Lf, *p):
                    continue
            else:
                p = random_pose(Lf, rng, thmax)
            if EX and exempt(p):
                continue
            v = capture(p, Pf, wpt)
            if v < 1 - 1e-7:
                p, v = refine(p, Lf, Pf, wpt, rng)
                if EX and exempt(p):
                    continue
                new.append(p)
            worst = min(worst, v)
        print(f"round {r} total {res.fun:.6f} poses {A.shape[0]} violated {len(new)} worst {worst:.5f} "
              f"support {(w > 1e-9).sum()} t={time.time()-t0:.0f}s", flush=True)
        if not new and not priced_now:
            break
        poses += new
        if a.save_poses:
            json.dump([list(p) for p in poses], open(a.save_poses, "w"))
        A = cap_rows(poses, Pf, orb, norb, tol=TOL)
    if a.save_poses:
        json.dump([list(p) for p in poses], open(a.save_poses, "w"))
    # rationalise: round weights up to multiples of 1/den (captures only grow)
    pts = []
    tot = F(0)
    for i, (x, y) in enumerate(P):
        wi = w[orb[i]]
        if wi <= 1e-9:
            continue
        q = F(math.ceil(wi * a.den - 1e-6), a.den)
        if q <= 0:
            continue
        tot += q
        pts.append({"x": q2s(x), "y": q2s(y), "w": str(q)})
    print(f"rational total {tot} = {float(tot):.6f} (< n={a.n}: {tot < a.n}), points {len(pts)}")
    json.dump({"L": q2s(L), "symmetry": "none" if a.nosym else "D1", "points": pts}, open(a.out, "w"), indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
