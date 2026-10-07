from fractions import Fraction as F
import pytest
from compile_box_capture_rows import quadmax,contains_all,validate_partition
from score import square,contains


def test_quadratic_interior_peak_is_not_missed():
    assert quadmax((F(-1,8),1,-1),0,1)==F(1,8)
    assert quadmax((0,-1,1),0,1)==0


def test_fixed_pose_matches_independent_polygon_including_boundary():
    for t in [F(0),F(1,4),F(1,2)]:
        poly=square(F(2),F(2),F(1),t);box=[2,2,2,2,t,t]
        for p in poly+[(F(2),F(2)),(F(3),F(2)),(F(7,4),F(9,4))]:
            assert contains_all(p,box)==contains(poly,p)


def test_box_containment_uses_all_centre_extrema():
    b=[F(19,10),F(21,10),F(19,10),F(21,10),0,F(1,4)]
    assert contains_all((2,2),b)
    assert not contains_all((F(5,2),2),b)


def test_partition_rejects_gap_and_overlap_even_when_total_volume_matches():
    root=[0,1,0,1,0,1];half=[0,F(1,2),0,1,0,1]
    assert validate_partition(root,[half,[F(1,2),1,0,1,0,1]])
    with pytest.raises(ValueError):validate_partition(root,[half])
    with pytest.raises(ValueError):validate_partition(root,[half,half])


def test_certificate_replays_changed_weights_but_rejects_forged_rows(tmp_path):
    import json
    from compile_box_capture_rows import compile_rows,replay_rows
    source=tmp_path/'source.txt';source.write_text('4 1\n10\n10\n1\n20 20 10\n')
    box=list(map(str,[F(19,10),F(21,10),F(19,10),F(21,10),0,F(1,10)]))
    cert=tmp_path/'rows.json';compile_rows(source,[dict(root_index=0,root=box,leaves=[dict(box=box,indices=[0])])],cert)
    assert replay_rows(cert,source)['retained_roots']==[0]
    reduced=tmp_path/'reduced.txt';reduced.write_text('4 1\n10\n10\n1\n20 20 5\n')
    assert replay_rows(cert,reduced)['passed_rows']==0
    changed=tmp_path/'changed.txt';changed.write_text('6 1\n10\n10\n1\n30 30 10\n')
    with pytest.raises(ValueError,match='geometry'):replay_rows(cert,changed)
    d=json.loads(cert.read_text());d['rows'][0]['indices']=[0,0];cert.write_text(json.dumps(d))
    with pytest.raises(ValueError,match='indices'):replay_rows(cert,source)
