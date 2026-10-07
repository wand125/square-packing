"""Constraint exchange with exact local witnesses on every iteration."""
import argparse,json
from pathlib import Path
from fractions import Fraction as F
from scipy.optimize import minimize,linprog
from scipy.sparse import csr_matrix
from repair_lemma_measure import np,coefficients,expand_primitives,poses,export,bounded_weights,expand,evaluate
from local_search_lemma_measure import physical


def separate(model,expanded,w,scan,values,starts=8):
    L=float(model[0]);B=model[1];rows=[]
    def objective(z):return float((coefficients([physical(L,z)],B,expanded,model[0])@w)[0])
    for i in np.argsort(values)[:starts]:
        x,y,t=map(float,scan[int(i)]);a=abs(t);h=(1-a*a+2*a)/(2*(1+a*a));z=[(x-h)/(L-2*h),(y-h)/(L-2*h),t]
        clipped=np.clip(z,[0.,0.,-.414],[1.,1.,.414])
        if np.max(np.abs(clipped-z))>1e-10:raise ValueError('Invalid physical start')
        fit=minimize(objective,clipped,method='Nelder-Mead',bounds=[(0,1),(0,1),(-.414,.414)],options={'maxiter':120,'xatol':1e-8,'fatol':1e-9})
        z=tuple(F(float(v)).limit_denominator(10**9) for v in fit.x);pose=physical(model[0],z)
        a=abs(pose[2]);h=(1-a*a+2*a)/(2*(1+a*a));assert all(h<=x<=model[0]-h for x in pose[:2])
        row=evaluate(model,*pose);row['evaluations']=int(fit.nfev);rows.append(row)
    return rows


def unrestricted_weights(A,reference,method='highs'):
    fit=linprog(np.ones(A.shape[1]),A_ub=-csr_matrix(A),b_ub=-np.ones(len(A)),bounds=(0,None),method=method,options={'time_limit':45})
    if not fit.success:raise RuntimeError(fit.message)
    w=np.maximum(fit.x,0.)
    dual=-fit.ineqlin.marginals
    if not np.all(np.isfinite(w)) or min(A@w)<1-1e-7:raise ValueError('Full primal residual failed')
    if min(dual)<-1e-7 or max(A.T@dual)>1+1e-7:raise ValueError('Full dual residual failed')
    if abs(sum(w)-sum(dual))>1e-5:raise ValueError('Primal dual gap failed')
    w*=sum(reference)/sum(w)
    return w,float(min(A@w))


def run(base,prior,known,out,unbounded=False):
    out.mkdir(parents=True,exist_ok=False);data=json.loads(base.read_text());L=F(data['L']);B=F(999999,1000000)
    primitives=[dict(kind='rectangle',geometry=r['rectangle']) for r in data['rectangles']]+[dict(kind='point',geometry=r['point']) for r in data['points']]
    expanded=expand_primitives(primitives,L);w0=np.array([float(F(r['mass'])) for r in data['rectangles']+data['points']])
    p=json.loads((prior/'poses.json').read_text());train=[tuple(map(F,x)) for x in p['train']+p['held']]
    previous=json.loads((prior/'local-separation.json').read_text())['records']
    if (prior/'unbounded-validation.json').exists():previous+=json.loads((prior/'unbounded-validation.json').read_text())['local_witnesses']
    train += [tuple(F(x[k]) for k in ('cx','cy','t')) for x in previous]
    train=list(dict.fromkeys(train));keys=set(train);A=coefficients(train,B,expanded,L);records=[]
    for iteration in range(4):
        w,minimum=unrestricted_weights(A,w0) if unbounded else bounded_weights(A,w0,0.,5.);candidate=export(data,primitives,w,B);model=expand(candidate)
        scan=poses(L,2048,(9271800 if unbounded else 9271500)+iteration);H=coefficients(scan,B,expanded,L);v=H@w
        local=separate(model,expanded,w,scan,v);new=[]
        if iteration<3:
            options=[tuple(F(x[k]) for k in ('cx','cy','t')) for x in local if F(x['score'])<F(str(minimum))]
            options += [scan[int(i)] for i in np.argsort(v)[:128] if v[i]<minimum-1e-8]
            for pose in options:
                if pose not in keys:keys.add(pose);new.append(pose)
        rec=dict(iteration=iteration,rows=len(train),training_minimum=minimum,scan_seed=(9271800 if unbounded else 9271500)+iteration,
                 scan_minimum=float(min(v)),scan_below_one=int(sum(v<1)),local_minimum=str(min(F(x['score']) for x in local)),local_witnesses=local,added=len(new))
        records.append(rec);(out/'progress.json').write_text(json.dumps(records,indent=2))
        print({k:v for k,v in rec.items() if k!='local_witnesses'},flush=True)
        if new:A=np.vstack([A,coefficients(new,B,expanded,L)]);train.extend(new)
    (out/'candidate.json').write_text(json.dumps(candidate,indent=2));held=poses(L,4096,9271900 if unbounded else 9271600)
    H=coefficients(held,B,expanded,L);v=H@w;old=H@w0;checks=[evaluate(model,*held[int(i)]) for i in np.argsort(v)[:16]]
    knownposes=[tuple(F(x[k]) for k in ('cx','cy','t')) for x in json.loads(known.read_text())['samples']]
    knownscores=[F(evaluate(model,*p)['score']) for p in knownposes]
    result=dict(status='FINITE_LOCAL_EXCHANGE_NOT_CERTIFIED',records=records,final_seed=9271900 if unbounded else 9271600,unbounded=unbounded,held_minimum=float(min(v)),original_held_minimum=float(min(old)),
                held_below_one=int(sum(v<1)),exact_held_checks=checks,exact_known_minimum=str(min(knownscores)),mass=str(model[4]),general_packing_exclusion=False)
    (out/'results.json').write_text(json.dumps(result,indent=2));(out/'poses.json').write_text(json.dumps(dict(train=[list(map(str,p)) for p in train],held=[list(map(str,p)) for p in held]),indent=2))
    (out/'local-separation.json').write_text(json.dumps(dict(records=records[-1]['local_witnesses']),indent=2))
    np.savez_compressed(out/'state.npz',weights=w,reference_weights=w0,matrix=A)
    print({k:v for k,v in result.items() if k not in ('records','exact_held_checks')},flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for k in ('base','prior','known','out'):p.add_argument(k,type=Path)
    p.add_argument('--unbounded',action='store_true');a=p.parse_args();run(a.base,a.prior,a.known,a.out,a.unbounded)
