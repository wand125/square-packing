import copy
import json
import hashlib
from fractions import Fraction as F
import pytest
from certify_near_axis_sweep import run
from compile_box_capture_rows import geometry
from adaptive_predicate_cover import cover
from near_axis_partition_bridge import split_at_band, replay_connection, replay_parent


def test_closed_band_connection_and_tampering(tmp_path):
    candidate=tmp_path/'candidate.txt'
    pts=[(x,y,1) for x in range(0,9,2) for y in range(0,9,2)]
    candidate.write_text('2 1\n4\n1\n25\n'+''.join(f'{x} {y} {w}\n' for x,y,w in pts))
    band=run(candidate,tmp_path/'band.json')
    T=F(band['interval']['upper']);parent=['9/10','11/10','9/10','11/10','0',str(2*T)]
    low,high=split_at_band(parent,T)
    L,coords,weights,_=geometry(candidate)
    records=cover([(*p,w) for p,w in zip(coords,weights)],L,high,max_depth=0,branch_nodes=0)['records']
    records=json.loads(json.dumps(records))
    result=replay_connection(candidate,parent,band,records)
    assert result['certified_unit_capture'] and not result['general_coverage_verified']
    sha=hashlib.sha256(candidate.read_bytes()).hexdigest()
    piece=dict(kind='NEAR_AXIS_CONNECTION',box=parent,proof=dict(parent=parent,band=band,high_records=records))
    checked=replay_parent(candidate,parent,json.loads(json.dumps([piece])),sha)
    assert checked['certified_unit_capture'] and checked['bands_recomputed']==1
    with pytest.raises(ValueError):replay_parent(candidate,parent,[piece,piece],sha)
    bad=copy.deepcopy(piece);bad['proof']['parent'][0]='0'
    with pytest.raises(ValueError):replay_parent(candidate,parent,[bad],sha)
    with pytest.raises(ValueError):replay_parent(candidate,parent,[],sha)
    physical=dict(kind='PHYSICAL_PARTITION',box=high,records=records)
    assert replay_parent(candidate,high,[physical],sha)['certified_unit_capture']
    bad=copy.deepcopy(band);bad['interval']['upper']=str(2*T)
    with pytest.raises(ValueError):replay_connection(candidate,parent,bad,records)
    bad=copy.deepcopy(band);bad['anchor_minimum']='999'
    with pytest.raises(ValueError):replay_connection(candidate,parent,bad,records)
    bad=copy.deepcopy(records);bad[0]['enclosure']['original_box'][4]=str(T+T/10)
    with pytest.raises(ValueError):replay_connection(candidate,parent,band,bad)
    with pytest.raises(ValueError):replay_connection(candidate,parent,band,[])
    candidate.write_text(candidate.read_text()+'\n')
    with pytest.raises(ValueError):replay_connection(candidate,parent,band,records)


def test_split_requires_nonempty_complete_pieces():
    parent=['0','1','0','1','0','1/10']
    for T in (0,F(1,10),F(1,5)):
        with pytest.raises(ValueError):split_at_band(parent,T)
