"""Evaluate low cells, independently replay local upgrades, then graph capacity.
The untouched source cover requires its own full replay.
"""
import argparse,json,hashlib
from fractions import Fraction as F
from pathlib import Path
from mixed_density_check import expand
from full_pose_low_cover import lower_function
from pose_symmetry import cached_bound
from pose_conflict_capacity import run as graph_run
from verify_pose_upgrade_structure import verify as verify_inheritance


def needs_upgrade(existing,method):
    ranks={'physical-correlated':0,'physical-adaptive1':1,'physical-adaptive2':2}
    return existing not in ranks or ranks[existing]<ranks[method]


def run(candidate,source,out,threshold,method="physical-adaptive1"):
    evaluate=lower_function(method)
    model=expand(json.loads(candidate.read_text()));q=json.loads(source.read_text())
    if q['digest']!=model[-1]:raise ValueError('Source mismatch')
    if threshold<=0:raise ValueError('Positive threshold required')
    out.mkdir(parents=True,exist_ok=True)
    selected={p:r for p,r in q['leaves'].items() if r['kind']!='OUTSIDE' and F(r['lower'])<threshold and needs_upgrade(r.get('bound_method',q.get('bound_method','square')),method)}
    bound,cache=cached_bound(model,evaluate,q.get('symmetry'))
    values={}
    for i,(p,rec) in enumerate(selected.items()):
        values[p]=str(bound(*map(F,rec['box'])))
        if (i+1)%50==0:print('UPGRADE',i+1,'/',len(selected),'unique',len(cache),flush=True)
    (out/'local-values.json').write_text(json.dumps(dict(source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),method=method,values=values),indent=2))
    replay,_=cached_bound(model,evaluate,q.get('symmetry'))
    for p,rec in selected.items():
        v=F(values[p]);assert replay(*map(F,rec['box']))==v
        if v>F(rec['lower']):rec.update(lower=str(v),bound_method=method)
    for rec in q['leaves'].values():
        if rec['kind']!='OUTSIDE':rec['kind']='HIGH' if F(rec['lower'])>=threshold else 'POSSIBLE_LOW'
    q['threshold']=str(threshold)
    # This derivative cover inherits unchanged subtrees, and upgraded values
    # were replayed above. It is NOT a new full-cover replay report.
    cover=out/'derived-cover.json';cover.write_text(json.dumps(q))
    inheritance=verify_inheritance(source,cover,out/'local-values.json')
    (out/'inheritance-replay.json').write_text(json.dumps(inheritance,indent=2))
    graph=graph_run(candidate,cover,threshold,out/'graph.json')
    n=json.loads(candidate.read_text())['n'];floor=min(F(rec['lower']) for rec in q['leaves'].values() if rec['kind']!='OUTSIDE')
    cap=min(n,graph['capacity']);lower=n*floor+(threshold-floor)*(n-cap)
    result=dict(status='LOCAL_UPGRADES_AND_GRAPH_CHECKED',source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                selected=len(selected),remaining=len(graph['paths']),threshold=str(threshold),capacity=cap,
                floor=str(floor),capture_sum_lower=str(lower),gap=str(lower-model[4]),
                requires_replayed_source=True,general_packing_exclusion=False)
    (out/'replay.json').write_text(json.dumps(result,indent=2));print(result,flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for name in ('candidate','source','out'):p.add_argument(name,type=Path)
    p.add_argument('--threshold',type=F,required=True)
    p.add_argument('--method',choices=['physical-adaptive1','physical-adaptive2'],default='physical-adaptive1');a=p.parse_args()
    run(a.candidate,a.source,a.out,a.threshold,a.method)
