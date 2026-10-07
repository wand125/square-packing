"""Close remaining target-size cliques by joint separation trees."""
from fractions import Fraction as F
from itertools import combinations
from pathlib import Path
import json,hashlib
from saturated_joint_search import search,replay_case
from replay_saturated_pairs import verify


def rotation_orbit(k,cell):
    """90-degree container rotations preserve both angle bands modulo pi/2."""
    result=set();m=k-1
    for _ in range(4):
        result.add(cell);i,j=divmod(cell,m);cell=(m-1-j)*m+i
    return result


def verify_all_missing(root,k,target):
    representatives=(0,1,4) if k==4 else (0,1,2,5)
    covered=set();results=[]
    for m in representatives:
        source=root/f'missing-k{k}-m{m}.json';base=json.loads(source.read_text())
        assert base['k']==k and base['missing']==[m]
        if results:
            for key in ('L','t','axis_h','rot_h','axis_inner','rot_inner','rot_half'):
                assert base[key]==reference[key]
        reference=base
        result=verify(base)
        excluded=result['rotated_count_upper']<target
        if not excluded:
            path=root/f'missing-k{k}-m{m}-full{target}.json'
            q=json.loads(path.read_text());assert q['target_rotated_count']==target
            assert q['source']==source.name and q['source_sha256']==hashlib.sha256(source.read_bytes()).hexdigest()
            completion=verify_completion(base,q);excluded=completion['target_excluded']
            result['joint_completion']=completion
        assert excluded
        orbit=rotation_orbit(k,m);assert not covered&orbit
        covered|=orbit;result['rotation_orbit']=sorted(orbit);results.append(result)
    assert covered==set(range((k-1)**2))
    return dict(status='EXACT_ALL_SINGLE_MISSING_CELLS_EXCLUDED',k=k,
                axis_boxes=(k-1)**2-1,rotated_boxes=target,representatives=results)


def survivors(base,target):
    excluded=set(map(tuple,base['excluded_pairs']))
    return [v for v in combinations(range(base['regions']),target)
            if not any(e in excluded for e in combinations(v,2))]


def verify_completion(base,q):
    verify(base)
    target=q['target_rotated_count'];assert type(target) is int and target>0
    expected=set(survivors(base,target));seen=set();proven=set()
    for case in q['cases']:
        chosen=tuple(case['chosen']);assert chosen in expected and chosen not in seen
        seen.add(chosen)
        for key in ('L','t','k','axis_inner','rot_inner','rot_half','missing'):
            assert case[key]==base[key]
        if replay_case(case):proven.add(chosen)
    return dict(target_rotated_count=target,remaining_combinations=len(expected-proven),
                target_excluded=expected==proven,joint_cases=len(expected))


def run(source,target,out):
    raw=source.read_bytes();base=json.loads(raw)
    verify(base)
    q=dict(source=source.name,source_sha256=hashlib.sha256(raw).hexdigest(),target_rotated_count=target,cases=[])
    for chosen in survivors(base,target):
        case=search(F(base['L']),F(base['t']),base['k'],list(chosen),node_limit=1000,
                    axis_inner=F(base['axis_inner']),rot_inner=F(base['rot_inner']),
                    rot_half=F(base['rot_half']),missing=base['missing'])
        q['cases'].append(case);out.write_text(json.dumps(q,indent=2))
        print(source.name,chosen,case['status'],case['nodes'],flush=True)
    q['replay']=verify_completion(base,q);out.write_text(json.dumps(q,indent=2))
    print(q['replay'],flush=True)
    return q


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('target',type=int);p.add_argument('out',type=Path);a=p.parse_args()
    run(a.source,a.target,a.out)
