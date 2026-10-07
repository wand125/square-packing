import copy
import json
from fractions import Fraction as F
import pytest
from test_physical_predicate_branch import fixture
from physical_predicate_conflict import strengthen
from reoptimize_capture_weights import reoptimize, replay


def test_physical_cuts_reweighted_and_tampering_rejected():
    old, base = fixture()
    source = strengthen(old, base['base'], base['box'], 2)
    new = [(x, y, w * 2) for x, y, w in old]
    artifact = json.loads(json.dumps(reoptimize(old, new, source, 2)))
    assert F(replay(old, new, source, 2, artifact)['lower']) >= 2
    bad = copy.deepcopy(source)
    bad['cuts'][0]['row']['rhs'] += 1
    with pytest.raises(ValueError):
        replay(old, new, bad, 2, artifact)
    with pytest.raises(ValueError):
        replay(old, new, source, 3, artifact)
    bad = copy.deepcopy(artifact)
    bad['lower'] = '100'
    with pytest.raises(ValueError):
        replay(old, new, source, 2, bad)


def test_plain_zero_weights_and_binding():
    old, base = fixture()
    source = base['base']
    new = [(x, y, F(0)) for x, y, w in old]
    artifact = reoptimize(old, new, source, 2)
    assert replay(old, new, source, 2, artifact)['lower'] == '0'
    with pytest.raises(ValueError):
        replay(old, old, source, 2, artifact)
    with pytest.raises(ValueError):
        reoptimize(old, [(x + 1, y, w) for x, y, w in old], source, 2)
    with pytest.raises(ValueError):
        reoptimize(old, [(x, y, -w) for x, y, w in old], source, 2)
