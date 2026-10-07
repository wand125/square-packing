"""Exact local exclusions in DIRECT normalized domains, never reference IDs.

A verified case excludes its chosen subset only under the stated occupied
axis cells and fixed rotor band. It is not an unrestricted packing bound.
"""
import argparse
import json
from pathlib import Path
from normalized_axis_cells import geometry, model
from saturated_joint_search import search_model, replay_model

TAG = 'DIRECT_NORMALIZED_STRICT_CORES_V1'


def reconstruct(q):
    assert q['model'] == TAG
    assert q['coordinate_system'] == 'DIRECT_NORMALIZED_CELL_CENTRES'
    missing = q['missing']; chosen = q['chosen']
    assert isinstance(missing, list) and missing == sorted(set(missing))
    assert isinstance(chosen, list) and chosen and chosen == sorted(set(chosen))
    _, pieces = geometry(q['config'], missing)
    assert all(type(i) is int and 0 <= i < len(pieces) for i in chosen)
    return model(q['config'], missing, chosen, reference_pieces=False, strict=True)


def verify(q):
    data = reconstruct(q)
    return replay_model(data, q['tree'], positive_index=len(data[0][0])-1)


def run(config, missing, chosen, nodes=100):
    q = dict(model=TAG, coordinate_system='DIRECT_NORMALIZED_CELL_CENTRES',
             config=config, missing=list(missing), chosen=list(chosen))
    data = reconstruct(q)
    q.update(search_model(data, nodes, branch_rule='fewest',
                          positive_index=len(data[0][0])-1))
    q['verified'] = verify(q)
    return q


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path)
    p.add_argument('out', type=Path)
    p.add_argument('--chosen', type=int, nargs='+', required=True)
    p.add_argument('--missing', type=int, nargs='*', default=[])
    p.add_argument('--nodes', type=int, default=100)
    a = p.parse_args()
    assert a.nodes > 0 and not a.out.exists()
    q = run(json.loads(a.source.read_text())['config'], a.missing, a.chosen, a.nodes)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    with a.out.open('x') as f:
        json.dump(q, f, indent=2)
    print(q['status'], q['verified'], flush=True)
