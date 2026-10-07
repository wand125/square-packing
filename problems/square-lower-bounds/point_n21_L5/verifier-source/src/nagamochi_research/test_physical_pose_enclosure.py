from fractions import Fraction as F
import pytest
from physical_pose_enclosure import enclose


def test_wall_clip_is_rational_and_keeps_closed_boundary():
    r=enclose(5,['3/5','7/10','23/10','12/5','9/32','37/128'])
    assert r['minimum_halfwidth']=='1519/2210' and r['enclosing_box'][0]=='1519/2210'
    assert enclose(1,[0,1,0,1,0,0])['enclosing_box']==['1/2','1/2','1/2','1/2','0','0']


def test_interval_straddling_halfwidth_maximum_and_empty_domain():
    r=enclose(5,[0,5,0,5,F(2,5),F(1,2)])
    assert F(r['minimum_halfwidth'])==F(7,10)
    assert enclose(1,[0,1,0,1,F(1,4),F(1,2)])['enclosing_box'] is None
    with pytest.raises(ValueError):enclose(5,[0,1,0,1,0,1])


def test_partition_composes_physical_enclosures_and_rejects_forgery(tmp_path):
    import hashlib,copy
    from predicate_lp_capture import certify
    from physical_pose_enclosure import replay_partition
    candidate=tmp_path/'candidate.txt';candidate.write_text('1 1\n10\n10\n1\n5 5 10\n')
    sha=hashlib.sha256(candidate.read_bytes()).hexdigest()
    parent=['0','3/5','2/5','3/5','0','1/100'];records=[]
    for interval in [('0','3/10'),('3/10','3/5')]:
        box=[*interval,*parent[2:]];e=enclose(1,box);proof=None
        if e['enclosing_box']:
            proof=certify([(F(1,2),F(1,2),F(1))],e['enclosing_box']);proof['box']=e['enclosing_box']
        records.append(dict(enclosure=e,proof=proof))
    result=replay_partition(candidate,parent,records,sha)
    assert result['certified_unit_capture'] and result['empty_leaves']==1 and not result['vacuous']
    bad=copy.deepcopy(records);bad[1]['enclosure']['minimum_halfwidth']='0'
    with pytest.raises(ValueError,match='enclosure'):replay_partition(candidate,parent,bad,sha)
    with pytest.raises(ValueError,match='Incomplete partition'):replay_partition(candidate,parent,records[1:],sha)


def test_physical_partition_accepts_verified_binary_tree(tmp_path):
    import hashlib
    from compile_box_capture_rows import geometry
    from predicate_lp_capture import certify
    from predicate_branch import replay_model,solve_tree
    from physical_pose_enclosure import replay_partition
    candidate=tmp_path/'candidate.txt';candidate.write_text('4 1\n10\n10\n5\n10 20 10\n20 20 10\n30 20 10\n20 10 10\n20 30 10\n')
    L,coords,weights,_=geometry(candidate);points=[(*p,w) for p,w in zip(coords,weights)]
    box=['7/5','8/5','199/100','201/100','0','1/100'];e=enclose(L,box)
    base=certify(points,e['enclosing_box']);base['box']=e['enclosing_box']
    cost,rows,B=replay_model(points,base);proof=dict(solve_tree(cost,rows,B),base=base,box=e['enclosing_box'])
    result=replay_partition(candidate,box,[dict(enclosure=e,proof=proof)],hashlib.sha256(candidate.read_bytes()).hexdigest())
    assert result['certified_unit_capture']
