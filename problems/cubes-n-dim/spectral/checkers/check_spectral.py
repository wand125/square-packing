"""Second system: independent checker for spectral certificates in dimension n = 3, 4, 5.
Written from ../n5/supplied/PROOF.md alone; the programs in ../n5/supplied/ were not read before this checker was
written and first run.
Python standard library, exact rationals (fractions.Fraction) and integer square roots.

Claim checked: q(p) = sqrt(2) Tr sqrt(diag(p) - p p^T) - 2 sum_i sqrt(p_i) + 2 > 0 on the ordered simplex
p_1 >= ... >= p_n >= 0, sum p = 1, cut by p_1 <= tau = 1 - 1/(n-1) (the complement is the near-axis lifting).

Checks:
 1. vertices 0..2n-3 are v2, w2, v3, w3, ..., vn, wn exactly (v_k = (1/k,..,1/k,0,..), w_k = (tau, (1-tau)/(k-1),..));
    the initial simplices are the staircase (pulling w2, w3, ...) {v_{j+1},..,v_n, w_2,..,w_{j+1}}, j = 1..n-1, with the
    degenerate ones (zero volume, n = 3 where w2 = v2) left out; their volumes add up to the volume of the truncated simplex.
 2. every vertex lies in the domain (sorted, nonnegative, sum 1, p_1 <= 3/4).
 3. depth-first replay of the records: a record [a, b, m] splits the current simplex along the edge between its
    positions a and b, and vertex m must equal the exact midpoint; the two halves replace position a resp. b by m.
    None is a leaf. All records are consumed and the stack ends empty.
 4. vertex lower bound: qlow(p) = lo(sqrt2) * max(0, Tr A - 5 up(sqrt(delta))) - 2 sum up(sqrt(p_i)) + 2,
    delta = max_i sum_j |C_ij - (A^2)_ij|, A = the rational witness (5 = n in general) of that vertex (any symmetric rational matrix).
 5. leaf: min over its vertices of qlow - sum_i up((sqrt(u_i) - sqrt(l_i))^2 / (2 (sqrt(u_i) + sqrt(l_i)))) > 0.
"""
import json, sys, hashlib
from fractions import Fraction as Fr
from math import isqrt

BITS = 160
SCALE = 1 << BITS

