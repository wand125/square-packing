from fractions import Fraction as F
import pytest
from pending_lemma_poses import collect,validate
from repair_lemma_measure import poses


def test_pending_survives_pricing_without_training_duplicates():
    saved={'train':[['2','2','0']], 'held':[['2','2','0'],['1','1','0']], 'pending':[['3','3','0']]}
    report={'local_witnesses':[{'cx':'3','cy':'3','t':'0'}]}
    result=collect(saved,report,F(4))
    assert result==[(F(1),F(1),F(0)),(F(3),F(3),F(0))]
    assert validate(result,F(4))==result


def test_pending_pose_must_fit_physical_unit_box():
    with pytest.raises(ValueError):validate([(F(1,4),F(2),F(0))],F(4))


def test_final_scan_and_final_local_witness_are_carried():
    report={'records':[{'scan_seed':9275000,'scan_count':2,
                        'local_witnesses':[{'cx':'2','cy':'2','t':'0'}]}]}
    result=set(collect({'train':[],'held':[]},report,F(4)))
    assert set(poses(F(4),2,9275000))|{(F(2),F(2),F(0))}==result
