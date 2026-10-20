"""Second checker for the quadratic-field certificates (SPEC-ALG.md, format alg-v1), written from the specification
only (the first checker is not read). Exact arithmetic in Q(sqrt d), d in {2, 3}; no floating point in any decision.

Checks: shape; orthogonality of every frame (R_i^T R_i = I, det +-1 allowed); container (c - h >= 0, s - c - h >= 0
with h = 1/2 sum_m |R[r][m]|); separation of every pair by a candidate axis (generalised cross products of
k' columns of R_i and n - 1 - k' of R_j, k' = 0..n-1; zero axes skipped).

usage: python3 alg_check2.py CERT.json        exit 0 ACCEPT, 1 REJECT, 2 unreadable
"""
import itertools
import json
import re
import sys
from fractions import Fraction

RAT = re.compile(r'-?[0-9]+(/[0-9]+)?')


class Reject(Exception):
    pass


class Q:
    """a + b sqrt d"""
    __slots__ = ('a', 'b', 'd')

    def __init__(self, a, b, d):
        self.a, self.b, self.d = a, b, d

    def __add__(self, o):
        return Q(self.a + o.a, self.b + o.b, self.d)

    def __sub__(self, o):
        return Q(self.a - o.a, self.b - o.b, self.d)

    def __neg__(self):
        return Q(-self.a, -self.b, self.d)

    def __mul__(self, o):
        return Q(self.a * o.a + self.d * self.b * o.b, self.a * o.b + self.b * o.a, self.d)

    def half(self):
        return Q(self.a / 2, self.b / 2, self.d)

    def sign(self):
        a, b = self.a, self.b
        if a == 0 and b == 0:
            return 0
        if a >= 0 and b >= 0:
            return 1
        if a <= 0 and b <= 0:
            return -1
        # opposite signs; a^2 = d b^2 is impossible for d in {2, 3} (sqrt d irrational) unless both are 0
        if a * a > self.d * b * b:
            return 1 if a > 0 else -1
        return 1 if b > 0 else -1

    def abs(self):
        return self if self.sign() >= 0 else -self

    def is_zero(self):
        return self.a == 0 and self.b == 0

    def __float__(self):
        return float(self.a) + float(self.b) * self.d ** 0.5

    def text(self):
        return f'{self.a} + ({self.b}) sqrt{self.d}'


def rat(v, where):
    if not (isinstance(v, str) and RAT.fullmatch(v)):
        raise Reject(f'{where}: {v!r} is not a string "p/q" or "p"')
    x = Fraction(v)
    if '/' in v and int(v.split('/')[1]) == 0:
        raise Reject(f'{where}: zero denominator')
    return x


def num(v, d, where):
    if not (isinstance(v, list) and len(v) == 2):
        raise Reject(f'{where}: {v!r} is not a pair ["a", "b"]')
    return Q(rat(v[0], where), rat(v[1], where), d)


def det(M, zero):
    """determinant by expansion along the first row (n - 1 <= 3 here; fine for small n)"""
    m = len(M)
    if m == 1:
        return M[0][0]
    if m == 2:
        return M[0][0] * M[1][1] - M[0][1] * M[1][0]
    tot = zero
    for j in range(m):
        minor = [row[:j] + row[j + 1:] for row in M[1:]]
        t = M[0][j] * det(minor, zero)
        tot = tot + t if j % 2 == 0 else tot - t
    return tot


def cross(vs, n, zero):
    out = []
    for m in range(n):
        minor = [v[:m] + v[m + 1:] for v in vs]
        t = det(minor, zero)
        out.append(t if m % 2 == 0 else -t)
    return out


def dot(u, v, zero):
    t = zero
    for x, y in zip(u, v):
        t = t + x * y
    return t


