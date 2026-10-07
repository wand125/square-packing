from fractions import Fraction as F
from copy import deepcopy
import json
import pytest
from full_pose_low_cover import run as initial,verify
from strengthen_pose_cover import run


def test_mixed_leaf_methods_resume_and_forgery(tmp_path):
    candidate=tmp_path/'candidate.json'
    candidate.write_text(json.dumps(dict(n=20,L='4',B='9/10',rectangles=[dict(rectangle=['0','0','4','4'],mass='16')],points=[],total_mass='16')))
    source=tmp_path/'source.json'
    q=initial(candidate,source,F(1,10),511,'robust');q['symmetry']='D4';source.write_text(json.dumps(q))
    out=tmp_path/'new.json';run(candidate,source,out)
    saved=json.loads(out.read_text());assert verify(candidate,saved)['leaves']==len(q['leaves'])
    assert any(r.get('bound_method')=='correlated' for r in saved['leaves'].values())
    assert any('bound_method' not in r for r in saved['leaves'].values())
    bad=deepcopy(saved)
    key=next(k for k,v in bad['leaves'].items() if v.get('bound_method')=='correlated')
    bad['leaves'][key]['lower']='100'
    with pytest.raises(AssertionError):verify(candidate,bad)
    run(candidate,source,out);assert json.loads(out.read_text())['leaves']==saved['leaves']


def test_bounded_adaptive_selection_keeps_unselected_leaves(tmp_path):
    candidate=tmp_path/'empty.json';candidate.write_text(json.dumps(dict(n=20,L='4',B='9/10',rectangles=[],points=[],total_mass='0')))
    source=tmp_path/'source.json';q=initial(candidate,source,F(4,5),63,'robust')
    q['symmetry']='D4';source.write_text(json.dumps(q));out=tmp_path/'adaptive.json'
    run(candidate,source,out,'correlated-adaptive1',1)
    saved=json.loads(out.read_text());selected=set(saved['strengthen_selected_paths'])
    assert 0<len(selected)<len(q['leaves'])
    assert all(saved['leaves'][p]==r for p,r in q['leaves'].items() if p not in selected)
    assert verify(candidate,saved)['leaves']==len(q['leaves'])
    run(candidate,source,out,'correlated-adaptive1',1)
    assert json.loads(out.read_text())['leaves']==saved['leaves']
