"""Retain a checked old tree and extend its leaves under new weights.

Every new cut is verified geometrically. New open leaves remain unproved;
old EMPTY leaves are reused only after replay of the complete old proof.
"""
from fractions import Fraction as F
from reoptimize_physical_tree_weights import _compile
from physical_predicate_branch import checked_model, callbacks
from predicate_branch import solve_tree
from replay_capture_margin import replay_tree_margin


def _prepare(old, new, source, L):
    cost, rows, B, binding, checked = _compile(old, new, source, L)
    _, _, _, polys, n = checked_model(old, source['base'], L)
    propose, verify = callbacks(polys, n, source['box'])
    return cost, rows, B, binding, checked, propose, verify


def _replay(source, saved, cost, rows, B, verify):
    kind = source['kind']
    if kind == 'CUT':
        if saved['kind'] != 'SOURCE_CUT':
            raise ValueError('Missing source cut')
        return _replay(source['child'], saved['child'], cost,
                       rows + [source['cut']['row']], B, verify)
    if kind == 'BRANCH':
        j = source['variable']
        if saved['kind'] != 'SOURCE_BRANCH' or saved['variable'] != j or set(saved['children']) != {'0', '1'}:
            raise ValueError('Changed or incomplete source branches')
        values = [_replay(source['children'][str(t)], saved['children'][str(t)],
                          cost, rows + [dict(terms=[(j, 1 if t else -1)], rhs=t)],
                          B, verify) for t in (0, 1)]
        values = [v for v in values if v is not None]
        return min(values) if values else None
    if kind == 'EMPTY':
        if saved['kind'] != 'SOURCE_EMPTY':
            raise ValueError('Changed source empty leaf')
        return None
    if saved['kind'] != 'EXTENSION' or F(saved['target']) != 1:
        raise ValueError('Missing new leaf proof')
    checked = replay_tree_margin(cost, rows, B, F(1), saved['tree'], cut_verifier=verify)
    return None if checked['vacuous'] else max(B, F(checked['lower']))


def extend(old, new, source, L, *, max_depth=6, max_nodes=255):
    cost, rows, B, binding, _, propose, verify = _prepare(old, new, source, L)

    def visit(node, active):
        kind = node['kind']
        if kind == 'CUT':
            return dict(kind='SOURCE_CUT', child=visit(node['child'], active + [node['cut']['row']]))
        if kind == 'BRANCH':
            j = node['variable']
            return dict(kind='SOURCE_BRANCH', variable=j, children={str(t): visit(
                node['children'][str(t)], active + [dict(terms=[(j, 1 if t else -1)], rhs=t)]
            ) for t in (0, 1)})
        if kind == 'EMPTY':
            return dict(kind='SOURCE_EMPTY')
        extra = solve_tree(cost, active, B, max_depth=max_depth, max_nodes=max_nodes,
                           cut_proposer=propose, cut_verifier=verify)
        return dict(kind='EXTENSION', target=extra['target'], tree=extra['tree'])

    tree = visit(source['tree'], rows)
    q = _replay(source['tree'], tree, cost, rows, B, verify)
    return dict(binding=binding, cost=list(map(str, cost)), baseline=str(B),
                tree=tree, lower=None if q is None else str(q),
                vacuous=q is None, general_coverage_verified=False)


def replay(old, new, source, L, artifact):
    cost, rows, B, binding, checked, _, verify = _prepare(old, new, source, L)
    if artifact['binding'] != binding or artifact['cost'] != list(map(str, cost)) or artifact['baseline'] != str(B):
        raise ValueError('Changed weight/geometry binding')
    q = _replay(source['tree'], artifact['tree'], cost, rows, B, verify)
    if artifact['lower'] != (None if q is None else str(q)) or artifact['vacuous'] != (q is None):
        raise ValueError('Saved result mismatch')
    return dict(lower=artifact['lower'], vacuous=q is None,
                certified_unit_capture=q is None or q >= 1,
                source_replay=checked, new_tree_replayed=True,
                general_coverage_verified=False)
