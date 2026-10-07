#!/usr/bin/env python3
"""Exact check of the zm_mixed run records for s(59) = 8 (standard library only).

    python3 check_records.py COVER ZM_ALL_ROOTS ZM_ROOT_R

COVER          the cover file (its SHA256 must match the records' headers)
ZM_ALL_ROOTS   roots.jsonl[.gz] of the depth-24 run over all D4 roots
ZM_ROOT_R      roots.jsonl of the depth-34 run restricted to the root R

Checks, in exact rational arithmetic (fractions.Fraction):
  1. both headers name the pinned checker files and the cover's SHA256, cert mode, D4, pitch 1/20, 16 u-bins;
     depth 24 for the first run and 34 for the second;
  2. the first run has a record for every one of the 80 x 80 x 16 = 102,400 root boxes
     [i/20,(i+1)/20] x [j/20,(j+1)/20] x [l/32,(l+1)/32] of the D4 region [0,4]^2 x u in [0,1/2], and nothing else;
  3. every record of the first run has UNCERT 0, except the records of the single root
     R = [27/20,7/5] x [13/10,27/20] x [1/4,9/32];
  4. every uncertified box listed for R (exact rational bounds) lies inside R;
  5. the second run has exactly one root, equal to R, and every record of it has UNCERT 0.
Records may repeat a root (a resumed run re-records a root it had started); every record is checked.
"""
import gzip
import hashlib
import json
import sys
from fractions import Fraction as F

PINNED = {
    'zm_mixed.py': 'ee3e2915349b8795128417bca6414b205d526db9f01f88cd4cd32c32e8d760ac',
    'mixed_cover.py': 'bb89de15ecf5821dd7e1a36ebab8a50d792a406b7fb0f5cb38059f99ef74aae5',
    'zeromargin.py': '640fe453c1a32f4aa580ca2b1261c6406923a4d7c131f65604a432c7fc2086ab',
}
R = (F(27, 20), F(7, 5), F(13, 10), F(27, 20), F(1, 4), F(9, 32))


def read(path):
    op = gzip.open if path.endswith('.gz') else open
    with op(path, 'rt') as f:
        lines = [json.loads(s) for s in f if s.strip()]
    head = [d for d in lines if d.get('kind') == 'zm_mixed cert header']
    recs = [d for d in lines if 'root' in d]
    assert len(head) >= 1, 'no header'
    assert all(h == head[0] for h in head), 'differing headers'
    assert len(head) + len(recs) == len(lines), 'unexpected lines'
    return head[0], recs


def check_header(h, cover_sha, depth):
    assert h['sha256']['input'] == cover_sha, 'cover SHA256 differs from the records'
    for k, v in PINNED.items():
        assert h['sha256'][k] == v, f'{k} is not the pinned checker file'
    s = h['settings']
    assert s['mode'] == 'D4' and s['cert_mode'] is True and s['tprime'] is False, s
    assert s['pitch'] == '1/20' and s['ubins'] == 16 and s['depth'] == depth, s
    assert h['total'] == '1474762899/25000000', h['total']


def box(rec):
    return tuple(F(v) for v in rec['root'])


def main(cover, all_roots, root_r):
    cover_sha = hashlib.sha256(open(cover, 'rb').read()).hexdigest()
    h1, r1 = read(all_roots)
    check_header(h1, cover_sha, 24)
    assert all(v is None for v in h1['settings']['region'].values()), 'first run is not over the whole region'
    want = {(F(i, 20), F(i + 1, 20), F(j, 20), F(j + 1, 20), F(l, 32), F(l + 1, 32))
            for i in range(80) for j in range(80) for l in range(16)}
    got = {box(r) for r in r1}
    assert got == want, f'root boxes: {len(got)} distinct, {len(got - want)} unexpected, {len(want - got)} missing'
    n_unc = 0
    for r in r1:
        b = box(r)
        u = r['st']['UNCERT']
        if b != R:
            assert u == 0 and not r['unc'], f'uncertified boxes outside R: {r["root"]}'
            continue
        assert u == len(r['unc']), r['st']
        for ub in r['unc']:
            x0, x1, y0, y1, u0, u1 = (F(v) for v in ub)
            assert R[0] <= x0 <= x1 <= R[1] and R[2] <= y0 <= y1 <= R[3] and R[4] <= u0 <= u1 <= R[5], ub
        n_unc = max(n_unc, u)
    print(f'depth 24: {len(want)} root boxes, all certified except R, which lists {n_unc} uncertified boxes, all inside R')
    h2, r2 = read(root_r)
    check_header(h2, cover_sha, 34)
    reg = h2['settings']['region']
    assert (reg['cx_lo'], reg['cx_hi'], reg['cy_lo'], reg['cy_hi'], reg['u_lo'], reg['u_hi']) == \
        ('27/20', '7/5', '13/10', '27/20', '1/4', '9/32'), reg
    assert r2 and all(box(r) == R for r in r2), 'second run is not exactly the root R'
    assert all(r['st']['UNCERT'] == 0 and not r['unc'] for r in r2), 'R not certified at depth 34'
    print('depth 34: the root R alone, certified, 0 uncertified boxes')
    print('ZM_RECORDS_OK')


if __name__ == '__main__':
    main(*sys.argv[1:4])
