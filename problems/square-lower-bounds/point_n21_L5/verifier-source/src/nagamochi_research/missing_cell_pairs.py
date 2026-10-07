"""Run short exact pair exclusions for one missing near-axis centre cell."""
from fractions import Fraction as F
from itertools import combinations
from pathlib import Path
import json,time
from saturated_axis_cells import build
from saturated_joint_search import search,replay_case
from replay_saturated_pairs import static_exclusions,clique_upper,verify


def run(source,missing,out):
    q=json.loads(source.read_text())
    q={key:q[key] for key in ('k','L','t','axis_h','rot_h','axis_inner','rot_inner','rot_half')}
    k=q['k'];L=F(q['L']);t=F(q['t']);A=F(q['axis_inner']);R=F(q['rot_inner']);H=F(q['rot_half'])
    pieces,_=build(L,t,k,A,R,H,[missing]);N=len(pieces)
    excluded=static_exclusions(pieces,t,R);cases=[];start=time.monotonic()
    q.update(status='RUNNING',missing=[missing],use_static_exclusions=True,regions=N)
    for edge in combinations(range(N),2):
        if edge in excluded:continue
        case=search(L,t,k,list(edge),node_limit=300,axis_inner=A,rot_inner=R,rot_half=H,missing=[missing]);cases.append(case)
        if replay_case(case):excluded.add(edge)
        q.update(cases=cases,excluded_pairs=sorted(excluded),seconds=time.monotonic()-start)
        out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(q,indent=2))
    q.update(status='EXACT_CONDITIONAL_MISSING_CELL_BOUND',rotated_count_upper=clique_upper(N,excluded))
    q['replay']=verify(q);out.write_text(json.dumps(q,indent=2))
    print(json.dumps(dict(file=str(out),**q['replay'],seconds=q['seconds'])),flush=True)
    return q


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('root',type=Path);a=p.parse_args()
    for k,representatives in ((4,[0,1,4]),(5,[0,1,2,5])):
        for m in representatives:
            run(a.root/f'band-pair-cuts-k{k}.json',m,a.root/f'missing-k{k}-m{m}.json')
