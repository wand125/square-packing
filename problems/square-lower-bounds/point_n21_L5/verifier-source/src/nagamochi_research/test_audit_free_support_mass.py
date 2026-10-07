import hashlib
import json
from fractions import Fraction as F
import numpy as np
import pytest
from audit_free_support_mass import run


def fixture(directory, count=1):
    candidate = directory/'candidate.txt'
    candidate.write_text('2 1\n2\n1\n4\n1 1 1\n1 3 1\n3 1 1\n3 3 1\n')
    (directory/'result.json').write_text(json.dumps(dict(
        sha256=hashlib.sha256(candidate.read_bytes()).hexdigest(),
        capture_target='10001/10000')))
    (directory/'poses.json').write_text(json.dumps([
        [x, y, '0'] for x in ['1/2', '3/2'] for y in ['1/2', '3/2']]))
    np.savez(directory/'incidence.npz', counts=np.full((4, 1), count),
             sizes=np.array([4]), orbit_ids=np.zeros(4, dtype=int))


def test_exact_four_disjoint_captures(tmp_path):
    fixture(tmp_path)
    run(tmp_path, tmp_path/'dual.json')
    result = json.loads((tmp_path/'dual.json').read_text())
    assert F(result['lower_at_capture_one']) == 4
    assert F(result['finite_upper_at_capture_one']) == 4
    assert F(result['primal_finite_minimum']) == 1
    assert F(result['maximum_scaled_load']) == 1
    assert result['all_positive_dual_geometry_replayed']


def test_rejects_wrong_geometry_counts(tmp_path):
    fixture(tmp_path, 2)
    with pytest.raises(AssertionError):
        run(tmp_path, tmp_path/'dual.json')