def sqrt_lo(x):
    """lower bound of sqrt(x) for a nonnegative Fraction: floor(sqrt(x) * 2^B) / 2^B"""
    assert x >= 0
    k = isqrt((x.numerator * SCALE * SCALE) // x.denominator)
    return Fr(k, SCALE)

def sqrt_hi(x):
    lo = sqrt_lo(x)
    return lo if lo * lo == x else lo + Fr(1, SCALE)

SQRT2_LO = sqrt_lo(Fr(2))

def det(M):
    """exact determinant (Fraction Gaussian elimination)"""
    M = [row[:] for row in M]; n = len(M); d = Fr(1)
    for c in range(n):
        p = next((r for r in range(c, n) if M[r][c] != 0), None)
        if p is None: return Fr(0)
        if p != c: M[c], M[p] = M[p], M[c]; d = -d
        d *= M[c][c]
        for r in range(c + 1, n):
            f = M[r][c] / M[c][c]
            if f: M[r] = [M[r][k] - f * M[c][k] for k in range(n)]
    return d

def simplex_volume(P):
    """|det| of the n-1 edge vectors in coordinates p_1..p_{n-1} (proportional to the volume in the hyperplane sum p = 1)"""
    m = len(P[0]) - 1
    return abs(det([[P[k][i] - P[0][i] for i in range(m)] for k in range(1, m + 1)]))

def vertex_qlow(p, A):
    n = len(p)
    C = [[(p[i] if i == j else 0) - p[i] * p[j] for j in range(n)] for i in range(n)]
    for i in range(n):
        for j in range(n):
            assert A[i][j] == A[j][i], "witness not symmetric"
    A2 = [[sum(A[i][k] * A[k][j] for k in range(n)) for j in range(n)] for i in range(n)]
    delta = max(sum(abs(C[i][j] - A2[i][j]) for j in range(n)) for i in range(n))
    trA = sum(A[i][i] for i in range(n))
    spec = trA - n * sqrt_hi(delta)
    if spec < 0: spec = Fr(0)
    return SQRT2_LO * spec - 2 * sum(sqrt_hi(x) for x in p) + 2

def chord_loss_hi(l, u):
    """upper bound of (sqrt(u) - sqrt(l))^2 / (2 (sqrt(u) + sqrt(l))), zero if l == u"""
    if l == u: return Fr(0)
    num = sqrt_hi(u) - sqrt_lo(l)
    den = 2 * (sqrt_lo(u) + sqrt_lo(l))
    assert den > 0, "loss denominator not positive"
    return num * num / den

def main(path):
    raw = open(path, "rb").read()
    print("sha256", hashlib.sha256(raw).hexdigest())
    cert = json.loads(raw)
    V = [tuple(Fr(x) for x in v) for v in cert["vertices"]]
    W = cert["witnesses"]; R = cert["records"]; init = cert["initial"]
    assert len(W) == len(V)

    # 1. initial geometry
    n = len(V[0]); tau = 1 - Fr(1, n - 1)
    assert n >= 3 and all(len(v) == n for v in V)
    def vk(k): return tuple([Fr(1, k)] * k + [Fr(0)] * (n - k))
    def wk(k): return tuple([tau] + [(1 - tau) / (k - 1)] * (k - 1) + [Fr(0)] * (n - k))
    expect = []
    for k in range(2, n + 1): expect += [vk(k), wk(k)]
    assert V[:len(expect)] == expect, "initial vertices differ from v2, w2, ..., vn, wn"
    vi = lambda k: 2 * (k - 2); wi = lambda k: 2 * (k - 2) + 1
    stair = [[vi(k) for k in range(j + 1, n + 1)] + [wi(k) for k in range(2, j + 2)] for j in range(1, n)]
    stair = [S for S in stair if simplex_volume([V[i] for i in S]) > 0]
    assert init == stair, f"initial simplices differ from the staircase {stair}"
    full = simplex_volume([vk(k) for k in range(1, n + 1)])
    corner = simplex_volume([vk(1)] + [wk(k) for k in range(2, n + 1)])
    parts = [simplex_volume([V[i] for i in S]) for S in init]
    assert sum(parts) == full - corner, "initial simplices do not add up to the truncated simplex"
    print(f"geometry n={n}, tau={tau}: {len(init)} initial simplices, volumes {[str(x) for x in parts]} sum = full - corner = {full - corner}")

    # 2. domain
    for v in V:
        assert all(v[i] >= v[i + 1] for i in range(n - 1)) and v[n - 1] >= 0 and sum(v) == 1 and v[0] <= tau, "vertex outside domain"

    # 4. vertex bounds
    qlow = []
    for i, (p, A) in enumerate(zip(V, W)):
        qlow.append(vertex_qlow(p, [[Fr(x) for x in row] for row in A]))
    print(f"vertices: {len(V)}, min vertex q lower bound {float(min(qlow)):.6g}")

    # 3 + 5. replay
    stack = [list(s) for s in init]   # depth first; the last pushed is processed first
    ri = 0; leaves = 0; splits = 0; minslack = None; maxdepth = 0
    stack = [(s, 0) for s in stack]
    while stack:
        S, depth = stack.pop()
        maxdepth = max(maxdepth, depth)
        assert ri < len(R), "records exhausted before the subdivision ended"
        rec = R[ri]; ri += 1
        if rec is None:
            loss = sum(chord_loss_hi(min(V[k][i] for k in S), max(V[k][i] for k in S)) for i in range(n))
            slack = min(qlow[k] for k in S) - loss
            assert slack > 0, f"leaf {ri - 1} not certified"
            minslack = slack if minslack is None or slack < minslack else minslack
            leaves += 1
        else:
            a, b, m = rec
            assert 0 <= a < n and 0 <= b < n and a != b
            mid = tuple((V[S[a]][i] + V[S[b]][i]) / 2 for i in range(n))
            assert V[m] == mid, f"record {ri - 1}: vertex {m} is not the midpoint"
            c1 = S[:]; c1[a] = m
            c2 = S[:]; c2[b] = m
            stack.append((c1, depth + 1)); stack.append((c2, depth + 1))
            splits += 1
    assert ri == len(R), "unused records"
    print(f"records {len(R)}: splits {splits}, leaves {leaves}, max depth {maxdepth}")
    print(f"min leaf slack {float(minslack):.6g} (> 1/5000000: {minslack > Fr(1, 5000000)})")
    print(f"PASS: q(p) > 0 on the ordered simplex in dimension {n} with p_1 <= {tau}")

if __name__ == "__main__":
    main(sys.argv[1])
