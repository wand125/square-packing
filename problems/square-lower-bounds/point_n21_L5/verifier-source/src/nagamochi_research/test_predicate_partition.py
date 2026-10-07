from fractions import Fraction as F
import hashlib,json
import pytest
from compile_box_capture_rows import geometry
from predicate_lp_capture import certify
from predicate_partition import replay_partition


def test_partition_replays_saved_proofs_and_rejects_gap(tmp_path):
    candidate=tmp_path/'candidate.txt'
    candidate.write_text('4 1\n10\n10\n5\n10 20 10\n20 20 10\n30 20 10\n20 10 10\n20 30 10\n')
    _,coords,weights,_=geometry(candidate);points=[(*p,w) for p,w in zip(coords,weights)]
    parent=list(map(F,['7/5','8/5','199/100','201/100','0','1/100']))
    records=[]
    for k in (0,1):
        box=parent.copy();box[1 if k==0 else 0]=F(3,2)
        rec=certify(points,box);rec.update(label=str(k),box=list(map(str,box)));records.append(rec)
    from predicate_conflict import strengthen
    first=records[0];records[0]=dict(strengthen(points,first,first['box']),label=first['label'])
    from predicate_branch import replay_model,solve_tree
    first=records[0];cost,rows,baseline=replay_model(points,first)
    records[0]=dict(solve_tree(cost,rows,baseline),base=first,label=first['label'],box=first['box'])
    proof=json.loads(json.dumps(dict(candidate_sha256=hashlib.sha256(candidate.read_bytes()).hexdigest(),records=records)))
    result=replay_partition(candidate,proof,parent,['0','1'])
    assert result['certified_unit_capture'] and F(result['lower'])>=1
    with pytest.raises(ValueError,match='Incomplete partition'):replay_partition(candidate,proof,parent,['0'])
    proof['candidate_sha256']='wrong'
    with pytest.raises(ValueError,match='hash mismatch'):replay_partition(candidate,proof,parent,['0','1'])
