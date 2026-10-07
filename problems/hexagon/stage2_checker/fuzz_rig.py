"""Soundness fuzz test for the pruning tests of bb_rig.py.

Builds random nodes (three pose boxes), mostly around the pinwheel and its flex (where the lemma tests act)
and around random near-packings, asks each pruning test, and for every node that a test prunes, samples
configurations inside the node and checks (float, with tolerance) that none of them is three pairwise disjoint
squares inside the hexagon.  A sampled feasible configuration inside a pruned node would be a bug.
Usage: python fuzz_rig.py [--nodes 20000] [--samples 200]
"""
import argparse, math, sys, os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bb_rig as R

R3 = math.sqrt(3); S = (1 + R3) / 2; H = S * R3 / 2
SG = np.array([(-.5, -.5), (.5, -.5), (.5, .5), (-.5, .5)])
NS = np.array([(math.cos(math.pi / 2 + k * math.pi / 3), math.sin(math.pi / 2 + k * math.pi / 3)) for k in range(6)])


def sq(x, y, t):
    c, s = math.cos(t), math.sin(t)
    return np.array([x, y]) + SG @ np.array([[c, s], [-s, c]])


def sep(P, Q):
    best = -9
    for poly in (P, Q):
        for k in range(4):
            e = poly[(k + 1) % 4] - poly[k]; n = np.array([-e[1], e[0]]) / math.hypot(*e)
            a, b = P @ n, Q @ n
            best = max(best, max(b.min() - a.max(), a.min() - b.max()))
    return best


def feasible(poses, tol=1e-9):
    Q = [sq(*p) for p in poses]
    if max(float((q @ NS.T - H).max()) for q in Q) > tol:
        return False
    return all(sep(Q[i], Q[j]) > -tol for i, j in ((0, 1), (0, 2), (1, 2)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--nodes", type=int, default=20000)
    ap.add_argument("--samples", type=int, default=200)
    a = ap.parse_args()
    C = R.setup()
    rng = np.random.default_rng(5)
    Pw = C["Pw"]
    tmp = np.empty((4, 4)); T1 = np.empty((4, 4)); T2 = np.empty((4, 4))
    counts = {"out": 0, "overlap": 0, "lemma": 0, "none": 0}
    bad = 0
    V = np.array([-S / 2, -H])
    for it in range(a.nodes):
        # centre configuration: pinwheel (or an image) flexed by t, plus noise
        t = rng.uniform(-0.05, 0.4) if rng.uniform() < 0.8 else rng.uniform(-0.5, 0.5)
        noise = rng.choice([0.002, 0.01, 0.03, 0.08])
        poses = []
        for i in range(3):
            an = 2 * math.pi * i / 3
            Ri = np.array([[math.cos(an), -math.sin(an)], [math.sin(an), math.cos(an)]])
            c0 = V + np.array([[math.cos(t), -math.sin(t)], [math.sin(t), math.cos(t)]]) @ np.array([.5, .5])
            c = Ri @ c0 + rng.normal(0, noise, 2)
            poses.append((c[0], c[1], an + t + rng.normal(0, noise)))
        # random D6 image and permutation
        g = rng.integers(12); k, mir = g // 2, g % 2 == 1
        al = k * math.pi / 3
        Rg = np.array([[math.cos(al), -math.sin(al)], [math.sin(al), math.cos(al)]])
        img = []
        for (x, y, th) in poses:
            p = np.array([x, y])
            if mir:
                p = np.array([-p[0], p[1]]); th = math.pi - th
            p = Rg @ p; th = th + al
            img.append((p[0], p[1], th % (math.pi / 2)))
        rng.shuffle(img)
        w = rng.choice([0.0005, 0.002, 0.005, 0.01, 0.03])
        bx = np.empty((3, 6))
        for i, (x, y, th) in enumerate(img):
            hw = w * rng.uniform(0.3, 1.0, 3)
            bx[i] = (x - hw[0], x + hw[0], y - hw[1], y + hw[1], th - hw[2], th + hw[2])
        why = None
        if any(R.outside_rig(bx[i], C["H0"], C["H1"], C["NSiv"], C["PI0"], C["PI1"], tmp) for i in range(3)):
            why = "out"
        elif any(R.overlap_rig(bx[i], bx[j], C["PI0"], C["PI1"], T1, T2) for i, j in ((0, 1), (0, 2), (1, 2))):
            why = "overlap"
        elif R.symmetric_rig(bx, Pw, C["V"], C["R3iv"], C["VV"], C["PI0"], C["PI1"], C["CA"], C["SA"], 0.08, 0.05):
            why = "lemma"
        if why is None:
            counts["none"] += 1; continue
        counts[why] += 1
        # check the test's own claim on samples (corners of the boxes included)
        def samp(b):
            if rng.uniform() < 0.3:
                return (b[rng.integers(2)], b[2 + rng.integers(2)], b[4 + rng.integers(2)])
            return (rng.uniform(b[0], b[1]), rng.uniform(b[2], b[3]), rng.uniform(b[4], b[5]))
        for _ in range(a.samples):
            ps = [samp(b) for b in bx]
            Q = [sq(*q) for q in ps]
            outv = [float((q @ NS.T - H).max()) for q in Q]
            if why == "out":
                # some box's every pose must stick out
                if not any(all(float((sq(*samp(bx[i])) @ NS.T - H).max()) > -1e-12 for _r in range(20)) for i in range(3)):
                    bad += 1; print("BUG? out", np.round(ps, 6).tolist(), flush=True); break
                break
            if why == "overlap":
                # some pair of boxes must overlap for every sampled pair of poses
                ok = False
                for i, j in ((0, 1), (0, 2), (1, 2)):
                    if all(sep(sq(*samp(bx[i])), sq(*samp(bx[j]))) < 1e-12 for _r in range(30)):
                        ok = True; break
                if not ok:
                    bad += 1; print("BUG? overlap", np.round(ps, 6).tolist(), flush=True)
                break
            if why == "lemma":
                if max(outv) <= 1e-12:              # contained configuration: some pair must intersect
                    if all(sep(Q[i], Q[j]) > 1e-12 for i, j in ((0, 1), (0, 2), (1, 2))):
                        bad += 1; print("BUG? lemma: contained disjoint configuration", np.round(ps, 6).tolist(), flush=True); break
                    counts["lemma_contained_checked"] = counts.get("lemma_contained_checked", 0) + 1
    print(f"nodes {a.nodes}: pruned by out {counts['out']}, overlap {counts['overlap']}, lemma {counts['lemma']}, "
          f"not pruned {counts['none']}; contained samples checked in lemma-pruned nodes {counts.get('lemma_contained_checked', 0)}; "
          f"violations of a test's claim: {bad}")


if __name__ == "__main__":
    main()
