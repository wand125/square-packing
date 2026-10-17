"""Second system: exact checker for the dimension-six cap and strip certificates.
Written from the prose of the supplied proof (supplied/d6_proof_handoff/PROOF.md, supplied/d6_spectral/EDGE_BOUND.md,
the two certificate READMEs and the determinant/exterior notes) only; none of the supplied programs was read.
Python standard library, exact rationals (fractions.Fraction) and integer roots.

usage: python3 -I check_d6.py cap|strip certificate.json   (do not use -O, which disables the assertions)

Claim checked, on the sorted domain p_1 >= ... >= p_6 >= 0, sum p = 1, with p_1 <= 13/20 (cap) or
13/20 <= p_1 <= 159/200 (strip):  L - 2(sum sqrt p_i - 1) > 0, where L is bounded below by the bound of each leaf.
Leaf bounds (type: lower bound A(p) of L, extra interpolation loss beyond the square-root chord loss E_sqrt):
 0: sqrt2 Tr sqrt(B) + R/2,                      sum_{i<j} D_i D_j / 8
 1: sqrt2 Tr sqrt(B) + (sqrt(1 + 18 R) - 1)/9,   sum_{i<j} D_i D_j / 4
 2: 10 (prod p)^(1/10)
 3: 8 ((p_5 + p_6) p_1 p_2 p_3 p_4)^(1/8)
 5: sum_k c_k H_k, H_k = ((k+1) e_{k+1}(p) / M_k)^(1/(2k)), M = (1/2, 1/4, 1/8, 9/256, 6/1024), with a recorded
    facet a (a_k >= 0, sum_k a_k binom(m,k)/m^(2k) <= 1 for m = 1..5) and tangent point t; c_k must not exceed
    2k a_k t_k^(2k-1) / (1 + sum_k (2k-1) a_k t_k^(2k)).
 R = sum of the ten smallest pair products p_i p_j; B = diag(p) - pp^T; Tr sqrt(B) >= Tr A - 6 sqrt(delta) for the
 rational symmetric witness A, delta = max row sum |B - A^2|.
Leaf accepted iff min over its vertices of [A_lo(v) - 2 sum up(sqrt v_i) + 2] - E_sqrt - extra > 0.
Initial cover: the five recorded simplices lie in the domain, have pairwise separating hyperplanes (staircase
structure), and their volumes add up to the exact domain volume.
"""
import json, sys, hashlib, time
from fractions import Fraction as Fr
from math import isqrt, comb, prod
from itertools import combinations

N = 6
BITS = 128
SC = 1 << BITS

