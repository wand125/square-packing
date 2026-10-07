"""Measure a direct normalized partition for an independent structural solver.

All results are conditional on saturated axis cells and one fixed rotor band.
The graph bound alone is not an unrestricted packing bound.
"""
from pathlib import Path
from fractions import Fraction as F
from itertools import combinations
from math import comb
import argparse,json,time
from normalized_axis_cells import geometry
from joint_angle_lp import rotation
from replay_saturated_pairs import static_exclusions


def run(source,out):
    q=json.loads(source.read_text());cfg=q['config'];start=time.monotonic()
    cells,pieces=geometry(cfg,[]);R=F(cfg['rot_inner']);t=F(cfg['t']);c,s=rotation(t)
    bad=[]
    for i,p in enumerate(pieces):
        if any(max(a*x+b*y for x,y in p)-min(a*x+b*y for x,y in p)>=R for a,b in ((c,s),(-s,c))):bad.append(i)
    edges=static_exclusions(pieces,t,R);N=len(pieces);groups=[]
    for i in sorted(range(N),key=lambda i:-sum(i in e for e in edges)):
        group=next((g for g in groups if all(tuple(sorted((i,j))) in edges for j in g)),None)
        if group is None:groups.append([i])
        else:group.append(i)
    assert sorted(i for g in groups for i in g)==list(range(N))
    assert all(tuple(sorted(e)) in edges for g in groups for e in combinations(g,2))
    target=q['necessary_outside_axis_band']
    r=dict(status='EXACT_CONDITIONAL_PARTITION' if not bad else 'REGION_CAPACITY_UNRESOLVED',n=q['n'],k=q['k'],config=cfg,
           direct_regions=N,reference_regions=q['saturated_reference_regions'],unproved_unit_capacity_regions=bad,
           static_conflicts=len(edges),clique_partition=groups,rotor_count_upper=len(groups) if not bad else None,
           target_rotor_count=target,raw_target_combinations=comb(N,target),seconds=time.monotonic()-start,
           limitation='Saturated near-axis cells plus a single chosen rotor band only; greedy graph bound need not be sharp.')
    out.write_text(json.dumps(r,indent=2));print(q['n'],r['status'],N,len(groups),r['raw_target_combinations'],r['seconds'],flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('root',type=Path);a=p.parse_args()
    for n in (32,45,61):run(a.root/f'n{n}.json',a.root/f'n{n}-partition.json')
