"""PL58 without branching: reuse checked predicate rows with new weights.

Coordinates and point order stay fixed. Omitted nonnegative uncertain mass
is not credited. Physical wall cuts require an independently supplied L.
"""
from fractions import Fraction as F
from compile_box_capture_rows import contains_all
from predicate_branch import replay_model, solve, replay_dual
from physical_predicate_branch import checked_model
from replay_capture_margin import replay_capture_margin
from reoptimize_physical_tree_weights import _digest


def compile_model(old_points, new_points, source, L):
    old = [tuple(map(F, p)) for p in old_points]
    new = [tuple(map(F, p)) for p in new_points]
    if any(len(p) != 3 for p in old + new) or [p[:2] for p in old] != [p[:2] for p in new]:
        raise ValueError('Changed support/order')
    if F(L) <= 0 or any(p[2] < 0 for p in old + new):
        raise ValueError('Invalid container or negative weight')
    if 'tree' in source:
        raise ValueError('Use the tree reoptimizer for branch proofs')
    checked = replay_capture_margin(old, source, L=L)
    if source.get('proof_type') == 'PHYSICAL_SIGNED_CONFLICTS':
        old_cost, rows, baseline, _, _ = checked_model(old, source, L)
    else:
        old_cost, rows, baseline = replay_model(old, source)
    plain = source
    while 'base' in plain:
        plain = plain['base']
    cost = [F(0)] * len(old_cost)
    mapped = cost.copy()
    next_y = plain['predicates']
    for rec in plain.get('point_records', []):
        ids = rec['predicates']
        j = ids[0] if len(ids) == 1 else next_y
        if len(ids) > 1:
            next_y += 1
        mapped[j] += old[rec['point']][2]
        cost[j] += new[rec['point']][2]
    if next_y != len(cost) or mapped != old_cost:
        raise ValueError('Source cost mapping mismatch')
    always = [i for i, p in enumerate(old) if contains_all(p[:2], source['box'])]
    if set(always) & {rec['point'] for rec in plain.get('point_records', [])}:
        raise ValueError('Overlapping baseline and uncertain costs')
    if sum((old[i][2] for i in always), F()) != baseline:
        raise ValueError('Source baseline mismatch')
    B = sum((new[i][2] for i in always), F())
    binding = dict(L=str(F(L)), box=source['box'], source_proof_sha256=_digest(source),
                   old_points_sha256=_digest(old), new_points_sha256=_digest(new))
    return cost, rows, B, binding, checked


def reoptimize(old_points, new_points, source, L):
    cost, rows, B, binding, _ = compile_model(old_points, new_points, source, L)
    if not cost:
        raise ValueError('Use a direct baseline proof for an empty LP model')
    solution, dual = solve(cost, rows)
    if dual is None:
        raise RuntimeError('No verified new dual: ' + solution.message)
    q = B + replay_dual(cost, rows, dual)
    return dict(binding=binding, cost=list(map(str, cost)), baseline=str(B),
                dual=dual, lower=str(q), general_coverage_verified=False)


def replay(old_points, new_points, source, L, artifact):
    cost, rows, B, binding, checked = compile_model(old_points, new_points, source, L)
    if artifact['binding'] != binding or artifact['cost'] != list(map(str, cost)) or artifact['baseline'] != str(B):
        raise ValueError('Changed weight/geometry binding')
    q = B + replay_dual(cost, rows, artifact['dual'])
    if artifact['lower'] != str(q):
        raise ValueError('New lower mismatch')
    return dict(lower=str(q), vacuous=False, certified_unit_capture=q >= 1,
                source_replay=checked, new_duals_replayed=True, general_coverage_verified=False)
