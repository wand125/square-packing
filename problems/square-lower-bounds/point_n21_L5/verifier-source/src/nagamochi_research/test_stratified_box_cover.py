import pytest
from stratified_box_cover import verify


def test_axis_face_must_be_retained():
    root=[0,1,0,1,0,1]
    with pytest.raises(ValueError):verify(root,[],[root])
    assert verify(root,[[0,1,0,1,0,0]],[root])['boundaries_checked']


def test_gaps_and_external_boxes():
    root=[0,1,0,1,0,1]
    with pytest.raises(ValueError):verify(root,[[0,1,0,1,0,'1/3'],[0,1,0,1,'2/3',1]],[])
    with pytest.raises(ValueError):verify(root,[[0,2,0,1,0,1]],[])
    assert verify(root,[[0,1,0,1,0,'1/2'],[0,1,0,1,'1/2',1]],[])['strata_checked']==45
