from pathlib import Path
from fractions import Fraction as F
import json,gzip,hashlib,copy
import pytest
from adaptive_predicate_cover import cover
from replay_frontier_manifest import replay


def test_partial_and_complete_overlay_with_tamper_rejection(tmp_path):
    candidate=tmp_path/'candidate.txt';candidate.write_text('1 1\n10\n10\n1\n5 5 10\n')
    sha=hashlib.sha256(candidate.read_bytes()).hexdigest()
    boxes=[['0','3/5','2/5','3/5','0','1/100'],['0','3/5','1/5','4/5','0','1/100']]
    frontier=tmp_path/'frontier.json';data=dict(candidate_sha256=sha,pending=[dict(parent_index=i,box=b) for i,b in enumerate(boxes)]);frontier.write_text(json.dumps(data));fsha=hashlib.sha256(frontier.read_bytes()).hexdigest();entries=[]
    for i,box in enumerate(boxes):
        records=cover([(F(1,2),F(1,2),F(1))],1,box)['records']
        if i==0:
            proof=dict(context=dict(candidate_sha256=sha,frontier_sha256=fsha,global_leaf_index=i,input=data['pending'][i]),proof=dict(records=records));path=tmp_path/'normal.json.gz';path.write_bytes(gzip.compress(json.dumps(proof).encode()));kind='CAMPAIGN'
        else:
            proof=dict(candidate_sha256=sha,parent=box,pieces=[dict(kind='PHYSICAL_PARTITION',box=box,records=records)]);path=tmp_path/'joined.json';path.write_text(json.dumps(proof));kind='JOINED_PARENT'
        entries.append(dict(index=i,kind=kind,path=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    partial=replay(candidate,frontier,entries[:1]);assert partial['missing']==[1] and not partial['frontier_capture_verified']
    full=replay(candidate,frontier,entries);assert full['frontier_capture_verified'] and not full['general_coverage_verified']
    with pytest.raises(ValueError):replay(candidate,frontier,entries+entries[:1])
    wrong=copy.deepcopy(entries);wrong[1]['index']=0
    with pytest.raises(ValueError):replay(candidate,frontier,wrong[1:])
    wrong=copy.deepcopy(entries);wrong[0]['sha256']='0'*64
    with pytest.raises(ValueError):replay(candidate,frontier,wrong)
