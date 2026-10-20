"""Hand-made tests for alg_check2.py: exact irrational boundary cases in Q(sqrt 2) and Q(sqrt 3).
usage: python3 alg_hand_tests.py"""
import json, os, subprocess, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))


def run(c):
    with tempfile.NamedTemporaryFile('w', suffix='.json', delete=False) as f:
        json.dump(c, f)
    r = subprocess.run([sys.executable, '-I', '-B', os.path.join(HERE, 'alg_check2.py'), f.name], capture_output=True, text=True)
    os.unlink(f.name)
    return r.returncode, r.stdout.strip()


Z, H2 = ['0', '0'], ['0', '1/2']
cases = []
# a unit square turned by 45 degrees fills [0, sqrt 2]^2 exactly
sq45 = {'format': 'alg-v1', 'n': 2, 'k': 1, 'd': 2, 's': ['0', '1'], 'c': [[H2, H2]],
        'R': [[[H2, ['0', '-1/2']], [H2, H2]]]}
cases.append(('45 deg square in [0, sqrt2]^2', sq45, 0))
v = json.loads(json.dumps(sq45)); v['s'] = ['-1/1000000', '1']
cases.append(('same, s smaller by 1e-6', v, 1))
# a unit square turned by 30 degrees fills [0, (1 + sqrt3)/2]^2 exactly
c30, s30 = ['0', '1/2'], ['1/2', '0']
sq30 = {'format': 'alg-v1', 'n': 2, 'k': 1, 'd': 3, 's': ['1/2', '1/2'], 'c': [[['1/4', '1/4'], ['1/4', '1/4']]],
        'R': [[[c30, ['-1/2', '0']], [s30, c30]]]}
cases.append(('30 deg square in [0, (1+sqrt3)/2]^2', sq30, 0))
v = json.loads(json.dumps(sq30)); v['s'] = ['1/2', '1/2 '.strip()]; v['s'] = ['1/2', '499999/1000000']
cases.append(('same, s smaller in the sqrt3 part', v, 1))
v = json.loads(json.dumps(sq30)); v['d'] = 2
cases.append(('the 30 deg file read with d = 2 (frame not orthogonal)', v, 1))
# two 45 deg squares side by side touching along a diagonal edge: centres sqrt 2 apart on the x axis
two = {'format': 'alg-v1', 'n': 2, 'k': 2, 'd': 2, 's': ['0', '2'], 'c': [[H2, ['0', '1']], [['0', '3/2'], ['0', '1']]],
       'R': [[[H2, ['0', '-1/2']], [H2, H2]], [[H2, ['0', '-1/2']], [H2, H2]]]}
cases.append(('two 45 deg squares, corners touching, in [0, 2 sqrt2] x ...', two, 0))
v = json.loads(json.dumps(two)); v['c'][1][0] = ['-1/1000000', '3/2']
cases.append(('same, pushed together by 1e-6', v, 1))
bad = 0
for name, c, want in cases:
    rc, msg = run(c)
    bad += rc != want
    print(f'{"ok " if rc == want else "BAD"} {name}: rc {rc}: {msg[:110]}')
print('ALL OK' if not bad else f'{bad} FAILURES')
sys.exit(1 if bad else 0)
