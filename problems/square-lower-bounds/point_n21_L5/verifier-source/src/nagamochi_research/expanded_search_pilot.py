"""Read-only saved-state n12/n21 pilot: rectangles, added points, OR charges.
Finite numerical LP comparison; exact combinatorial budgets, NOT a certificate.
"""
import os
for key in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMBA_NUM_THREADS'):
    os.environ[key]='1'
from pathlib import Path
import sys,json,hashlib,argparse
from fractions import Fraction as F
from itertools import combinations
from time import perf_counter
import numpy as np
from scipy.optimize import linprog

REPO=Path(__file__).resolve().parents[2]
CODE=REPO/'runs/working_lp_n17_n21_20260926/inputs/21/code'
sys.path.insert(0,str(CODE))
from geometry import Geometry
from points import capture
ROOT=REPO/'runs/expanded_n12_n21_20260926'

def load(n):
    if n==21:
        p=REPO/'runs/working_lp_n17_n21_20260926/inputs/21/repair-27-state.npz'
        d=np.load(p);return p,d['rectangles'],d['poses'],float(d['L']),float(d['B']),float(d['rhs']),d['dual']
    p=REPO/'runs/n12_certificate396_20260926/source/n12_rich_L396_c/resume-state.npz'
    d=np.load(p);meta=json.loads((p.parent/'candidate-46.json').read_text())
    assert np.array_equal(d['rectangles'],np.array(meta['rectangles']))
    return p,d['rectangles'],d['poses'],meta['L'],meta['B'],meta['rhs'],np.zeros(len(d['poses']))

def solve(a,rhs):
    start=perf_counter()
    limit=float(os.environ.get('MIXED_LP_TIME_LIMIT','45'));assert limit>0
    lp=linprog(np.ones(a.shape[1]),A_ub=-a,b_ub=-np.full(len(a),rhs),bounds=(0,None),method='highs',options={'time_limit':limit,'primal_feasibility_tolerance':1e-9,'dual_feasibility_tolerance':1e-9})
    if not lp.success:raise RuntimeError(lp.message)
    dual=-lp.ineqlin.marginals
    checks=dict(minimum=float(np.min(a@lp.x)),dual_violation=float(np.max(a.T@dual-1)),gap=float(lp.fun-rhs*sum(dual)))
    assert checks['minimum']>=rhs-1e-8 and checks['dual_violation']<=1e-8 and abs(checks['gap'])<1e-6
    return lp,dict(mass=float(lp.fun),seconds=perf_counter()-start,**checks)

def candidates(poses,dual,L,B):
    atoms=json.loads((REPO/'runs/bridge_lp_20260926/results.json').read_text())['atoms'][:3]
    centers=[]
    for i in np.argsort(-dual):
        theta=poses[i,2]*np.pi/4;r=(L-B*(np.cos(theta)+np.sin(theta)))/2
        center=np.round(L/2+poses[i,:2]*r,6)
        if all(np.linalg.norm(center-c)>.22 for c in centers):centers.append(center)
        if len(centers)==4:break
    rules=[];lf=F(str(L))
    for atom in atoms:
        raw=[tuple(map(F,p)) for p in atom['sites']];bags=atom['winning_subsets']
        assert all(set(a)&set(b) for a,b in combinations(bags,2))
        cx=sum(p[0] for p in raw)/6;cy=sum(p[1] for p in raw)/6
        for center in centers:
            for scale in (F(3,4),F(1),F(5,4)):
                pts=[(F(str(center[0]))+scale*(x-cx),F(str(center[1]))+scale*(y-cy)) for x,y in raw]
                if any(not(0<=x<=lf and 0<=y<=lf) for x,y in pts):continue
                rules.append(dict(sites=pts,bags=bags,cost=1))
    return rules

def columns(poses,rules,L,B):
    points=[];index={};mapped=[]
    lf=F(str(L))
    def trans(p,g):
        x,y=p
        if g>=4:x,y=y,x
        return (lf-x if g%4&1 else x,lf-y if g%4&2 else y)
    point_orbits=[];oi={}
    def addpoint(p):
        if p not in index:index[p]=len(points);points.append(p)
        return index[p]
    for rule in rules:
        images=[[addpoint(trans(p,g)) for p in rule['sites']] for g in range(8)]
        mapped.append(images)
        for j in range(6):
            orbit=tuple(images[g][j] for g in range(8))
            key=tuple(sorted(orbit))
            if key not in oi:oi[key]=len(point_orbits);point_orbits.append(orbit)
    hits=capture(poses,L,B,np.array(points,float)).astype(bool)
    pc=np.array([hits[:,list(o)].mean(axis=1) for o in point_orbits]).T
    rc=np.array([np.mean([np.logical_or.reduce([np.all(hits[:,[image[j] for j in bag]],axis=1) for bag in rule['bags']]) for image in images],axis=0) for rule,images in zip(rules,mapped)]).T
    return pc,rc,dict(points=points,point_orbits=point_orbits,rule_images=mapped)

