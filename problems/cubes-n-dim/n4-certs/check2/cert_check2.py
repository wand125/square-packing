"""Second checker for cube-packing certificates in [0, s]^n (SPEC.md section 7, v0.2).

Written from section 7 of the specification only; the first checker's code was not read.

Claim: the k closed unit cubes { c_i + R_i u : u in [-1/2, 1/2]^n }, R_i = (I - A_i)^-1 (I + A_i), lie in
[0, s]^n and no two have intersecting interiors.  Everything is exact (fractions.Fraction); floats are used only
for printing.

Checks, in order (section 7.3):
  1. shape: n >= 2, k >= 1, k matrices n x n and k vectors of length n, all entries strings "p/q" or "p";
  2. A_i skew-symmetric (zero diagonal);
  3. container: c_i[r] - h_i[r] >= 0 and c_i[r] + h_i[r] <= s with h_i[r] = 1/2 sum_m |R_i[r][m]|;
  4. separation of each pair i < j on some candidate axis: the generalized cross product of k' columns of R_i
     and n-1-k' columns of R_j (k' = 0 .. n-1, all choices, C(2n, n-1) axes; zero axes skipped), with
     2 |a.(c_i - c_j)| >= sum_m |a.R_i[:, m]| + sum_m |a.R_j[:, m]|.
  As an extra (not required by the spec) R_i^T R_i = I and det R_i = 1 are also checked.

Output: on success the value of s (exact and float) and the least wall slack, exit code 0.  On failure the item
and the indices, exit code 1.  Exit code 2 for a file that cannot be read as JSON.

usage: python3 cert_check2.py CERT.json [--quiet]
"""
import json
import re
import sys
from fractions import Fraction
from itertools import combinations


class Reject(Exception):
    pass


RAT = re.compile(r'-?[0-9]+(/[0-9]+)?')


def rat(v, where):
    if not isinstance(v, str):
        raise Reject(f'shape: {where} is not a string')
    # section 7.1: entries are the strings "p/q", or "p" for an integer (no decimals, exponents or spaces)
    if not RAT.fullmatch(v):
        raise Reject(f'shape: {where} = {v!r} is not of the form "p/q" or "p"')
    try:
        return Fraction(v)
    except (ValueError, ZeroDivisionError):
        raise Reject(f'shape: {where} = {v!r} is not a rational')


def det(M):
    """Exact determinant by Gaussian elimination."""
    M = [row[:] for row in M]
    n = len(M)
    d = Fraction(1)
    for col in range(n):
        piv = next((r for r in range(col, n) if M[r][col] != 0), None)
        if piv is None:
            return Fraction(0)
        if piv != col:
            M[col], M[piv] = M[piv], M[col]
            d = -d
        p = M[col][col]
        d *= p
        for r in range(col + 1, n):
            f = M[r][col] / p
            if f:
                for c in range(col, n):
                    M[r][c] -= f * M[col][c]
    return d


def solve(Mat, B):
    """X with Mat X = B (square Mat, exact Gauss-Jordan); None if Mat is singular."""
    n = len(Mat)
    W = [Mat[r][:] + B[r][:] for r in range(n)]
    m = len(W[0])
    for col in range(n):
        piv = next((r for r in range(col, n) if W[r][col] != 0), None)
        if piv is None:
            return None
        W[col], W[piv] = W[piv], W[col]
        p = W[col][col]
        W[col] = [x / p for x in W[col]]
        for r in range(n):
            if r != col and W[r][col] != 0:
                f = W[r][col]
                W[r] = [a - f * b for a, b in zip(W[r], W[col])]
    return [row[n:m] for row in W]


def cross(cols, n):
    """Generalized cross product of n-1 vectors in R^n: a_m = (-1)^m det(matrix without row m)."""
    a = []
    for m in range(n):
        minor = [[v[r] for v in cols] for r in range(n) if r != m]
        a.append((-1) ** m * det(minor))
    return a


def dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def check(cert):
    # 1. shape
    try:
        n, k = cert['n'], cert['k']
        A_raw, c_raw, s_raw = cert['A'], cert['c'], cert['s']
    except (KeyError, TypeError) as e:
        raise Reject(f'shape: missing field {e}')
    if not (isinstance(n, int) and not isinstance(n, bool) and n >= 2):
        raise Reject(f'shape: n = {n!r} is not an integer >= 2')
    if not (isinstance(k, int) and not isinstance(k, bool) and k >= 1):
        raise Reject(f'shape: k = {k!r} is not an integer >= 1')
    s = rat(s_raw, 's')
    if not (isinstance(A_raw, list) and len(A_raw) == k):
        raise Reject(f'shape: A does not have k = {k} matrices')
    if not (isinstance(c_raw, list) and len(c_raw) == k):
        raise Reject(f'shape: c does not have k = {k} vectors')
    A, c = [], []
    for i in range(k):
        Ai = A_raw[i]
        if not (isinstance(Ai, list) and len(Ai) == n and all(isinstance(r, list) and len(r) == n for r in Ai)):
            raise Reject(f'shape: A[{i}] is not {n} x {n}')
        A.append([[rat(Ai[p][q], f'A[{i}][{p}][{q}]') for q in range(n)] for p in range(n)])
        ci = c_raw[i]
        if not (isinstance(ci, list) and len(ci) == n):
            raise Reject(f'shape: c[{i}] does not have {n} entries')
        c.append([rat(ci[r], f'c[{i}][{r}]') for r in range(n)])
    # 2. skew-symmetry
    for i in range(k):
        for p in range(n):
            for q in range(p, n):
                if A[i][p][q] != -A[i][q][p]:
                    raise Reject(f'skew: A[{i}][{p}][{q}] != -A[{i}][{q}][{p}]')
    # rotations (Cayley)
    I = [[Fraction(int(p == q)) for q in range(n)] for p in range(n)]
    R = []
    for i in range(k):
        Im = [[I[p][q] - A[i][p][q] for q in range(n)] for p in range(n)]
        Ip = [[I[p][q] + A[i][p][q] for q in range(n)] for p in range(n)]
        Ri = solve(Im, Ip)
        if Ri is None:
            raise Reject(f'rotation: I - A[{i}] is singular')
        # extra: orthogonal with det +1 (follows from skew-symmetry)
        for p in range(n):
            for q in range(n):
                if sum(Ri[r][p] * Ri[r][q] for r in range(n)) != I[p][q]:
                    raise Reject(f'rotation: R[{i}] is not orthogonal')
        if det(Ri) != 1:
            raise Reject(f'rotation: det R[{i}] != 1')
        R.append(Ri)
    # 3. container
    half = Fraction(1, 2)
    hw = [[half * sum(abs(x) for x in R[i][r]) for r in range(n)] for i in range(k)]
    slack = None
    for i in range(k):
        for r in range(n):
            lo = c[i][r] - hw[i][r]
            hi = s - (c[i][r] + hw[i][r])
            if lo < 0:
                raise Reject(f'container: cube {i}, coordinate {r}: c - h = {lo} < 0')
            if hi < 0:
                raise Reject(f'container: cube {i}, coordinate {r}: s - (c + h) = {hi} < 0')
            m = min(lo, hi)
            slack = m if slack is None else min(slack, m)
    # 4. separation
    cols = [[[R[i][r][m] for r in range(n)] for m in range(n)] for i in range(k)]
    axes_tried = 0
    for i in range(k):
        for j in range(i + 1, k):
            d = [c[i][r] - c[j][r] for r in range(n)]
            ok = False
            for kp in range(n - 1, -1, -1):  # face normals first: k' = n-1 (R_i), then k' = 0 (R_j) last
                for ci_ in combinations(range(n), kp):
                    for cj_ in combinations(range(n), n - 1 - kp):
                        a = cross([cols[i][m] for m in ci_] + [cols[j][m] for m in cj_], n)
                        if not any(a):
                            continue
                        axes_tried += 1
                        lhs = 2 * abs(dot(a, d))
                        rhs = sum(abs(dot(a, v)) for v in cols[i]) + sum(abs(dot(a, v)) for v in cols[j])
                        if lhs >= rhs:
                            ok = True
                            break
                    if ok:
                        break
                if ok:
                    break
            if not ok:
                raise Reject(f'separation: cubes {i} and {j} are not separated on any candidate axis')
    return {'n': n, 'k': k, 's': s, 'min_wall_slack': slack, 'axes_tried': axes_tried}


def main(argv):
    if len(argv) < 2:
        print(__doc__.strip().splitlines()[-1])
        return 2
    try:
        cert = json.load(open(argv[1]))
    except (OSError, ValueError) as e:
        print(f'REJECT read: {e}')
        return 2
    try:
        r = check(cert)
    except Reject as e:
        print(f'REJECT {e}')
        return 1
    print(f"ACCEPT n={r['n']} k={r['k']} s={r['s']} (~{float(r['s']):.12g}) "
          f"min_wall_slack={r['min_wall_slack']} (~{float(r['min_wall_slack']):.3g})")
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
