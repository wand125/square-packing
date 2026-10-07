"""Replay saved local refinements; never certify the untouched global cover."""
import argparse
import hashlib
import json
from fractions import Fraction as F
from pathlib import Path
from full_pose_low_cover import root_box, split
from mixed_density_check import expand
from physical_pose_bound import physical_lower_bound
from pose_symmetry import cached_bound


def check_tree(root, leaves, bound):
    if not leaves:
        raise ValueError('Empty local cover')
    prefixes = set()
    for path in leaves:
        if not isinstance(path, str) or set(path) - set('01'):
            raise ValueError('Invalid binary path')
        prefixes.update(path[:i] for i in range(len(path) + 1))
    stack = [('', root)]
    seen = set()
    values = []
    while stack:
        path, box = stack.pop()
        if path in leaves:
            row = leaves[path]
            if tuple(map(F, row['box'])) != box:
                raise ValueError('Wrong leaf box')
            value = bound(*box)
            if value != F(row['lower']):
                raise ValueError('Wrong leaf lower bound')
            values.append(value)
            seen.add(path)
        else:
            if path + '0' not in prefixes or path + '1' not in prefixes:
                raise ValueError('Missing child')
            left, right = split(box)
            stack.extend([(path + '0', left), (path + '1', right)])
    if seen != set(leaves):
        raise ValueError('Leaf below terminal ancestor')
    return values


def replay(candidate, source, local):
    model = expand(json.loads(candidate.read_text()))
    cover = json.loads(source.read_text())
    q = json.loads(local.read_text())
    if hashlib.sha256(source.read_bytes()).hexdigest() != q['source_sha256']:
        raise ValueError('Source hash mismatch')
    if cover['digest'] != model[-1]:
        raise ValueError('Candidate mismatch')
    bound = cached_bound(model, physical_lower_bound, cover.get('symmetry'))[0]
    records = []
    roots = set()
    for rec in q['records']:
        path = rec['source_path']
        if not isinstance(path, str) or set(path) - set('01') or path in roots:
            raise ValueError('Invalid or repeated root')
        roots.add(path)
        box = root_box(model[0])
        for bit in path:
            box = split(box)[int(bit)]
        if tuple(map(F, rec['root'])) != box or tuple(map(F, cover['leaves'][path]['box'])) != box:
            raise ValueError('Root not anchored in global tree')
        values = check_tree(box, rec['leaves'], bound)
        threshold = F(rec['threshold'])
        minimum = min(values)
        unresolved = sum(v < threshold for v in values)
        if minimum != F(rec['minimum']) or unresolved != rec['unresolved']:
            raise ValueError('Wrong summary')
        records.append(dict(source_path=path, leaves=len(values), minimum=str(minimum), unresolved=unresolved))
    if not records:
        raise ValueError('No local trees')
    return dict(status='EXACT_LOCAL_POSE_TREES_REPLAYED', records=records,
                source_sha256=q['source_sha256'], candidate_digest=model[-1],
                untouched_global_cover_replayed=False, general_packing_exclusion=False)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('candidate', 'source', 'local', 'out'):
        p.add_argument(name, type=Path)
    a = p.parse_args()
    result = replay(a.candidate, a.source, a.local)
    a.out.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result), flush=True)
