"""Negative tests of the leaf replay (seamleaf) on a small real record: the original passes, each corruption is refused.

usage: python3 leaf_neg.py INPUTS_DIR SEAMLEAF WORKDIR
"""
import copy
import json
import os
import subprocess
import sys
from fractions import Fraction as F

base, exe, work = sys.argv[1:4]
os.makedirs(work, exist_ok=True)
pdir = f'{base}/seams/i042_050_b_a_a_a__i042_050_b_b_b_b/L1'
fam = json.load(open(f'{pdir}/fam_fix.json'))
lines = open(f'{pdir}/merged.rec').read().splitlines()
results = []


def run(name, fam_obj, rec_lines, want_ok):
    fp, rp = f'{work}/{name}.fam.json', f'{work}/{name}.rec'
    json.dump(fam_obj, open(fp, 'w'))
    open(rp, 'w').write('\n'.join(rec_lines) + '\n')
    p = subprocess.run([exe, fp, rp, '--out', f'{work}/{name}.out.json'], capture_output=True, text=True)
    ok = p.returncode == 0
    good = ok == want_ok
    results.append(good)
    reason = ''
    if os.path.exists(f'{work}/{name}.out.json'):
        r = json.load(open(f'{work}/{name}.out.json'))
        reason = str(r['refusals'][:1])
    print(f'  {"ok " if good else "BAD"} {name}: exit {p.returncode} {(p.stderr.strip() or reason)[:110]}')


def roots():
    return [json.loads(l) for l in lines if not l.startswith('{"header"')]


def dump(rs):
    return [json.dumps(r) for r in rs]


run('original', fam, lines, True)
rs = roots(); multi = next(r for r in rs if len(r['leaves']) > 1); multi['leaves'] = multi['leaves'][1:]
run('leaf_dropped_tiling', fam, dump(rs), False)
rs = roots(); multi = next(r for r in rs if len(r['leaves']) > 1); multi['leaves'].append(copy.deepcopy(multi['leaves'][0]))
run('leaf_duplicated_tiling', fam, dump(rs), False)
rs = roots(); r0 = next(r for r in rs if any(k == 'CORE' for _, k in r['leaves']))
i = next(j for j, (_, k) in enumerate(r0['leaves']) if k == 'CORE'); r0['leaves'][i][1] = 'EMPTY'
run('CORE_relabelled_EMPTY', fam, dump(rs), False)
rs = roots(); rs[0]['uncert'] = [[rs[0]['root'], 'x']]
run('uncert_not_empty', fam, dump(rs), False)
rs = roots(); rs[0]['f3d'] = [[rs[0]['root'][:4], []]]
run('f3d_not_empty', fam, dump(rs), False)
rs = roots(); rs[0]['leaves'][0][1] = 'B9X'
run('unknown_kind', fam, dump(rs), False)
f = copy.deepcopy(fam); f['F'] = [r[:4] + [str(F(r[4]) / 2)] for r in f['F']]
run('family_masses_halved', f, lines, False)
f = copy.deepcopy(fam); f['d1'] = '1/200'
run('family_delta_shorter_than_leaves', f, lines, False)
rs = roots(); rs[0]['root'][4], rs[0]['root'][5] = '-1/64', '1/64'
for lf in rs[0]['leaves']:
    lf[0][4], lf[0][5] = '-1/64', '1/64'
run('root_crosses_u0', fam, dump(rs), False)
bad = sum(not g for g in results)
print('ALL AS EXPECTED' if bad == 0 else f'{bad} UNEXPECTED')
sys.exit(1 if bad else 0)
