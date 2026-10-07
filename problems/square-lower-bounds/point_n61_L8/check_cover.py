#!/usr/bin/env python3
"""Exact, dependency-free checks of cover.txt: format, nonnegativity, D4 invariance, total < 61.

The capture condition itself (every closed unit square has mass >= 1) is checked by zmx2; see verify.sh.
"""
from collections import Counter
from fractions import Fraction
from hashlib import sha256
from pathlib import Path
import json

HERE = Path(__file__).resolve().parent
raw = (HERE / 'cover.txt').read_bytes()
expected = json.loads((HERE / 'provenance.json').read_text())
assert sha256(raw).hexdigest() == expected['cover_sha256'], 'cover.txt differs from provenance.json'
v = [int(t) for t in raw.split()]
sn, sd, D, W, m = v[:5]
assert (sn, sd) == (8, 1) and len(v) == 5 + 3 * m and D > 0 and W > 0
span = 8 * D
mass = Counter()
for i in range(5, len(v), 3):
    x, y, w = v[i:i + 3]
    assert 0 <= x <= span and 0 <= y <= span and w >= 0
    mass[x, y] += w
for (x, y), w in mass.items():
    for image in ((span - x, y), (x, span - y), (y, x)):
        assert mass.get(image, 0) == w, 'not D4-invariant'
total = Fraction(sum(mass.values()), W)
assert total < 61 and str(total) == expected['total']
print(f'COVER_OK points={len(mass)} total={total} ({float(total):.12f}) < 61, D4-invariant')
