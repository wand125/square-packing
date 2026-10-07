"""All-centre cover for a fixed inner-square orientation.

Supports are on a rational lattice of pitch B/subdiv. Arrangement faces
meeting the exact centre polygon are exhaustively checked. Physical squares
have side 1; scored squares have side B<1, preventing atomic double counting.
"""
from fractions import Fraction as F
from pathlib import Path
from math import floor,ceil
import argparse,json,time
import numpy as np
from scipy.optimize import linprog
from scipy.sparse import csr_matrix
from joint_angle_lp import rotation
from score import clip,area


def angle_envelope(t,h):
    t,h=F(t),F(h);lo,hi=t-h,t+h
    assert 0<=lo<=hi<=1
    q=max(abs((v-t)/(1+v*t)) for v in (lo,hi))
    assert q<=F(2,5)  # safely below tan(pi/8): cos(delta)+sin(delta) increases
    extent=(1-q*q+2*q)/(1+q*q)
    # w(t) has a single maximum on [0,1], so its minimum is at an endpoint.
    min_span=min(sum(rotation(v)) for v in (lo,hi))
    return extent,min_span


def geometry(L,t,B,subdiv,angle_radius=F(0),tight_angles=False):
    L,t,B,angle_radius=map(F,(L,t,B,angle_radius))
    assert 0<B<1 and 0<=t<=1 and angle_radius>=0
    # |theta_i-theta|<=2h and |cos(delta)|+|sin(delta)|<=1+2h.
    # Strict containment in each physical box gives disjoint scored squares.
    c,s=rotation(t);w=c+s
    if tight_angles:
        extent,min_span=angle_envelope(t,angle_radius)
        assert B*extent<1
        H=(L-min_span)/2
    else:
        assert B*(1+2*angle_radius)<1
        H=(L-w)/2+2*angle_radius
    assert H>0
    poly=[(c*x+s*y,-s*x+c*y) for x,y in ((-H,-H),(H,-H),(H,H),(-H,H))]
    pitch=B/subdiv
    # Include supports potentially captured by a centre in the relaxed domain.
    span=H*w+B/2;imax=ceil(span/pitch)+1
    support_indices=[(i,j) for i in range(-imax,imax+1) for j in range(-imax,imax+1)]
    index={p:i for i,p in enumerate(support_indices)}
    # Breaks are lattice supports +/- B/2. For even subdiv these are again
    # the same lattice. Interior face captures exactly subdiv points per axis.
    assert subdiv>0 and subdiv%2==0
    bound=ceil(H*w/pitch)+1;faces=[];patterns=[]
    for i in range(-bound,bound):
        strip=clip(clip(poly,0,i*pitch,True),0,(i+1)*pitch,False)
        if not strip or area(strip)==0:continue
        for j in range(-bound,bound):
            cell=clip(clip(strip,1,j*pitch,True),1,(j+1)*pitch,False)
            if not cell or area(cell)==0:continue
            pattern=[index[(x,y)] for x in range(i-subdiv//2+1,i+subdiv//2+1)
                     for y in range(j-subdiv//2+1,j+subdiv//2+1)]
            faces.append([i,j]);patterns.append(pattern)
    result=dict(L=str(L),t=str(t),B=str(B),angle_radius=str(angle_radius),subdiv=subdiv,
                pitch=str(pitch),support_indices=support_indices,faces=faces,patterns=patterns)
    if tight_angles:result['tight_angles']=True
    return result


def run(L,t,B,out,subdiv=8,angle_radius=F(0),tight_angles=False):
    start=time.monotonic();g=geometry(L,t,B,subdiv,angle_radius,tight_angles)
    rows=[];cols=[]
    for i,p in enumerate(g['patterns']):rows.extend([i]*len(p));cols.extend(p)
    A=csr_matrix((np.ones(len(rows)),(rows,cols)),shape=(len(g['patterns']),len(g['support_indices'])))
    result=linprog(np.ones(A.shape[1]),A_ub=-A,b_ub=-np.ones(A.shape[0]),bounds=(0,None),method='highs')
    assert result.success,result.message
    nums=[max(0,ceil(float(v)*10**9)) for v in result.x]
    denominator=min(sum(nums[j] for j in p) for p in g['patterns']);assert denominator>0
    mass=F(sum(nums),denominator)
    # Each scored closed square at a boundary face contains the support set
    # of at least one incident positive-area face. Thus verifying open faces
    # covers the full closed centre domain, including its boundary.
    payload=dict(status='EXACT_ALL_CENTRES_ANGLE_CLASS_COVER',geometry=g,
                 numerators=nums,denominator=denominator,mass=str(mass),mass_float=float(mass),
                 positive_supports=sum(v>0 for v in nums),seconds=time.monotonic()-start,
                 limitation='Only physical boxes whose t lies in the stated angle interval are counted. No assumption that all boxes have those angles is proved.')
    out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(payload,indent=2))
    print(L,t,B,angle_radius,len(g['faces']),float(mass),payload['seconds'],flush=True)
    return payload


def verify(payload):
    saved=payload['geometry']
    rebuilt=geometry(saved['L'],saved['t'],saved['B'],saved['subdiv'],saved['angle_radius'],saved.get('tight_angles',False))
    # JSON converts lattice-index tuples to lists; compare canonical encoding.
    assert json.dumps(rebuilt,sort_keys=True)==json.dumps(saved,sort_keys=True)
    nums=payload['numerators'];den=payload['denominator']
    assert type(den) is int and den>0
    assert len(nums)==len(rebuilt['support_indices'])
    assert all(type(v) is int and v>=0 for v in nums)
    assert min(sum(nums[i] for i in row) for row in rebuilt['patterns'])>=den
    mass=F(sum(nums),den);assert mass==F(payload['mass'])
    return dict(status='EXACT_ANGLE_CLASS_REPLAYED',mass=str(mass),
                count_upper=mass.numerator//mass.denominator,
                faces=len(rebuilt['faces']),supports=sum(v>0 for v in nums))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('out',type=Path);p.add_argument('--L',type=F,required=True)
    p.add_argument('--t',type=F,required=True);p.add_argument('--B',type=F,default=F(9999,10000))
    p.add_argument('--angle-radius',type=F,default=F(0));p.add_argument('--subdiv',type=int,default=8)
    a=p.parse_args();run(a.L,a.t,a.B,a.out,a.subdiv,a.angle_radius)
