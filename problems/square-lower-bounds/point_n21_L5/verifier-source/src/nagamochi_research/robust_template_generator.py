"""Offline mixed-measure template training with retained adversarial scenarios.

Fixed total mass, adjustable angular core, active-column screening, dual-guided
support refinement, and separate fresh random/event audits. Never a proof.
"""
import os
for name in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMBA_NUM_THREADS'):os.environ[name]='1'
import argparse,json,hashlib,time,sys,math
from pathlib import Path
from fractions import Fraction as F
import numpy as np
from scipy import sparse
from scipy.optimize import linprog
from unified_measure import primitive_key,net_check


def solve_lp(*args,**kwargs):
    """Retry an indeterminate solver status without presolve, keep all rows."""
    r=linprog(*args,**kwargs)
    if r.status==4:
        retry=dict(kwargs);retry['method']='highs-ds'
        retry['options']=dict(kwargs.get('options',{}),presolve=False)
        r=linprog(*args,**retry)
    return r


def maximin(A,target,uniform_fraction,reference=None):
    """Solve a subset, then separate against ALL retained finite rows."""
    A=sparse.csr_matrix(A);m,n=A.shape
    if not 0<target or not 0<=uniform_fraction<=1 or not m:raise ValueError('invalid budget')
    initial=np.asarray(A@reference).ravel() if reference is not None else np.asarray(A[:,0].toarray()).ravel()
    active=set(map(int,np.argsort(initial)[:256]));active.update(map(int,np.linspace(0,m-1,min(m,256))))
    for separation_round in range(100):
        ids=np.array(sorted(active));sub=A[ids]
        r=solve_lp(np.r_[np.zeros(n),-1.],A_ub=sparse.hstack([-sub,np.ones((len(ids),1))],format='csr'),b_ub=np.zeros(len(ids)),
            A_eq=sparse.csr_matrix(np.r_[np.ones(n),0.].reshape(1,-1)),b_eq=[target],
            bounds=[(target*uniform_fraction,None)]+[(0,None)]*n,method='highs',
            options=dict(primal_feasibility_tolerance=1e-8,dual_feasibility_tolerance=1e-8))
        if not r.success:raise RuntimeError(r.message)
        w=np.maximum(r.x[:-1],0.);values=A@w;minimum=float(values.min())
        if abs(w.sum()-target)>1e-7 or w[0]<target*uniform_fraction-1e-7:raise RuntimeError('LP residual')
        bad=np.flatnonzero(values<r.x[-1]-2e-7)
        if not len(bad):
            dual=np.zeros(m);scale=-float(r.eqlin.marginals[0])
            if scale>1e-12:dual[ids]=-np.asarray(r.ineqlin.marginals)/scale
            return w,minimum,dual
        add=[int(i) for i in bad[np.argsort(values[bad])] if int(i) not in active][:256]
        if not add:raise RuntimeError('retained-row separation stalled')
        active.update(add)
    raise RuntimeError('retained-row separation budget')


def minimum_change(A,target,reference,uniform_fraction,goal):
    """Keep the current template unless coverage cuts force weight changes."""
    A=sparse.csr_matrix(A);m,n=A.shape;ref=np.asarray(reference,float)
    values=A@ref
    if values.min()>=goal-1e-8:return ref.copy(),float(values.min())
    active=set(map(int,np.argsort(values)[:256]));active.update(map(int,np.linspace(0,m-1,min(m,256))))
    I=sparse.eye(n,format='csr');distance=sparse.vstack([sparse.hstack([I,-I]),sparse.hstack([-I,-I])],format='csr')
    for _ in range(100):
        ids=np.array(sorted(active));C=sparse.vstack([sparse.hstack([-A[ids],sparse.csr_matrix((len(ids),n))]),distance],format='csr')
        r=solve_lp(np.r_[np.zeros(n),np.ones(n)],A_ub=C,b_ub=np.r_[np.full(len(ids),-goal),ref,-ref],
            A_eq=sparse.csr_matrix(np.r_[np.ones(n),np.zeros(n)].reshape(1,-1)),b_eq=[target],
            bounds=[(target*uniform_fraction,None)]+[(0,None)]*(2*n-1),method='highs',
            options=dict(primal_feasibility_tolerance=1e-8,dual_feasibility_tolerance=1e-8))
        if not r.success:
            if r.status==2:raise ValueError('coverage goal infeasible')
            raise RuntimeError(r.message)
        w=np.maximum(r.x[:n],0.);values=A@w
        if abs(w.sum()-target)>1e-7 or w[0]<target*uniform_fraction-1e-7:raise RuntimeError('repair residual')
        bad=np.flatnonzero(values<goal-2e-7)
        if not len(bad):return w,float(values.min())
        add=[int(i) for i in bad[np.argsort(values[bad])] if int(i) not in active][:256]
        if not add:raise RuntimeError('repair separation stalled')
        active.update(add)
    raise RuntimeError('repair separation limit')


