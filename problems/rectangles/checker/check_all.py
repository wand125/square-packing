"""Re-check every certificate listed in data/edges/k*.json and data/sweeps/*.json with both checkers.

Run from problems/rectangles after unpacking the release asset:
    python checker/check_all.py
Exit status 0 if every certificate passes both exact checkers and matches its listing.
"""
import json
import sys
from fractions import Fraction as F
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import verify        # noqa: E402  exact vertex separating-axis checker
import verify_fast   # noqa: E402  exact checker with rational bounding-box rejection

base = HERE.parent
fails = 0
count = 0
for edge in sorted((base / 'data' / 'edges').glob('k*.json')):
    data = json.loads(edge.read_text())
    k = data['k']
    for piece in data['pieces']:
        for w in piece['witnesses']:
            count += 1
            cert = json.loads((base / w['file']).read_text())
            problems = []
            if cert.get('schema') != 'rational-unit-square-v1':
                problems.append('schema')
            if cert['n'] != k or len(cert['squares']) != k:
                problems.append('number of squares')
            if F(cert['a']) != F(w['a']) or F(cert['b']) != F(w['b']):
                problems.append('box differs from the listing')
            if not (piece['a0'] - 1e-6 <= float(F(cert['a'])) <= piece['a1'] + 1e-6):
                problems.append('box height outside the piece')
            if not verify.exact(cert).get('exact_verified'):
                problems.append('verify.py')
            if not verify_fast.exact(cert).get('exact_verified'):
                problems.append('verify_fast.py')
            if problems:
                fails += 1
                print(f'FAIL k={k} {piece["key"]} {w["file"]}: {", ".join(problems)}')
for sweep in sorted((base / 'data' / 'sweeps').glob('*.json')) if (base / 'data' / 'sweeps').exists() else []:
    data = json.loads(sweep.read_text())
    k = data['k']
    for w in data['certificates']:
        count += 1
        cert = json.loads((base / w['file']).read_text())
        problems = []
        if cert.get('schema') != 'rational-unit-square-v1':
            problems.append('schema')
        if cert['n'] != k or len(cert['squares']) != k:
            problems.append('number of squares')
        if F(cert['a']) != F(w['a']) or F(cert['b']) != F(w['b']):
            problems.append('box differs from the listing')
        if not verify.exact(cert).get('exact_verified'):
            problems.append('verify.py')
        if not verify_fast.exact(cert).get('exact_verified'):
            problems.append('verify_fast.py')
        if problems:
            fails += 1
            print(f'FAIL {sweep.name} {w["file"]}: {", ".join(problems)}')
print(f'{count} certificates checked, {fails} failed')
sys.exit(1 if fails else 0)
