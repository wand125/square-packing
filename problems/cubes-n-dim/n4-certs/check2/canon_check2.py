"""Canonical form and nesting of alg-v1 certificates (SPEC-ALG.md "Canonical form"), written from the specification
only. Exact arithmetic in Q(sqrt d) through alg_check2.py.

  rule 1  every rational in lowest terms with positive denominator, "p" when the denominator is 1, zero as "0"
  rule 2  each frame is the lexicographically largest R P over the 2^n n! signed permutation matrices P
          (row-major entries compared exactly)
  rule 4  cubes sorted by centre (lexicographic, exact), ties by the row-major frame
  rule 5  the file is exactly json with keys format, n, k, d, s, c, R in this order, separators "," and ":", no
          whitespace, one final newline, no other key
  nesting (with --nest A.json B.json ..., increasing k) every certificate is the next one with one cube removed, all
          else equal (same s, d, n; positions and order kept), and the removed cube follows the rule: the largest
          number of rotated coordinate planes, then the fewest contacts (walls touched exactly plus pairs whose best
          separation margin over the candidate axes is exactly 0), then the last in the order

usage: python3 canon_check2.py CERT.json ...          (rules 1, 2, 4, 5)
       python3 canon_check2.py --nest K1.json K2.json ...  (nesting, smallest k first)
"""
import itertools
import json
import os
import re
import sys
from fractions import Fraction

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.dont_write_bytecode = True
import alg_check2 as ac   # noqa: E402

KEYS = ['format', 'n', 'k', 'd', 's', 'c', 'R']


def canon_rat(t):
    x = Fraction(t)
    want = str(x.numerator) if x.denominator == 1 else f'{x.numerator}/{x.denominator}'
    return t == want


def all_pairs(c):
    yield c['s']
    for ci in c['c']:
        yield from ci
    for M in c['R']:
        for row in M:
            yield from row


def cmp(x, y):
    return (x - y).sign()


def lex_cmp(u, v):
    for x, y in zip(u, v):
        s = cmp(x, y)
        if s:
            return s
    return 0


def rule2_frame(M, n, d):
    best = None
    flat = lambda A: [A[r][m] for r in range(n) for m in range(n)]
    for perm in itertools.permutations(range(n)):
        for signs in itertools.product((1, -1), repeat=n):
            # (R P)[r][m] = signs[m] R[r][perm[m]]
            A = [[M[r][perm[m]] if signs[m] == 1 else -M[r][perm[m]] for m in range(n)] for r in range(n)]
            if best is None or lex_cmp(flat(A), flat(best)) > 0:
                best = A
    return lex_cmp(flat(best), flat(M)) == 0


def parse(c):
    d, n = c['d'], c['n']
    C = [[ac.num(x, d, 'c') for x in ci] for ci in c['c']]
    R = [[[ac.num(x, d, 'R') for x in row] for row in M] for M in c['R']]
    return C, R


def check_canon(path):
    raw = open(path, 'rb').read()
    c = json.loads(raw)
    probs = []
    if list(c.keys()) != KEYS:
        probs.append(f'rule 5: keys {list(c.keys())}')
    if raw != (json.dumps(c, separators=(',', ':'), ensure_ascii=False) + '\n').encode():
        probs.append('rule 5: bytes differ from the compact json with one final newline')
    bad = [p for p in all_pairs(c) if not (canon_rat(p[0]) and canon_rat(p[1]))]
    if bad:
        probs.append(f'rule 1: {len(bad)} numbers not in canonical form, e.g. {bad[0]}')
    C, R = parse(c)
    n = c['n']
    flat = lambda M: [M[r][m] for r in range(n) for m in range(n)]
    for i in range(c['k'] - 1):
        s = lex_cmp(C[i], C[i + 1]) or lex_cmp(flat(R[i]), flat(R[i + 1]))
        if s > 0:
            probs.append(f'rule 4: cubes {i} and {i + 1} out of order')
            break
    nb = [i for i in range(c['k']) if not rule2_frame(R[i], n, c['d'])]
    if nb:
        probs.append(f'rule 2: frames of cubes {nb[:5]} are not the lexicographically largest R P')
    return probs


def rotated_planes(M, n):
    one = lambda x: x.b == 0 and abs(x.a) == 1
    zero = lambda x: x.is_zero()
    cnt = 0
    for p, q in itertools.combinations(range(n), 2):
        if any(not (zero(M[a][b]) or one(M[a][b])) for a, b in ((p, q), (q, p))):
            cnt += 1
    return cnt


def contacts(c, C, R, i):
    n, d = c['n'], c['d']
    zero = ac.Q(Fraction(0), Fraction(0), d)
    s = ac.num(c['s'], d, 's')
    cols = [[[M[r][m] for r in range(n)] for m in range(n)] for M in R]
    cnt = 0
    for r in range(n):
        h = zero
        for m in range(n):
            h = h + R[i][r][m].abs()
        h = h.half()
        cnt += (C[i][r] - h).is_zero()
        cnt += (s - C[i][r] - h).is_zero()
    for j in range(c['k']):
        if j == i:
            continue
        delta = [C[i][r] - C[j][r] for r in range(n)]
        best = -2          # sign of the best margin: 1 separated with room, 0 touching
        for kp in range(n):
            for ci in itertools.combinations(range(n), kp):
                for cj in itertools.combinations(range(n), n - 1 - kp):
                    a = ac.cross([cols[i][m] for m in ci] + [cols[j][m] for m in cj], n, zero)
                    if all(x.is_zero() for x in a):
                        continue
                    lhs = ac.dot(a, delta, zero).abs()
                    lhs = lhs + lhs
                    rhs = zero
                    for m in range(n):
                        rhs = rhs + ac.dot(a, cols[i][m], zero).abs() + ac.dot(a, cols[j][m], zero).abs()
                    best = max(best, (lhs - rhs).sign())
        cnt += best == 0
    return cnt


def check_nest(paths):
    certs = [json.load(open(p)) for p in paths]
    out = []
    for small, big, ps, pb in zip(certs, certs[1:], paths, paths[1:]):
        ok = all(small[f] == big[f] for f in ('format', 'n', 'd', 's')) and small['k'] == big['k'] - 1
        rem = [t for t in range(big['k']) if big['c'][:t] + big['c'][t + 1:] == small['c']
               and big['R'][:t] + big['R'][t + 1:] == small['R']]
        if not ok or len(rem) == 0:
            out.append(f'{os.path.basename(ps)} is not {os.path.basename(pb)} minus one cube')
            continue
        C, R = parse(big)
        n = big['n']
        rot = [rotated_planes(R[t], n) for t in range(big['k'])]
        top = max(rot)
        cand = [t for t in range(big['k']) if rot[t] == top]
        con = {t: contacts(big, C, R, t) for t in cand}
        fewest = min(con.values())
        chosen = [t for t in cand if con[t] == fewest][-1]
        line = f'{big["k"]} -> {small["k"]}: removed {rem}, rule gives {chosen} (rotated {top}, contacts {fewest})'
        if chosen not in rem:
            line += '  RULE MISMATCH'
        out.append(line)
    return out


def main(argv):
    if '--nest' in argv:
        lines = check_nest([a for a in argv[1:] if a.endswith('.json')])
        print('\n'.join(lines))
        return 1 if any('MISMATCH' in l or 'not' in l for l in lines) else 0
    bad = 0
    for p in argv[1:]:
        probs = check_canon(p)
        bad += bool(probs)
        print(f'{os.path.basename(p)}: ' + ('canonical (rules 1, 2, 4, 5)' if not probs else 'NOT canonical: ' + '; '.join(probs)))
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
