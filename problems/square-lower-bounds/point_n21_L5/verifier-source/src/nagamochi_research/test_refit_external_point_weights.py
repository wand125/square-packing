from fractions import Fraction as F
import pytest
from refit_external_point_weights import exact_hits
from score import square,contains

@pytest.mark.parametrize('pose',[(F(2),F(2),F(0)),(F(2),F(2),F(1,3)),(F(2),F(2),F(-1,3)),(F(7,10),F(3,2),F(1,3))])
def test_exact_integer_hits_match_closed_polygon(pose):
    pts=[(x,y,1) for x in range(41) for y in range(41)]
    actual=exact_hits(pts,F(4),40,pose);poly=square(*pose[:2],F(1),pose[2])
    expected=[contains(poly,(F(x,10),F(y,10))) for x,y,w in pts]
    assert list(actual)==expected

def test_negative_angle_wall_admissibility():
    with pytest.raises(ValueError):exact_hits([(1,1,1)],F(4),40,(F(1,2),F(2),F(-1,3)))


def test_point_linf_tiebreak_balances_per_point_changes():
 import numpy as np
 from scipy.sparse import csr_matrix
 from refit_external_point_weights import solve_weights
 sol,primary,secondary=solve_weights(csr_matrix([[1.,1.]]),np.zeros(2),np.array([1,2]),1.,1.,'point_linf')
 assert abs(primary-1)<1e-8
 assert np.allclose(sol.x[:2],[1/3,2/3],atol=1e-7)
 assert abs(secondary-1/3)<1e-7


def test_heterogeneous_row_targets_and_integer_rounding():
 import numpy as np
 from scipy.sparse import csr_matrix
 from refit_external_point_weights import solve_weights,round_to_row_targets
 sol,_,_=solve_weights(csr_matrix(np.eye(2)),np.zeros(2),np.ones(2),3,[F(1001,1000),F(1)],'none')
 assert np.allclose(sol.x[:2],[1.001,1.0],atol=1e-8)
 nums,captures=round_to_row_targets(np.eye(2,dtype=int),np.array([999,1000]),np.array([1001,1000]))
 assert np.all(captures>=np.array([1001,1000]))


def test_refit_replays_proof_rows_after_export(tmp_path):
 import json,hashlib
 from compile_box_capture_rows import compile_rows
 from refit_external_point_weights import run
 src=tmp_path/'source.txt';src.write_text('4 1\n10\n10\n1\n20 20 10\n')
 box=list(map(str,[F(19,10),F(21,10),F(19,10),F(21,10),0,F(1,10)]))
 proof=tmp_path/'proof.json';compile_rows(src,[dict(root_index=0,root=box,leaves=[dict(box=box,indices=[0])])],proof)
 witnesses=tmp_path/'witnesses.json';witnesses.write_text(json.dumps(dict(source_sha256=hashlib.sha256(src.read_bytes()).hexdigest(),L='4',witnesses=[dict(pose=['2','2','0'],before='1')])))
 out=tmp_path/'out';run(src,witnesses,out,count=0,capture_target=F(1001,1000),proof_rows=proof)
 r=json.loads((out/'result.json').read_text());assert r['proof_rows']==1 and r['certified_regions_preserved']==1
 assert F(r['training_minimum'])>=F(1001,1000) and F(r['proof_minimum'])>=1


@pytest.mark.parametrize('tiebreak',['none','point_linf'])
def test_predicate_blocks_restrict_both_optimization_stages(tiebreak):
 import numpy as np
 from scipy.sparse import csr_matrix
 from predicate_lp_capture import certify
 from predicate_weight_rows import compile_model,weight_rows,evaluate
 from refit_external_point_weights import solve_weights
 points=[(F(0),F(0),F(1)),(F(1),F(0),F(1))]
 box=list(map(F,['2/5','3/5','0','0','0','1/100']))
 model=compile_model(points,box,certify(points,box));block=weight_rows(model,[0,1],[1,1])
 A=csr_matrix([[1.,1.]])
 control,_,_=solve_weights(A,np.zeros(2),np.ones(2),3,.1,tiebreak)
 sol,_,_=solve_weights(A,np.zeros(2),np.ones(2),3,.1,tiebreak,[block,block])
 assert control.x[:2].sum()==pytest.approx(.1)
 assert sol.x[:2].sum()==pytest.approx(2)
 assert evaluate(model,[(x,y,F(str(sol.x[i]))) for i,(x,y,w) in enumerate(points)])>=1


def test_predicate_refit_replays_rounded_export(tmp_path):
 import json,hashlib
 from compile_box_capture_rows import geometry
 from predicate_lp_capture import certify
 from refit_external_point_weights import run
 src=tmp_path/'source.txt';src.write_text('4 1\n10\n10\n5\n10 20 10\n20 20 10\n30 20 10\n20 10 10\n20 30 10\n')
 sha=hashlib.sha256(src.read_bytes()).hexdigest()
 _,coords,weights,_=geometry(src);points=[(*p,w) for p,w in zip(coords,weights)]
 box=list(map(F,['7/5','8/5','2','2','0','1/100']))
 record=certify(points,box);assert F(record['lower'])>=1
 record.update(label='test',box=list(map(str,box)))
 proof=tmp_path/'predicate.json';proof.write_text(json.dumps(dict(candidate_sha256=sha,records=[record])))
 witnesses=tmp_path/'witnesses.json';witnesses.write_text(json.dumps(dict(source_sha256=sha,L='4',witnesses=[dict(pose=['2','2','0'])])))
 out=tmp_path/'out';run(src,witnesses,out,count=0,capture_target=F(11,10),tiebreak='point_linf',predicate_proofs=proof)
 r=json.loads((out/'result.json').read_text());assert r['predicate_regions_preserved']==1 and F(r['predicate_minimum'])>=1
 assert (out/'candidate.txt').exists() and json.loads((out/'predicate-replay.json').read_text())['all_passed']
 bad=json.loads(proof.read_text());bad['candidate_sha256']='wrong';proof.write_text(json.dumps(bad))
 with pytest.raises(ValueError,match='source mismatch'):run(src,witnesses,tmp_path/'bad',count=0,predicate_proofs=proof)
