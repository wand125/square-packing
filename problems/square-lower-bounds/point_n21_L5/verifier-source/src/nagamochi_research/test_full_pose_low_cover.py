from fractions import Fraction as F
from copy import deepcopy
import json
import pytest
from full_pose_low_cover import run,verify,root_box,outside_container


def test_full_cover_retains_unknown_and_rejects_gap_or_forged_bound(tmp_path):
    p=tmp_path/'candidate.json'
    p.write_text(json.dumps(dict(n=20,L='4',B='9/10',rectangles=[dict(rectangle=['0','0','4','4'],mass='16')],points=[],total_mass='16')))
    q=run(p,tmp_path/'cover.json',F(1,10),63)
    r=verify(p,q);assert r['possible_low']>0 and not r['general_packing_exclusion']
    bad=deepcopy(q);del bad['leaves'][next(iter(bad['leaves']))]
    with pytest.raises(AssertionError):verify(p,bad)
    bad=deepcopy(q);key=next(k for k,v in bad['leaves'].items() if v['kind']=='POSSIBLE_LOW')
    bad['leaves'][key]['lower']='1';bad['leaves'][key]['kind']='HIGH'
    with pytest.raises(AssertionError):verify(p,bad)


def test_physical_domain_and_angle_endpoint_coverage():
    assert (1+F(5,12))**2>2  # 5/12 > sqrt(2)-1, without float.
    assert not outside_container(root_box(F(4)),F(4))
    assert outside_container((F(1,2),F(51,100),F(1,2),F(51,100),F(1,3),F(1,3)),F(4))
    assert not outside_container((F(1,2),F(1,2),F(1,2),F(1,2),F(0),F(0)),F(4))
