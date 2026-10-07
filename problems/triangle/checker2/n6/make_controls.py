"""Negative controls for the n = 6 second check: perturbed inputs written to controls/, each run must FAIL.

Usage: python make_controls.py [--jobs J] [--quick]   (--quick: a subset, a few minutes)
"""
import argparse
import copy
import json
import os
import subprocess
import sys
from fractions import Fraction

HERE = os.path.dirname(os.path.abspath(__file__))
N6 = os.environ.get('N6_CERTS', os.path.join(os.path.dirname(os.path.dirname(HERE)), 'certificates', 'n6'))
OUT = os.path.join(HERE, 'controls')
PY = sys.executable


def load(rel):
    return json.load(open(os.path.join(N6, rel)))


def save(name, d):
    p = os.path.join(OUT, name)
    json.dump(d, open(p, 'w'))
    return p


def run(args):
    r = subprocess.run([PY] + args, cwd=HERE, capture_output=True, text=True)
    last = (r.stdout.strip().splitlines() or [''])[-1].split()
    if last and last[0] in ('verified', 'failed'):      # lemma2.py ends with "<status> <seconds>"
        return last[0]
    try:
        js = json.loads(r.stdout[r.stdout.index('{'):])
    except ValueError:
        return 'error: ' + (r.stderr.strip().splitlines() or ['?'])[-1]
    return js.get('status', '?')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--jobs', default='6')
    ap.add_argument('--quick', action='store_true')
    a = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    J = a.jobs
    rows = []
    cg = ['cellgrid.py', '--pieces', '2000', '--jobs', J, '--min-width', '1/1000000']
    # cert_o13b
    c = load('stage2/cert_o13b.json')
    vs = {'o13b_Lplus.json': dict(c, L='201/100+4/3*sqrt3'),
          'o13b_drop0.json': dict(c, points=c['points'][1:]),
          'o13b_w0.json': dict(c, points=[dict(c['points'][0], w='1/4')] + c['points'][1:]),
          'o13b_dropexc.json': dict(c, exclusions=c['exclusions'][:1]),
          'o13b_noobs.json': dict(c, obstacle_points=[])}
    for name, d in vs.items():
        rows.append((name, run([*cg[:1], save(name, d), '--n', '4', *cg[1:]])))
    # cert_w_o0_p13_auto
    c = load('stage2/cert_w_o0_p13_auto.json')
    vs = {'o0_Lplus.json': dict(c, L='201/100+4/3*sqrt3'),
          'o0_noexc3.json': dict(c, exclusions=c['exclusions'][:2]),
          'o0_innerobs.json': dict(c, obstacle_points=c['obstacle_points'][:81])}
    drops = range(len(c['points'])) if not a.quick else (0, 7)
    for k in drops:
        d = copy.deepcopy(c)
        del d['points'][k]
        vs[f'o0_drop{k}.json'] = d
    for name, d in vs.items():
        rows.append((name, run([*cg[:1], save(name, d), '--n', '5', *cg[1:]])))
    # stage-1 window with every weight x 9/10
    c = copy.deepcopy(load('loc3/cert_e1_100.json'))
    for p in c['points']:
        p['w'] = str(Fraction(p['w']) * Fraction(9, 10))
    p = save('e1_w90.json', c)
    rows.append(('e1_w90.json (sweepwin window)',
                 run(['sweepwin.py', p, '--window', '2,23/10,4999/10000,50001/100000', '--E', '1/100000000'])))
    # obstacle points
    o13 = os.path.join(N6, 'stage2/cert_o13b.json')
    w1 = os.path.join(N6, 'stage2/cert_w_o1.json')
    wit = [('witness o13b without chain', [o13, '--obstacles', '1,3', '--D', '41/2500', '--DTH', '3/250']),
           ('witness o13b chain angle 1/10', [o13, '--obstacles', '1,3', '--D', '41/2500', '--DTH', '3/250', '--chain', '1:1/10']),
           ('witness w_o1 D = 3/100', [w1, '--obstacles', '1', '--D', '3/100', '--DTH', '1/100']),
           ('witness w_o1 DTH = 4/100', [w1, '--obstacles', '1', '--D', '1/100', '--DTH', '4/100'])]
    for name, args in wit:
        rows.append((name, run(['witness.py', *args, '--jobs', J])))
    rows.append(('lemma2 (1/10, 3/20, 3/50)', run(['lemma2.py', '--params', '1/10,3/20,3/50'])))
    bad = [r for r in rows if r[1] != 'failed']
    for name, st in rows:
        print(f'{name:40s} {st}')
    print('all controls failed as required' if not bad else f'UNEXPECTED: {bad}')
    sys.exit(1 if bad else 0)


if __name__ == '__main__':
    main()