def iroot(n, k):
    """floor(n^(1/k)) for an integer n >= 0"""
    if n < 2: return n
    x = 1 << ((n.bit_length() + k - 1) // k)
    while True:
        y = ((k - 1) * x + n // x ** (k - 1)) // k
        if y >= x: break
        x = y
    while x ** k > n: x -= 1
    while (x + 1) ** k <= n: x += 1
    return x

def root_lo(x, k):
    """lower bound of x^(1/k) for a Fraction x >= 0, on the grid 2^-BITS"""
    assert x >= 0
    return Fr(iroot((x.numerator << (BITS * k)) // x.denominator, k), SC)

def root_hi(x, k):
    lo = root_lo(x, k)
    return lo if lo ** k == x else lo + Fr(1, SC)

SQ_LO = {}; SQ_HI = {}
def sqlo(x):
    r = SQ_LO.get(x)
    if r is None: r = SQ_LO[x] = root_lo(x, 2)
    return r
def sqhi(x):
    r = SQ_HI.get(x)
    if r is None: r = SQ_HI[x] = root_hi(x, 2)
    return r

SQRT2_LO = root_lo(Fr(2), 2)
M = [None, Fr(1, 2), Fr(1, 4), Fr(1, 8), Fr(9, 256), Fr(6, 1024)]

def esym(p, k):
    return sum(prod(c) for c in combinations(p, k))

def det(Mx):
    Mx = [r[:] for r in Mx]; n = len(Mx); d = Fr(1)
    for c in range(n):
        piv = next((r for r in range(c, n) if Mx[r][c] != 0), None)
        if piv is None: return Fr(0)
        if piv != c: Mx[c], Mx[piv] = Mx[piv], Mx[c]; d = -d
        d *= Mx[c][c]
        for r in range(c + 1, n):
            f = Mx[r][c] / Mx[c][c]
            if f: Mx[r] = [Mx[r][j] - f * Mx[c][j] for j in range(n)]
    return d

def vol(P):   # |det| of edge vectors in coordinates p_1..p_5 (proportional to volume in the hyperplane sum p = 1)
    return abs(det([[P[k][i] - P[0][i] for i in range(N - 1)] for k in range(1, N)]))

def hyperplane(P):
    """normal (c, c0) with c.x = c0 through 5 points P in coordinates p_1..p_5, exact (cofactor expansion)"""
    rows = [[x[i] for i in range(N - 1)] + [Fr(1)] for x in P]
    c = []
    for j in range(N):   # cofactors of the 5x6 matrix rows, giving a vector orthogonal to all rows
        sub = [[r[i] for i in range(N) if i != j] for r in rows]
        c.append((-1) ** j * det(sub))
    return c   # sum_i c_i x_i + c_5 * 1 = 0 on the hyperplane

def side(c, x):
    return sum(c[i] * x[i] for i in range(N - 1)) + c[N - 1]

class Checker:
    def __init__(self, kind, cert):
        self.kind = kind
        self.V = [tuple(Fr(s) for s in v) for v in cert["vertices"]]
        self.W = cert.get("witnesses") or cert.get("spectral_witnesses")
        assert len(self.W) == len(self.V)
        self.R = cert["records"]; self.init = cert["initial"]
        self.facets = [[Fr(s) for s in f] for f in cert.get("facets", [])]
        self.tangents = cert.get("tangents", [])
        self.cache = {}
        self.base_c = {}

    # ---------- geometry ----------
    def check_geometry(self):
        V = self.V; c1 = Fr(13, 20); c2 = Fr(159, 200)
        def vk(k): return tuple([Fr(1, k)] * k + [Fr(0)] * (N - k))
        def wk(c, k): return tuple([c] + [(1 - c) / (k - 1)] * (k - 1) + [Fr(0)] * (N - k))
        if self.kind == "cap":
            lo, hi = Fr(0), c1
            expect = []
            for k in range(2, N + 1): expect += [vk(k), wk(c1, k)]
        else:
            lo, hi = c1, c2
            expect = []
            for k in range(2, N + 1): expect += [wk(c1, k), wk(c2, k)]
        assert V[:10] == expect, "initial vertices differ from the stated ones"
        # w_k(c) is the point of the edge e_1 -- v_k with p_1 = c (so conv(e_1, w_2(c), ..., w_6(c)) is {p_1 >= c})
        for c in ((c1,) if self.kind == "cap" else (c1, c2)):
            for k in range(2, N + 1):
                t = (1 - c) / (1 - Fr(1, k))
                pt = tuple((1 - t) * (1 if i == 0 else 0) + t * vk(k)[i] for i in range(N))
                assert pt == wk(c, k)
        assert self.init == [[0, 2, 4, 6, 8, 1], [2, 4, 6, 8, 1, 3], [4, 6, 8, 1, 3, 5], [6, 8, 1, 3, 5, 7], [8, 1, 3, 5, 7, 9]]
        full = vol([vk(k) for k in range(1, N + 1)])
        corner = lambda c: vol([vk(1)] + [wk(c, k) for k in range(2, N + 1)])
        target = full - corner(c1) if self.kind == "cap" else corner(c1) - corner(c2)
        parts = [vol([V[i] for i in S]) for S in self.init]
        assert all(x > 0 for x in parts) and sum(parts) == target, "initial volumes do not add up to the domain"
        # pairwise separation: simplex i = {v_i..v_4} + {w_0..w_i} (bottom index 2k, top index 2k+1)
        bot = lambda k: 2 * k; top = lambda k: 2 * k + 1
        for i in range(5):
            for j in range(i + 1, 5):
                H = [V[top(k)] for k in range(i + 1)] + [V[bot(k)] for k in range(i + 1, 5)]
                c = hyperplane(H)
                assert any(x != 0 for x in c[:N - 1])
                si = [side(c, V[x]) for x in self.init[i]]; sj = [side(c, V[x]) for x in self.init[j]]
                assert (all(x >= 0 for x in si) and all(x <= 0 for x in sj) and max(si) > 0 and min(sj) < 0) or \
                       (all(x <= 0 for x in si) and all(x >= 0 for x in sj) and min(si) < 0 and max(sj) > 0), (i, j)
        for v in V:
            assert all(v[i] >= v[i + 1] for i in range(N - 1)) and v[N - 1] >= 0 and sum(v) == 1, "vertex not sorted/normalized"
            assert lo <= v[0] <= hi, "vertex outside the p_1 range"
        print(f"geometry: 10 initial vertices and 5 simplices as stated, pairwise separated, volumes sum to the "
              f"domain volume {target}; all {len(V)} vertices in the domain", flush=True)

    def check_tangents(self):
        self.coef = []
        for f in self.facets:
            assert len(f) == 5 and all(a >= 0 for a in f)
            for m in range(1, 6):
                assert sum(f[k - 1] * comb(m, k) / Fr(m) ** (2 * k) for k in range(1, 6)) <= 1, "facet violates support inequality"
        for tg in self.tangents:
            a = self.facets[tg["facet"]]; t = [Fr(s) for s in tg["t"]]; c = [Fr(s) for s in tg["coeff"]]
            assert all(x >= 0 for x in t) and len(t) == 5 and len(c) == 5
            D = 1 + sum((2 * k - 1) * a[k - 1] * t[k - 1] ** (2 * k) for k in range(1, 6))
            for k in range(1, 6):
                ck = 2 * k * a[k - 1] * t[k - 1] ** (2 * k - 1) / D
                assert 0 <= c[k - 1] <= ck, "tangent coefficient too large"
            self.coef.append(c)
        print(f"tangents: {len(self.facets)} facets satisfy the support inequalities, {len(self.tangents)} tangent "
              f"coefficient vectors are within the exact tangency bound", flush=True)

    # ---------- vertex values ----------
    def base(self, k):
        r = self.base_c.get(k)
        if r is None:
            r = self.base_c[k] = 2 - 2 * sum(sqhi(x) for x in self.V[k])
        return r

    def qlo(self, k):
        key = ("q", k); r = self.cache.get(key)
        if r is not None: return r
        p = self.V[k]; A = [[Fr(s) for s in row] for row in self.W[k]]
        for i in range(N):
            for j in range(N): assert A[i][j] == A[j][i], "witness not symmetric"
        delta = Fr(0)
        for i in range(N):
            row = Fr(0)
            for j in range(N):
                Bij = (p[i] if i == j else 0) - p[i] * p[j]
                row += abs(Bij - sum(A[i][l] * A[l][j] for l in range(N)))
            delta = max(delta, row)
        tr = sum(A[i][i] for i in range(N)) - N * sqhi(delta)
        r = self.cache[key] = SQRT2_LO * max(tr, Fr(0))
        return r

    def Rv(self, k):
        key = ("R", k); r = self.cache.get(key)
        if r is None:
            p = self.V[k]
            r = self.cache[key] = sum(sorted(p[i] * p[j] for i, j in combinations(range(N), 2))[:10])
        return r

    def value(self, k, typ, tg):
        key = (typ, tg, k); r = self.cache.get(key)
        if r is not None: return r
        p = self.V[k]
        if typ == 0:
            A = self.qlo(k) + self.Rv(k) / 2
        elif typ == 1:
            A = self.qlo(k) + (root_lo(1 + 18 * self.Rv(k), 2) - 1) / 9
        elif typ == 2:
            A = 10 * root_lo(p[0] * p[1] * p[2] * p[3] * p[4] * p[5], 10)
        elif typ == 3:
            A = 8 * root_lo((p[4] + p[5]) * p[0] * p[1] * p[2] * p[3], 8)
        elif typ == 5:
            c = self.coef[tg]; A = Fr(0)
            for kk in range(1, 6):
                if c[kk - 1]:
                    A += c[kk - 1] * root_lo((kk + 1) * esym(p, kk + 1) / M[kk], 2 * kk)
        else:
            raise AssertionError(f"leaf bound type {typ} not supported")
        r = self.cache[key] = A + self.base(k)
        return r

    # ---------- replay ----------
    def loss(self, S):
        E = Fr(0); Ds = []
        for i in range(N):
            l = min(self.V[k][i] for k in S); u = max(self.V[k][i] for k in S)
            Ds.append(u - l)
            if l != u:
                num = sqhi(u) - sqlo(l); den = 2 * (sqlo(u) + sqlo(l))
                assert den > 0
                E += num * num / den
        X = (sum(Ds) ** 2 - sum(d * d for d in Ds)) / 2
        return E, X

    def replay(self):
        R = self.R; V = self.V
        stack = [(list(S), 0) for S in self.init]
        ri = 0; leaves = 0; counts = {}; minslack = None; maxd = 0; used = set(range(10)); t0 = time.time()
        while stack:
            S, d = stack.pop(); maxd = max(maxd, d)
            assert ri < len(R), "records exhausted"
            rec = R[ri]; ri += 1
            if self.kind == "cap":
                split = rec is not None
                if split: a, b, m = rec
                else: typ, tg = 0, None
            else:
                split = rec[0] == "split"
                if split: _, a, b, m = rec
                else:
                    assert rec[0] == "leaf"
                    typ = rec[1]; tg = rec[2] if typ == 5 else None
                    assert len(rec) == (3 if typ == 5 else 2)
            if split:
                assert 0 <= a < N and 0 <= b < N and a != b
                mid = tuple((V[S[a]][i] + V[S[b]][i]) / 2 for i in range(N))
                assert V[m] == mid, f"record {ri - 1}: vertex {m} is not the midpoint"
                used.add(m)
                c1 = S[:]; c1[a] = m; c2 = S[:]; c2[b] = m
                stack.append((c1, d + 1)); stack.append((c2, d + 1))
            else:
                E, X = self.loss(S)
                extra = X / 8 if typ == 0 else X / 4 if typ == 1 else 0
                slack = min(self.value(k, typ, tg) for k in S) - E - extra
                assert slack > 0, f"leaf at record {ri - 1} (type {typ}) not certified: {float(slack)}"
                minslack = slack if minslack is None or slack < minslack else minslack
                leaves += 1; counts[typ] = counts.get(typ, 0) + 1
                if leaves % 200000 == 0:
                    print(f"  {leaves} leaves, {time.time() - t0:.0f} s", flush=True)
        assert ri == len(R), "unused records"
        print(f"records {len(R)}, leaves {leaves} by type {dict(sorted(counts.items()))}, max depth {maxd}, "
              f"vertices used {len(used)} of {len(V)}", flush=True)
        print(f"min leaf slack {float(minslack):.6g} = {minslack}", flush=True)
        return dict(records=len(R), leaves=leaves, by_type={str(k): v for k, v in sorted(counts.items())}, max_depth=maxd,
                    vertices=len(V), vertices_used=len(used), min_leaf_slack=str(minslack), min_leaf_slack_float=float(minslack))

def main(kind, path):
    t0 = time.time()
    raw = open(path, "rb").read(); sha = hashlib.sha256(raw).hexdigest()
    print("certificate sha256", sha, flush=True)
    me = hashlib.sha256(open(__file__, "rb").read()).hexdigest()
    print("checker sha256", me, flush=True)
    cert = json.loads(raw); del raw
    ch = Checker(kind, cert); del cert
    ch.check_geometry()
    ch.check_tangents()
    res = ch.replay()
    res.update(kind=kind, certificate_sha256=sha, checker_sha256=me, seconds=round(time.time() - t0, 1), verdict="PASS")
    print(json.dumps(res), flush=True)
    print(f"PASS: L - 2(sum sqrt p - 1) > 0 on the {kind} domain", flush=True)

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
