"""Negative tests for cert_check2.py: break a valid certificate in several ways and require rejection.

usage: python3 neg_tests.py CERT.json [CERT.json ...]
Each valid certificate must be accepted (exit 0), and every broken copy rejected (exit 1, or 2 for bad JSON).
"""
import copy
import json
import os
import subprocess
import sys
import tempfile
from fractions import Fraction

HERE = os.path.dirname(os.path.abspath(__file__))


def run(obj=None, text=None):
    with tempfile.NamedTemporaryFile('w', suffix='.json', delete=False) as f:
        f.write(text if text is not None else json.dumps(obj))
        p = f.name
    try:
        r = subprocess.run([sys.executable, os.path.join(HERE, 'cert_check2.py'), p], capture_output=True, text=True)
    finally:
        os.unlink(p)
    return r.returncode, r.stdout.strip()


def variants(c):
    k, n = c['k'], c['n']
    s = Fraction(c['s'])
    out = []

    v = copy.deepcopy(c); v['c'][1] = list(v['c'][0])
    out.append(('overlap: cube 1 moved onto cube 0', v, 1))

    eps = Fraction(1, 10**6)
    v = copy.deepcopy(c)
    v['c'] = [[str((Fraction(x) - s / 2) * (1 - eps) + s / 2) for x in ci] for ci in v['c']]
    out.append(('overlap: centres pulled to the middle by 1e-6 (touching pairs overlap)', v, 1))

    v = copy.deepcopy(c); v['s'] = str(s - Fraction(1, 10**12))
    out.append(('container: s reduced by 1e-12', v, 1))

    # a cube touching the wall at 0 (slack exactly 0), pushed out through that wall by 1e-12
    sys.path.insert(0, HERE)
    import cert_check2 as cc
    R = [cc.solve([[int(p == q) - Fraction(A[p][q]) for q in range(n)] for p in range(n)],
                  [[int(p == q) + Fraction(A[p][q]) for q in range(n)] for p in range(n)]) for A in c['A']]
    hit = next(((i, r) for i in range(k) for r in range(n)
                if Fraction(c['c'][i][r]) - sum(abs(x) for x in R[i][r]) / 2 == 0), None)
    if hit:
        i, r = hit
        v = copy.deepcopy(c); v['c'][i][r] = str(Fraction(v['c'][i][r]) - Fraction(1, 10**12))
        out.append((f'container: cube {i} touching the wall x_{r} = 0 pushed out by 1e-12', v, 1))

    v = copy.deepcopy(c); v['A'][0][0][1] = str(Fraction(v['A'][0][0][1]) + Fraction(1, 1000))
    out.append(('skew: one entry of A[0] changed (R not orthogonal)', v, 1))

    v = copy.deepcopy(c); v['A'][0][1][1] = '1/1000'
    out.append(('skew: nonzero diagonal', v, 1))

    v = copy.deepcopy(c); v['k'] = k + 1
    out.append(('shape: k larger than the lists', v, 1))

    v = copy.deepcopy(c); v['A'][0] = v['A'][0][:-1]
    out.append(('shape: A[0] has n-1 rows', v, 1))

    v2 = copy.deepcopy(c); v2['c'][0][0] = 'x'
    out.append(('shape: entry "x" not rational', v2, 1))

    v = copy.deepcopy(c); v['c'][0][0] = '0.5'
    out.append(('shape: decimal string "0.5" (only "p/q" or "p" allowed)', v, 1))

    v = copy.deepcopy(c); v['s'] = v['s'].split('/')[0] + '/0'
    out.append(('shape: s with denominator 0', v, 1))

    v = copy.deepcopy(c); v['c'][0][0] = 0.5
    out.append(('shape: entry is a JSON number, not a string', v, 1))

    v = copy.deepcopy(c); v['n'] = 1
    out.append(('shape: n = 1', v, 1))

    v = copy.deepcopy(c)
    # swap the frame of cube 0 by a signed permutation is allowed by the spec; a different cube is not:
    # rotate cube 0 by a small extra Cayley angle about axis (0,1) -> should usually overlap or leave the box
    v['A'][0][0][1] = str(Fraction(v['A'][0][0][1]) + Fraction(1, 100))
    v['A'][0][1][0] = str(-Fraction(v['A'][0][0][1]))
    out.append(('rotation: cube 0 turned by about 0.02 rad (skew kept; informative)', v, None))
    return out


def main(paths):
    bad = 0
    for p in paths:
        c = json.load(open(p))
        rc, msg = run(c)
        print(f'{os.path.basename(p)}: valid -> rc {rc}: {msg[:90]}')
        if rc != 0:
            bad += 1
        for name, v, want in variants(c):
            rc, msg = run(v)
            flag = 'info' if want is None else ('ok ' if rc == want else 'BAD')
            if want is not None and rc != want:
                bad += 1
            print(f'  {flag} {name}: rc {rc}: {msg[:110]}')
        rc, msg = run(text='{"n": 3, "k": ')
        print(f'  {"ok " if rc == 2 else "BAD"} truncated JSON: rc {rc}')
        if rc != 2:
            bad += 1
    print('ALL OK' if bad == 0 else f'{bad} UNEXPECTED')
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
