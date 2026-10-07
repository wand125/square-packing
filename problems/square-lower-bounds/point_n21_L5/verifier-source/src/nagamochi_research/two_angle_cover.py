"""Shared atomic measure with type-dependent capture floors.

For type counts a,b, a*c0+b*c1 > total mass is a packing contradiction.
Every capture floor is checked over the entire closed centre domain.
"""
from fractions import Fraction as F
from math import ceil
from pathlib import Path
import json,time
import numpy as np
from scipy.optimize import linprog
from scipy.sparse import csr_matrix
from joint_angle_lp import rotation
from fixed_orientation_cover import angle_envelope
from score import clip,area


def patterns(points,L,t,B,h=F(0),representatives=False):
    extent,span=angle_envelope(t,h);assert 0<B<1 and B*extent<1
    c,s=rotation(t);H=(L-span)/2;bound=H*(c+s)
    poly=[(c*x+s*y,-s*x+c*y) for x,y in ((-H,-H),(H,-H),(H,H),(-H,H))]
    uv=[(c*x+s*y,-s*x+c*y) for x,y in points]
    axes=[];masks=[]
    for axis in (0,1):
        breaks=sorted({-bound,bound}|{p[axis]+d for p in uv for d in (-B/2,B/2) if -bound<p[axis]+d<bound})
        axes.append(breaks)
        masks.append([{i for i,p in enumerate(uv) if abs(p[axis]-(lo+hi)/2)<B/2}
                      for lo,hi in zip(breaks,breaks[1:])])
    found=set();faces=0;centres={}
    for i,(lo,hi) in enumerate(zip(axes[0],axes[0][1:])):
        strip=clip(clip(poly,0,lo,True),0,hi,False)
        if not strip or area(strip)==0:continue
        for j,(low,high) in enumerate(zip(axes[1],axes[1][1:])):
            cell=clip(clip(strip,1,low,True),1,high,False)
            if cell and area(cell)>0:
                key=tuple(sorted(masks[0][i]&masks[1][j]));found.add(key);faces+=1
                if representatives and key not in centres:
                    u=sum(p[0] for p in cell)/len(cell);v=sum(p[1] for p in cell)/len(cell)
                    centres[key]=[str(c*u-s*v),str(s*u+c*v)]
    result=dict(patterns=[list(p) for p in sorted(found)],faces=faces)
    if representatives:result['centres']=[centres[p] for p in sorted(found)]
    return result


def supports(seed,L,B,symmetry=False,prune_seed=False):
    g=seed['geometry'];t=F(g['t']);c,s=rotation(t);coords=list(map(F,g['coordinates']));m=len(coords)
    points=set()
    for i,num in enumerate(seed['numerators']):
        # Parent weights only propose locations. Dropping tiny seed locations
        # does not reuse a weakened certificate: the new domain is rebuilt.
        if num and (not prune_seed or num*10**8>=max(seed['numerators'])):
            u,v=coords[i//m],coords[i%m];points.add((c*u-s*v,s*u+c*v))
    H=(L-1)/2;number=ceil((L-1)/B)
    axis=[F(0)] if number==1 else [-H+B/2+j*(2*H-B)/(number-1) for j in range(number)]
    points|={(x,y) for x in axis for y in axis}
    if symmetry:points|={q for x,y in list(points) for q in ((-y,x),(-x,-y),(y,-x))}
    return sorted(points)


def run(seed_path,L,n,out,h=F(0),symmetry=False,prune_seed=False):
    start=time.monotonic();seed=json.loads(seed_path.read_text());t=F(seed['geometry']['t'])
    B=min(F(seed['geometry']['B']),F(999999,1000000)/angle_envelope(t,h)[0])
    points=supports(seed,L,B,symmetry,prune_seed);N=len(points)
    domains=[patterns(points,L,F(0),B),patterns(points,L,t,B,h)]
    rows=[];cols=[];vals=[];row=0
    for kind,domain in enumerate(domains):
        for p in domain['patterns']:
            rows.extend([row]*(len(p)+1));cols.extend(p+[N+kind]);vals.extend([-1]*len(p)+[1]);row+=1
    A=csr_matrix((vals,(rows,cols)),shape=(row,N+2));cases=[]
    for a in range(n+1):
        b=n-a;r=linprog([0]*N+[-a,-b],A_ub=A,b_ub=np.zeros(row),
                       A_eq=[[1]*N+[0,0]],b_eq=[1],bounds=(0,None),method='highs')
        assert r.success,r.message
        nums=[max(0,ceil(float(x)*10**10)) for x in r.x[:N]]
        floors=[min(sum(nums[j] for j in p) for p in domain['patterns']) for domain in domains]
        total=sum(nums);gap=a*floors[0]+b*floors[1]-total
        cases.append(dict(axis_count=a,rotated_count=b,numerators=nums,total=total,floors=floors,
                          gap=gap,excluded=gap>0,ratio=float(F(a*floors[0]+b*floors[1],total))))
    result=dict(status='EXACT_TWO_ANGLE_COUNT_DIAGNOSTIC',n=n,L=str(L),t=str(t),h=str(h),B=str(B),
                points=[list(map(str,p)) for p in points],domains=domains,cases=cases,seconds=time.monotonic()-start,pruned_seed_locations=prune_seed,
                limitation='Only the two specified orientation classes and stated counts. Failure to exclude is not a feasible packing witness.')
    out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(result,indent=2))
    print(n,L,t,h,N,[len(d['patterns']) for d in domains],[(q['axis_count'],q['ratio'],q['excluded']) for q in cases],result['seconds'],flush=True)
    return result


def verify(q):
    points=[tuple(map(F,p)) for p in q['points']];L,t,B,h=map(F,(q['L'],q['t'],q['B'],q['h']))
    domains=[patterns(points,L,F(0),B),patterns(points,L,t,B,h)];assert domains==q['domains']
    for case in q['cases']:
        nums=case['numerators'];assert len(nums)==len(points) and all(type(v) is int and v>=0 for v in nums)
        floors=[min(sum(nums[j] for j in p) for p in d['patterns']) for d in domains]
        assert floors==case['floors'] and sum(nums)==case['total']>0
        a,b=case['axis_count'],case['rotated_count'];assert a+b==q['n'] and min(a,b)>=0
        gap=a*floors[0]+b*floors[1]-sum(nums)
        assert gap==case['gap'] and case['excluded']==(gap>0)
    return [c['axis_count'] for c in q['cases'] if c['excluded']]


def axis_band_radius(B):
    B=F(B);assert 0<B<1
    h=(1-B)/(4*B)
    assert h>0 and B*(1+2*h)<1
    # Every unit square has coordinate half-span >=1/2, so its centre is
    # already in the axis-type domain. For |tan(theta/2)|<=h, the nominal
    # axis-aligned B-square is strictly inside the physical square.
    return h
