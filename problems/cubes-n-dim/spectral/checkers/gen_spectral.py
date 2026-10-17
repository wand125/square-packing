"""First system: generator of spectral certificates for q(p) > 0 in dimension n (n = 3, 4, 5).
Written from the description in ../n5/supplied/PROOF.md (now ../PROOF.md §4–§7); the supplied generator
../n5/supplied/certify.py was not read before this generator was written and first run.

Domain: ordered simplex p_1 >= .. >= p_n >= 0, sum p = 1, p_1 <= tau = 1 - 1/(n-1).
q(p) = sqrt2 Tr sqrt(diag(p) - pp^T) - 2 sum sqrt(p_i) + 2.
Witness at a vertex: A = rational rounding (denominator 2^D) of the float symmetric square root of C = diag(p) - pp^T.
Vertex bound: sqrt2_lo * max(0, Tr A - n * sqrt_up(delta)) - 2 sum sqrt_up(p_i) + 2, delta = max row sum |C - A^2|.
Leaf: min over vertices of the vertex bounds minus sum_i (sqrt u_i - sqrt l_i)^2 / (2 (sqrt u_i + sqrt l_i)) > 0
(upper bound of the loss), otherwise split the longest edge at its midpoint.
Output format (same as the dimension-five certificate): {"initial", "vertices", "witnesses", "records"}; records in
depth-first order (stack; the child with position a replaced is pushed first, the child with position b replaced
is processed first), [a, b, m] for a split, null for a leaf.
Acceptance here is exact (Fraction); floats only propose witnesses and choose edges."""
import os
for v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ[v] = "1"
import sys, json, time, hashlib
from fractions import Fraction as Fr
from math import isqrt
import numpy as np

PREC = 128           # bits of the square-root enclosures
D = 60               # witness denominator 2^D

def rt_floor(x):     # floor(sqrt(x) * 2^PREC) / 2^PREC for x >= 0, as a Fraction
    return Fr(isqrt(x.numerator * (1 << (2 * PREC)) // x.denominator), 1 << PREC)

def rt_ceil(x):
    f = rt_floor(x)
    return f if f * f == x else f + Fr(1, 1 << PREC)

R2_LO = rt_floor(Fr(2))

class Gen:
    def __init__(self, n):
        self.n = n; self.tau = 1 - Fr(1, n - 1)
        self.V = []; self.index = {}; self.W = []; self.qlo = []

    def vertex(self, p):
        p = tuple(p)
        if p in self.index: return self.index[p]
        n = self.n
        pf = np.array([float(x) for x in p]); C = np.diag(pf) - np.outer(pf, pf)
        lam, U = np.linalg.eigh(C); S = (U * np.sqrt(np.clip(lam, 0, None))) @ U.T; S = (S + S.T) / 2
        A = [[Fr(int(round(S[i][j] * 2 ** D)), 2 ** D) for j in range(n)] for i in range(n)]
        for i in range(n):
            for j in range(i): A[i][j] = A[j][i]
        Cx = [[(p[i] if i == j else 0) - p[i] * p[j] for j in range(n)] for i in range(n)]
        delta = Fr(0)
        for i in range(n):
            row = Fr(0)
            for j in range(n):
                row += abs(Cx[i][j] - sum(A[i][k] * A[k][j] for k in range(n)))
            delta = max(delta, row)
        tr = sum(A[i][i] for i in range(n)) - n * rt_ceil(delta)
        q = R2_LO * max(tr, Fr(0)) - 2 * sum(rt_ceil(x) for x in p) + 2
        self.index[p] = len(self.V); self.V.append(p); self.W.append(A); self.qlo.append(q)
        return self.index[p]

    def loss(self, S):
        tot = Fr(0)
        for i in range(self.n):
            l = min(self.V[k][i] for k in S); u = max(self.V[k][i] for k in S)
            if l != u:
                a = rt_ceil(u) - rt_floor(l); b = 2 * (rt_floor(u) + rt_floor(l))
                tot += a * a / b
        return tot

    def run(self, tlimit=1500):
        n = self.n; t0 = time.time()
        for k in range(2, n + 1):   # vertices 0..2n-3: v2, w2, ..., vn, wn (w2 = v2 when n = 3 is kept as a separate entry)
            vk = tuple([Fr(1, k)] * k + [Fr(0)] * (n - k))
            wk = tuple([self.tau] + [(1 - self.tau) / (k - 1)] * (k - 1) + [Fr(0)] * (n - k))
            for p in (vk, wk):
                self.index.pop(p, None)
                self.vertex(p); self.index[p] = len(self.V) - 1
        vi = lambda k: 2 * (k - 2); wi = lambda k: 2 * (k - 2) + 1
        init = [[vi(k) for k in range(j + 1, n + 1)] + [wi(k) for k in range(2, j + 2)] for j in range(1, n)]
        def vol(S):
            M = np.array([[float(self.V[S[k]][i] - self.V[S[0]][i]) for i in range(n - 1)] for k in range(1, n)])
            return abs(np.linalg.det(M))
        init = [S for S in init if vol(S) > 1e-12]
        recs = []; stack = [S[:] for S in init]; leaves = 0; minslack = None; maxd = 0
        stack = [(S, 0) for S in stack]
        while stack:
            S, d = stack.pop(); maxd = max(maxd, d)
            slack = min(self.qlo[k] for k in S) - self.loss(S)
            if slack > 0:
                recs.append(None); leaves += 1
                minslack = slack if minslack is None or slack < minslack else minslack
                continue
            best = None
            for a in range(n):
                for b in range(a + 1, n):
                    L = sum(float(self.V[S[a]][i] - self.V[S[b]][i]) ** 2 for i in range(n))
                    if best is None or L > best[0]: best = (L, a, b)
            _, a, b = best
            m = self.vertex(tuple((self.V[S[a]][i] + self.V[S[b]][i]) / 2 for i in range(n)))
            recs.append([a, b, m])
            c1 = S[:]; c1[a] = m; c2 = S[:]; c2[b] = m
            stack.append((c1, d + 1)); stack.append((c2, d + 1))
            if time.time() - t0 > tlimit: raise SystemExit("time limit")
        cert = {"initial": init,
                "vertices": [[str(x) for x in p] for p in self.V],
                "witnesses": [[[str(x) for x in row] for row in A] for A in self.W],
                "records": recs}
        return cert, dict(n=n, vertices=len(self.V), records=len(recs), leaves=leaves, max_depth=maxd,
                          min_vertex_q=float(min(self.qlo)), min_leaf_slack=float(minslack),
                          seconds=round(time.time() - t0, 1))

if __name__ == "__main__":
    n = int(sys.argv[1]); out = sys.argv[2]
    cert, info = Gen(n).run()
    raw = json.dumps(cert, separators=(",", ":")).encode()
    open(out, "wb").write(raw)
    info["sha256"] = hashlib.sha256(raw).hexdigest()
    print(json.dumps(info))
