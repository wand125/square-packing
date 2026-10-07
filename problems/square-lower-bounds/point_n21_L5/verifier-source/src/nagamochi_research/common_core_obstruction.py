"""Exact obstruction to auxiliary covering of a FIXED common-core family.

Disjoint shrunken common polygons are not a unit-square packing witness.
"""
from pathlib import Path
from fractions import Fraction as F
import argparse,json,hashlib,time,math,random
from robust_pose_core import common_polygon
from score import area


def separating_axis(P,Q):
    for poly in (P,Q):
        for a,b in zip(poly,poly[1:]+poly[:1]):
            d=(a[1]-b[1],b[0]-a[0])
            if d==(0,0):continue
            p=[d[0]*x+d[1]*y for x,y in P];q=[d[0]*x+d[1]*y for x,y in Q]
            if max(p)<min(q):return d
            if max(q)<min(p):return (-d[0],-d[1])
    return None


def replay(candidate,cover_path,certificate):
    raw=json.loads(candidate.read_text());L=F(raw['L']);cover=json.loads(cover_path.read_text())
    assert certificate['candidate_sha256']==hashlib.sha256(candidate.read_bytes()).hexdigest()
    assert certificate['cover_sha256']==hashlib.sha256(cover_path.read_bytes()).hexdigest()
    paths=certificate['paths'];assert len(paths)==len(set(paths))
    polys=[]
    for path in paths:
        rec=cover['leaves'][path];assert rec['kind']=='POSSIBLE_LOW'
        poly=common_polygon((L,F(999999,1000000)),*map(F,rec['box']));assert area(poly)>0
        polys.append(poly)
    axes=[]
    for i,P in enumerate(polys):
        for j,Q in enumerate(polys[:i]):
            d=separating_axis(Q,P);assert d is not None,(j,i)
            axes.append(dict(pair=[j,i],axis=list(map(str,d))))
    assert certificate['auxiliary_mass_lower_bound']==len(paths)
    return dict(status='EXACT_FIXED_COMMON_CORE_COVER_OBSTRUCTION',mass_lower_bound=len(paths),pairs=len(axes),separations=axes,
                limitation='Only the auxiliary measure covering these common polygons. Not a packing of physical unit squares; not an obstruction to better pose refinement.')


def run(candidate,cover_path,out,grid=4):
    start=time.monotonic();L=F(json.loads(candidate.read_text())['L']);cover=json.loads(cover_path.read_text())
    bins={};polys={}
    sites=[.5+(float(L)-1)*i/(grid-1) for i in range(grid)]
    for path,rec in cover['leaves'].items():
        if rec['kind']!='POSSIBLE_LOW':continue
        b=list(map(F,rec['box']));x=float((b[0]+b[1])/2);y=float((b[2]+b[3])/2)
        i=min(range(grid),key=lambda z:abs(x-sites[z]));j=min(range(grid),key=lambda z:abs(y-sites[z]))
        if abs(x-sites[i])>.23 or abs(y-sites[j])>.23:continue
        poly=common_polygon((L,F(999999,1000000)),*b)
        if not poly or area(poly)==0:continue
        polys[path]=poly;bins.setdefault((i,j),[]).append((float(area(poly)),path))
    candidates={key:[path for _,path in sorted(v)[:12]] for key,v in bins.items()}
    chosen=[];compatibility={};rng=random.Random(92712)
    def compatible(a,b):
        key=tuple(sorted((a,b)))
        if key not in compatibility:compatibility[key]=separating_axis(polys[a],polys[b]) is not None
        return compatibility[key]
    for attempt in range(256):
        keys=sorted(candidates)
        if attempt:rng.shuffle(keys)
        trial=[]
        for key in keys:
            options=list(candidates[key])
            if attempt:rng.shuffle(options)
            for path in options:
                if all(compatible(other,path) for other in trial):trial.append(path);break
        if len(trial)>len(chosen):chosen=trial;print('DISJOINT',len(chosen),'bins',len(bins),flush=True)
    # A numerical integer solver only proposes a set; exact pair checks below
    # are the certificate. No optimality claim is needed or trusted.
    from scipy.optimize import milp,Bounds,LinearConstraint
    from scipy.sparse import csr_matrix
    import numpy as np
    pool=sorted({p for group in candidates.values() for p in group});rr=[];cc=[];edge=0
    for i,a in enumerate(pool):
        for j,b in enumerate(pool[:i]):
            if not compatible(a,b):rr.extend([edge,edge]);cc.extend([i,j]);edge+=1
    A=csr_matrix((np.ones(len(rr)),(rr,cc)),shape=(edge,len(pool)))
    fit=milp(-np.ones(len(pool)),integrality=np.ones(len(pool)),bounds=Bounds(0,1),
             constraints=LinearConstraint(A,-np.inf,np.ones(edge)),options={'time_limit':20})
    if fit.x is not None:
        proposed=[p for p,x in zip(pool,fit.x) if x>.5]
        if all(compatible(a,b) for i,a in enumerate(proposed) for b in proposed[:i]) and len(proposed)>len(chosen):chosen=proposed
    print('MILP_DISJOINT',len(chosen),'status',fit.status,'pool',len(pool),flush=True)
    q=dict(cover_sha256=hashlib.sha256(cover_path.read_bytes()).hexdigest(),paths=chosen,auxiliary_mass_lower_bound=len(chosen),
           candidate_sha256=hashlib.sha256(candidate.read_bytes()).hexdigest(),seconds=time.monotonic()-start)
    out.write_text(json.dumps(q,indent=2));result=replay(candidate,cover_path,q)
    out.with_suffix('.replay.json').write_text(json.dumps(result,indent=2))
    print({k:v for k,v in result.items() if k!='separations'},flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for key in ('candidate','cover','out'):p.add_argument(key,type=Path)
    a=p.parse_args();run(a.candidate,a.cover,a.out)
