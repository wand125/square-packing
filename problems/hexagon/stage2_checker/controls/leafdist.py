"""Max-norm distance (centre x, y and angle) from each recorded leaf to the pinwheel, minimised over the
4 D6-classes of the pinwheel and the 6 labellings."""
import itertools, math, sys
import numpy as np
S = (1 + math.sqrt(3)) / 2; H = S * math.sqrt(3) / 2
def rot(p, a): return (math.cos(a) * p[0] - math.sin(a) * p[1], math.sin(a) * p[0] + math.cos(a) * p[1])
base = [(*rot((-S / 2 + .5, -H + .5), 2 * math.pi * i / 3), 2 * math.pi * i / 3) for i in range(3)]
confs = []
for m in (False, True):
    for k in (0, 1):
        c = []
        for x, y, t in base:
            if m: x, t = -x, -t
            x, y = rot((x, y), k * math.pi / 3); t += k * math.pi / 3
            c.append((x, y, t % (math.pi / 2)))
        confs.append(c)
def dist(b, p):
    d = 0
    for (lo, hi), v in zip(((b[0], b[1]), (b[2], b[3])), p[:2]):
        d = max(d, lo - v, v - hi, 0)
    best = min(max(b[4] - (p[2] + j * math.pi / 2), (p[2] + j * math.pi / 2) - b[5], 0) for j in range(-1, 4))
    return max(d, best)
for f in sys.argv[1:]:
    a = np.load(f); a = a[(a != 0).any(axis=(1, 2))]
    ds = [min(max(dist(L[i], c[s[i]]) for i in range(3)) for c in confs for s in itertools.permutations(range(3))) for L in a]
    print(f"{f}: {len(a)} recorded leaves, max-norm distance to the pinwheel {min(ds):.4f} .. {max(ds):.4f}")
