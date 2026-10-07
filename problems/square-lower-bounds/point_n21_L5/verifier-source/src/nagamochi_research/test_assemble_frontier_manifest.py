import copy
import hashlib
import json
import pytest
from assemble_frontier_manifest import assemble, validate_allocation


def test_allocation_gaps_overlap_and_bool_rejected():
    a=dict(total=3,saved=[dict(index=0)],remaining=[1,2],groups={'0':[1],'1':[2]})
    validate_allocation(a,3)
    for values in ([1], [1,1,2], [True,2], [0,1,2]):
        bad=copy.deepcopy(a);bad['groups']={'0':values}
        with pytest.raises(ValueError):validate_allocation(bad,3)


def test_binding_replacement_and_missing_never_certify(tmp_path):
    c=tmp_path/'candidate';c.write_text('fixture')
    sha=hashlib.sha256(c.read_bytes()).hexdigest()
    f=tmp_path/'frontier';data=dict(candidate_sha256=sha,pending=[dict(box=['0','1','0','1','0','1'])]*2)
    f.write_text(json.dumps(data));fs=hashlib.sha256(f.read_bytes()).hexdigest()
    a=dict(total=2,candidate_sha256=sha,frontier_sha256=fs,saved=[dict(index=0)],remaining=[1],groups={'0':[1]})
    def artifact(name,kind,proof):
        p=tmp_path/name;p.write_text(json.dumps(proof));return dict(index=0,kind=kind,path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest())
    normal=artifact('normal','CAMPAIGN',dict(context=dict(candidate_sha256=sha,frontier_sha256=fs,global_leaf_index=0,input=data['pending'][0])))
    repair=artifact('repair','JOINED_PARENT',dict(candidate_sha256=sha,parent=data['pending'][0]['box']))
    unavailable=dict(index=1,kind='CAMPAIGN',remote_job='remote',sha256='unknown')
    out=assemble(c,f,a,[normal,unavailable],[repair])
    assert out['missing']==[1] and len(out['superseded'])==1 and len(out['unavailable'])==1
    assert out['entries'][0]['kind']=='JOINED_PARENT' and not out['frontier_capture_verified']
    assert not out['numerical_replay_performed']
    with pytest.raises(ValueError):assemble(c,f,a,[normal,normal],[])
    bad=dict(normal,index=1)
    with pytest.raises(ValueError):assemble(c,f,a,[bad],[])
    bad=dict(repair,sha256='0'*64)
    with pytest.raises(ValueError):assemble(c,f,a,[],[bad])
