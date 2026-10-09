"""Point-measure LP for the right isosceles container: weights on candidate points so that every closed unit square in the
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

Usage: python3 lp_points.py n "<L>" --out cert.json [--grid 4] [--grid45 0] [--rounds 40]
"""
import argparse, json, math, os, sys, time
from fractions import Fraction as F
import numpy as np
from scipy.optimize import linprog
from scipy.sparse import csr_matrix

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "checker"))
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
    rows, cols, vals = [], [], []
    for r, (cx, cy, th) in enumerate(poses):
        c, s = math.cos(th), math.sin(th)
        d = Pf - np.array([cx, cy])
        hit = np.nonzero((np.abs(d[:, 0] * c + d[:, 1] * s) <= .5 + tol) & (np.abs(-d[:, 0] * s + d[:, 1] * c) <= .5 + tol))[0]
        o, cnt = np.unique(orb[hit], return_counts=True)
        rows += [r] * len(o); cols += o.tolist(); vals += cnt.tolist()
    return csr_matrix((np.array(vals, float), (rows, cols)), shape=(len(poses), norb))


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
    ap.add_argument("--harvest-n", type=int, default=3000, help="float samples per uncertified box")
    a = ap.parse_args()
    L = Q2.parse(a.L); Lf = float(L)
    extra = []
    for t in a.extra.split(";"):
        if t.strip():
            xs, ys = t.split(",")
            extra.append((Q2.parse(xs), Q2.parse(ys)))
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
    hboxes = []
    for hf in [t for t in a.harvest.split(",") if t.strip()]:
        for b in json.load(open(hf)).get("uncertified_boxes", []):
            hboxes.append(tuple(float(Q2.parse(b[k][i])) for k in ("x", "y", "u") for i in (0, 1)))
    hpool = []
    for (x0, x1, y0, y1, u0, u1) in hboxes:
        for _ in range(a.harvest_n):
            th = 2 * math.atan(rng.uniform(u0, u1))
            p = (rng.uniform(x0, x1), rng.uniform(y0, y1), th)
            if admissible(Lf, *p):
                hpool.append(p)
    print(f"harvest boxes {len(hboxes)} poses {len(hpool)}", flush=True)
    poses += hpool
    A = cap_rows(poses, Pf, orb, norb)
    t0 = time.time()
    w = None
    for r in range(a.rounds):
        res = linprog(mult, A_ub=-A, b_ub=-np.ones(A.shape[0]), bounds=(0, None), method="highs")
        if res.status != 0:
            print("LP failed", res.message); return 1
        w = res.x
        wpt = w[orb]
        new = []
        worst = 9.0
        for _ in range(a.samples):
            p = random_pose(Lf, rng, thmax)
            v = capture(p, Pf, wpt)
            if v < 1 - 1e-7:
                p, v = refine(p, Lf, Pf, wpt, rng)
                new.append(p)
            worst = min(worst, v)
        print(f"round {r} total {res.fun:.6f} poses {A.shape[0]} violated {len(new)} worst {worst:.5f} "
              f"support {(w > 1e-9).sum()} t={time.time()-t0:.0f}s", flush=True)
        if not new:
            break
        poses += new
        A = cap_rows(poses, Pf, orb, norb)
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
