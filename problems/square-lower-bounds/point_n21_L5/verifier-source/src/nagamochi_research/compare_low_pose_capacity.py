"""Compare finer supports against finer domains, preserving old supports."""
from fractions import Fraction as F
from pathlib import Path
from math import ceil,floor
import json,argparse,time,hashlib
import numpy as np
from scipy.optimize import linprog
from scipy.sparse import csr_matrix
from low_pose_point_capacity import patterns,replay_many


def run(candidate,cover_path,baseline,out,schemes=None,core_method='robust'):
    cover=json.loads(cover_path.read_text());old=json.loads(baseline.read_text())
    extra=[tuple(map(F,p)) for p in old['points']]
    results=[];out.mkdir(exist_ok=True)
    if schemes is None:schemes=[('finer-points',F(1,8),0),('finer-domains',F(1,4),2)]
    for name,pitch,depth in schemes:
        start=time.monotonic();print('BUILD',name,flush=True)
        pts,rows,paths,empty=patterns(candidate,cover,pitch,depth,extra,core_method)
        assert not empty,('uncovered common core',len(empty))
        rr=[];cc=[]
        for i,row in enumerate(rows):rr.extend([i]*len(row));cc.extend(row)
        A=csr_matrix((np.ones(len(rr)),(rr,cc)),shape=(len(rows),len(pts)))
        # Check the old measure is still feasible before optimizing.
        weights={tuple(map(F,p)):w for p,w in zip(old['points'],old['numerators'])}
        inherited=[weights.get(p,0) for p in pts]
        assert all(sum(inherited[i] for i in row)>=old['denominator'] for row in rows)
        r=linprog(np.ones(len(pts)),A_ub=-A,b_ub=-np.ones(len(rows)),bounds=(0,None),method='highs')
        assert r.success,r.message
        nums=[max(0,ceil(float(x)*10**9)) for x in r.x];den=min(sum(nums[i] for i in row) for row in rows)
        mass=F(sum(nums),den)
        if mass>F(sum(inherited),old['denominator']):nums=inherited;den=old['denominator'];mass=F(sum(nums),den)
        q=dict(model='LOW_POSE_POINT_CAPACITY_V3' if core_method!='robust' else 'LOW_POSE_POINT_CAPACITY_V2',core_method=core_method,cover_sha256=hashlib.sha256(cover_path.read_bytes()).hexdigest(),
               pitch=str(pitch),refinement_depth=depth,extra_points=[list(map(str,p)) for p in extra],
               paths=paths,points=[list(map(str,p)) for p in pts],numerators=nums,denominator=den,mass=str(mass),capacity=floor(mass),seconds=time.monotonic()-start)
        (out/(name+'.json')).write_text(json.dumps(q,indent=2));results.append(q)
        print(name,'cells',len(rows),'points',len(pts),'mass',float(mass),'capacity',floor(mass),'seconds',q['seconds'],flush=True)
    replays=replay_many(candidate,cover_path,results)
    (out/'replays.json').write_text(json.dumps(replays,indent=2));print('REPLAYED',[(q['capacity'],q['mass']) for q in replays],flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for name in ('candidate','cover','baseline','out'):p.add_argument(name,type=Path)
    a=p.parse_args();run(a.candidate,a.cover,a.baseline,a.out)
