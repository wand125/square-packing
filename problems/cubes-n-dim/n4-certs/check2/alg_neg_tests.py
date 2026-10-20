"""Negative tests for alg_check2.py (SPEC-ALG.md "Suggested negative tests" and a few more): each valid certificate
must be accepted, and every broken copy rejected (exit 1, or 2 for unreadable JSON).

usage: python3 alg_neg_tests.py CERT.json ...
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
        r = subprocess.run([sys.executable, '-I', '-B', os.path.join(HERE, 'alg_check2.py'), p], capture_output=True, text=True)
    finally:
        os.unlink(p)
    return r.returncode, r.stdout.strip()


def sub(x, y):
    return str(Fraction(x) - Fraction(y))


def variants(c):
    out = []
    v = copy.deepcopy(c)
    e = v['R'][0][0][0]
    v['R'][0][0][0] = [sub(e[0], '-1/1000'), e[1]]
    out.append(('frame entry changed (not orthogonal)', v, 1))
    v = copy.deepcopy(c)
    v['s'] = [v['s'][0], sub(v['s'][1], '1/1000000')] if Fraction(v['s'][1]) else [sub(v['s'][0], '1/1000000'), v['s'][1]]
    out.append(('s decreased by 1e-6 in the sqrt d part', v, 1))
    v = copy.deepcopy(c)
    v['s'] = [sub(v['s'][0], '1/1000000'), v['s'][1]]
    out.append(('s decreased by 1e-6', v, 1))
    # move one cube of the tightest pair (smallest float separation gap over the candidate axes) by 1/64 towards
    # the other, along the coordinate of largest |delta|; that pair touches, so the move makes them overlap
    import itertools
    import numpy as np
    f = lambda x: float(Fraction(x[0])) + float(Fraction(x[1])) * c['d'] ** 0.5
    n = c['n']
    C = [np.array([f(x) for x in ci]) for ci in c['c']]
    R = [np.array([[f(x) for x in row] for row in M]) for M in c['R']]

    def gap(i, j):
        best = -9.0
        for kp in range(n):
            for ci in itertools.combinations(range(n), kp):
                for cj in itertools.combinations(range(n), n - 1 - kp):
                    M = np.array([R[i][:, m] for m in ci] + [R[j][:, m] for m in cj])
                    a = np.array([(-1) ** m * np.linalg.det(np.delete(M, m, axis=1)) for m in range(n)]) if n > 1 else None
                    if np.linalg.norm(a) < 1e-12:
                        continue
                    a = a / np.linalg.norm(a)
                    g = 2 * abs(a @ (C[i] - C[j])) - sum(abs(a @ R[i][:, m]) + abs(a @ R[j][:, m]) for m in range(n))
                    best = max(best, g)
        return best
    if c['k'] > 1:
        i, j = min(itertools.combinations(range(c['k']), 2), key=lambda p: gap(*p))
        r = int(np.argmax(abs(C[j] - C[i])))
        step = Fraction(1, 64) if C[j][r] > C[i][r] else Fraction(-1, 64)
        v = copy.deepcopy(c)
        v['c'][i][r] = [str(Fraction(v['c'][i][r][0]) + step), v['c'][i][r][1]]
        out.append((f'tightest pair ({i}, {j}), float gap {gap(i, j):.1e}: cube {i} moved by 1/64 towards cube {j}', v, 1))
        v = copy.deepcopy(c)
        v['c'][1] = copy.deepcopy(v['c'][0])
        out.append(('two centres made equal', v, 1))
    v = copy.deepcopy(c)
    v['c'][0][0] = [float(Fraction(v['c'][0][0][0])), v['c'][0][0][1]]
    out.append(('a number given as a JSON float', v, 1))
    v = copy.deepcopy(c)
    v['c'][0][0] = ['0.5', '0']
    out.append(('a decimal string', v, 1))
    v = copy.deepcopy(c)
    v['c'][0][0] = ['1/0', '0']
    out.append(('a zero denominator', v, 1))
    v = copy.deepcopy(c)
    v['c'][0][0] = 'sqrt2'
    out.append(('a bare sqrt string', v, 1))
    v = copy.deepcopy(c)
    v['d'] = 5 - c['d']
    out.append((f'd changed from {c["d"]} to {5 - c["d"]}', v, 1))
    v = copy.deepcopy(c)
    v['k'] = c['k'] + 1
    out.append(('k larger than the lists', v, 1))
    v = copy.deepcopy(c)
    v['R'][0] = v['R'][0][:-1]
    out.append(('a frame with n - 1 rows', v, 1))
    v = copy.deepcopy(c)
    v['format'] = 'alg-v0'
    out.append(('wrong format tag', v, 1))
    v = copy.deepcopy(c)
    v['n'] = 1
    out.append(('n = 1', v, 1))
    return out


def main(argv):
    bad = 0
    for p in argv[1:]:
        c = json.load(open(p))
        rc, msg = run(c)
        print(f'{os.path.basename(p)}: original rc {rc}: {msg[:90]}')
        if rc != 0:
            bad += 1
            continue
        for name, v, want in variants(c):
            rc, msg = run(v)
            ok = rc == want
            bad += not ok
            print(f'  {"ok " if ok else "BAD"} {name}: rc {rc}: {msg[:110]}')
        rc, msg = run(text=json.dumps(c)[:-20])
        bad += rc != 2
        print(f'  {"ok " if rc == 2 else "BAD"} truncated JSON: rc {rc}')
    print('ALL OK' if not bad else f'{bad} FAILURES')
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
