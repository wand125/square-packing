from fractions import Fraction as F
import hashlib
import json
import pytest
from adaptive_predicate_cover import cover
from compile_box_capture_rows import validate_partition
from physical_pose_enclosure import replay_partition


def test_budget_exhaustion_preserves_unproved_original_partition():
    parent=['0','1','0','1','0','1/100']
    result=cover([(F(1,2),F(1,2),F(0))],2,parent,max_depth=2)
    validate_partition(parent,[r['enclosure']['original_box'] for r in result['records']])
    assert any(r['proof'] is not None and F(r['proof']['lower'])==0 for r in result['records'])
    assert not result['general_coverage_verified']
    with pytest.raises(ValueError):cover([],2,parent,max_depth=-1)


def test_physical_boundary_coverage_replays_after_json(tmp_path):
    candidate=tmp_path/'candidate.txt'
    candidate.write_text('1 1\n10\n10\n1\n5 5 10\n')
    parent=['0','3/5','2/5','3/5','0','1/100']
    result=json.loads(json.dumps(cover([(F(1,2),F(1,2),F(1))],1,parent)))
    replay=replay_partition(candidate,parent,result['records'],hashlib.sha256(candidate.read_bytes()).hexdigest())
    assert replay['partition_verified'] and replay['certified_unit_capture']
    assert not replay['general_coverage_verified']
