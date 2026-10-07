"""Fixed-budget finite refit of lemma witnesses, with independent held-out poses."""
import os
for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','NUMBA_NUM_THREADS'):os.environ[k]='1'
import argparse,json,sys,random
from pathlib import Path
from fractions import Fraction as F
import numpy as np
from expanded_search_pilot import CODE  # selects the frozen fast_geometry engine
from unified_geometry import expand_primitives,matrix
from unified_measure import orbit
from template_repair import bounded_weights
from mixed_density_check import expand,evaluate


def coefficients(poses,B,expanded,L):
    # The frozen overlap engine assumes c,s>=0. Each basis is D4 averaged,
    # so reflect the complete pose, never only the angle.
    p=np.array(poses,float,copy=True)
    negative=p[:,2]<0
    p[negative,1]=float(L)-p[negative,1]
    p[negative,2]*=-1
    return matrix(p,float(B),expanded)


def poses(L,count,seed):
    rng=random.Random(seed);out=[]
    for i in range(count):
        t=F(0) if i%10==0 else F(rng.randrange(-414000,414001),1000000)
        u=abs(t);h=(1-u*u+2*u)/(2*(1+u*u));reach=L-2*h
        p=[h+reach*F(rng.randrange(1000001),1000000) for _ in range(2)]
        if i%5==0:p[i%2]=h if i%4<2 else L-h
        out.append((*p,t))
    return out


def export(data,primitives,weights,B):
    M=F(data['total_mass']);raw=[F(max(0,round(float(x)*10**12)),10**12) for x in weights]
    ws=[w*M/sum(raw) for w in raw];d=dict(data);d['B']=str(B);d.pop('proof_net',None)
    d['status']='FINITE_REFIT_NOT_CERTIFIED';d['rectangles']=[];points={};L=F(d['L'])
    for primitive,w in zip(primitives,ws):
        if not w:continue
        if primitive['kind']=='rectangle':d['rectangles'].append(dict(rectangle=primitive['geometry'],mass=str(w)))
        else:
            for p in orbit('point',primitive['geometry'],L):points[p]=points.get(p,F(0))+w/8
    d['points']=[dict(point=list(map(str,p)),mass=str(w)) for p,w in sorted(points.items())]
    expand(d);return d


def run(candidate,samples,out):
    out.mkdir(parents=True,exist_ok=False);data=json.loads(candidate.read_text());model=expand(data);L=model[0]
    primitives=[dict(kind='rectangle',geometry=r['rectangle']) for r in data['rectangles']]+[dict(kind='point',geometry=r['point']) for r in data['points']]
    w0=np.array([float(F(r['mass'])) for r in data['rectangles']+data['points']]);expanded=expand_primitives(primitives,L)
    witnesses=[tuple(map(F,[r['cx'],r['cy'],r['t']])) for r in json.loads(samples.read_text())['samples']]
    train=witnesses+poses(L,1024,9271201);held=poses(L,2048,9271202)
    (out/'poses.json').write_text(json.dumps(dict(train=[list(map(str,p)) for p in train],held=[list(map(str,p)) for p in held]),indent=2))
    records=[]
    for B in [model[1],F(999999,1000000)]:
        A=coefficients(train,B,expanded,L);H=coefficients(held,B,expanded,L)
        original=H@w0
        baseline=dict(data);baseline['B']=str(B);baseline.pop('proof_net',None);base_model=expand(baseline)
        check_ids=list(range(12))+[int(original.argmin())]
        numeric_error=max(abs(float(F(evaluate(base_model,*held[i])['score']))-original[i]) for i in check_ids)
        if numeric_error>1e-6:raise ValueError(f'Numeric/exact mismatch {numeric_error}')
        print('BASELINE_CHECK',str(B),numeric_error,flush=True)
        for label,lo,hi in [('tight',.95,1.1),('medium',.8,1.5),('wide',0.,5.)]:
            weights,minimum=bounded_weights(A,w0,lo,hi);d=export(data,primitives,weights,B);m=expand(d)
            name=f'B{B.numerator}_{B.denominator}-{label}';(out/f'{name}.json').write_text(json.dumps(d,indent=2))
            vals=H@weights;checks=[]
            for i in np.argsort(vals)[:8]:
                checks.append(evaluate(m,*held[int(i)]))
            witness_checks=[evaluate(m,*p) for p in witnesses]
            row=dict(name=name,B=str(B),trust=[lo,hi],training_minimum=minimum,
                     original_held_minimum=float(min(original)),held_minimum=float(min(vals)),
                     held_below_one=int(sum(vals<1)),held_worse_than_original=int(sum(vals<original-1e-8)),
                     exact_witness_minimum=str(min(F(x['score']) for x in witness_checks)),
                     exact_held_checks=checks,exact_mass=str(m[4]),general_packing_exclusion=False)
            records.append(row);(out/'results.json').write_text(json.dumps(records,indent=2))
            print({k:v for k,v in row.items() if k!='exact_held_checks'},flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for k in ('candidate','samples','out'):p.add_argument(k,type=Path)
    a=p.parse_args();run(a.candidate,a.samples,a.out)
