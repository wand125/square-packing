"""Retain a complete rectangle checkpoint and add existing D4 point supports."""
import argparse,json
from pathlib import Path
from fractions import Fraction as F
import numpy as np
from expanded_search_pilot import Geometry,columns,capture,solve
from mixed_density_refit import export


def prepare(state,rules_file,out,n,budget):
    out.mkdir(parents=True,exist_ok=False)
    with np.load(state) as z:
        rects=z['rectangles'].copy();poses=z['poses'].copy();dual=z['dual'].copy()
        L=float(z['L']);B=float(z['B']);rhs=float(z['rhs'])
    rules=json.loads(rules_file.read_text())['rules'];r=len(rects)
    meta=dict(n=n,L=L,B=B,rhs=rhs,rectangles=rects.tolist(),rules=rules,base_pose_count=len(poses),budget=str(budget),source_state=str(state.resolve()))
    for rule in rules:rule['sites']=[tuple(map(F,p)) for p in rule['sites']]
    def block(ps):
        pc,_,mapping=columns(ps,rules,L,B)
        return np.hstack([Geometry(L,B,rects).matrix(ps),pc]),mapping
    ids=np.flatnonzero(dual>1e-9).tolist()
    if not ids:ids=list(range(min(512,len(poses))))
    a,mapping=block(poses[ids]);p=a.shape[1]-r;meta['point_columns']=p
    # JSON retains rational strings, not Python Fraction objects.
    meta['rules']=[dict(rule,sites=[list(map(str,q)) for q in rule['sites']]) for rule in rules]
    (out/'model.json').write_text(json.dumps(meta,indent=2))
    def audit(w):
        ri=np.flatnonzero(w[:r]>0);pi=np.flatnonzero(w[r:]>0)
        unique=sorted({i for j in pi for i in mapping['point_orbits'][j]});idx={i:k for k,i in enumerate(unique)};vals=[]
        for lo in range(0,len(poses),1024):
            q=poses[lo:lo+1024];v=Geometry(L,B,rects[ri]).matrix(q)@w[ri]
            if unique:
                hit=capture(q,L,B,np.array([mapping['points'][i] for i in unique],float))
                for j in pi:v+=w[r+j]*hit[:,[idx[i] for i in mapping['point_orbits'][j]]].mean(axis=1)
            vals.extend(v)
        return np.array(vals)
    records=[]
    for iteration in range(30):
        bad=set();weights={};coverage={}
        for name,end in [('rectangles',r),('mixed',r+p)]:
            fit,stat=solve(a[:,:end],rhs);w=np.zeros(r+p);w[:end]=fit.x
            v=audit(w);bad.update(np.flatnonzero(v<rhs-1e-8).tolist())
            stat.update(iteration=iteration,model=name,rows=len(a),all_min=float(v.min()),violations=int(sum(v<rhs-1e-8)),point_mass=float(sum(w[r:])))
            records.append(stat);weights[name]=w;coverage[name]=v;print(json.dumps(stat),flush=True)
        if not bad:break
        missing=sorted(bad-set(ids))
        if not missing:raise RuntimeError('Numerical disagreement on existing rows')
        more,_=block(poses[missing]);a=np.vstack([a,more]);ids+=missing
    if bad:raise RuntimeError('Full saved-pose audit did not finish')
    w=weights['mixed'];mass=sum(map(lambda x:F(str(x)),w),F(0))
    np.savez_compressed(out/'replay.npz',matrix=a,row_ids=ids,selected_rectangles=np.empty((0,4)),poses=poses,weights_added_density=w,coverage_added_density=coverage['mixed'],weights_rectangles=weights['rectangles'])
    (out/'cumulative-witnesses.json').write_text('[]')
    result=dict(status='BUDGET_EXHAUSTED' if mass>budget else 'FINITE_REPAIRED_NOT_CERTIFIED',n=n,mass=str(mass),total_poses=len(poses),support_columns=len(w),records=records)
    if mass<=budget:
        candidate=export(out/'mixed-candidate.json',meta,rects,w,mapping)
        result['point_mass']=str(sum((F(p['mass']) for p in candidate['points']),F(0)))
    (out/'results.json').write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items() if k!='records'}),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--state',type=Path,required=True);p.add_argument('--rules',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--n',type=int,required=True);p.add_argument('--budget',type=F,required=True);a=p.parse_args();prepare(a.state,a.rules,a.out,a.n,a.budget)
