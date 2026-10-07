"""Propose shared support points from weighted dual-pose intersections.

Floating pricing is heuristic. Each final bound is recomputed on every exact
centre-domain face with rational integer weights; no pricing optimum is claimed.
"""
from fractions import Fraction as F
from pathlib import Path
import json,time
import numpy as np
from scipy.optimize import linprog
from scipy.sparse import csr_matrix
from two_angle_cover import patterns
from score import square
from joint_angle_lp import rotation


def proposals(poses,weights,B,existing,count=4):
    polys=[square(x,y,B,t) for x,y,t in poses];edges=[];candidates=[]
    for p in polys:
        candidates.extend(p);edges.extend(zip(p,p[1:]+p[:1]))
    def cross(a,b):return a[0]*b[1]-a[1]*b[0]
    # Exact intersections, candidate ranking only in floating arithmetic.
    for i,(a,b) in enumerate(edges):
        u=(b[0]-a[0],b[1]-a[1])
        for c,d in edges[:i]:
            v=(d[0]-c[0],d[1]-c[1]);den=cross(u,v)
            if not den:continue
            delta=(c[0]-a[0],c[1]-a[1]);r=cross(delta,v)/den;s=cross(delta,u)/den
            if 0<=r<=1 and 0<=s<=1:candidates.append((a[0]+r*u[0],a[1]+r*u[1]))
    candidates=list(set(candidates)-existing)
    if not candidates:return [],0.0
    xyz=np.array([[float(x),float(y)] for x,y in candidates]);load=np.zeros(len(candidates))
    for (x,y,t),weight in zip(poses,weights):
        c,s=map(float,rotation(t));dx=xyz[:,0]-float(x);dy=xyz[:,1]-float(y)
        load+=weight*((abs(c*dx+s*dy)<=float(B)/2+1e-10)&(abs(-s*dx+c*dy)<=float(B)/2+1e-10))
    chosen=np.argsort(-load)[:count]
    return [candidates[i] for i in chosen],float(max(load))


def run(source,a,out,rounds=4):
    old=json.loads(source.read_text());L,t,B,h=map(F,(old['L'],old['t'],old['B'],old['h']));n=old['n'];b=n-a
    assert h==0,'pricing representatives currently use fixed orientations only'
    points=set(tuple(map(F,p)) for p in old['points']);records=[];start=time.monotonic()
    for iteration in range(rounds+1):
        ordered=sorted(points);N=len(ordered);ds=[patterns(ordered,L,F(0),B,representatives=True),patterns(ordered,L,t,B,representatives=True)]
        rows=[];cols=[];values=[];row=0
        for kind,d in enumerate(ds):
            for p in d['patterns']:
                rows.extend([row]*(len(p)+1));cols.extend(p+[N+kind]);values.extend([-1]*len(p)+[1]);row+=1
        A=csr_matrix((values,(rows,cols)),shape=(row,N+2))
        r=linprog([0]*N+[-a,-b],A_ub=A,b_ub=np.zeros(row),A_eq=[[1]*N+[0,0]],b_eq=[1],bounds=(0,None),method='highs');assert r.success
        nums=[max(0,int(np.ceil(v*10**10))) for v in r.x[:N]]
        floors=[min(sum(nums[j] for j in p) for p in d['patterns']) for d in ds];mass=sum(nums);gap=a*floors[0]+b*floors[1]-mass
        record=dict(iteration=iteration,points=N,gap=gap,ratio=float(F(gap+mass,mass)),seconds=time.monotonic()-start);records.append(record);print(a,record,flush=True)
        if gap>0 or iteration==rounds:break
        poses=[];weights=[];offset=0
        for kind,d in enumerate(ds):
            for j,centre in enumerate(d['centres']):
                weight=-r.ineqlin.marginals[offset+j]
                if weight>1e-8:poses.append((*map(F,centre),F(0) if kind==0 else t));weights.append(float(weight))
            offset+=len(d['patterns'])
        new,max_load=proposals(poses,weights,B,points)
        record['pricing_max_float_load']=max_load;record['dual_pose_count']=len(poses)
        record['pricing_violation']=max_load+r.fun
        if not new or max_load<=-r.fun+1e-8:break
        points.update(q for x,y in new for q in ((x,y),(-y,x),(-x,-y),(y,-x)))
    payload=dict(status='EXACT_TWO_ANGLE_PRICED_DIAGNOSTIC',n=n,L=str(L),t=str(t),h=str(h),B=str(B),
                 points=[list(map(str,p)) for p in ordered],domains=[{k:v for k,v in d.items() if k!='centres'} for d in ds],
                 cases=[dict(axis_count=a,rotated_count=b,numerators=nums,total=mass,floors=floors,gap=gap,excluded=gap>0)],records=records)
    out.write_text(json.dumps(payload,indent=2));return payload
