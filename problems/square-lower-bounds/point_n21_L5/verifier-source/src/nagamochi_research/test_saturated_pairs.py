from copy import deepcopy
from fractions import Fraction as F
import json
from pathlib import Path
import pytest
from saturated_axis_cells import halfplane, subtract_open, remove_contained
from replay_saturated_pairs import verify

ROOT=Path(__file__).resolve().parents[2]/'runs/saturated_axis_cells_20260927'


def test_closed_boundary_retained():
    p=[(F(0),F(0)),(F(1),F(0)),(F(1),F(1)),(F(0),F(1))]
    assert set(halfplane(p,1,0,0))=={(0,0),(0,1)}
    assert halfplane(halfplane(p,1,0,0),0,1,0)==[(0,0)]
    residual=subtract_open(p,[(1,0,1),(-1,0,0),(0,1,1),(0,-1,0)])
    assert set(v for piece in residual for v in piece)==set(p)
    assert all(len(piece)<=2 for piece in residual)


@pytest.mark.parametrize('name,upper',[('pair-cuts-k4.json',1),('pair-cuts-k5.json',2),('band-pair-cuts-k4.json',1),('band-pair-cuts-k5.json',2)])
def test_full_replay(name,upper):
    assert verify(json.loads((ROOT/name).read_text()))['rotated_count_upper']==upper


def test_corrupt_certificate_and_angle_scope_rejected():
    q=json.loads((ROOT/'band-pair-cuts-k4.json').read_text())
    bad=deepcopy(q);node=bad['cases'][0]['tree']
    while 'children' in node:node=node['children'][0]
    node['farkas']['weights'][0]='0'
    with pytest.raises(AssertionError):verify(bad)
    bad=deepcopy(q);bad['axis_h']='1/10'
    with pytest.raises(AssertionError):verify(bad)
    bad=deepcopy(q);bad['rotated_count_upper']=0
    with pytest.raises(AssertionError):verify(bad)


def test_unresolved_pairs_stay_compatible():
    q=json.loads((ROOT/'pair-cuts-k5.json').read_text())
    assert any(case['tree']['status']=='UNRESOLVED_BRANCH' for case in q['cases'])
    assert verify(q)['rotated_count_upper']==2


def test_containment_preserves_uncovered_degenerate_parts():
    square=[(F(0),F(0)),(F(1),F(0)),(F(1),F(1)),(F(0),F(1))]
    boundary=[(F(0),F(0)),(F(1),F(0))]
    outside=[(F(2),F(0)),(F(2),F(1))]
    assert remove_contained([square,boundary,outside,square])==[square,outside]


def test_missing_central_cell_requires_joint_four_box_proof():
    from complete_missing_cells import verify_completion
    base=json.loads((ROOT/'missing-k4-m4.json').read_text())
    q=json.loads((ROOT/'missing-k4-m4-full4.json').read_text())
    assert verify(base)['rotated_count_upper']==5
    assert verify_completion(base,q)['target_excluded']
    bad=deepcopy(q);bad['cases'].pop()
    assert not verify_completion(base,bad)['target_excluded']
    bad=deepcopy(q);bad['cases'][0]['missing']=[0]
    with pytest.raises(AssertionError):verify_completion(base,bad)


def test_all_n21_missing_positions_are_covered():
    from complete_missing_cells import verify_all_missing
    q=verify_all_missing(ROOT,5,6)
    assert q['axis_boxes']==15 and q['rotated_boxes']==6
    assert sorted(v for r in q['representatives'] for v in r['rotation_orbit'])==list(range(16))
