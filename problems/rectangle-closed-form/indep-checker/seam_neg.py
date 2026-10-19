"""Negative tests of seam_check2.py: each corruption must be detected (in memory, on real pairs).

usage: python3 seam_neg.py INPUTS_DIR
"""
import copy
import json
import sys
from fractions import Fraction as F

import seam_check2 as sc

base = sys.argv[1]
fams = {}
import os
for fn in sorted(os.listdir(f'{base}/families')):
    fams[fn[:-5]] = sc.profile(json.load(open(f'{base}/families/{fn}')))
results = []


def expect(name, detected):
    results.append((name, detected))
    print(f'  {"ok " if detected else "BAD"} {name}: {"detected" if detected else "NOT detected"}')


pair = 'i005_012__i012_020_a'                      # four levels with fam_r5
pdir = f'{base}/seams/{pair}'
a, b = pair.split('__')
P, Pp = fams[a], fams[b]
fr5 = json.load(open(f'{pdir}/fam_r5.json'))
fl2 = json.load(open(f'{pdir}/L2/fam_fix.json'))


def item1(fam):
    r, M, tr = sc.seam_family_checks(fam, P, Pp, 'x')
    return r, M, tr


# item 1
f = copy.deepcopy(fr5)
k = next(i for i, r in enumerate(f['F']) if F(r[0]) >= 2 and max(F(r[0]), F(r[2])) <= 4 and F(r[4]) > 0)
f['F'][k][4] = str(F(f['F'][k][4]) * F(1001, 1000))
expect('item 1: one mass inside the P periods raised by 0.1%', not item1(f)[0]['ok'])
f = copy.deepcopy(fr5)
f['F'].append(['19/2', '0', '19/2', '1/5', '1/1000'])
expect('item 1: a segment beyond x = 9', not item1(f)[0]['ok'])
f = copy.deepcopy(fr5)
f['T'] = [['2', '0', '2', '1/5', '1/1000']]
expect('item 1: T not empty', not item1(f)[0]['ok'])
f = copy.deepcopy(fr5)
f['F'][0][4] = '-' + f['F'][0][4]
try:
    item1(f); det = False
except ValueError:
    det = True
expect('item 1: a negative mass', det)
f = copy.deepcopy(fr5)
k = next(i for i, r in enumerate(f['F']) if 5 < F(r[0]) < 6 and F(r[4]) > 0)
f['F'][k][4] = str(F(f['F'][k][4]) + F(1, 10**6))
expect('item 1: a transition mass raised by 1e-6 changes e from the recorded value',
       item1(f)[0]['e'] != F(json.load(open(f'{base}/tables/seam_e_rigorous.json'))['pairs'][2]['e']))
# item 2: the final family without the added band segment fails the band condition (the L2 family)
expect('item 2: L2 family (before the band repair) fails the band condition',
       not sc.band_check(item1(fl2)[2], P, Pp)['ok'])
f = copy.deepcopy(fr5)
P5 = P.shift(sc.S_SEAM)
lines = [key for key in P5.lines if key[0] == 'v' and sc.S_SEAM <= key[1] < sc.S_SEAM + sc.D_BAND]
k = next(i for i, r in enumerate(f['F']) if F(r[0]) == F(r[2]) and ('v', F(r[0])) in lines and F(r[4]) > 0
         and P5.density_at(('v', F(r[0])), min(F(r[1]), F(r[3])), max(F(r[1]), F(r[3]))) > 0)
f['F'][k][4] = '0'
expect('item 2: a left-band vertical row (on a line where P has mass) set to 0', not sc.band_check(item1(f)[2], P, Pp)['ok'])
# item 3
f = copy.deepcopy(fr5)
k = next(i for i, r in enumerate(f['F']) if 5 <= F(r[0]) < 6 and F(r[4]) > 0)
f['F'][k][4] = str(F(f['F'][k][4]) / 2)
Mf = sc.Measure.from_rows(f['F'], 'f'); Ml2 = sc.Measure.from_rows(fl2['F'], 'l2')
expect('item 3: final family with one transition mass halved no longer dominates L2', not sc.dominates(f, fl2, Mf, Ml2)[0])
f = copy.deepcopy(fr5); f['d1'] = '1/50'
expect('item 3: different d1', not sc.dominates(f, fl2, sc.Measure.from_rows(fr5['F'], 'f'), Ml2)[0])
# item 4
allr, touch = sc.r5_roots()
old = sc.D_BAND
sc.D_BAND = F(1, 2)
_, touch2 = sc.r5_roots()
sc.D_BAND = old
expect(f'item 4: band d = 1/2 changes the root set ({len(touch2)} roots)', set(touch2) != set(touch))
lst = [tuple(F(v) for v in r) for r in json.load(open(f'{base}/seams/roots_r5.json'))]
expect('item 4: one root removed from the list', set(lst[1:]) != set(touch))
# item 5
pieces = sc.record_roots(f'{pdir}/merged.rec') + sc.record_roots(f'{pdir}/L1/merged.rec') + sc.record_roots(f'{pdir}/L2/merged.rec')
d0, d1 = F(fr5['d0']), F(fr5['d1'])
expect('item 5: original pieces cover (control, must PASS)', sc.coverage(pieces, lst, d0, d1)['ok'])
expect('item 5: one piece dropped', not sc.coverage(pieces[1:], lst, d0, d1)['ok'])
expect('item 5: one piece duplicated', not sc.coverage(pieces + [pieces[5]], lst, d0, d1)['ok'])
p = list(pieces[7]); p[1] = p[1] + F(1, 10**6)
expect('item 5: one piece widened past its root', not sc.coverage(pieces[:7] + [tuple(p)] + pieces[8:], lst, d0, d1)['ok'])
q = list(pieces[9]); q[7] = q[7] / 2
expect('item 5: one piece with half the delta range', not sc.coverage(pieces[:9] + [tuple(q)] + pieces[10:], lst, d0, d1)['ok'])
# item 7
order = [r['name'].replace('interval_', '') for r in json.load(open(f'{base}/tables/m25_table.json'))]
ej = json.load(open(f'{base}/tables/seam_e_rigorous.json'))
edges = {(x['a'], x['b']): F(x['e']) for x in ej['pairs']}
for u, v in [('i040_042_a_b', 'i040_042_b'), ('i060_080_a_a_a', 'i060_080_a_a_b'), ('i060_080_a_a_b', 'i060_080_a_b_a'),
             ('i060_080_a_b_a', 'i060_080_a_b_b')]:
    edges[(u, v)] = F(0)
pj = json.load(open(f'{base}/tables/paths.json'))
def mism(ed):
    res = sc.paths(order, ed)
    return sum(1 for row in pj if F(row['E']) != res[(row['a'], row['b'])]['E'] or row['r'] != res[(row['a'], row['b'])]['r'])
expect('item 7: correct edges (control, must give 0 mismatches)', mism(edges) == 0)
e2 = dict(edges); e2[('i020_038', '038_040')] += F(1, 10**6)
expect('item 7: one e raised by 1e-6', mism(e2) > 0)
e3 = dict(edges); del e3[('i060_080_a_a_b', 'i060_080_a_b_a')]
e3[('i060_080_a_a_b', 'i060_080_a_b_a')] = F(1, 10**3)
expect('item 7: an equal-profile pair given e = 1/1000', mism(e3) > 0)
bad = sum(1 for _, d in results if not d)
print('ALL AS EXPECTED' if bad == 0 else f'{bad} UNEXPECTED')
sys.exit(1 if bad else 0)
