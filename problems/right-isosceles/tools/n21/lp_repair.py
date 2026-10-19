"""Point LP with rows for degenerate poses of a leg-frame D1 certificate (n = 15, 2026-10-13).

At a pose where points sit exactly on the edges of the square (theta = 0, centre on x = k + 1/2 or y = j + 1/2), the
checker needs one set of points that is inside for every pose of a small box around it.  The box rows of this LP count
exactly what the checker can prove there:
  - points strictly inside the square, and edge points that stay inside on the whole quarter box (dx, dy of fixed
    signs, theta >= 0 small; to first order a left point (k, s) stays inside iff theta (s - cy) >= dx, so it is robust
    when dx <= 0 and s > cy; right points when dx >= 0 and s < cy; bottom points (s, j) when dy <= 0 and s < cx; top
    points when dy >= 0 and s > cx);
  - chord pairs (k, s)-(k + 1, s) and (s, j)-(s, j + 1) (Lemma P: one of them is inside), counted with a variable
    m <= w_p, m <= w_q; no point is in two counted pairs.
Rows: crossings (k + 1/2, j + 1/2) for every quarter, and slabs x = k + 1/2 (y = j + 1/2 by symmetry) at heights on a
1/16 grid for dx of both signs.  Ordinary pose rows (capture >= 1) come from a grid and a cutting-plane loop as in
lp_points.py.  Floats only: the certificate written here must be checked with checker/check.py.

Usage: python3 lp_repair.py base.json out.json [--rounds 30] [--grid 8] [--poses-out P.json --resume P.json]
With --poses-out the poses added by the cutting planes are saved after every round; rerunning with --resume on the same
file continues from the next round (the initial grid and the box rows are rebuilt; they are deterministic).
"""
import argparse, json, math, os, sys, time
from fractions import Fraction as F
import numpy as np
from scipy.optimize import linprog
from scipy.sparse import csr_matrix, hstack, vstack, coo_matrix

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "checker"))
from q2 import Q2  # noqa: E402
import lp_points as LPP  # noqa: E402

