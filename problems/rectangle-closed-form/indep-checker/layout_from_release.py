#!/usr/bin/env python3
"""Rebuild, from the release, the input layout that seam_check2.py and jobs.tsv read.

The second check was run on the records and families in their working layout, which names intervals by labels
(tables/intervals_order.json gives the label of each interval number) instead of the numbers used in the release:

    INPUTS/families/<label>.json                  the interval family (here: the published family from the release)
    INPUTS/seams/roots_r5.json                    the R5 root list
    INPUTS/seams/<A>__<B>/fam.json, merged.rec    level 0 of the seam between intervals A and B
    INPUTS/seams/<A>__<B>/L<j>/fam_fix.json, L<j>/merged.rec   level j >= 1
    INPUTS/seams/<A>__<B>/fam_r5.json             the final family, where it was repaired after the last level
    INPUTS/seams/<A>__<B>/fam_r1.json, *.rec      the two seams checked as one level before the others (their
                                                  records keep their release names)
    INPUTS/tables/seam_e_rigorous.json, m25_table.json, paths.json   copies of tables/ in this folder

This script was written for publication; it was not part of the run. The run read the interval families in their
working byte format; the published families are equal to them as rationals (checked), and seam_check2.py reads
families as rationals. The records in the release differ from the records that were checked only in their first
line (../data/seam_records.json), so seam_check2.py --leaf-reports with the published leaf reports reports a hash
mismatch on the release records; items 1 to 5 and 7 are unaffected, and new leaf reports can be made with seamleaf.

usage: layout_from_release.py RELEASE_DIR INPUTS_DIR
"""
import glob
import json
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
R1 = ('seam_08_09', 'seam_11_12')  # the two seams checked as one level before the others


def main(rel, out):
    order = [r['name'].replace('interval_', '') for r in json.load(open(os.path.join(HERE, 'tables', 'intervals_order.json')))]
    iv = json.load(open(os.path.normpath(os.path.join(HERE, '..', '..', 'closed-form', 'intervals.json'))))
    iv = iv.get('intervals', iv)
    os.makedirs(os.path.join(out, 'families'))
    for e in iv:
        src = os.path.join(rel, 'families', e['asset'].replace('.tar.gz', ''), 'family.json')
        shutil.copy(src, os.path.join(out, 'families', order[e['index'] - 1] + '.json'))
    seams = os.path.join(rel, 'rectangle-closed-form-v1')
    os.makedirs(os.path.join(out, 'seams'))
    shutil.copy(os.path.join(seams, 'roots_r5.json'), os.path.join(out, 'seams', 'roots_r5.json'))
    for e in json.load(open(os.path.join(HERE, '..', 'data', 'edges.json')))['edges']:
        if e['kind'] != 'seam':
            continue
        s = os.path.join(seams, e['folder'])
        d = os.path.join(out, 'seams', order[e['a'] - 1] + '__' + order[e['b'] - 1])
        os.makedirs(d)
        levels = sorted(os.path.basename(p) for p in glob.glob(os.path.join(s, 'L*')))
        if e['folder'] in R1:
            shutil.copy(os.path.join(s, 'L0', 'family.json'), os.path.join(d, 'fam_r1.json'))
            for p in glob.glob(os.path.join(s, 'L0', '*.rec')):
                name = 'merged.rec' if os.path.basename(p) == 'record.rec' else os.path.basename(p)
                shutil.copy(p, os.path.join(d, name))
            shutil.copy(os.path.join(seams, 'roots_r5.json'), os.path.join(d, 'roots_r5.json'))
            continue
        for L in levels:
            j = int(L[1:])
            t = d if j == 0 else os.path.join(d, L)
            os.makedirs(t, exist_ok=True)
            shutil.copy(os.path.join(s, L, 'family.json'), os.path.join(t, 'fam.json' if j == 0 else 'fam_fix.json'))
            shutil.copy(os.path.join(s, L, 'record.rec'), os.path.join(t, 'merged.rec'))
        last = os.path.join(s, levels[-1], 'family.json')
        if open(os.path.join(s, 'family_final.json'), 'rb').read() != open(last, 'rb').read():
            shutil.copy(os.path.join(s, 'family_final.json'), os.path.join(d, 'fam_r5.json'))
    os.makedirs(os.path.join(out, 'tables'))
    for a, b in (('seam_e.json', 'seam_e_rigorous.json'), ('intervals_order.json', 'm25_table.json'),
                 ('paths_internal.json', 'paths.json')):
        shutil.copy(os.path.join(HERE, 'tables', a), os.path.join(out, 'tables', b))
    print('layout written to', out)


if __name__ == '__main__':
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])
