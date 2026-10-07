"""Transfer pure envelope exclusions, never correlated-epsilon certificates."""
from pathlib import Path
from itertools import combinations
import argparse,hashlib,json,os,time
from epsilon_cell_envelope import model as envelope_model
from normalized_certificate_transfer import check_embedding
from normalized_pair_refinement import verify as verify_pairs,target_groups
from normalized_axis_cells import verify as verify_normalized,run as search
from saturated_joint_search import replay_model

TRANSFER='NORMALIZED_ENVELOPE_TRANSFER_V1'


def verify_case(base,c):
    assert c['model'] in (TRANSFER,'NORMALIZED_CELLS_V1','NORMALIZED_STRICT_CORES_V2')
    chosen=c['chosen'];assert 2<=len(chosen) and chosen==sorted(set(chosen))
    assert all(type(i) is int and 0<=i<base['regions'] for i in chosen)
    if c['model']==TRANSFER:
        assert c['source_model']=='ENVELOPE'
        check_embedding(base)
        return replay_model(envelope_model(base['config'],base['missing'],chosen),c['tree'])
    assert c['config']==base['config'] and c['missing']==base['missing']
    return verify_normalized(c)


def verify(base,pairs,q):
    verify_pairs(base,pairs);check_embedding(base)
    assert q['coordinate_system']=='NORMALIZED_CELL_CENTRES' and q['target']==pairs['target']
    remaining=target_groups(base,pairs);seen=set()
    for c in q['cases']:
        key=(c['model'],tuple(c['chosen']));assert key not in seen;seen.add(key)
        assert len(c['chosen'])<=q['target']
        if verify_case(base,c):remaining={v for v in remaining if not set(c['chosen'])<=set(v)}
    return dict(target_excluded=not remaining,remaining_groups=len(remaining)),remaining


def transfer(source,pair_path,old,out):
    raw=source.read_bytes();base=json.loads(raw);pairs=json.loads(pair_path.read_text());saved=json.loads(old.read_text())
    digest=hashlib.sha256(raw).hexdigest();assert saved['source_sha256']==pairs['source_sha256']==digest
    check_embedding(base)
    q=dict(source=str(source),source_sha256=digest,pair_path=str(pair_path),pair_sha256=hashlib.sha256(pair_path.read_bytes()).hexdigest(),
           coordinate_system='NORMALIZED_CELL_CENTRES',target=pairs['target'],cases=[],
           input=dict(path=str(old),sha256=hashlib.sha256(old.read_bytes()).hexdigest()),status='VERIFYING')
    for c in saved['cases']:
        if c.get('model','ENVELOPE')!='ENVELOPE':continue
        wrapped=dict(model=TRANSFER,source_model='ENVELOPE',chosen=c['chosen'],tree=c['tree'])
        if verify_case(base,wrapped):q['cases'].append(wrapped)
    q['replay'],_=verify(base,pairs,q);q['status']='EXACT_TRANSFERRED_PARTIAL_SEED'
    out.write_text(json.dumps(q,indent=2));print(len(q['cases']),q['replay'],flush=True)
    return q


def campaign(source,pair_path,seeds,out,node_limit=3000):
    raw=source.read_bytes();base=json.loads(raw);pairs=json.loads(pair_path.read_text());digest=hashlib.sha256(raw).hexdigest()
    assert pairs['source_sha256']==digest
    q=dict(source=str(source),source_sha256=digest,pair_path=str(pair_path),pair_sha256=hashlib.sha256(pair_path.read_bytes()).hexdigest(),
           coordinate_system='NORMALIZED_CELL_CENTRES',target=pairs['target'],cases=[],status='RUNNING',worker_pid=os.getpid(),seeds=[])
    seen=set();start=time.monotonic()
    print('worker_pid',os.getpid(),'verifying seeds',flush=True)
    for path in seeds:
        seed=json.loads(path.read_text());assert seed['source_sha256']==digest and seed['target']==q['target']
        assert seed['coordinate_system']=='NORMALIZED_CELL_CENTRES'
        q['seeds'].append(dict(path=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
        for c in seed['cases']:
            key=(c['model'],tuple(c['chosen']))
            if key not in seen and verify_case(base,c):q['cases'].append(c);seen.add(key)
    _,remaining=verify(base,pairs,q)
    def save():
        q.update(remaining_groups=len(remaining),seconds=time.monotonic()-start)
        tmp=out.with_suffix('.tmp');tmp.write_text(json.dumps(q,indent=2));tmp.replace(out)
    save();print('worker_pid',os.getpid(),'remaining',len(remaining),flush=True)
    for chosen in sorted(remaining):
        c=search(base['config'],base['missing'],chosen,node_limit,strict=True)
        key=(c['model'],tuple(c['chosen']));assert key not in seen;seen.add(key);q['cases'].append(c)
        if verify_case(base,c):remaining.remove(chosen)
        save();print(chosen,c['status'],len(remaining),flush=True)
    q['replay'],_=verify(base,pairs,q);q['status']='EXACT_NORMALIZED_FIXED_BAND_EXCLUSION' if not remaining else 'STOPPED_LOCAL_PROOF_REVIEW';save()


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['transfer','campaign']);p.add_argument('source',type=Path);p.add_argument('pairs',type=Path);p.add_argument('out',type=Path);p.add_argument('seeds',nargs='+',type=Path);a=p.parse_args()
    if a.mode=='transfer':
        assert len(a.seeds)==1;transfer(a.source,a.pairs,a.seeds[0],a.out)
    else:campaign(a.source,a.pairs,a.seeds,a.out)