def check(c):
    if not isinstance(c, dict):
        raise Reject('shape: not an object')
    if c.get('format') != 'alg-v1':
        raise Reject(f'shape: format {c.get("format")!r} is not alg-v1')
    n, k, d = c.get('n'), c.get('k'), c.get('d')
    if not (type(n) is int and n >= 2):
        raise Reject(f'shape: n = {n!r} is not an integer >= 2')
    if not (type(k) is int and k >= 1):
        raise Reject(f'shape: k = {k!r} is not an integer >= 1')
    if d not in (2, 3) or type(d) is not int:
        raise Reject(f'shape: d = {d!r} is not 2 or 3')
    s = num(c.get('s'), d, 's')
    C, R = c.get('c'), c.get('R')
    if not (isinstance(C, list) and len(C) == k and all(isinstance(x, list) and len(x) == n for x in C)):
        raise Reject('shape: c is not k lists of n numbers')
    if not (isinstance(R, list) and len(R) == k and all(isinstance(M, list) and len(M) == n and
                                                        all(isinstance(r, list) and len(r) == n for r in M) for M in R)):
        raise Reject('shape: R is not k n x n matrices')
    zero, one = Q(Fraction(0), Fraction(0), d), Q(Fraction(1), Fraction(0), d)
    C = [[num(x, d, f'c[{i}][{r}]') for r, x in enumerate(ci)] for i, ci in enumerate(C)]
    R = [[[num(x, d, f'R[{i}][{r}][{m}]') for m, x in enumerate(row)] for r, row in enumerate(M)] for i, M in enumerate(R)]
    cols = [[[M[r][m] for r in range(n)] for m in range(n)] for M in R]
    # 1 orthogonality
    for i in range(k):
        for p in range(n):
            for q in range(p, n):
                v = dot(cols[i][p], cols[i][q], zero)
                if not (v - (one if p == q else zero)).is_zero():
                    raise Reject(f'orthogonality: cube {i}, columns {p}, {q}: dot = {v.text()}')
    # 2 container
    slack = None
    for i in range(k):
        for r in range(n):
            h = zero
            for m in range(n):
                h = h + R[i][r][m].abs()
            h = h.half()
            lo, hi = C[i][r] - h, s - C[i][r] - h
            for v, side in ((lo, 'c - h'), (hi, 's - c - h')):
                if v.sign() < 0:
                    raise Reject(f'container: cube {i}, coordinate {r}: {side} = {v.text()} (~{float(v):.3e})')
                if slack is None or float(v) < float(slack):
                    slack = v
    # 3 separation
    for i in range(k):
        for j in range(i + 1, k):
            delta = [C[i][r] - C[j][r] for r in range(n)]
            ok = False
            for kp in range(n - 1, -1, -1):
                for ci in itertools.combinations(range(n), kp):
                    for cj in itertools.combinations(range(n), n - 1 - kp):
                        a = cross([cols[i][m] for m in ci] + [cols[j][m] for m in cj], n, zero)
                        if all(x.is_zero() for x in a):
                            continue
                        lhs = dot(a, delta, zero).abs()
                        lhs = lhs + lhs
                        rhs = zero
                        for m in range(n):
                            rhs = rhs + dot(a, cols[i][m], zero).abs() + dot(a, cols[j][m], zero).abs()
                        if (lhs - rhs).sign() >= 0:
                            ok = True
                            break
                    if ok:
                        break
                if ok:
                    break
            if not ok:
                raise Reject(f'separation: cubes {i} and {j} are not separated on any candidate axis')
    return s, slack


def main(argv):
    try:
        c = json.load(open(argv[1]))
    except (OSError, ValueError) as e:
        print(f'UNREADABLE {e}')
        return 2
    try:
        s, slack = check(c)
    except Reject as e:
        print(f'REJECT {e}')
        return 1
    print(f'ACCEPT n={c["n"]} k={c["k"]} d={c["d"]} s=[{s.a}, {s.b}] = {s.text()} (~{float(s):.12f}) '
          f'min_wall_slack={slack.text()} (~{float(slack):.3e})')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
