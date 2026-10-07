"""Resume conditional epsilon proofs with verified certificates from both models."""
from pathlib import Path
from datetime import datetime,timezone
import os,json,hashlib,time
from epsilon_cell_envelope import verify as verify_base,remaining_groups,model as envelope_model
from correlated_epsilon_lp import run as correlated_run,verify as verify_correlated
from saturated_joint_search import search_model,replay_model


def verify_case(base,case):
    variant=case.get('model','ENVELOPE')
    if variant.startswith('CORRELATED_EPSILON_'):
        assert case['config']==base['config'] and case['missing']==base['missing']
        return verify_correlated(case)
    assert variant=='ENVELOPE'
    return replay_model(envelope_model(base['config'],base['missing'],case['chosen']),case['tree'])


def verify(base,q):
    verify_base(base);target=q['target'];assert type(target) is int and target>0
    remaining=set(remaining_groups(base,target));seen=set()
    for case in q['cases']:
        chosen=tuple(case['chosen']);key=(case.get('model','ENVELOPE'),chosen)
        assert 2<=len(chosen)<=target and tuple(sorted(set(chosen)))==chosen
        assert all(0<=i<base['regions'] for i in chosen) and key not in seen;seen.add(key)
        if verify_case(base,case):remaining={v for v in remaining if not set(chosen)<=set(v)}
    return dict(target_rotated_count=target,remaining_groups=len(remaining),target_excluded=not remaining)


def run(source,seeds,out,target=5):
    raw=source.read_bytes();base=json.loads(raw);verify_base(base);digest=hashlib.sha256(raw).hexdigest()
    q=dict(source=source.name,source_sha256=digest,target=target,cases=[],status='RUNNING',
           worker_pid=os.getpid(),started=datetime.now(timezone.utc).isoformat(),
           seeds=[dict(path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in seeds])
    remaining=set(remaining_groups(base,target));seen=set();start=time.monotonic()
    for seed in seeds:
        payload=json.loads(seed.read_text());assert payload['source_sha256']==digest and payload['target']==target
        for case in payload['cases']:
            chosen=tuple(case['chosen']);key=(case.get('model','ENVELOPE'),chosen)
            if key not in seen and verify_case(base,case):
                seen.add(key);q['cases'].append(case);remaining={v for v in remaining if not set(chosen)<=set(v)}
    def save():
        q.update(remaining_groups=len(remaining),seconds=time.monotonic()-start)
        tmp=out.with_suffix('.tmp');tmp.write_text(json.dumps(q,indent=2));tmp.replace(out)
    save()
    for chosen in sorted(remaining):
        case=correlated_run(base['config'],base['missing'],chosen,1000,branch_rule='fewest')
        q['cases'].append(case);ok=verify_case(base,case)
        if not ok:
            data=envelope_model(base['config'],base['missing'],chosen)
            fallback=search_model(data,1000,branch_rule='fewest');fallback.update(chosen=list(chosen),model='ENVELOPE',branch_rule='fewest')
            q['cases'].append(fallback);ok=verify_case(base,fallback)
        if ok:remaining.remove(chosen)
        save();print(chosen,case['status'],case['nodes'],'excluded',ok,'remaining',len(remaining),flush=True)
    q['replay']=verify(base,q)
    q['status']='EXACT_CONDITIONAL_UNIFORM_EPSILON_EXCLUSION' if q['replay']['target_excluded'] else 'STOPPED_LOCAL_PROOF_REVIEW'
    save();print(q['replay'],flush=True)
    return q


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('seed',type=Path);p.add_argument('out',type=Path)
    a=p.parse_args();run(a.source,[a.seed],a.out)
