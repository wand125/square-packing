from fractions import Fraction as F
import json
from compile_box_capture_rows import compile_rows,replay_rows
from certify_pose_neighbourhoods import run


def test_expansion_preserves_old_box_and_adds_continuous_pose_box(tmp_path):
    src=tmp_path/'candidate.txt';src.write_text('4 1\n10\n10\n1\n20 20 12\n')
    box=list(map(str,[F(19,10),F(21,10),F(19,10),F(21,10),0,F(1,10)]))
    old=tmp_path/'proof.json';compile_rows(src,[dict(root_index=0,root=box,leaves=[dict(box=box,indices=[0])])],old)
    r=run(src,[[F(2),F(2),F(1,4)]],old,tmp_path/'new',start=F(1,10))
    assert r['new_roots']==1 and r['total_roots']==2
    assert replay_rows(tmp_path/'new/expanded-proof-rows.json',src)['passed_rows']==2


def test_failed_box_search_is_not_reported_as_certified(tmp_path):
    src=tmp_path/'candidate.txt';src.write_text('4 1\n10\n10\n1\n20 20 12\n')
    box=list(map(str,[F(19,10),F(21,10),F(19,10),F(21,10),0,F(1,10)]))
    old=tmp_path/'proof.json';compile_rows(src,[dict(root_index=0,root=box,leaves=[dict(box=box,indices=[0])])],old)
    r=run(src,[[F(3),F(3),F(1,4)]],old,tmp_path/'new',max_halvings=2)
    assert r['new_roots']==0 and r['total_roots']==1
    assert r['attempts'][0]['status']=='NO_CERTIFICATE_AT_TESTED_SCALES'
