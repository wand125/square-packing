"""Final proof assembly, conditional on the explicitly reviewed checker lemmas.
Rechecks evidence bindings and stage linkage; does not replace numerical replay.
"""
from pathlib import Path
from fractions import Fraction as F
import hashlib, json, sys, importlib.util
ROOT=Path(__file__).resolve().parents[4]
R=ROOT/'runs/evand_n21_n32_bridge_20260927/results'
HERE=Path(__file__).resolve().parent

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def audit():
    gate=R/'n21_L5_refit29_scoped_gate/check.py'
    spec=importlib.util.spec_from_file_location('scoped_endpoint_gate',gate)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    linkage=module.audit(terminals=R/'n21_L5_refit29_scoped_gate/terminals.json')
    assert linkage['status']=='SCOPED_COMPLETE_REPLAY_LINKAGE'
    assert linkage['stage_linkage_verified'] and linkage['all_numerical_records_present']
    evidence=dict(linkage['artifact_bindings'])
    evidence[str(gate)]=sha(gate)
    reviews=[]
    for name in ['review-bindings.json','partition-bindings.json','near-axis-bindings.json','predicate-model-review.json','physical-witness-review.json']:
        p=R/'n21_L5_refit29_soundness_review'/name;d=json.loads(p.read_text())
        bindings=d.get('source_bindings',d)
        for source,h in bindings.items():
            source=ROOT/source
            assert sha(source)==h,('reviewed source changed',source)
            evidence[str(source)]=h
        evidence[str(p)]=sha(p);reviews.append(dict(file=str(p),entries=len(bindings)))
    # The numerical gate checks the measure and D4 generators directly.
    M,q=F(linkage['mass']),F(linkage['threshold'])
    assert M==F(2624862500021,125000000000) and q==F(249987,250000)>0
    assert 21*q-M==F(999979,125000000000)>0
    assert linkage['required']==31678 and linkage['excluded']==7052
    assert F(17,12)**2>2 # sqrt(2)-1 < 5/12
    cells=[(i,j) for i in range(5) for j in range(4)]+[(0,4)]
    assert len(cells)==len(set(cells))==21
    assert all(0<=x<x+1<=5 and 0<=y<y+1<=5 for x,y in cells)
    assert all(abs(x-u)>=1 or abs(y-v)>=1 for k,(x,y) in enumerate(cells) for u,v in cells[:k])
    methods={};minimum=None
    for shard in range(3):
        folder=R/f'n21_L5_refit29_final_frontier_s{shard}'
        for path in (folder/'proofs').glob('*.json'):
            d=json.loads(path.read_text())
            for leaf in d['leaves']:
                name=leaf['method'];methods[name]=methods.get(name,0)+1
                if leaf['lower'] is not None:
                    v=F(leaf['lower']);minimum=v if minimum is None else min(minimum,v)
    assert minimum>=q
    for p in [HERE/'review.md',Path(__file__)]:evidence[str(p)]=sha(p)
    assert all(sha(p)==h for p,h in evidence.items())
    return dict(status='ENDPOINT_PROOF_ASSEMBLY_VERIFIED',n=21,endpoint='5',candidate_sha256=linkage['candidate_sha256'],mass=str(M),threshold=str(q),strict_gap=str(21*q-M),frontier_minimum=str(minimum),frontier_leaf_methods=methods,upper_bound_cells=cells,review_bindings=reviews,artifact_bindings=evidence,checker_modules=linkage['dependency_scope_audit']['modules'],proof_basis='Exact numerical replay plus the reviewed PL35/PL42-60 argument in review.md; not a formal proof-assistant certificate.',formal_verification=False,independent_external_review=False)
if __name__=='__main__':
    result=audit();p=HERE/'result.json'
    assert not p.exists(),'Keep the original final audit immutable'
    p.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ['artifact_bindings','checker_modules','upper_bound_cells','review_bindings']},indent=2))
