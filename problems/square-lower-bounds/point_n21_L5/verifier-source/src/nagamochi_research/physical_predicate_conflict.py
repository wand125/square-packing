"""Signed-predicate cuts conditional on all four physical container walls.

These proofs cover only physically admissible poses, not the entire pose box.
The container side must be supplied independently by the replay caller.
"""
from fractions import Fraction as F
from itertools import product
import json
from predicate_conflict import geometry_polynomials, find_conflict, verify_sum
from predicate_branch import replay_model, solve, replay_dual


def wall_polynomials(L, box):
    L = F(L)
    b = list(map(F, box))
    if L <= 0 or len(b) != 6 or any(b[k] > b[k+1] for k in (0,2,4)) or not 0 <= b[4] <= b[5] <= F(1,2):
        raise ValueError('Invalid physical domain')
    corners = list(product((b[0], b[1]), (b[2], b[3])))
    # 2(1+t²)(h(t)-cx), 2(1+t²)(cx+h(t)-L), and y analogues.
    return [[(1-2*x, F(2), -1-2*x) for x,y in corners],
            [(1-2*L+2*x, F(2), -1-2*L+2*x) for x,y in corners],
            [(1-2*y, F(2), -1-2*y) for x,y in corners],
            [(1-2*L+2*y, F(2), -1-2*L+2*y) for x,y in corners]]


def reduce_wall_clause(polynomials, n, box, cut):
    if len(cut['pattern']) != n+4 or cut['pattern'][n:] != [1]*4:
        raise ValueError('Physical walls must all be true')
    full = verify_sum(polynomials, cut['pattern'], box, cut['multipliers'])
    # Wall predicates have fixed value one. Substitute them, rather than
    # adding free LP variables or treating physical assumptions as conclusions.
    return dict(terms=[(j,v) for j,v in full['terms'] if j<n],
                rhs=full['rhs']-sum(v for j,v in full['terms'] if j>=n),
                kind='physical_signed_conflict')


def model(points, base, box, L):
    if tuple(map(F, base['box'])) != tuple(map(F, box)):
        raise ValueError('Changed physical proof box')
    plain = base['base'] if 'base' in base else base
    if not plain.get('cost'):
        raise ValueError('Physical cuts require a nontrivial stored predicate model')
    cost, rows, baseline = replay_model(points, base)
    polys = geometry_polynomials(points, plain, box)
    return cost, list(rows), baseline, polys+wall_polynomials(L, box), len(polys)


def strengthen(points, base, box, L, max_cuts=16):
    if type(max_cuts) is not int or max_cuts < 0:
        raise ValueError('Invalid cut budget')
    cost, rows, baseline, polys, n = model(points, base, box, L)
    cuts, history = [], []
    for step in range(max_cuts+1):
        solution, dual = solve(cost, rows)
        if dual is None:
            raise RuntimeError('Physical cut LP failed: '+solution.message)
        lower = baseline+F(dual['lower'])
        history.append(str(lower))
        if lower >= 1:
            reason = 'CERTIFIED'; break
        if step == max_cuts:
            reason = 'CUT_LIMIT'; break
        proposal = find_conflict(polys, [int(x>=.5) for x in solution.x[:n]]+[1]*4, box)
        if proposal is None:
            reason = 'NO_CONFLICT_CERTIFICATE'; break
        row = reduce_wall_clause(polys, n, box, proposal)
        if sum(float(v)*solution.x[j] for j,v in row['terms']) >= row['rhs']-1e-9:
            reason = 'CUT_NOT_VIOLATED'; break
        cuts.append(dict(pattern=proposal['pattern'], multipliers=proposal['multipliers'], row=row))
        rows.append(row)
    return dict(proof_type='PHYSICAL_SIGNED_CONFLICTS', L=str(F(L)), box=list(map(str,box)),
                base=base, cuts=cuts, dual=dual, lower=str(lower), history=history,
                stop_reason=reason, general_coverage_verified=False)


def replay(points, record, expected_L):
    if record.get('proof_type') != 'PHYSICAL_SIGNED_CONFLICTS' or F(record['L']) != F(expected_L):
        raise ValueError('Physical proof container mismatch')
    cost, rows, baseline, polys, n = model(points, record['base'], record['box'], expected_L)
    for cut in record['cuts']:
        row = reduce_wall_clause(polys, n, record['box'], cut)
        if json.loads(json.dumps(row)) != json.loads(json.dumps(cut['row'])):
            raise ValueError('Physical cut mismatch')
        rows.append(row)
    lower = baseline+replay_dual(cost, rows, record['dual'])
    if str(lower) != record['lower']:
        raise ValueError('Physical lower mismatch')
    return dict(lower=str(lower), certified_unit_capture=lower>=1,
                scope='physically admissible poses in box', L=str(F(expected_L)),
                conflicts_replayed=len(record['cuts']), general_coverage_verified=False)
