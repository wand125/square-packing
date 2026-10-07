"""Refine a pure envelope graph in normalized coordinates, never mixing epsilon LPs."""
from pathlib import Path
from itertools import combinations
import json,hashlib,time,os
from fractions import Fraction as F
from epsilon_cell_envelope import verify as verify_base
from normalized_certificate_transfer import check_embedding
from normalized_axis_cells import run as search,verify as verify_case
from replay_saturated_pairs import clique_upper


def verify(base,q):
    verify_base(base);check_embedding(base)
    assert q['coordinate_system']=='NORMALIZED_CELL_CENTRES'
    excluded=set(map(tuple,base['excluded_pairs']));seen=set();N=base['regions']
    for case in q['cases']:
        assert case['model'] in ('NORMALIZED_CELLS_V1','NORMALIZED_STRICT_CORES_V2')
        edge=tuple(case['chosen']);assert len(edge)==2 and 0<=edge[0]<edge[1]<N and edge not in seen
        seen.add(edge)
        assert case['config']==base['config'] and case['missing']==base['missing']
        if verify_case(case):excluded.add(edge)
    assert excluded==set(map(tuple,q['excluded_pairs']))
    upper=clique_upper(N,excluded);assert upper==q['rotated_count_upper']
    return dict(rotated_count_upper=upper,remaining_target_groups=sum(
        not any(e in excluded for e in combinations(v,2)) for v in combinations(range(N),q['target'])))


def run(source,out,target=4,strict=False):
    raw=source.read_bytes();base=json.loads(raw);verify_base(base);check_embedding(base)
    excluded=set(map(tuple,base['excluded_pairs']));N=base['regions'];start=time.monotonic()
    q=dict(source=str(source),source_sha256=hashlib.sha256(raw).hexdigest(),target=target,
           coordinate_system='NORMALIZED_CELL_CENTRES',cases=[],status='RUNNING',worker_pid=os.getpid())
    for edge in combinations(range(N),2):
        if edge in excluded:continue
        case=search(base['config'],base['missing'],edge,1000,strict=strict);q['cases'].append(case)
        if verify_case(case):excluded.add(edge)
        q.update(excluded_pairs=sorted(excluded),seconds=time.monotonic()-start)
        tmp=out.with_suffix('.tmp');tmp.write_text(json.dumps(q,indent=2));tmp.replace(out)
    q['rotated_count_upper']=clique_upper(N,excluded);q['replay']=verify(base,q)
    q['status']='EXACT_NORMALIZED_PAIR_REFINEMENT';out.write_text(json.dumps(q,indent=2))
    print(out.name,q['replay'],q['seconds'],flush=True);return q


def target_groups(base,pairs):
    excluded=set(map(tuple,pairs['excluded_pairs']))
    return set(v for v in combinations(range(base['regions']),pairs['target'])
               if not any(e in excluded for e in combinations(v,2)))


def verify_completion(base,pairs,q):
    verify(base,pairs);expected=target_groups(base,pairs);remaining=set(expected);seen=set()
    assert q['coordinate_system']=='NORMALIZED_CELL_CENTRES' and q['target']==pairs['target']
    rule=q.get('rotated_t_halfwidth_rule','fixed')
    assert rule in ('fixed','epsilon/10000','min(rot_h,epsilon/(2*(k-1)))')
    if rule=='epsilon/10000':assert F(base['config']['eps_max'])/10000<=F(base['config']['rot_h'])
    for case in q['cases']:
        if case['model']=='NORMALIZED_MOVING_BANDS_V3':assert rule=='epsilon/10000'
        if case['model']=='NORMALIZED_CAPPED_BANDS_V4':
            assert rule in ('epsilon/10000','min(rot_h,epsilon/(2*(k-1)))')
            assert 2*(base['config']['k']-1)<=10000
        chosen=tuple(case['chosen']);assert chosen in expected and chosen not in seen;seen.add(chosen)
        assert case['config']==base['config'] and case['missing']==base['missing']
        if verify_case(case):remaining.remove(chosen)
    return dict(target_rotated_count=q['target'],target_groups=len(expected),remaining_groups=len(remaining),target_excluded=not remaining)


def complete(source,pair_path,out,strict=False):
    raw=source.read_bytes();base=json.loads(raw);pairs=json.loads(pair_path.read_text())
    assert pairs['source_sha256']==hashlib.sha256(raw).hexdigest();verify(base,pairs)
    groups=target_groups(base,pairs);remaining=set(groups);start=time.monotonic()
    q=dict(coordinate_system='NORMALIZED_CELL_CENTRES',source=str(source),source_sha256=hashlib.sha256(raw).hexdigest(),
           pair_path=str(pair_path),pair_sha256=hashlib.sha256(pair_path.read_bytes()).hexdigest(),
           target=pairs['target'],cases=[],status='RUNNING',worker_pid=os.getpid())
    for chosen in sorted(groups):
        case=search(base['config'],base['missing'],chosen,3000,strict=strict);q['cases'].append(case)
        if verify_case(case):remaining.remove(chosen)
        q.update(remaining_groups=len(remaining),seconds=time.monotonic()-start)
        tmp=out.with_suffix('.tmp');tmp.write_text(json.dumps(q,indent=2));tmp.replace(out)
        print(out.name,chosen,case['status'],case['nodes'],'remaining',len(remaining),flush=True)
    q['replay']=verify_completion(base,pairs,q)
    q['status']='EXACT_NORMALIZED_TARGET_EXCLUSION' if q['replay']['target_excluded'] else 'STOPPED_LOCAL_PROOF_REVIEW'
    out.write_text(json.dumps(q,indent=2));print(q['replay'],flush=True);return q


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('root',type=Path);p.add_argument('out',type=Path);a=p.parse_args();a.out.mkdir(exist_ok=True)
    for m in (1,4):run(a.root/f'k4-m{m}.json',a.out/f'n12-m{m}-pairs.json')
