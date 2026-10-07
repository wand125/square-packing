"""Certificate for n = T_{m-1} + 1 at L = m + 2/sqrt3: the unit triangular lattice triangle of side m-2
(T_{m-1} points, weight 1) with the same centroid as the container; all unit-distance pairs listed."""
import json, sys, os
from fractions import Fraction as F
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'checker'))
from q3 import Q3

def q3s(z):
    return f"{z.a}+{z.b}*sqrt3" if z.b != 0 else f"{z.a}"

def make(m):
    s3 = Q3(0, 1)
    L = Q3(m) + s3 * F(2, 3)
    y0 = Q3(F(1, 3)) + s3 / 3
    pts = []
    for r in range(m - 1):                # row r has m-1-r points
        for i in range(m - 1 - r):
            x = Q3(1) + s3 / 3 + Q3(F(r, 2)) + Q3(i)
            y = y0 + s3 * F(r, 2)
            pts.append((x, y))
    pairs = []
    for i in range(len(pts)):
        for j in range(i + 1, len(pts)):
            dx, dy = pts[j][0] - pts[i][0], pts[j][1] - pts[i][1]
            if dx * dx + dy * dy == Q3(1):
                pairs.append([i, j])
    n = len(pts) + 1
    return n, {"L": q3s(L), "symmetry": "D3",
               "points": [{"x": q3s(x), "y": q3s(y), "w": "1"} for x, y in pts], "pairs": pairs}

if __name__ == "__main__":
    m = int(sys.argv[1])
    n, c = make(m)
    json.dump(c, open(sys.argv[2], "w"), indent=1)
    print(f"m={m} n={n} points={len(c['points'])} pairs={len(c['pairs'])} total={len(c['points'])} < n")
