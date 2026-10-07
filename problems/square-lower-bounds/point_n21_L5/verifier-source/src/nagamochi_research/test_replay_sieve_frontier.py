import hashlib,json,copy
from fractions import Fraction as F
import pytest
from physical_pose_enclosure import enclose
from replay_sieve_frontier import replay


def fixture(tmp_path):
    candidate=tmp_path/'candidate.txt'
    pts=[(x,y,1) for x in range(0,9,2) for y in range(0,9,2)]
    candidate.write_text('2 1\n4\n1\n25\n'+''.join(f'{x} {y} {w}\n' for x,y,w in pts))
    sha=hashlib.sha256(candidate.read_bytes()).hexdigest()
    root=['9/10','11/10','9/10','11/10','0','1/1000']
    left=root.copy();left[1]='1';right=root.copy();right[0]='1'
    source=dict(candidate_sha256=sha,pending=[dict(parent_index=7,box=root)])
    row=dict(index=0,parent_index=7,root=root,completed=False,leaves=[
        dict(enclosure=enclose(2,left),proof=dict(indices=[12],lower='1')),
        dict(enclosure=enclose(2,right),proof=None)])
    residual=dict(candidate_sha256=sha,pending=[dict(parent_index=7,frontier_index=0,box=right)])
    paths=[candidate,tmp_path/'source.json',tmp_path/'records.jsonl',tmp_path/'residual.json']
    for p,data in zip(paths[1:],[source,row,residual]):p.write_text(json.dumps(data)+'\n')
    return paths,row,residual


def test_replay_and_residual_tampering(tmp_path):
    paths,row,residual=fixture(tmp_path)
    result=replay(*paths)
    assert result['captured_leaves']==1 and result['residual_leaves']==1
    assert result['residual_list_verified'] and not result['general_coverage_verified']
    for pending in ([],residual['pending']*2):
        changed=copy.deepcopy(residual);changed['pending']=pending;paths[3].write_text(json.dumps(changed))
        with pytest.raises(ValueError):replay(*paths)


def test_missing_partition_and_false_capture_rejected(tmp_path):
    paths,row,residual=fixture(tmp_path)
    for change in ('gap','mass','index','completion'):
        changed=copy.deepcopy(row)
        if change=='gap':changed['leaves'].pop()
        if change=='mass':changed['leaves'][0]['proof']['lower']='2'
        if change=='index':changed['parent_index']=8
        if change=='completion':changed['completed']=True
        paths[2].write_text(json.dumps(changed)+'\n')
        with pytest.raises(ValueError):replay(*paths)
    paths[2].write_text('')
    with pytest.raises(ValueError):replay(*paths)
