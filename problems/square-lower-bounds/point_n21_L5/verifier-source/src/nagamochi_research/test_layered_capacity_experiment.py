from pathlib import Path
from fractions import Fraction as F
from copy import deepcopy
import json
import pytest
from merge_pose_covers import merge
from full_pose_low_cover import run as initial,verify
from layered_capacity_experiment import run


def test_merge_keeps_full_partition_and_rejects_mismatch(tmp_path):
    p=tmp_path/'candidate.json';p.write_text(json.dumps(dict(n=12,L='4',B='9/10',rectangles=[],points=[],total_mass='0')))
    q=initial(p,tmp_path/'cover.json',F(4,5),3,'robust')
    merged=merge([q,deepcopy(q)],F(11,10));assert verify(p,merged)['leaves']==2
    bad=deepcopy(q);del bad['leaves']['0']
    with pytest.raises(AssertionError):merge([q,bad],F(4,5))
    bad=deepcopy(q);bad['leaves']['0']['box'][0]='999'
    with pytest.raises(AssertionError):merge([q,bad],F(4,5))


def test_empty_common_cores_remain_unresolved_not_excluded(tmp_path):
    p=tmp_path/'candidate.json';p.write_text(json.dumps(dict(n=12,L='4',B='9/10',rectangles=[],points=[],total_mass='0')))
    source=tmp_path/'cover.json';initial(p,source,F(4,5),1,'robust')
    run(p,source,tmp_path/'result')
    r=json.loads((tmp_path/'result/replay.json').read_text())
    assert not r['general_packing_exclusion'] and r['capture_sum_lower']=='0'
    assert all(v['unresolved_common_cores']==1 and v['capacity']==12 for v in r['records'])
