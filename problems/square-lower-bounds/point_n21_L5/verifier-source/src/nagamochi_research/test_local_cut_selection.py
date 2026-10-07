from resume_priced_exchange import informative_local


def test_above_one_noise_is_skipped_but_real_cut_is_kept():
    assert not informative_local({'score':'1.0009999999999'},1.001)
    assert informative_local({'score':'1.0009'},1.001)


def test_subunit_witness_is_preserved_at_budget_boundary():
    assert informative_local({'score':'0.9999999999999'},1.0000000000001)
    assert informative_local({'score':'0.9998999999999'},0.9999)
    assert not informative_local({'score':'1'},1.)
