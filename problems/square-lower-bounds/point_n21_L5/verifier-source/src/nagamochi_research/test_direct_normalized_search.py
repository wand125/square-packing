from copy import deepcopy
from fractions import Fraction as F
import pytest
import direct_normalized_search as direct


def test_direct_namespace_and_positive_gap_certificate(monkeypatch):
    monkeypatch.setattr(direct, 'geometry', lambda config, missing: ({}, [[], []]))
    def build(config, missing, chosen, **kwargs):
        assert kwargs == dict(reference_pieces=False, strict=True)
        return ([[F(1)]], [F(0)], [], [], [])
    monkeypatch.setattr(direct, 'model', build)
    q = dict(model=direct.TAG, coordinate_system='DIRECT_NORMALIZED_CELL_CENTRES',
             config={}, missing=[], chosen=[0, 1],
             tree=dict(status='EXACT_NONPOSITIVE_COORDINATE',
                       bound=dict(index=0, rows=[0], weights=['1'], upper_bound='0')))
    assert direct.verify(q)
    for field, value in [('model', 'NORMALIZED_STRICT_CORES_V2'),
                         ('coordinate_system', 'NORMALIZED_CELL_CENTRES'),
                         ('chosen', [-1]), ('chosen', [2]), ('chosen', [0, 0])]:
        bad = deepcopy(q); bad[field] = value
        with pytest.raises(AssertionError): direct.verify(bad)
    bad = deepcopy(q); bad['tree']['bound']['weights'] = ['0']
    with pytest.raises(AssertionError): direct.verify(bad)
    bad = deepcopy(q); bad['tree'] = dict(status='PENDING_NODE_LIMIT')
    assert not direct.verify(bad)
