"""Scoped adaptation; original check.py SHA aeb1f73d076fc68c9ee83ff040a6739a22d3cf165277580a4e20bead2403b2dc. Original worker artifacts are read-only."""
"""Fail-closed linkage audit of completed numerical replay stages.
This aggregates numerical replay outputs; it does not replace those replays.
"""
from pathlib import Path
from fractions import Fraction as F
from collections import defaultdict
import sys,json,hashlib,argparse
ROOT=Path(__file__).resolve().parents[4]
R=ROOT/'runs/evand_n21_n32_bridge_20260927/results'
sys.path.insert(0,str(R/'n21_L5_refit29_final_replay'))
from frontier import Checker,sha,boxkey
from compile_box_capture_rows import validate_partition
from checkpoint_external_cover import atomic

sys.path.insert(0,str(R/'n21_L5_refit29_binding_scope_review'))
from audit import audit as binding_audit, EXCLUDED

def validate_terminal(d,shard):
    assert d['tool_session']==[8674,49803,88851][shard]
    response=d['response'];assert response.get('exit_code')==1 and not response.get('session_id')
    log=response['output']
    assert 'run_frontier.py", line 11' in log and 'assert all(sha(p)==h for p,h in bindings.items())' in log
    assert log.rstrip().endswith('AssertionError')

