"""Second system: exact checker for the positive C5 saved tree (positive_c5_exact_tree.json.gz).
Written from supplied/general_dimension/positive_c5_certificate_proof.md only; the supplied replay and generator
were not read.
Python standard library, exact rationals.

usage: python3 -I check_c5.py positive_c5_exact_tree.json.gz   (do not use -O)

Domain: u = (1, x, y, z, w), 1 >= x >= y >= z >= w >= 0, i.e. the 4-simplex with vertices (0000), (1000), (1100),
(1110), (1111) in (x, y, z, w). Preorder records: ['s', i, j] splits the edge between positions i and j at its
midpoint (child with position i replaced pushed first, child with position j replaced pushed second, so visited
first); ['a'] is an analytic near-axis leaf: sum over the four tail coordinates of (max over the cell)^2 <= 1/100;
['f', h] is a fixed-flow leaf: h_ij in [0, 1] for i = 0..4, j < i, r_ij = (1 - h^2)/(1 + h^2), r_ji = 2h/(1 + h^2),
r_ii = 0, and for d = m / M (m the centroid of the cell's vertices with the leading 1, M >= |m| rational) every row
i and every vertex w satisfy sum_j (d_j + r_ij - 1) w_j >= 0.
"""
import gzip, json, sys, hashlib
from fractions import Fraction as Fr
from math import isqrt

BITS = 128

def sqrt_hi(x):
    k = isqrt((x.numerator << (2 * BITS)) // x.denominator)
    lo = Fr(k, 1 << BITS)
    return lo if lo * lo == x else lo + Fr(1, 1 << BITS)

def main(path):
    raw = open(path, "rb").read()
    print("tree sha256 (compressed)", hashlib.sha256(raw).hexdigest())
    print("checker sha256", hashlib.sha256(open(__file__, "rb").read()).hexdigest())
    R = json.loads(gzip.decompress(raw))
    one = Fr(1); zero = Fr(0)
    init = [tuple([one] * k + [zero] * (4 - k)) for k in range(5)]
    stack = [(init, 0)]; ri = 0; counts = {"s": 0, "a": 0, "f": 0}; maxd = 0; vol = Fr(0)
    while stack:
        S, d = stack.pop(); maxd = max(maxd, d)
        assert ri < len(R), "records exhausted"
        rec = R[ri]; ri += 1
        if rec[0] == "s":
            _, i, j = rec
            assert 0 <= i < 5 and 0 <= j < 5 and i != j
            m = tuple((S[i][t] + S[j][t]) / 2 for t in range(4))
            c1 = list(S); c1[i] = m; c2 = list(S); c2[j] = m
            stack.append((c1, d + 1)); stack.append((c2, d + 1))
        elif rec[0] == "a":
            assert len(rec) == 1
            assert sum(max(v[t] for v in S) ** 2 for t in range(4)) <= Fr(1, 100), f"record {ri - 1}: analytic leaf too far from the axis"
            vol += Fr(1, 2 ** d)
        elif rec[0] == "f":
            h = [Fr(x) for x in rec[1]]; assert len(h) == 10
            r = [[zero] * 5 for _ in range(5)]; k = 0
            for i in range(5):
                for j in range(i):
                    hh = h[k]; k += 1
                    assert 0 <= hh <= 1
                    r[i][j] = (1 - hh * hh) / (1 + hh * hh); r[j][i] = 2 * hh / (1 + hh * hh)
                    assert r[i][j] ** 2 + r[j][i] ** 2 == 1
            W = [(one,) + v for v in S]
            m = [sum(w[t] for w in W) / 5 for t in range(5)]
            Mx = sqrt_hi(sum(x * x for x in m)); assert Mx > 0 and Mx * Mx >= sum(x * x for x in m)
            dv = [x / Mx for x in m]
            for i in range(5):
                for w in W:
                    assert sum((dv[t] + r[i][t] - 1) * w[t] for t in range(5)) >= 0, f"record {ri - 1}: demand fails"
            vol += Fr(1, 2 ** d)
        else:
            raise AssertionError(f"unknown record {rec}")
        counts[rec[0]] += 1
    assert ri == len(R), "unused records"
    assert vol == 1
    print(f"records {len(R)} {counts}, max depth {maxd}, covered relative volume {vol}")
    print("PASS: positive C5 holds on every cell (fixed flows and analytic near-axis cells)")

if __name__ == "__main__":
    main(sys.argv[1])
