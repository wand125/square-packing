from adaptive_conflict_experiment import needs_upgrade


def test_skip_only_known_dominating_physical_bounds():
    assert not needs_upgrade('physical-adaptive2','physical-adaptive1')
    assert not needs_upgrade('physical-adaptive1','physical-adaptive1')
    assert needs_upgrade('physical-adaptive1','physical-adaptive2')
    assert needs_upgrade('physical-correlated','physical-adaptive1')
    assert needs_upgrade('correlated-adaptive1','physical-adaptive1')
