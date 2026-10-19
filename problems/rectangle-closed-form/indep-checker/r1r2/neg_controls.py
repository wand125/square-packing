#!/usr/bin/env python3
"""Negative controls for rect_r1r2_all.py: each corrupted copy of a family (or of intervals.json) must FAIL.
The content checks are exercised with --no-sha (otherwise the sha256 binding alone would reject every copy); one
extra control keeps the binding on and changes nothing but one byte of a family.

usage: python3 neg_controls.py FAMILIES_DIR INTERVALS_JSON [INDEX]     (ends with ALL CONTROLS FAIL AS REQUIRED)
"""
import copy
import json
import shutil
import subprocess
import sys
import tempfile
from fractions import Fraction as Q
from pathlib import Path

HERE = Path(__file__).resolve().parent


def run(fam_dir, ipath, index, extra=()):
    r = subprocess.run([sys.executable, str(HERE / 'rect_r1r2_all.py'), str(fam_dir), str(ipath), '--only', str(index), *extra],
                       capture_output=True, text=True)
    return r.returncode, r.stdout


def main(argv):
    fam_dir, ipath = Path(argv[1]), Path(argv[2])
    index = int(argv[3]) if len(argv) > 3 else 34
    data = json.loads(ipath.read_bytes())
    entry = next(e for e in data['intervals'] if e['index'] == index)
    asset = entry['asset'][:-len('.tar.gz')]
    family = json.loads((fam_dir / asset / 'family.json').read_bytes())

    def f_mass(f):            # one corner row (F, both ends with y <= 2 and x <= 2): mass + 1/10^6
        for row in f['F']:
            if all(Q(v) <= 2 for v in row[:4]) and Q(row[4]) > 0:
                row[4] = str(Q(row[4]) + Q(1, 10**6))
                return
        raise SystemExit('no corner row')

    def t_shift(f):           # one wall-period row of T in [5, 6): x + 1/100
        for row in f['T']:
            if all(5 <= Q(row[i]) <= 6 for i in (0, 2)) and Q(row[0]) != Q(row[2]):
                for i in (0, 2):
                    row[i] = str(Q(row[i]) + Q(1, 100))
                return
        raise SystemExit('no wall row')

    def wrong_d1(f):          # d1 of the family differs from intervals.json
        f['d1'] = str(Q(f['d1']) - Q(1, 1000))

    def v_negative(f):        # a negative V density
        f['V'][0][2] = str(-Q(1, 10**6))

    def u_shift(f):           # a non-standard Lebesgue part
        f['U'] = [['9/5', '2'], ['1000', '2'], ['1000', '1000'], ['9/5', '1000']]

    def t_drop(f):            # drop one T row (a missing zero-mass piece would be invisible; this one has mass)
        f['T'].pop(len(f['T']) // 2)

    cases = [('perturbed corner mass in F (+1e-6)', f_mass, None), ('wall period row shifted by 1/100', t_shift, None),
             ('wrong d1 in the family', wrong_d1, None), ('negative V density', v_negative, None),
             ('non-standard U', u_shift, None), ('one T row removed', t_drop, None),
             ('certified line raised by 1e-9 (intervals.json)', None, 'line'),
             ('one byte changed, sha binding on', None, 'byte')]
    bad = 0
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        for name, fmut, imut in cases:
            fd = td / 'fam'
            if fd.exists():
                shutil.rmtree(fd)
            (fd / asset).mkdir(parents=True)
            f2 = copy.deepcopy(family)
            if fmut:
                fmut(f2)
            text = json.dumps(f2)
            if imut == 'byte':
                text = (fam_dir / asset / 'family.json').read_text() + ' '
            (fd / asset / 'family.json').write_text(text)
            d2 = copy.deepcopy(data)
            if imut == 'line':
                e2 = next(e for e in d2['intervals'] if e['index'] == index)
                e2['certified_line']['beta'] = str(Q(e2['certified_line']['beta']) + Q(1, 10**9))
            ip2 = td / 'intervals.json'
            ip2.write_text(json.dumps(d2))
            rc, out = run(fd, ip2, index, () if imut == 'byte' else ('--no-sha',))
            fails = [ln.strip() for ln in out.splitlines() if ln.strip().startswith('FAIL')]
            ok = rc != 0
            bad += not ok
            print(f'{"rejected" if ok else "NOT REJECTED"}  {name}: {fails[0][:110] if fails else out.strip().splitlines()[-1][:110]}')
    print('ALL CONTROLS FAIL AS REQUIRED' if not bad else f'{bad} controls were not rejected')
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
