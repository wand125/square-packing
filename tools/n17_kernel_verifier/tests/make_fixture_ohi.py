"""An owned_hulls_intersect closure fixture, built like make_fixtures.py from the
supplied verifier only. Owner 1's seed group is a small owned triangle; owner 0's step-0
kernel and compression put one grid point inside it, so the hulls meet after step 0."""
import copy, gzip, hashlib, json
from fractions import Fraction as Q
from pathlib import Path
import make_fixtures as F

v, OUT, P, C = F.v, F.OUT, F.P, F.C
TRI = [['67/64', '67/64'], ['71/64', '67/64'], ['69/64', '71/64']]   # owned, inside [1, 1.1]^2
K = ['69/64', '68/64']                                                # inside TRI, on the 2^-20 grid


def build(kernel_point, declared):
    seed = copy.deepcopy(F.seed)
    seed['groups'] = {'0': [], '1': TRI}
    node = copy.deepcopy(F.node)
    node['source'] = {'sha256': hashlib.sha256(v.canonical(seed)).hexdigest()}
    node['initial']['groups'] = seed['groups']
    step = F.make_step(0, 0, seed['cells']['0'], seed['cells']['1'], seed['groups'], True)
    step['common_owned_kernel'] = [kernel_point]
    step['compression_source_hull'] = [kernel_point]
    step['inner_grid_compression'] = {'mode': 'replace', 'vertices': [kernel_point],
                                      'witnesses': [{'indices': [0], 'weights': ['1'], 'point': kernel_point}]}
    node.update(steps=[step], contradiction=declared, closed=True, terminal=True,
                final_state={'groups': {'0': [kernel_point], '1': TRI},
                             'cells': {'0': step['rows'], '1': seed['cells']['1']}})
    return seed, node


CASES = {
    'ohi': (K, {'kind': 'owned_hulls_intersect', 'owners': [0, 1], 'step': 0}),
    'ohi-wrong-kind': (K, {'kind': 'all_parent_poses_forbidden', 'owner': 0, 'step': 0}),
    'ohi-point-outside': (['66/64', '66/64'], {'kind': 'owned_hulls_intersect', 'owners': [0, 1], 'step': 0}),
}
for label, (point, declared) in CASES.items():
    seed, node = build(point, declared)
    path = OUT / label
    path.mkdir(exist_ok=True)
    for kind, data in (('seed', seed), ('node', node)):
        (path / f'{kind}-fixture.json.gz').write_bytes(gzip.compress(v.canonical(data), mtime=0))
    try:
        result = v.verify_objects(path, F.cells)
        expected = {'status': 'PASS' if result['closed'] else 'FAIL', 'closure': result['closure'], 'counts': result['counts']}
    except v.VerificationError as exc:
        expected = {'status': 'FAIL', 'failure': str(exc)}
    (OUT / f'{label}-expected.json').write_text(json.dumps(expected, indent=1) + '\n')
    print(label, expected)
