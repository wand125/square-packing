from fractions import Fraction as F
import pytest
from stratified_lemma_probe import angle_starts


def test_angle_bins_keep_both_endpoints_and_local_minima():
    scan = [(0, 0, F(t)) for t in ['-.414', '-.3', '0', '.2', '.414']]
    selected, occupancy = angle_starts(scan, [4, 3, 2, 1, 0], bins=2, per_bin=1)
    assert selected == [1, 4]
    assert occupancy == [2, 3]
    selected, _ = angle_starts(scan, [4, 3, 2, 1, 0], bins=2, per_bin=4)
    assert set(selected) == set(range(5))


def test_invalid_domain_is_not_silently_clipped():
    with pytest.raises(ValueError):
        angle_starts([(0, 0, F('.415'))], [0])
    with pytest.raises(ValueError):
        angle_starts([], [], bins=0)