def audit(prefix_only=False,terminals=None):
    folders=[R/f'n21_L5_refit29_final_{s}_replay' for s in ('root','sieve')]+[R/f'n21_L5_refit29_final_frontier_s{i}' for i in range(3)]
    if prefix_only:folders=folders[:2]
    missing=[str(p) for p in folders[:2] if not (p/'result.json').exists() or not (p/'progress.json').exists() or json.loads((p/'progress.json').read_text()).get('status')!='COMPLETED']
    if not prefix_only:
        for folder in folders[2:]:
            inp=json.loads((folder/'inputs.json').read_text())
            if {p.name for p in (folder/'proofs').glob('*.json')}!={f'{i:06d}.json' for i in inp['indices']}:missing.append(str(folder)+': incomplete proof set')
        if terminals is None or not terminals.exists():missing.append('terminal tool responses not supplied')
    if missing:return dict(status='INCOMPLETE',missing_stages=missing,general_coverage_verified=False)
    evidence={}
    def read(p):
        raw=Path(p).read_bytes();evidence[str(p)]=hashlib.sha256(raw).hexdigest();return json.loads(raw)
    scope=binding_audit()
    scope_path=R/'n21_L5_refit29_binding_scope_review/audit.py'
    evidence[str(scope_path)]=sha(scope_path)
    for p,h in scope['input_manifests'].items():evidence[p]=h
    for v in scope['modules'].values():evidence[v['path']]=v['sha256']
    terminal_records={} if prefix_only else read(terminals)
    ch=Checker();candidate=ch.newsha;q=ch.q
    assert candidate=='84a7dae793f05ff72de52ddcd3058e8518c1f84c461f94d11305adefe6137679'
    weights=defaultdict(F)
    for (x,y),w in zip(ch.c,ch.v):
        assert 0<=x<=5 and 0<=y<=5 and w>=0
        weights[x,y]+=w
    for (x,y),w in weights.items():
        assert all(weights.get(p,F())==w for p in [(5-x,y),(x,5-y),(y,x)])
    M=sum(weights.values(),F());assert M<21*q
    stages=[];seen_bindings={}
    for folder in folders:
        inp=read(folder/'inputs.json')
        if folder in folders[:2]:result=read(folder/'result.json')
        else:
            shard=folders.index(folder)-2;validate_terminal(terminal_records[str(shard)],shard)
            assert not (folder/'result.json').exists(), 'Expected only the reviewed final binding assertion failure'
            progress=read(folder/'progress.json');ids=inp['indices']
            assert progress['status']=='RUNNING' and progress['done']==len(ids)-1 and progress['total']==len(ids) and progress['current']==ids[-1]
            # Transient metadata for linkage, never written to worker artifacts.
            # Every numerical record and partition is checked in the loop below.
            result=dict(candidate_sha256=inp['candidate_sha256'],threshold=inp['threshold'],indices=ids,total=len(ids),numerically_replayed=True,origin='complete per-parent output set plus original runner terminal log')
        assert inp['candidate_sha256']==result['candidate_sha256']==candidate and F(result['threshold'])==q
        for p,h in inp['bindings'].items():
            if p in seen_bindings:assert seen_bindings[p]==h
            else:
                if Path(p)!=EXCLUDED:assert sha(p)==h
                else:
                    reviewed=next(z for z in scope['stages'] if z['stage']==folder.name)['changed']
                    assert any(z['path']==p and z['original_sha256']==h and z['current_sha256']==sha(p) for z in reviewed)
                seen_bindings[p]=h
        stages.append(result)
    root,sieve=stages[:2]
    for name,result,count in [('root',root,12),('sieve',sieve,104)]:
        assert result['stage']==name and result['local_parts_numerically_replayed'] is True and result['complete_stage_partition_verified'] is True and result['counts']['repairs']==count
    root_transfer=read(R/'n21_L5_refit29_root_transfer_trial/frontier-output.json')
    assert root['pending']==root_transfer['inherited_pending'] and len(root['pending'])==8758
    assert sieve['pending']==ch.f['pending'] and len(sieve['pending'])==38730
    for i in range(5000):
        d=read(folders[0]/'proofs'/f'{i:06d}.json');x,z=divmod(i,200);y,t=divmod(z,8)
        assert d['index']==i and d['local_parts_numerically_replayed'] is True
        assert boxkey(d['root'])==(F(x,10),F(x+1,10),F(y,10),F(y+1,10),F(t,16),F(t+1,16))
    for i,parent in enumerate(root['pending']):
        d=read(folders[1]/'proofs'/f'{i:06d}.json')
        assert d['index']==i and boxkey(d['parent'])==boxkey(parent['box']) and d['partition_recomputed'] is True and d['local_parts_numerically_replayed'] is True
    if prefix_only:
        assert all(sha(p)==h for p,h in evidence.items())
        return dict(status='SCOPED_PREFIX_LINKAGE_VERIFIED',dependency_scope_audit=scope,candidate_sha256=candidate,root_pending=len(root['pending']),sieve_pending=len(sieve['pending']),mass=str(M),threshold=str(q),strict_gap=str(21*q-M),general_coverage_verified=False,artifact_bindings=evidence,code_and_input_bindings=seen_bindings)
    used=set()
    for shard,(folder,result) in enumerate(zip(folders[2:],stages[2:])):
        expected=sorted(i for i in ch.required if i%3==shard)
        inp=read(folder/'inputs.json')
        assert result['indices']==inp['indices']==expected and result['total']==len(expected) and result['numerically_replayed'] is True
        for i in expected:
            assert i not in used;used.add(i);d=read(folder/'proofs'/f'{i:06d}.json')
            assert d['index']==i and d['candidate_sha256']==candidate and d['source_sha256']==ch.m['entries'][i]['sha256']
            assert boxkey(d['parent'])==boxkey(sieve['pending'][i]['box']) and d['partition_recomputed'] is True and d['numerically_replayed'] is True
            validate_partition(d['parent'],[z['box'] for z in d['leaves']])
            values=[]
            for z in d['leaves']:
                if z['lower'] is None:assert z['method'] in ['GEOMETRIC_EMPTY','SOURCE_GEOMETRIC_EMPTY','DIRECT_EMPTY','EXTENDED_EMPTY','MODEL_EMPTY']
                else:values.append(F(z['lower']));assert F(z['lower'])>=q
            lower=min(values,default=None)
            assert (d['lower'] is None and lower is None) or (d['lower'] is not None and F(d['lower'])==lower)
    assert used==ch.required and len(used)==31678
    excluded=set(range(len(sieve['pending'])))-used
    assert len(excluded)==7052 and all(F(sieve['pending'][i]['box'][4])>F(5,12) for i in excluded)
    # Bind the metadata used to derive required indices and source identities too.
    for p in [ch.new,ch.old,ch.front,R/'n21_L5_refit27_full_assembly_trial/manifest-with-third.json',R/'n21_L5_refit29_frontier_inventory10/inventory.json',Path(__file__)]:evidence[str(p)]=sha(p)
    assert all(sha(p)==h for p,h in evidence.items())
    return dict(status='SCOPED_COMPLETE_REPLAY_LINKAGE',dependency_scope_audit=scope,terminal_records=terminal_records,candidate_sha256=candidate,mass=str(M),threshold=str(q),strict_gap=str(21*q-M),required=len(used),excluded=len(excluded),all_numerical_records_present=True,original_workers_exit_code=1,reviewed_failure='irrelevant file binding only',stage_linkage_verified=True,PL35_PL59_algebraic_hypotheses_checked=True,general_coverage_verified=False,interpretation='Linkage audit of numerical worker outputs; final theorem review remains separate.',artifact_bindings=evidence,code_and_input_bindings=seen_bindings)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);ap.add_argument('--prefix-only',action='store_true');ap.add_argument('--terminals',type=Path);a=ap.parse_args()
    result=audit(prefix_only=a.prefix_only,terminals=a.terminals);atomic(a.out,result)
    print(json.dumps({k:v for k,v in result.items() if not k.endswith('bindings') and k not in ['dependency_scope_audit','terminal_records']},ensure_ascii=False,indent=2))
    sys.exit(2 if result['status']=='INCOMPLETE' else 0)
