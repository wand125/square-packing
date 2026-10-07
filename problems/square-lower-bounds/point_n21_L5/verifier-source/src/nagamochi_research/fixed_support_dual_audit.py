"""Rational dual lower bound for a FIXED D4 rectangle/point basis."""
import argparse,json,math,hashlib
from pathlib import Path
from fractions import Fraction as F
from repair_lemma_measure import np,expand,expand_primitives
from scipy.optimize import linprog
from scipy.sparse import csr_matrix
from unified_measure import orbit
from mixed_density_check import polygon_score
from score import square,contains


def ordered_primitives(data):
    if 'primitives' in data:return data['primitives']
    return [dict(kind='rectangle',geometry=r['rectangle']) for r in data['rectangles']]+[dict(kind='point',geometry=r['point']) for r in data['points']]


def exact_columns(data,pose,B):
    L=F(data['L']);poly=square(pose[0],pose[1],B,pose[2]);values=[]
    for primitive in ordered_primitives(data):
        g=tuple(map(F,primitive['geometry']));kind=primitive['kind']
        if kind=='rectangle':
            if len(g)!=4 or not(0<=g[0]<g[2]<=L and 0<=g[1]<g[3]<=L):raise ValueError('Invalid rectangle')
            rects=[]
            for x0,y0,x1,y1 in orbit(kind,g,L):rects.append((x0,y0,x1,y1,F(1,8)/((x1-x0)*(y1-y0))))
            v,_=polygon_score(poly,rects,[]);values.append(v)
        elif kind=='point':
            if len(g)!=2 or not all(0<=x<=L for x in g):raise ValueError('Invalid point')
            values.append(F(sum(contains(poly,p) for p in orbit(kind,g,L)),8))
        else:raise ValueError('Unsupported basis')
    return values


def run(base,experiment,out,core_only=False,working=False):
    d=json.loads(base.read_text());z=np.load(experiment/'state.npz');A=z['matrix']
    if A.shape[1]!=len(ordered_primitives(d)):raise ValueError('Basis count mismatch')
    if working:
        from working_measure_lp import solve
        _,report=solve(A,z['weights']);ids=np.array(report['dual_rows']);raw_weights=report['dual_weights'];objective=report['mass']
    else:
        fit=linprog(np.ones(A.shape[1]),A_ub=-csr_matrix(A),b_ub=-np.ones(len(A)),bounds=(0,None),method='highs',options={'time_limit':45})
        if not fit.success:raise RuntimeError(fit.message)
        dual=-fit.ineqlin.marginals;ids=np.flatnonzero(dual>1e-9);raw_weights=[dual[i] for i in ids];objective=fit.fun
    weights=[F(math.floor(float(w)*10**9),10**9) for w in raw_weights]
    train=json.loads((experiment/'poses.json').read_text())['train'];poses=[tuple(map(F,train[int(i)])) for i in ids]
    L=F(d['L']);assert len(train)==len(A)
    print('DUAL',objective,'poses',len(ids),'columns',A.shape[1],flush=True)
    results=[]
    for B in ([F(999999,1000000)] if core_only else [F(999999,1000000),F(1)]):
        loads=[F(0)]*A.shape[1]
        for k,(pose,w) in enumerate(zip(poses,weights)):
            assert all(0<=x<=L and 0<=y<=L for x,y in square(pose[0],pose[1],F(1),pose[2]))
            coefficients=exact_columns(d,pose,B)
            loads=[a+w*b for a,b in zip(loads,coefficients)]
            if (k+1)%25==0:print('EXACT',str(B),k+1,flush=True)
        scale=max([F(1)]+loads);lower=sum(weights)/scale
        results.append(dict(B=str(B),scale=str(scale),mass_lower_bound=str(lower),column_loads=list(map(str,loads)),exceeds_twelve=lower>12))
        print('BOUND',str(B),float(lower),flush=True)
    cert=dict(status='EXACT_FIXED_SUPPORT_DUAL_BOUND',source_sha256=hashlib.sha256(base.read_bytes()).hexdigest(),poses=[list(map(str,p)) for p in poses],
              unscaled_weights=list(map(str,weights)),records=results,general_packing_exclusion=False,
              scope='Only the listed fixed D4 basis; no bound on arbitrary new supports or nonadditive methods.')
    out.write_text(json.dumps(cert,indent=2))

def replay(base,certificate):
    d=json.loads(base.read_text());q=json.loads(certificate.read_text())
    if q['source_sha256']!=hashlib.sha256(base.read_bytes()).hexdigest():raise ValueError('Source changed')
    ps=[tuple(map(F,p)) for p in q['poses']];ws=list(map(F,q['unscaled_weights']));L=F(d['L'])
    if len(ps)!=len(ws) or not ws or min(ws)<0:raise ValueError('Invalid dual')
    for p in ps:
        if not all(0<=x<=L and 0<=y<=L for x,y in square(p[0],p[1],F(1),p[2])):raise ValueError('Nonphysical witness')
    records=[]
    for rec in q['records']:
        B=F(rec['B']);assert 0<B<=1
        loads=[F(0)]*len(ordered_primitives(d))
        for p,w in zip(ps,ws):loads=[a+w*b for a,b in zip(loads,exact_columns(d,p,B))]
        assert loads==list(map(F,rec['column_loads']))
        scale=F(rec['scale']);assert scale>=1 and all(x<=scale for x in loads)
        lower=sum(ws)/scale;assert lower==F(rec['mass_lower_bound'])
        assert rec['exceeds_twelve']==(lower>12)
        records.append(dict(B=str(B),mass_lower_bound=str(lower),columns=len(loads),exceeds_twelve=lower>12))
    return dict(status='EXACT_FIXED_SUPPORT_DUAL_REPLAYED',records=records,poses=len(ps),general_packing_exclusion=False)


if __name__=='__main__':
    p=argparse.ArgumentParser()
    for k in ('base','experiment','out'):p.add_argument(k,type=Path)
    p.add_argument('--replay',action='store_true');p.add_argument('--core-only',action='store_true');p.add_argument('--working',action='store_true');a=p.parse_args()
    if a.replay:
        result=replay(a.base,a.experiment);a.out.write_text(json.dumps(result,indent=2));print(result,flush=True)
    else:run(a.base,a.experiment,a.out,a.core_only,a.working)
