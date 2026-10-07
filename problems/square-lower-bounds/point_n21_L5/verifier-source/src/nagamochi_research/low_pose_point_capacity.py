"""PL23: certify a capacity upper bound for ALL retained low-pose cells.

Points are inside common strict physical cores. An auxiliary point measure
bounds the number of low-capture boxes; it is not added to the old measure.
"""
from fractions import Fraction as F
from pathlib import Path
from math import ceil,floor
import argparse,json,hashlib,time
import numpy as np
from scipy.optimize import linprog
from scipy.sparse import csr_matrix
from robust_pose_core import common_polygon
from full_pose_low_cover import verify as verify_cover,split,outside_container
from mixed_density_check import expand
from score import contains,area


def patterns(candidate,cover,pitch=F(1,4),depth=0,extra_points=(),core_method='robust'):
    if type(depth) is not int or not 0<=depth<=6:raise ValueError('Invalid refinement depth')
    if pitch<=0:raise ValueError('Positive pitch required')
    if core_method=='robust':core=common_polygon
    elif core_method=='correlated':
        from correlated_pose_core import correlated_polygon
        core=correlated_polygon
    elif core_method=='physical-correlated':
        from correlated_pose_core import correlated_polygon
        from physical_pose_bound import restrict_centres
        def core(model,*box):
            tight=restrict_centres(model[0],box)
            return [] if tight is None else correlated_polygon(model,*tight)
    else:raise ValueError('Unknown common core method')
    model=expand(json.loads(candidate.read_text()));L=model[0]
    # Distinct from the score core: each physical box contains this strict core.
    physical=(L,F(999999,1000000));points=[];index={};rows=[];paths=[];empty=[]
    def point_id(p):
        if p not in index:index[p]=len(points);points.append(p)
        return index[p]
    cells=[]
    for path,rec in sorted(cover['leaves'].items()):
        if rec['kind']!='POSSIBLE_LOW':continue
        children=[(path,tuple(map(F,rec['box'])))]
        for _ in range(depth):
            children=[(key+str(i),child) for key,box in children for i,child in enumerate(split(box))]
        cells.extend(children)
    for path,box in cells:
        if outside_container(box,L):continue
        poly=core(physical,*box)
        if not poly or area(poly)==0:empty.append(path);continue
        xmin,xmax=min(p[0] for p in poly),max(p[0] for p in poly)
        ymin,ymax=min(p[1] for p in poly),max(p[1] for p in poly)
        pts=[]
        for i in range(ceil(xmin/pitch),floor(xmax/pitch)+1):
            for j in range(ceil(ymin/pitch),floor(ymax/pitch)+1):
                p=(pitch*i,pitch*j)
                if contains(poly,p):pts.append(point_id(p))
        for p in extra_points:
            if xmin<=p[0]<=xmax and ymin<=p[1]<=ymax and contains(poly,p):pts.append(point_id(p))
        pts=sorted(set(pts))
        if not pts:
            p=tuple(sum(v[d] for v in poly)/len(poly) for d in (0,1))
            assert contains(poly,p);pts=[point_id(p)]
        rows.append(pts);paths.append(path)
    return points,rows,paths,empty


def replay_many(candidate,cover_path,certificates):
    cover=json.loads(cover_path.read_text());verify_cover(candidate,cover)
    results=[]
    for q in certificates:
        assert q['model'] in ('LOW_POSE_POINT_CAPACITY_V1','LOW_POSE_POINT_CAPACITY_V2','LOW_POSE_POINT_CAPACITY_V3')
        assert q['cover_sha256']==hashlib.sha256(cover_path.read_bytes()).hexdigest()
        extras=[tuple(map(F,p)) for p in q.get('extra_points',[])]
        method=q.get('core_method','robust')
        if q['model']!='LOW_POSE_POINT_CAPACITY_V3':assert method=='robust'
        pts,rows,paths,empty=patterns(candidate,cover,F(q['pitch']),q.get('refinement_depth',0),extras,method)
        assert not empty and q['paths']==paths and q['points']==[list(map(str,p)) for p in pts]
        w=q['numerators'];den=q['denominator'];assert type(den) is int and den>0
        assert len(w)==len(pts) and all(type(x) is int and x>=0 for x in w)
        assert all(sum(w[i] for i in row)>=den for row in rows)
        mass=F(sum(w),den);assert str(mass)==q['mass'] and q['capacity']==floor(mass)
        results.append(dict(status='EXACT_LOW_POSE_POINT_CAPACITY_REPLAYED',capacity=floor(mass),mass=str(mass),cells=len(rows),
                    limitation='Capacity of the saved possible-low domain only; combine with capture thresholds separately.'))
    return results


def replay(candidate,cover_path,q):return replay_many(candidate,cover_path,[q])[0]


def run(candidate,cover_path,out):
    start=time.monotonic();cover=json.loads(cover_path.read_text());verify_cover(candidate,cover)
    pts,rows,paths,empty=patterns(candidate,cover)
    if empty:
        q=dict(status='COMMON_CORE_EMPTY_UNRESOLVED',empty=empty,cells=len(rows)+len(empty))
        out.write_text(json.dumps(q,indent=2));print(json.dumps(dict(status=q['status'],empty=len(empty))),flush=True);return q
    if not rows:
        q=dict(status='NO_POSSIBLE_LOW_CELLS',capacity=0);out.write_text(json.dumps(q));return q
    rr=[];cc=[]
    for j,row in enumerate(rows):rr.extend([j]*len(row));cc.extend(row)
    A=csr_matrix((np.ones(len(rr)),(rr,cc)),shape=(len(rows),len(pts)))
    fit=linprog(np.ones(len(pts)),A_ub=-A,b_ub=-np.ones(len(rows)),bounds=(0,None),method='highs')
    assert fit.success,fit.message
    w=[max(0,ceil(float(x)*10**9)) for x in fit.x];den=min(sum(w[i] for i in row) for row in rows)
    assert den>0;mass=F(sum(w),den)
    q=dict(model='LOW_POSE_POINT_CAPACITY_V1',cover_sha256=hashlib.sha256(cover_path.read_bytes()).hexdigest(),pitch='1/4',
           paths=paths,points=[list(map(str,p)) for p in pts],numerators=w,denominator=den,mass=str(mass),capacity=floor(mass),seconds=time.monotonic()-start)
    out.write_text(json.dumps(q,indent=2));result=replay(candidate,cover_path,json.loads(out.read_text()))
    out.with_suffix('.replay.json').write_text(json.dumps(result,indent=2));print(json.dumps(result),flush=True);return q

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('candidate',type=Path);p.add_argument('cover',type=Path);p.add_argument('out',type=Path)
    a=p.parse_args();run(a.candidate,a.cover,a.out)