def remap_poses(q,L,B0,B1):
    q=np.array(q,float,copy=True);t=q[:,2];extent=(1-t*t+2*t)/(1+t*t)
    old=(L-B0*extent)/2;new=(L-B1*extent)/2
    if np.any(old<=0) or np.any(new<=0):raise ValueError('empty pose domain')
    q[:,:2]=L/2+(q[:,:2]-L/2)*(new/old)[:,None]
    return q


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--config',type=Path,required=True);a=ap.parse_args()
    cfg=json.loads(a.config.read_text());base=a.config.resolve().parent
    for key in ('code_dir','research_dir'):sys.path.insert(0,str((base/cfg[key]).resolve()))
    from unified_geometry import expand_primitives,matrix
    from mixed_grid_pricing import screening_poses,refine_witnesses,quality_metrics,propose_mixed_grid
    from event_screening import event_poses
    from template_search import candidate_from_state
    L=F(cfg['L']);B=F(cfg['B']);net=cfg['net'];target=float(cfg['target']);net_check(dict(B=str(B),net=net))
    if not 0<target<cfg['n']:raise ValueError('mass target')
    core=cfg.get('core')
    if core:
        from trimmed_numeric import matrix as trimmed_matrix
        from trimmed_core import parameters
        h,g=parameters(net['step'],core['margin'])
        if B*(1+g)>2*h:raise ValueError('square radial core must fit trimmed core')
        matrix=lambda q,b,e:trimmed_matrix(q,b,e,float(h),float(g))
    out=base/cfg['out'];out.mkdir(parents=True,exist_ok=False);start=time.perf_counter();records=[]
    def write(name,d):
        p=out/name;t=p.with_suffix(p.suffix+'.tmp');t.write_text(json.dumps(d,indent=2)+'\n');t.replace(p)
    def emit(**d):
        d['elapsed']=time.perf_counter()-start;records.append(d);write('progress.json',dict(records=records));print(json.dumps(d),flush=True)
    parent=base/cfg['checkpoint'];z=np.load(parent,allow_pickle=False)
    if float(z['L'])!=float(L):raise ValueError('L mismatch')
    ps=json.loads(str(z['primitives_json']));w=z['weights'].copy();w*=target/w.sum()
    if ps[0]['kind']!='rectangle' or list(map(F,ps[0]['geometry']))!=[0,0,L,L]:raise ValueError('first column must be full-board uniform measure')
    poses=remap_poses(z['poses'],float(L),float(z['B']),float(B))
    poses=np.vstack([poses,screening_poses(L,B,count=8192,seed=cfg['seed'],boundary_fraction=.25)])
    poses=np.unique(np.round(poses,13),axis=0)
    keys={tuple(p) for p in poses};pkeys={primitive_key(p['kind'],p['geometry'],L) for p in ps}
    dependencies=['robust_template_generator.py','event_screening.py','mixed_grid_pricing.py','unified_geometry.py','template_search.py','trimmed_core.py','trimmed_numeric.py','unified_measure.py']
    write('manifest.json',dict(config=cfg,parent_sha256=hashlib.sha256(parent.read_bytes()).hexdigest(),
        source_sha256={name:hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest() for name in dependencies}))
    def build(q,cols):
        expanded=expand_primitives(cols,L)
        return sparse.vstack([sparse.csr_matrix(matrix(q[i:i+128],float(B),expanded)) for i in range(0,len(q),128)],format='csr')
    def scorer():
        ids=np.flatnonzero(w>0);expanded=expand_primitives([ps[i] for i in ids],L);weights=w[ids].copy()
        return lambda q:np.concatenate([matrix(q[i:i+256],float(B),expanded)@weights for i in range(0,len(q),256)])
    def save(name):
        tmp=out/(name+'.tmp.npz')
        np.savez_compressed(tmp,primitives_json=json.dumps(ps),weights=w,poses=poses,dual=np.zeros(len(poses)),L=float(L),B=float(B),rhs=1.001,net_json=json.dumps(net),**(dict(core_json=json.dumps(core)) if core else {}))
        tmp.replace(out/(name+'.npz'))
    # Previously independent stress cases become training here, explicitly.
    score=scorer();catalog_info=[]
    for spec in cfg.get('catalogs',[]):
        path=base/spec['path'];q=np.load(path,allow_pickle=False)['poses']
        if F(spec['B'])!=B:q=remap_poses(q,float(L),float(F(spec['B'])),float(B))
        values=score(q);ids=np.argsort(values);ids=ids[values[ids]<cfg.get('train_margin',1.001)][:cfg.get('catalog_rows',4096)]
        new=[]
        for p in q[ids]:
            key=tuple(np.round(p,13))
            if key not in keys:keys.add(key);new.append(p)
        if new:poses=np.vstack([poses,new])
        catalog_info.append(dict(path=spec['path'],sha256=hashlib.sha256(path.read_bytes()).hexdigest(),screened=len(q),added=len(new),minimum=float(values.min())))
    write('catalogs.json',dict(catalogs=catalog_info));A=build(poses,ps)
    consecutive=0
    for it in range(cfg.get('rounds',12)):
        stable=False
        if cfg.get('stable_repair',False):
            try:
                w,floor=minimum_change(A,target,w,cfg.get('uniform_fraction',.5),cfg.get('train_margin',1.001));dual=np.zeros(len(poses));stable=True
            except ValueError:pass
        if not stable:w,floor,dual=maximin(A,target,cfg.get('uniform_fraction',.5),w)
        if not stable and it and it<=cfg.get('pricing_until',4) and it%cfg.get('pricing_every',2)==0:
            extra,report=propose_mixed_grid(poses,dual,L,B,ps,w,k=10,per_kind=64,max_columns=24,grid_fraction=.25,refinement_per_kind=96,seed=cfg['seed']+100+it)
            extra=[p for p in extra if primitive_key(p['kind'],p['geometry'],L) not in pkeys]
            if extra:
                A=sparse.hstack([A,build(poses,extra)],format='csr');ps+=extra;pkeys.update(primitive_key(p['kind'],p['geometry'],L) for p in extra)
                w,floor,dual=maximin(A,target,cfg.get('uniform_fraction',.5),np.pad(w,(0,len(extra))))
            emit(operation='pricing',iteration=it,added=len(extra),training_minimum=floor)
        save('resume-state');save(f'state-{it:03}')
        score=scorer();q=np.vstack([screening_poses(L,B,count=32768,seed=cfg['seed']+1000+it,boundary_fraction=.25),
            event_poses(ps,w,L,B,per_angle=cfg.get('event_per_angle',16384),seed=cfg['seed']+2000+it)])
        values=score(q);rq,rv=refine_witnesses(q,values,L,B,score,starts=48);q=np.vstack([q,rq]);values=np.r_[values,rv]
        emit(operation='screen',iteration=it,rows=len(poses),columns=len(ps),active=int(np.sum(w>0)),mass=float(w.sum()),
            training_minimum=floor,samples=len(q),minimum=float(values.min()),below_one=int(np.sum(values<1)),globally_verified=False)
        if values.min()>=cfg.get('stop_margin',1.0008):consecutive+=1
        else:consecutive=0
        if consecutive>=3 or it+1==cfg.get('rounds',12):break
        new=[]
        for i in np.argsort(values):
            if values[i]>=cfg.get('train_margin',1.001):break
            key=tuple(np.round(q[i],13))
            if key not in keys:keys.add(key);new.append(q[i])
            if len(new)>=cfg.get('max_new_rows',512):break
        if new:A=sparse.vstack([A,build(np.asarray(new),ps)],format='csr');poses=np.vstack([poses,new])
    save('resume-state');candidate=candidate_from_state(out/'resume-state.npz',cfg['n'],cfg['target']);write('candidate.json',candidate)
    offline_seconds=time.perf_counter()-start;score=scorer();checks={}
    for label,seed in [('random',cfg['seed']+100000),('events',cfg['seed']+200000)]:
        q=screening_poses(L,B,count=262144,seed=seed,boundary_fraction=.25) if label=='random' else event_poses(ps,w,L,B,per_angle=32768,seed=seed)
        values=score(q)
        if label=='events':
            rq,rv=refine_witnesses(q,values,L,B,score,starts=96);q=np.vstack([q,rq]);values=np.r_[values,rv]
        checks[label]=dict(seed=seed,quality=quality_metrics(values,w.sum(),target))
        np.savez_compressed(out/(label+'-audit-bad.npz'),poses=q[values<1.001],values=values[values<1.001])
    passed=all(c['quality']['target_mass']['minimum']>=1.0001 for c in checks.values())
    write('result.json',dict(config=cfg,offline_seconds=offline_seconds,assessment_seconds=time.perf_counter()-start-offline_seconds,checks=checks,
        quality_passed=passed,certified=False,state_sha256=hashlib.sha256((out/'resume-state.npz').read_bytes()).hexdigest()))
    emit(operation='finish',status='SAVED_QUALITY_CHECKED_INITIAL' if passed else 'SAVED_INITIAL_NEEDS_REPAIR',quality_passed=passed,globally_verified=False)

if __name__=='__main__':main()
