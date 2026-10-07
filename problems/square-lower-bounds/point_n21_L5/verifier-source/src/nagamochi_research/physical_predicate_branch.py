"""PL47 trees retaining PL48 wall assumptions and cuts at every node."""
from fractions import Fraction as F
import json
from physical_predicate_conflict import model, reduce_wall_clause, replay as replay_base
from predicate_conflict import find_conflict
from predicate_branch import solve_tree, replay_tree


def checked_model(points, base, expected_L):
    replay_base(points, base, expected_L)
    cost, rows, baseline, polys, n = model(points, base['base'], base['box'], expected_L)
    rows += [cut['row'] for cut in base['cuts']]
    return cost, rows, baseline, polys, n


def callbacks(polys, n, box):
    def verify(cut):
        row = reduce_wall_clause(polys, n, box, cut)
        if json.loads(json.dumps(row)) != json.loads(json.dumps(cut['row'])):
            raise ValueError('Physical branch cut mismatch')
        return row
    def propose(x):
        cut = find_conflict(polys, [int(v>=.5) for v in x[:n]]+[1]*4, box)
        if cut is None:return None
        row = reduce_wall_clause(polys, n, box, cut)
        return dict(pattern=cut['pattern'], multipliers=cut['multipliers'], row=row)
    return propose, verify


def branch(points, base, expected_L, *, max_depth=6, max_nodes=127):
    cost, rows, baseline, polys, n = checked_model(points, base, expected_L)
    propose, verify = callbacks(polys, n, base['box'])
    tree = solve_tree(cost, rows, baseline, max_depth=max_depth, max_nodes=max_nodes,
                      cut_proposer=propose, cut_verifier=verify)
    record = dict(tree, proof_type='PHYSICAL_PREDICATE_TREE', base=base,
                  L=str(F(expected_L)), box=base['box'])
    record['physical_replay'] = replay(points, record, expected_L)
    return record


def replay(points, record, expected_L):
    if record.get('proof_type')!='PHYSICAL_PREDICATE_TREE' or F(record['L'])!=F(expected_L):
        raise ValueError('Physical branch container mismatch')
    if tuple(map(F,record['box']))!=tuple(map(F,record['base']['box'])):
        raise ValueError('Physical branch box mismatch')
    cost, rows, baseline, polys, n = checked_model(points, record['base'], expected_L)
    _, verify = callbacks(polys, n, record['box'])
    checked = replay_tree(cost, rows, baseline, F(record['target']), record['tree'], cut_verifier=verify)
    # If a tree is incomplete, retain the verified box-wide physical base
    # bound rather than silently deleting its open branches.
    lower = record['target'] if checked['certified_unit_capture'] else record['base']['lower']
    return dict(checked, lower=lower, scope='physically admissible poses in box', L=str(F(expected_L)))
