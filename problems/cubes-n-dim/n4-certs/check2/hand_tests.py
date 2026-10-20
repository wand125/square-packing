"""Hand-made cases for cert_check2.py (exact touching, n = 2 and 4, a rotated cube).

usage: python3 hand_tests.py
"""
import itertools
import json
import os
import subprocess
import sys
import tempfile
from fractions import Fraction as F

HERE = os.path.dirname(os.path.abspath(__file__))


def run(obj):
    with tempfile.NamedTemporaryFile('w', suffix='.json', delete=False) as f:
        json.dump(obj, f)
        p = f.name
    r = subprocess.run([sys.executable, os.path.join(HERE, 'cert_check2.py'), p], capture_output=True, text=True)
    os.unlink(p)
    return r.returncode, r.stdout.strip()


def grid(n, shift=F(0)):
    cs = [[str(F(1, 2) + x) for x in v] for v in itertools.product((0, 1), repeat=n)]
    cs[1] = [str(F(cs[1][r]) - (shift if r == n - 1 else 0)) for r in range(n)]
    Z = [['0'] * n for _ in range(n)]
    return {'n': n, 'k': 2 ** n, 's': '2', 'A': [Z] * 2 ** n, 'c': cs}


def rotated(t, s):
    # n = 2, A = [[0, -t], [t, 0]] -> rotation with cos = (1-t^2)/(1+t^2); half-width (|cos|+|sin|)/2
    t = F(t)
    co, si = (1 - t * t) / (1 + t * t), 2 * t / (1 + t * t)
    h = (abs(co) + abs(si)) / 2
    return {'n': 2, 'k': 1, 's': str(F(s)), 'A': [[['0', str(-t)], [str(t), '0']]], 'c': [[str(h), str(h)]]}, 2 * h


cases = []
for n in (2, 3, 4):
    cases.append((f'n={n}: 2^n axis-parallel cubes in [0,2]^n, faces touching', grid(n), 0))
    cases.append((f'n={n}: one cube pushed into its neighbour by 1e-12', grid(n, F(1, 10**12)), 1))
cert, side = rotated(F(1, 3), 0)
cert['s'] = str(side)
cases.append(('n=2: cube turned by 2 atan(1/3), container exactly its bounding box', cert, 0))
cert2 = dict(cert); cert2['s'] = str(side - F(1, 10**15))
cases.append(('n=2: same with s smaller by 1e-15', cert2, 1))
# two turned cubes: the same rotation, side by side along the rotated axis, touching exactly
t = F(1, 3); co, si = (1 - t * t) / (1 + t * t), 2 * t / (1 + t * t)
h = (co + si) / 2
c0 = [h + 2, h + 2]
c1 = [c0[0] + co, c0[1] + si]  # c0 + R e1: faces touching
A = [['0', str(-t)], [str(t), '0']]
pair = {'n': 2, 'k': 2, 's': '6', 'A': [A, A], 'c': [[str(x) for x in c0], [str(x) for x in c1]]}
cases.append(('n=2: two turned cubes with faces touching', pair, 0))
pair2 = dict(pair); pair2['c'] = [pair['c'][0], [str(c0[0] + co * F(999999, 10**6)), str(c0[1] + si * F(999999, 10**6))]]
cases.append(('n=2: the same pushed together by 1e-6', pair2, 1))
# edge-to-face (non-face-normal axis needed in n=3 is not constructed here)

bad = 0
for name, obj, want in cases:
    rc, msg = run(obj)
    ok = rc == want
    bad += not ok
    print(f"{'ok ' if ok else 'BAD'} {name}: rc {rc}: {msg[:100]}")
print('ALL OK' if not bad else f'{bad} UNEXPECTED')
sys.exit(1 if bad else 0)