def run(n):
    start=perf_counter();out=ROOT/f'n{n}';out.mkdir(parents=True,exist_ok=True)
    assert not list(out.iterdir()), 'Use a fresh output directory'
    path,rects,allposes,L,B,rhs,prior=load(n);rng=np.random.default_rng(926000+n)
    # Preserve all supports; sample rows for a bounded pilot, never a production solve.
    top=np.flatnonzero(prior>1e-9);top=top[np.argsort(-prior[top])][:512]
    remaining=np.setdiff1d(np.arange(len(allposes)),top)
    train=np.r_[top,rng.choice(remaining,1024-len(top),replace=False)]
    held=rng.choice(np.setdiff1d(np.arange(len(allposes)),train),512,replace=False)
    ids=np.r_[train,held];ps=allposes[ids]
    t=perf_counter();rect=Geometry(L,B,rects).matrix(ps);matrix_seconds=perf_counter()-t
    base,bstat=solve(rect[:len(train)],rhs)
    rules=candidates(ps[:len(train)],-base.ineqlin.marginals,L,B)
    pc,rc,mapping=columns(ps,rules,L,B);a=np.hstack([rect,pc,rc]);r=len(rects);p=pc.shape[1]
    models={'rectangles':r,'plus_points':r+p,'plus_rules':a.shape[1]};records={};weights={}
    for name,end in models.items():
        fit,stat=(base,bstat) if name=='rectangles' else solve(a[:len(train),:end],rhs)
        validation=a[len(train):,:end]@fit.x
        stat.update(holdout_minimum=float(min(validation)),holdout_deficit_sum=float(np.maximum(rhs-validation,0).sum()))
        refit,rs=solve(a[:,:end],rhs)
        rs['new_point_mass']=float(sum(refit.x[r:min(end,r+p)]));rs['new_rule_mass']=float(sum(refit.x[r+p:]))
        stat['refit']=rs;records[name]=stat;weights['weights_'+name]=refit.x
        print(json.dumps(dict(n=n,model=name,**stat)),flush=True)
    np.savez_compressed(out/'replay.npz',matrix=a,rhs=rhs,row_ids=ids,poses=ps,rectangles=rects,**weights)
    # Audit all saved rows using only active columns. This is still finite.
    full_checks={}
    for name in ('rectangles','plus_points'):
        w=weights['weights_'+name];active=np.flatnonzero(w[:r]>0)
        values=[]
        for lo in range(0,len(allposes),1024):
            batch=allposes[lo:lo+1024]
            value=Geometry(L,B,rects[active]).matrix(batch)@w[active]
            if name=='plus_points':
                activep=np.flatnonzero(w[r:]>0)
                unique=sorted({i for j in activep for i in mapping['point_orbits'][j]})
                lookup={i:j for j,i in enumerate(unique)}
                hits=capture(batch,L,B,np.array([mapping['points'][i] for i in unique],float))
                for j in activep:
                    value+=w[r+j]*hits[:,[lookup[i] for i in mapping['point_orbits'][j]]].mean(axis=1)
            values.extend(value)
        values=np.array(values);bad=np.maximum(rhs-values,0)
        full_checks[name]=dict(minimum=float(values.min()),deficit_sum=float(bad.sum()),violations_1e7=int(sum(bad>1e-7)),worst_rows=np.argsort(values)[:128].tolist())
        np.save(out/('saved_coverage_'+name+'.npy'),values)
        print(json.dumps(dict(n=n,full_saved_audit=name,**{k:v for k,v in full_checks[name].items() if k!='worst_rows'})),flush=True)
    result=dict(full_saved_audit=full_checks,n=n,L=L,B=B,rhs=rhs,input=str(path.relative_to(REPO)),input_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),total_saved_rows=len(allposes),training_rows=len(train),holdout_rows=len(held),rectangle_columns=r,point_columns=p,rule_columns=len(rules),rules=rules,mapping=mapping,models=records,matrix_seconds=matrix_seconds,seconds=perf_counter()-start,
                scope='Sampled saved rows, all saved rectangle supports. Numerical geometry/LP only. OR rule budget is exact: pairwise intersecting winning bags; D4 average cost1. No full-domain certificate; original production state unmodified.')
    (out/'results.json').write_text(json.dumps(result,default=str,indent=2))
    print(json.dumps(dict(n=n,seconds=result['seconds'],columns=[r,p,len(rules)],status='FINITE_COMPARISON_COMPLETE')),flush=True)
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--n',type=int,choices=[12,21],required=True);run(ap.parse_args().n)
