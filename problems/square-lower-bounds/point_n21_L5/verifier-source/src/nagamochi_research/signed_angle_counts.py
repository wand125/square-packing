"""Shared measure for axis / positive / negative angle bands (PL12, PL13).

No fixed near-axis occupancy and no common angle among rotated boxes.
Each specified count composition gets its own nonnegative measure, with
all-centre rational recertification. Three bands are NOT all orientations.
"""
from fractions import Fraction as F
from pathlib import Path
from math import ceil
import argparse, json, time, hashlib
import numpy as np
from scipy.optimize import linprog
from scipy.sparse import csr_matrix
from two_angle_cover import patterns
from packing_lemmas import normalized_axis_bounds, axis_core_halfwidth


def domains(points,L,t,B,h):
    return [patterns(points,L,F(0),B), patterns(points,L,t,B,h),
            patterns([(x,-y) for x,y in points],L,t,B,h)]


def compositions(n,axis_cap):
    return [(a,b,n-a-b) for a in range(min(n,axis_cap)+1) for b in range(n-a+1)]


def verify(q):
    assert q['model']=='SIGNED_THREE_BAND_SHARED_MEASURE_V1'
    n,k=q['n'],q['k'];assert type(n) is int and n>0 and type(k) is int
    L,t,B,h=map(F,(q['L'],q['t'],q['B'],q['h']))
    assert t>h>=0
    bound=normalized_axis_bounds(k,F(k)-L)
    assert 0<F(q['axis_h'])<=min(axis_core_halfwidth(B),bound['halfwidth'])
    assert q['axis_cap']==bound['capacity']
    points=[tuple(map(F,p)) for p in q['points']]
    ds=domains(points,L,t,B,h)
    expected=compositions(n,bound['capacity'])
    assert [tuple(c['counts']) for c in q['cases']]==expected
    for c in q['cases']:
        w=c['numerators'];assert len(w)==len(points) and all(type(x) is int and x>=0 for x in w)
        total=sum(w);assert total>0
        floors=[min(sum(w[i] for i in p) for p in d['patterns']) for d in ds]
        gap=sum(a*b for a,b in zip(c['counts'],floors))-total
        assert c['floors']==floors and c['total']==total and c['gap']==gap
        assert c['excluded']==(gap>0)
    return dict(status='EXACT_THREE_BAND_COUNTS_REPLAYED',cases=len(q['cases']),
                excluded=sum(c['excluded'] for c in q['cases']),
                unresolved=[c['counts'] for c in q['cases'] if not c['excluded']],
                general_packing_exclusion=False)


def run(parent,out,k,L):
    start=time.monotonic();seed=json.loads(parent.read_text())
    n=seed['n'];t,B,h=map(F,(seed['t'],seed['B'],seed['h']))
    points={tuple(map(F,p)) for p in seed['points']}
    points=sorted(points|{(x,-y) for x,y in points})
    ds=domains(points,L,t,B,h);N=len(points);rr=[];cc=[];vv=[];ridx=0
    for j,d in enumerate(ds):
        for p in d['patterns']:
            rr.extend([ridx]*(len(p)+1));cc.extend(p+[N+j]);vv.extend([-1]*len(p)+[1]);ridx+=1
    A=csr_matrix((vv,(rr,cc)),shape=(ridx,N+3))
    cap=normalized_axis_bounds(k,F(k)-L);cases=[]
    for case_index,counts in enumerate(compositions(n,cap['capacity'])):
        r=linprog([0]*N+[-x for x in counts],A_ub=A,b_ub=np.zeros(ridx),
                  A_eq=[[1]*N+[0]*3],b_eq=[1],bounds=(0,None),method='highs')
        assert r.success,r.message
        nums=[max(0,ceil(float(x)*10**10)) for x in r.x[:N]]
        floors=[min(sum(nums[i] for i in p) for p in d['patterns']) for d in ds]
        total=sum(nums);gap=sum(a*b for a,b in zip(counts,floors))-total
        if case_index%50==0:print('COUNT_PROGRESS',n,str(L),case_index,flush=True)
        cases.append(dict(counts=counts,numerators=nums,floors=floors,total=total,gap=gap,excluded=gap>0))
    q=dict(model='SIGNED_THREE_BAND_SHARED_MEASURE_V1',n=n,k=k,L=str(L),t=str(t),B=str(B),h=str(h),
           axis_h=str(min(axis_core_halfwidth(B),cap['halfwidth'])),axis_cap=cap['capacity'],
           points=[list(map(str,p)) for p in points],cases=cases,
           pattern_counts=[len(d['patterns']) for d in ds],source_sha256=hashlib.sha256(parent.read_bytes()).hexdigest(),
           seconds=time.monotonic()-start,
           limitation='All centres and all counts within three specified angle bands only. Other orientations remain uncovered.')
    out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(q,indent=2))
    replay=verify(json.loads(out.read_text()));out.with_suffix('.replay.json').write_text(json.dumps(replay,indent=2))
    print(json.dumps(dict(n=n,L=str(L),supports=N,seconds=q['seconds'],patterns=q['pattern_counts'],
                         cases=replay['cases'],excluded=replay['excluded'],unresolved=len(replay['unresolved']))),flush=True)
    return q

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('parent',type=Path);p.add_argument('out',type=Path)
    p.add_argument('--k',type=int,required=True);p.add_argument('--L',type=F,required=True)
    a=p.parse_args();run(a.parent,a.out,a.k,a.L)
