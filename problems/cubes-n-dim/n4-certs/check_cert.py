#!/usr/bin/env python3
"""Exact checker for a packing certificate of k unit n-cubes in the cube [0, s]^n (first system).

Python standard library only; every quantity is a Fraction, floats are used only for printing.
Certificate (JSON): {"n", "k", "s", "A": k skew-symmetric n x n matrices, "c": k centres}, rationals as strings.
Cube i is c_i + R_i [-1/2, 1/2]^n with R_i = (I - A_i)^{-1} (I + A_i) (Cayley transform, orthogonal, det +1).
Accepted if (1) every A_i is skew-symmetric, (2) every cube lies in [0, s]^n, (3) every pair of cubes is
separated by one of the C(2n, n-1) candidate axes (generalized cross products of k' columns of R_i and
n-1-k' columns of R_j, k' = 0..n-1): 2 |a.(c_i - c_j)| >= sum_m |a.R_i[:,m]| + sum_m |a.R_j[:,m]|.
Closed cubes may touch. Acceptance proves s_n(k) <= s. Usage: check_cert.py cert.json [cert2.json ...]
"""
import itertools
import json
import sys
from fractions import Fraction as F


def mat_inv(M):
    n = len(M)
    A = [row[:] + [F(int(i == j)) for j in range(n)] for i, row in enumerate(M)]
    for col in range(n):
        piv = next(r for r in range(col, n) if A[r][col] != 0)
        A[col], A[piv] = A[piv], A[col]
        p = A[col][col]
        A[col] = [x / p for x in A[col]]
        for r in range(n):
            if r != col and A[r][col] != 0:
                f = A[r][col]
                A[r] = [x - f * y for x, y in zip(A[r], A[col])]
    return [row[n:] for row in A]


def mat_mul(A, B):
    return [[sum(A[i][k] * B[k][j] for k in range(len(B))) for j in range(len(B[0]))] for i in range(len(A))]


def cayley(A):
    n = len(A)
    I = [[F(int(i == j)) for j in range(n)] for i in range(n)]
    ImA = [[I[i][j] - A[i][j] for j in range(n)] for i in range(n)]
    IpA = [[I[i][j] + A[i][j] for j in range(n)] for i in range(n)]
    return mat_mul(mat_inv(ImA), IpA)


def det(M):
    n = len(M)
    if n == 1:
        return M[0][0]
    if n == 2:
        return M[0][0] * M[1][1] - M[0][1] * M[1][0]
    return sum((-1) ** j * M[0][j] * det([row[:j] + row[j + 1:] for row in M[1:]]) for j in range(n))


def gcross(vectors):
    n = len(vectors) + 1
    return [(-1) ** m * det([[v[r] for r in range(n) if r != m] for v in vectors]) for m in range(n)]


def column(R, m):
    return [R[r][m] for r in range(len(R))]


def pair_separated(ci, Ri, cj, Rj):
    n = len(ci)
    d = [ci[r] - cj[r] for r in range(n)]
    for kk in range(n):
        for a_i in itertools.combinations(range(n), kk):
            for a_j in itertools.combinations(range(n), n - 1 - kk):
                a = gcross([column(Ri, m) for m in a_i] + [column(Rj, m) for m in a_j])
                if all(x == 0 for x in a):
                    continue
                wi = sum(abs(sum(a[r] * Ri[r][m] for r in range(n))) for m in range(n))
                wj = sum(abs(sum(a[r] * Rj[r][m] for r in range(n))) for m in range(n))
                if 2 * abs(sum(a[r] * d[r] for r in range(n))) >= wi + wj:
                    return True
    return False


def check(cert):
    n, k = cert['n'], cert['k']
    assert n >= 2 and k >= 1 and len(cert['A']) == k and len(cert['c']) == k, 'shape'
    s = F(cert['s'])
    As = [[[F(x) for x in row] for row in A] for A in cert['A']]
    for A in As:
        assert len(A) == n and all(len(row) == n for row in A), 'shape'
        for i in range(n):
            for j in range(n):
                assert A[i][j] == -A[j][i], 'A not skew-symmetric'
    Rs = [cayley(A) for A in As]
    c = [[F(x) for x in row] for row in cert['c']]
    wall = None
    for i in range(k):
        assert len(c[i]) == n, 'shape'
        for r in range(n):
            half = sum(abs(Rs[i][r][m]) for m in range(n)) / 2
            lo, hi = c[i][r] - half, s - (c[i][r] + half)
            assert lo >= 0 and hi >= 0, f'cube {i} outside container'
            wall = min(lo, hi) if wall is None else min(wall, lo, hi)
    for i in range(k):
        for j in range(i + 1, k):
            assert pair_separated(c[i], Rs[i], c[j], Rs[j]), f'pair {i},{j} not separated'
    return s, wall


if __name__ == '__main__':
    bad = 0
    for path in sys.argv[1:]:
        cert = json.load(open(path))
        try:
            s, wall = check(cert)
            print(f"ACCEPT {path}: n={cert['n']} k={cert['k']} s={s} ~ {float(s):.12f} min wall margin {float(wall):.3e}")
        except AssertionError as e:
            print(f'REJECT {path}: {e}')
            bad += 1
    sys.exit(1 if bad else 0)
