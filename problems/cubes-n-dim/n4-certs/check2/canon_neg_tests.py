"""Negative tests for canon_check2.py: break the canonical form of a certificate (the packing itself unchanged)
and require canon_check2 to object.
usage: python3 canon_neg_tests.py CERT.json"""
import json, os, subprocess, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))


def run(text):
    with tempfile.NamedTemporaryFile('w', suffix='.json', delete=False) as f:
        f.write(text)
    r = subprocess.run([sys.executable, '-I', '-B', os.path.join(HERE, 'canon_check2.py'), f.name], capture_output=True, text=True)
    os.unlink(f.name)
    return r.returncode, r.stdout.strip()


def dump(c):
    return json.dumps(c, separators=(',', ':')) + '\n'


c = json.load(open(sys.argv[1]))
cases = []
v = json.loads(json.dumps(c)); v['s'] = [v['s'][0] + '/1', v['s'][1]]
cases.append(('rule 1: "2/1" for 2', dump(v)))
v = json.loads(json.dumps(c)); a, b = v['s'][1].split('/'); v['s'][1] = f'{2 * int(a)}/{2 * int(b)}'
cases.append(('rule 1: a fraction not in lowest terms', dump(v)))
v = json.loads(json.dumps(c)); v['c'][0][0][1] = '0/1' if v['c'][0][0][1] == '0' else v['c'][0][0][1] + '/1'
cases.append(('rule 1: zero written "0/1"', dump(v)))
v = json.loads(json.dumps(c)); v['c'][0], v['c'][-1] = v['c'][-1], v['c'][0]; v['R'][0], v['R'][-1] = v['R'][-1], v['R'][0]
cases.append(('rule 4: first and last cubes swapped', dump(v)))
v = json.loads(json.dumps(c)); M = v['R'][-1]; v['R'][-1] = [[row[1], row[0]] + row[2:] for row in M]
cases.append(('rule 2: two columns of the last frame swapped', dump(v)))
v = json.loads(json.dumps(c)); M = v['R'][-1]; v['R'][-1] = [[[('-' + x[0]).replace('--', '') if x[0] != '0' else '0',
                                                                ('-' + x[1]).replace('--', '') if x[1] != '0' else '0']] + row[1:] for row in M for x in [row[0]]]
cases.append(('rule 2: first column of the last frame negated', dump(v)))
cases.append(('rule 5: indented json', json.dumps(c, indent=1) + '\n'))
cases.append(('rule 5: no final newline', dump(c)[:-1]))
v = {k: c[k] for k in ['n', 'format', 'k', 'd', 's', 'c', 'R']}
cases.append(('rule 5: keys out of order', dump(v)))
v = dict(c); v['note'] = 'x'
cases.append(('rule 5: an extra key', dump(v)))
rc, msg = run(open(sys.argv[1]).read())
print(f'original: rc {rc}: {msg}')
bad = rc != 0
for name, text in cases:
    rc, msg = run(text)
    ok = rc == 1
    bad += not ok
    print(f'  {"ok " if ok else "BAD"} {name}: {msg[:120]}')
print('ALL OK' if not bad else f'{bad} FAILURES')
sys.exit(1 if bad else 0)