E = 1e-9


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("base")
    ap.add_argument("out")
    ap.add_argument("--grid", type=int, default=8)
    ap.add_argument("--rounds", type=int, default=30)
    ap.add_argument("--samples", type=int, default=20000)
    ap.add_argument("--nth", type=int, default=46)
    ap.add_argument("--cstep", type=float, default=0.05)
    ap.add_argument("--den", type=int, default=2520)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--box-need", type=float, default=1.0, help="right-hand side of the box rows")
    ap.add_argument("--slab-step", type=int, default=16)
    ap.add_argument("--save", default="", help="write the LP solution after every round (JSON)")
    ap.add_argument("--resume", default="", help="pose file written by an earlier run (--poses-out): continue with its poses")
    ap.add_argument("--poses-out", default="", help="write the added poses after every round (resumable)")
    ap.add_argument("--stop-at", type=float, default=0.0, help="stop (exit 3) once the LP total reaches this value: "
                    "the LP total only grows with more rows, so no point certificate on this grid has total below it")
    ap.add_argument("--cross-grid", type=int, default=0, help="also box rows at every theta = 0 crossing (i/G, j/G) of the "
                    "1/G grid, boundary included (wedged against a side; n = 21, 10/15), all admissible quarters")
    ap.add_argument("--all-pairs", action="store_true", help="chord pairs at distance 1 on every grid line, not only on the "
                    "integer lines (Lemma P holds for any pair with |pq| <= 1)")
    a = ap.parse_args()
    base = json.load(open(a.base))
    L = Q2.parse(base["L"]); Lf = float(L)
    extra = [(Q2.parse(p["x"]), Q2.parse(p["y"])) for p in base["points"]]
    P, orb, norb = LPP.candidates(L, a.grid, 0, extra, False, 0)
    Pf = np.array([(float(x), float(y)) for x, y in P])
    mult = np.bincount(orb, minlength=norb).astype(float)
    key = {(round(x, 9), round(y, 9)): i for i, (x, y) in enumerate(Pf)}
    print(f"L={Lf} candidates {len(P)} orbits {norb}", flush=True)

    # ---- chord pairs on the lattice lines: (k, s)-(k+1, s) and (s, j)-(s, j+1), not at corners of the line pair
    pairs = []
    for i, (x, y) in enumerate(Pf):
        for (dx, dy) in ((1, 0), (0, 1)):
            j = key.get((round(x + dx, 9), round(y + dy, 9)))
            if j is None:
                continue
            on_line = abs(x - round(x)) < E if dx else abs(y - round(y)) < E
            if on_line or a.all_pairs:
                pairs.append((i, j))
    print(f"lattice chord pairs {len(pairs)}", flush=True)
    pidx = {pr: n for n, pr in enumerate(pairs)}

    # ---- box rows: list of (point index list, pair index list)
    def box_row(C, sx, sy):
        Cx, Cy = C
        x0, y0 = Cx - .5, Cy - .5
        pts, prs = [], []
        robust = set()
        for i, (x, y) in enumerate(Pf):
            if not (x0 - E <= x <= x0 + 1 + E and y0 - E <= y <= y0 + 1 + E):
                continue
            inx, iny = x0 + E < x < x0 + 1 - E, y0 + E < y < y0 + 1 - E
            if inx and iny:
                robust.add(i); continue
            onL, onR, onB, onT = abs(x - x0) < E, abs(x - x0 - 1) < E, abs(y - y0) < E, abs(y - y0 - 1) < E
            ok = True
            if onL: ok &= (sx < 0 and y > Cy + E)
            if onR: ok &= (sx > 0 and y < Cy - E)
            if onB: ok &= (sy < 0 and x < Cx - E)
            if onT: ok &= (sy > 0 and x > Cx + E)
            if ok and (onL or onR or onB or onT):
                robust.add(i)
        used = set(robust)
        for n, (i, j) in enumerate(pairs):
            if i in used or j in used:
                continue
            xi, yi = Pf[i]; xj, yj = Pf[j]
            horiz = abs(yi - yj) < E
            if horiz:
                if not (abs(min(xi, xj) - x0) < E and y0 + E < yi < y0 + 1 - E):
                    continue
            else:
                if not (abs(min(yi, yj) - y0) < E and x0 + E < xi < x0 + 1 - E):
                    continue
            prs.append(n); used |= {i, j}
        return sorted(robust), prs

    rows = []
    adm = lambda cx, cy: LPP.admissible(Lf, cx, cy, 0.0, tol=1e-9)
    for k in range(1, int(Lf)):
        for j in range(1, int(Lf)):
            C = (k + .5, j + .5)
            if not adm(*C):
                continue
            for sx in (-1, 1):
                for sy in (-1, 1):
                    if adm(C[0] + sx * 1e-6, C[1] + sy * 1e-6):
                        rows.append(box_row(C, sx, sy))
    if a.cross_grid:
        G2, seen = a.cross_grid, {(k + .5, j + .5) for k in range(1, int(Lf)) for j in range(1, int(Lf))}
        for i in range(int(Lf * G2) + 1):
            for j in range(int(Lf * G2) + 1):
                C = (i / G2, j / G2)
                if C in seen or not adm(*C):
                    continue
                for sx in (-1, 1):
                    for sy in (-1, 1):
                        if adm(C[0] + sx * 1e-6, C[1] + sy * 1e-6):
                            rows.append(box_row(C, sx, sy))
    ncross = len(rows)
    for k in range(1, int(Lf)):
        for t in range(int(Lf * a.slab_step) + 1):
            cy = t / a.slab_step
            if abs(cy - round(cy - .5) - .5) < E:      # crossing heights are already there
                continue
            C = (k + .5, cy)
            for sx in (-1, 1):
                for sy in (-1, 1):
                    if adm(C[0] + sx * 1e-6, cy + sy * 1e-6):
                        rows.append(box_row(C, sx, sy))
    print(f"box rows: crossings {ncross}, slabs {len(rows) - ncross}", flush=True)

    # ---- ordinary pose rows
    thmax = math.pi / 4
    poses = []
    for th in np.linspace(0, thmax, a.nth):
        for cx in np.arange(0, Lf + 1e-9, a.cstep):
            for cy in np.arange(0, Lf + 1e-9, a.cstep):
                if LPP.admissible(Lf, cx, cy, th):
                    poses.append((cx, cy, th))
    added, r0 = [], 0
    if a.resume and os.path.exists(a.resume):
        st = json.load(open(a.resume))
        added, r0 = [tuple(p) for p in st["poses"]], st["round"] + 1
        poses += added
        print(f"resumed: {len(added)} added poses, next round {r0}", flush=True)
    rng = np.random.default_rng(a.seed + r0)
    npair = len(pairs)

    def box_matrix():
        R, Cc, V = [], [], []
        for r, (pts, prs) in enumerate(rows):
            o, cnt = np.unique(orb[pts], return_counts=True) if pts else (np.zeros(0, int), np.zeros(0))
            for oo, cc in zip(o, cnt):
                R.append(r); Cc.append(oo); V.append(float(cc))
            for n in prs:
                R.append(r); Cc.append(norb + n); V.append(1.0)
        return csr_matrix((V, (R, Cc)), shape=(len(rows), norb + npair))

    # pair caps: m_n - w_orb(i) <= 0, m_n - w_orb(j) <= 0
    cr, cc, cv = [], [], []
    for n, (i, j) in enumerate(pairs):
        for q, end in enumerate((i, j)):
            r = 2 * n + q
            cr += [r, r]; cc += [norb + n, orb[end]]; cv += [1.0, -1.0]
    CAP = csr_matrix((cv, (cr, cc)), shape=(2 * npair, norb + npair))
    BOX = box_matrix()
    cost = np.concatenate([mult, np.zeros(npair)])
    t0 = time.time()
    w = None
    A = hstack([LPP.cap_rows(poses, Pf, orb, norb), csr_matrix((len(poses), npair))]).tocsr()
    for r in range(r0, a.rounds):
        t1 = time.time()
        Aub = vstack([-A, -BOX, CAP]).tocsr()
        bub = np.concatenate([-np.ones(A.shape[0]), -a.box_need * np.ones(BOX.shape[0]), np.zeros(CAP.shape[0])])
        res = linprog(cost, A_ub=Aub, b_ub=bub, bounds=(0, None), method="highs")
        if res.status != 0:
            print("LP failed", res.message); return 1
        w = res.x[:norb]
        wpt = w[orb]
        t2 = time.time()
        new, worst = [], 9.0
        for _ in range(a.samples):
            p = LPP.random_pose(Lf, rng, thmax)
            v = LPP.capture(p, Pf, wpt)
            if v < 1 - 1e-7:
                p, v = LPP.refine(p, Lf, Pf, wpt, rng)
                new.append(p)
            worst = min(worst, v)
        print(f"round {r} total {res.fun:.6f} poses {len(poses)} violated {len(new)} worst {worst:.5f} "
              f"lp {t2-t1:.0f}s sample {time.time()-t2:.0f}s t={time.time()-t0:.0f}s ep={time.time():.0f}", flush=True)
        if a.stop_at and res.fun >= a.stop_at:
            print(f"LP total {res.fun:.6f} >= {a.stop_at}: no certificate below it on this grid", flush=True); return 3
        if a.save:
            json.dump({"round": r, "total": res.fun, "x": res.x.tolist(), "poses": len(poses)}, open(a.save, "w"))
        if not new:
            break
        poses += new
        added += [tuple(map(float, p)) for p in new]
        if a.poses_out:
            json.dump({"round": r, "poses": added}, open(a.poses_out + ".tmp", "w"))
            os.replace(a.poses_out + ".tmp", a.poses_out)
        A = vstack([A, hstack([LPP.cap_rows(new, Pf, orb, norb), csr_matrix((len(new), npair))])]).tocsr()
    # rational weights (round up) and the counted pairs
    pts, tot, newidx = [], F(0), {}
    for i, (x, y) in enumerate(P):
        wi = w[orb[i]]
        if wi <= 1e-9:
            continue
        q = F(math.ceil(wi * a.den - 1e-6), a.den)
        newidx[i] = len(pts)
        tot += q
        pts.append({"x": LPP.q2s(x), "y": LPP.q2s(y), "w": str(q)})
    m = res.x[norb:]
    used = {(i, j) for n, (i, j) in enumerate(pairs) if m[n] > 1e-9 and i in newidx and j in newidx}
    img = lambda i: key[(round(Pf[i][1], 9), round(Pf[i][0], 9))]
    used |= {tuple(sorted((img(i), img(j)))) for i, j in used if img(i) in newidx and img(j) in newidx}
    out_pairs = sorted({tuple(sorted((newidx[i], newidx[j]))) for i, j in used})
    print(f"rational total {tot} = {float(tot):.6f}, points {len(pts)}, lattice pairs used {len(out_pairs)}")
    json.dump({"L": base["L"], "symmetry": "D1", "points": pts, "pairs": [list(t) for t in out_pairs]}, open(a.out, "w"), indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
