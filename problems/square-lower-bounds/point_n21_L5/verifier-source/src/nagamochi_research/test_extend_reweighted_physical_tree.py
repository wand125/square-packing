from fractions import Fraction as F
import copy
import json
import pytest
from test_physical_predicate_branch import fixture
from physical_predicate_branch import checked_model, callbacks
from predicate_branch import solve_tree
from extend_reweighted_physical_tree import extend, replay


def source_fixture(split=False):
    old, base = fixture()
    cost, rows, B, polys, n = checked_model(old, base, 2)
    if split:
        propose, verify = callbacks(polys, n, base['box'])
        tree = dict(kind='BRANCH', variable=0, children={str(t): solve_tree(
            cost, rows + [dict(terms=[(0, 1 if t else -1)], rhs=t)], B,
            cut_proposer=propose, cut_verifier=verify)['tree'] for t in (0, 1)})
    else:
        tree = solve_tree(cost, rows, B, max_nodes=1)['tree']
    return old, dict(proof_type='PHYSICAL_PREDICATE_TREE', L='2', box=base['box'],
                     base=base, target='1', tree=tree)


def test_new_cut_replay_and_tampering():
    old, source = source_fixture()
    new = [(x, y, w * F(6, 5)) for x, y, w in old]
    artifact = json.loads(json.dumps(extend(old, new, source, 2)))
    assert F(replay(old, new, source, 2, artifact)['lower']) >= F(6, 5)
    assert artifact['tree']['tree']['kind'] == 'CUT'
    bad = copy.deepcopy(artifact)
    bad['tree']['tree']['cut']['row']['rhs'] += 1
    with pytest.raises(ValueError):
        replay(old, new, source, 2, bad)
    with pytest.raises(ValueError):
        replay(old, old, source, 2, artifact)


def test_old_branches_and_empty_are_retained():
    old, source = source_fixture(split=True)
    artifact = extend(old, old, source, 2)
    assert replay(old, old, source, 2, artifact)['certified_unit_capture']
    empty = artifact['tree']['children']['0']
    while empty['kind'] == 'SOURCE_CUT':
        empty = empty['child']
    assert empty['kind'] == 'SOURCE_EMPTY'
    bad = copy.deepcopy(artifact)
    del bad['tree']['children']['0']
    with pytest.raises(ValueError):
        replay(old, old, source, 2, bad)
    bad = copy.deepcopy(artifact)
    bad['tree']['children']['1'] = dict(kind='SOURCE_EMPTY')
    with pytest.raises(ValueError):
        replay(old, old, source, 2, bad)


def test_budget_exhaustion_and_forged_result():
    old, source = source_fixture()
    artifact = extend(old, old, source, 2, max_nodes=1)
    checked = replay(old, old, source, 2, artifact)
    assert not checked['vacuous'] and not checked['certified_unit_capture']
    assert checked['lower'] == '0'
    bad = copy.deepcopy(artifact)
    bad['lower'] = '1'
    with pytest.raises(ValueError):
        replay(old, old, source, 2, bad)
