#!/usr/bin/env python3
"""Float verifier for a packing of k unit n-cubes in [0, s]^n (standard library only).

Input JSON: {"n", "k", "s", "c": [[...]], "R": [[[...]]]}  (R_i columns = cube axes).
Checks: (1) each R_i orthogonal (|R^T R - I| <= tol_orth), (2) every vertex inside [0, s]^n,
(3) every pair separated: there is a candidate axis (generalized cross product of k columns of
R_i and n-1-k columns of R_j, k = 0..n-1) along which the projections do not overlap.
Exit code 0 and prints the minimum margins if all pass. Independent of search.py / geom.py.
"""
import itertools
import json
import math
import sys


def det(M):
    n = len(M)
    if n == 1:
        return M[0][0]
    if n == 2:
        return M[0][0] * M[1][1] - M[0][1] * M[1][0]
    total = 0.0
    for j in range(n):
        minor = [row[:j] + row[j + 1:] for row in M[1:]]
        total += (-1) ** j * M[0][j] * det(minor)
    return total


def gcross(vectors):
    """Generalized cross product of n-1 vectors in R^n."""
    n = len(vectors) + 1
    out = []
    for m in range(n):
        minor = [[v[r] for r in range(n) if r != m] for v in vectors]
        out.append((-1) ** m * det(minor))
    return out


def column(R, m):
    return [R[r][m] for r in range(len(R))]


def verify(data, tol_orth=1e-12):
    n, k, s = data['n'], data['k'], float(data['s'])
    c, R = data['c'], data['R']
    assert len(c) == k and len(R) == k
    worst_orth = 0.0
    for Ri in R:
        for a in range(n):
            for b in range(n):
                dot = sum(Ri[r][a] * Ri[r][b] for r in range(n))
                worst_orth = max(worst_orth, abs(dot - (1.0 if a == b else 0.0)))
    if worst_orth > tol_orth:
        return False, f'orthogonality error {worst_orth:.2e}'
    wall = math.inf
    for i in range(k):
        for signs in itertools.product((-0.5, 0.5), repeat=n):
            for r in range(n):
                v = c[i][r] + sum(R[i][r][m] * signs[m] for m in range(n))
                wall = min(wall, v, s - v)
    if wall < 0:
        return False, f'vertex outside container by {-wall:.2e}'
    pair_margin = math.inf
    for i in range(k):
        for j in range(i + 1, k):
            d = [c[i][r] - c[j][r] for r in range(n)]
            best = -math.inf
            for kk in range(n):
                for ci in itertools.combinations(range(n), kk):
                    for cj in itertools.combinations(range(n), n - 1 - kk):
                        vecs = [column(R[i], m) for m in ci] + [column(R[j], m) for m in cj]
                        a = gcross(vecs)
                        na = math.sqrt(sum(x * x for x in a))
                        if na < 1e-9:
                            continue
                        a = [x / na for x in a]
                        wi = 0.5 * sum(abs(sum(a[r] * R[i][r][m] for r in range(n))) for m in range(n))
                        wj = 0.5 * sum(abs(sum(a[r] * R[j][r][m] for r in range(n))) for m in range(n))
                        gap = abs(sum(a[r] * d[r] for r in range(n))) - wi - wj
                        best = max(best, gap)
            pair_margin = min(pair_margin, best)
            if best < 0:
                return False, f'pair ({i},{j}) overlaps by {-best:.2e}'
    return True, f'ok s={s:.10f} min_wall={wall:.3e} min_pair_gap={pair_margin:.3e} orth={worst_orth:.1e}'


if __name__ == '__main__':
    data = json.load(open(sys.argv[1]))
    ok, msg = verify(data)
    print(msg)
    sys.exit(0 if ok else 1)
