#!/usr/bin/env python3
"""Checker (first system) for exact certificates over the quadratic field Q(sqrt d) (d = 2 or 3) for packings whose best known side is a closed
form such as 2 + 1/sqrt2.  Numbers are pairs [a, b] of rationals meaning a + b*sqrt(d).

Certificate (format "alg-v1"):
  {"format": "alg-v1", "n": 3, "k": 9, "d": 2, "s": ["2", "1/2"],
   "c": [[[a, b], ...], ...],              # k centres, n numbers each
   "R": [[[[a, b], ...], ...], ...]}       # k frames, n x n numbers (columns = cube axes)
Accepted iff (all arithmetic exact in Q(sqrt d)):
  1. every R_i satisfies R_i^T R_i = I (orthogonal; det is not needed, the cube is symmetric);
  2. every cube is inside the container: for every coordinate r, c_i[r] - h_i[r] >= 0 and c_i[r] + h_i[r] <= s,
     where h_i[r] = (1/2) * sum_m |R_i[r][m]|;
  3. every pair i < j is separated by a candidate axis a (generalised cross product of k' columns of R_i and
     n-1-k' columns of R_j, k' = 0..n-1, zero axes skipped): 2|a.(c_i - c_j)| >= sum_m |a.R_i[:,m]| + sum_m |a.R_j[:,m]|.
Sign of a + b*sqrt(d): if a and b have the same sign it is that sign; otherwise compare a^2 with d*b^2.

Usage: python3 check_alg.py certs/n4k25.json [more files]   (prints ACCEPT/REJECT per file, exit 0 only if all accepted)
"""
import itertools, json, math, sys
from fractions import Fraction as F


class Q:
    __slots__ = ('a', 'b', 'd')
    def __init__(self, a, b=0, d=2):
        self.a, self.b, self.d = F(a), F(b), d
    def __add__(self, o): o = self._q(o); return Q(self.a + o.a, self.b + o.b, self.d)
    def __sub__(self, o): o = self._q(o); return Q(self.a - o.a, self.b - o.b, self.d)
    def __mul__(self, o): o = self._q(o); return Q(self.a * o.a + self.d * self.b * o.b, self.a * o.b + self.b * o.a, self.d)
    __radd__ = __add__; __rmul__ = __mul__
    def __neg__(self): return Q(-self.a, -self.b, self.d)
    def _q(self, o): return o if isinstance(o, Q) else Q(o, 0, self.d)
    def sign(self):
        a, b = self.a, self.b
        if a == 0 and b == 0: return 0
        if a >= 0 and b >= 0: return 1
        if a <= 0 and b <= 0: return -1
        # opposite signs: sign(a + b sqrt d) = sign(a) iff a^2 > d b^2
        return (1 if a > 0 else -1) if a * a > self.d * b * b else (1 if b > 0 else -1)
    def __abs__(self): return self if self.sign() >= 0 else -self
    def __eq__(self, o): o = self._q(o); return self.a == o.a and self.b == o.b
    def __ge__(self, o): return (self - self._q(o)).sign() >= 0
    def __le__(self, o): return (self - self._q(o)).sign() <= 0
    def __float__(self): return float(self.a) + float(self.b) * math.sqrt(self.d)
    def dump(self): return [str(self.a), str(self.b)]
    @staticmethod
    def load(v, d): return Q(F(v[0]), F(v[1]), d)
    def __repr__(self): return f'({self.a}+{self.b}√{self.d})'


def det(M):
    n = len(M)
    if n == 1: return M[0][0]
    if n == 2: return M[0][0] * M[1][1] - M[0][1] * M[1][0]
    total = Q(0, 0, M[0][0].d)
    for j in range(n):
        minor = [row[:j] + row[j + 1:] for row in M[1:]]
        t = M[0][j] * det(minor)
        total = total + (t if j % 2 == 0 else -t)
    return total


def gcross(vectors):
    n = len(vectors) + 1
    out = []
    for m in range(n):
        minor = [[v[r] for r in range(n) if r != m] for v in vectors]
        dm = det(minor); out.append(dm if m % 2 == 0 else -dm)
    return out


def column(R, m): return [R[r][m] for r in range(len(R))]
def dot(u, v): return sum((x * y for x, y in zip(u, v)), Q(0, 0, u[0].d))
def zero(v): return all(x.sign() == 0 for x in v)


def halfwidth(R):
    n = len(R); half = Q(F(1, 2), 0, R[0][0].d)
    return [half * sum((abs(R[r][m]) for m in range(n)), Q(0, 0, R[0][0].d)) for r in range(n)]


def check_orth(R):
    n = len(R)
    for p in range(n):
        for q in range(n):
            if not dot(column(R, p), column(R, q)) == (1 if p == q else 0): return False
    return True


def cube_ok(i, c, R, s, others):
    """Walls for cube i and separation against every index in others; returns (ok, reason)."""
    n = len(R[i]); h = halfwidth(R[i])
    for r in range(n):
        if (c[i][r] - h[r]).sign() < 0 or (s - c[i][r] - h[r]).sign() < 0: return False, f'wall {i} coord {r}'
    for j in others:
        if not separated(c[i], R[i], c[j], R[j]): return False, f'pair {i},{j}'
    return True, ''


def separated(ci, Ri, cj, Rj):
    n = len(Ri); d = [x - y for x, y in zip(ci, cj)]
    for kk in range(n):
        for pi in itertools.combinations(range(n), kk):
            for pj in itertools.combinations(range(n), n - 1 - kk):
                a = gcross([column(Ri, m) for m in pi] + [column(Rj, m) for m in pj])
                if zero(a): continue
                wi = sum((abs(dot(a, column(Ri, m))) for m in range(n)), Q(0, 0, a[0].d))
                wj = sum((abs(dot(a, column(Rj, m))) for m in range(n)), Q(0, 0, a[0].d))
                if (abs(dot(a, d)) * 2 - wi - wj).sign() >= 0: return True
    return False


def check(cert):
    n, k, d = cert['n'], cert['k'], cert['d']
    s = Q.load(cert['s'], d)
    c = [[Q.load(v, d) for v in row] for row in cert['c']]
    R = [[[Q.load(v, d) for v in row] for row in M] for M in cert['R']]
    assert len(c) == k and len(R) == k
    for i in range(k):
        if not check_orth(R[i]): return False, f'frame {i} not orthogonal'
    for i in range(k):
        ok, why = cube_ok(i, c, R, s, range(i + 1, k))
        if not ok: return False, why
    return True, f'ok n={n} k={k} d={d} s={float(s):.12f}'



if __name__ == '__main__':
    bad = 0
    for path in sys.argv[1:]:
        ok, msg = check(json.load(open(path)))
        print(('ACCEPT ' if ok else 'REJECT ') + path + ': ' + msg); bad += 0 if ok else 1
    sys.exit(1 if bad else 0)
