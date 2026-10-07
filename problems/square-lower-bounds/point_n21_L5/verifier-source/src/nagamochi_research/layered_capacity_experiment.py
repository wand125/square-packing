"""One complete pose replay, shared geometry, and several exact capacity cuts."""
from pathlib import Path
from fractions import Fraction as F
from copy import deepcopy
from math import ceil
import argparse,hashlib,json,time
import numpy as np
from scipy.optimize import linprog
from scipy.sparse import csr_matrix
from full_pose_low_cover import verify
from low_pose_point_capacity import patterns
from mixed_density_check import expand
from packing_lemmas import low_capture_bound


def run(candidate,cover_path,out):
    source=json.loads(cover_path.read_text());model=expand(json.loads(candidate.read_text()))
    start=time.monotonic();replayed=verify(candidate,source)
    print('COVER_REPLAYED',replayed,flush=True)
    out.mkdir(exist_ok=True);(out/'cover-replay.json').write_text(json.dumps(replayed,indent=2))
    n=json.loads(candidate.read_text())['n'];floor=min(F(r['lower']) for r in source['leaves'].values() if r['kind']!='OUTSIDE')
    thresholds=[t for t in map(F,['0.3','0.5','0.7','0.8','0.9','1','1.1','1.2']) if t>floor]
    assert thresholds
    q=deepcopy(source);q['threshold']=str(max(thresholds))
    for r in q['leaves'].values():
        if r['kind']!='OUTSIDE':r['kind']='POSSIBLE_LOW' if F(r['lower'])<max(thresholds) else 'HIGH'
    print('BUILD_SHARED_GEOMETRY',flush=True)
    pts,rows,paths,empty=patterns(candidate,q,F(1,8),core_method='physical-correlated')
    trivial=min(n,(model[0]*model[0]).numerator//(model[0]*model[0]).denominator)
    records=[]
    for threshold in thresholds:
        chosen=[i for i,path in enumerate(paths) if F(q['leaves'][path]['lower'])<threshold]
        unresolved=[path for path in empty if F(q['leaves'][path]['lower'])<threshold]
        rec=dict(threshold=str(threshold),capacity=trivial,unresolved_common_cores=len(unresolved),rows=len(chosen))
        if not unresolved and not chosen:rec.update(capacity=0,status='EMPTY_LOW_DOMAIN')
        elif not unresolved:
            rr=[];cc=[]
            for j,i in enumerate(chosen):rr.extend([j]*len(rows[i]));cc.extend(rows[i])
            A=csr_matrix((np.ones(len(rr)),(rr,cc)),shape=(len(chosen),len(pts)))
            fit=linprog(np.ones(len(pts)),A_ub=-A,b_ub=-np.ones(len(chosen)),bounds=(0,None),method='highs',options={'time_limit':15})
            rec['solver_status']=int(fit.status)
            if fit.x is not None and np.all(np.isfinite(fit.x)):
                w=[max(0,ceil(float(v)*10**9)) for v in fit.x]
                denominator=min(sum(w[j] for j in rows[i]) for i in chosen)
                if denominator>0:
                    mass=F(sum(w),denominator)
                    rec.update(numerators=w,denominator=denominator,mass=str(mass),capacity=min(trivial,mass.numerator//mass.denominator))
        records.append(rec);(out/'candidates.json').write_text(json.dumps(records))
        print({k:v for k,v in rec.items() if k!='numerators'},flush=True)
    # Rebuild the geometric rows independently. The source cover was already
    # checked above and is not mutated; only the threshold labels were changed.
    print('REPLAY_GEOMETRY',flush=True)
    P,R,K,E=patterns(candidate,q,F(1,8),core_method='physical-correlated')
    assert (P,R,K,E)==(pts,rows,paths,empty)
    for rec in records:
        t=F(rec['threshold']);chosen=[i for i,path in enumerate(K) if F(q['leaves'][path]['lower'])<t]
        if 'numerators' in rec:
            w=rec['numerators'];d=rec['denominator']
            assert len(w)==len(P) and all(type(v) is int and v>=0 for v in w) and type(d) is int and d>0
            assert not any(F(q['leaves'][path]['lower'])<t for path in E)
            assert all(sum(w[j] for j in R[i])>=d for i in chosen)
            mass=F(sum(w),d);assert str(mass)==rec['mass'] and rec['capacity']==min(trivial,mass.numerator//mass.denominator)
        elif rec.get('status')=='EMPTY_LOW_DOMAIN':assert not chosen and not any(F(q['leaves'][path]['lower'])<t for path in E)
        else:assert rec['capacity']==trivial
    lower=low_capture_bound([n],[floor],[t-floor for t in thresholds],[r['capacity'] for r in records])
    result=dict(status='LAYERED_CAPACITIES_AND_COMPLETE_COVER_REPLAYED',cover_sha256=hashlib.sha256(cover_path.read_bytes()).hexdigest(),
                floor=str(floor),points=[list(map(str,p)) for p in pts],records=records,
                capture_sum_lower=str(lower),mass=str(model[4]),gap=str(lower-model[4]),
                general_packing_exclusion=lower>model[4],seconds=time.monotonic()-start)
    (out/'replay.json').write_text(json.dumps(result,indent=2))
    print({k:v for k,v in result.items() if k not in ('points','records')},flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser()
    for key in ('candidate','cover','out'):p.add_argument(key,type=Path)
    a=p.parse_args();run(a.candidate,a.cover,a.out)
