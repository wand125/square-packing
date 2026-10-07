"""PL26: exact dual obstruction for a fixed common-polygon covering model.

Bound weighted polygon overlap by enclosing rectangles, including all
closed boundaries. Valid for arbitrary nonnegative auxiliary measures.
"""
from pathlib import Path
from fractions import Fraction as F
import json,argparse,hashlib,time
import numpy as np
from scipy.optimize import linprog
from scipy.sparse import csr_matrix
from low_pose_point_capacity import patterns
from robust_pose_core import common_polygon


def maximum_closed_rectangle_load(rects,weights):
    if not rects or len(rects)!=len(weights):raise ValueError('Empty or mismatched rectangles')
    assert all(type(w) is int and w>=0 for w in weights) and sum(weights)<2**62
    ys=sorted({v for x0,x1,y0,y1 in rects for v in (y0,y1)});yi={y:i for i,y in enumerate(ys)}
    events={}
    for r,w in zip(rects,weights):
        x0,x1,y0,y1=r;assert x0<=x1 and y0<=y1
        events.setdefault(x0,[[],[]])[0].append((yi[y0],yi[y1],w))
        events.setdefault(x1,[[],[]])[1].append((yi[y0],yi[y1],w))
    loads=np.zeros(len(ys),dtype=np.int64);peak=0;witness=None
    for x,(start,end) in sorted(events.items()):
        for lo,hi,w in start:loads[lo:hi+1]+=w
        j=int(np.argmax(loads));v=int(loads[j])
        if v>peak:peak=v;witness=(x,ys[j])
        for lo,hi,w in end:loads[lo:hi+1]-=w
    assert np.all(loads==0)
    return peak,witness


def boxes(cover,L,paths):
    result=[]
    for path in paths:
        rec=cover['leaves'][path];assert rec['kind']=='POSSIBLE_LOW'
        poly=common_polygon((L,F(999999,1000000)),*map(F,rec['box']));assert poly
        result.append((min(x for x,y in poly),max(x for x,y in poly),min(y for x,y in poly),max(y for x,y in poly)))
    return result


def replay(candidate,cover_path,q):
    L=F(json.loads(candidate.read_text())['L']);cover=json.loads(cover_path.read_text())
    assert q['cover_sha256']==hashlib.sha256(cover_path.read_bytes()).hexdigest()
    assert len(q['paths'])==len(set(q['paths']))
    rects=boxes(cover,L,q['paths']);peak,_=maximum_closed_rectangle_load(rects,q['weights'])
    bound=F(sum(q['weights']),peak);assert str(bound)==q['mass_lower_bound'] and peak==q['maximum_load']
    return dict(status='EXACT_FIXED_COMMON_CORE_DUAL',mass_lower_bound=str(bound),lower_float=float(bound),
                polygons=len(rects),blocks_mass_below_12=bound>=12,
                limitation='Only the fixed auxiliary common-core covering model. Not a physical packing or an obstruction to better pose domains.')


def run(candidate,cover_path,primal_path,out):
    start=time.monotonic();L=F(json.loads(candidate.read_text())['L']);cover=json.loads(cover_path.read_text());primal=json.loads(primal_path.read_text())
    extras=[tuple(map(F,p)) for p in primal.get('extra_points',[])]
    pts,rows,paths,empty=patterns(candidate,cover,F(primal['pitch']),primal.get('refinement_depth',0),extras);assert not empty
    rr=[];cc=[]
    for j,row in enumerate(rows):rr.extend([j]*len(row));cc.extend(row)
    A=csr_matrix((np.ones(len(rr)),(rr,cc)),shape=(len(rows),len(pts)))
    fit=linprog(np.ones(len(pts)),A_ub=-A,b_ub=-np.ones(len(rows)),bounds=(0,None),method='highs');assert fit.success
    w=[max(0,round(-float(v)*10**6)) for v in fit.ineqlin.marginals]
    paths=[p for p,v in zip(paths,w) if v];w=[v for v in w if v]
    rects=boxes(cover,L,paths);peak,witness=maximum_closed_rectangle_load(rects,w);assert peak>0
    q=dict(cover_sha256=hashlib.sha256(cover_path.read_bytes()).hexdigest(),paths=paths,weights=w,
           maximum_load=peak,load_witness=list(map(str,witness)),mass_lower_bound=str(F(sum(w),peak)),seconds=time.monotonic()-start)
    out.write_text(json.dumps(q,indent=2));result=replay(candidate,cover_path,json.loads(out.read_text()))
    out.with_suffix('.replay.json').write_text(json.dumps(result,indent=2));print(json.dumps(result),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for key in ('candidate','cover','primal','out'):p.add_argument(key,type=Path)
    a=p.parse_args();run(a.candidate,a.cover,a.primal,a.out)
