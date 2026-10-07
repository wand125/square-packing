"""All saved rows, dual-guided radial search, and matched-center controls.

Experimental numerical optimization. Never emits CERTIFIED. Geometry checking
is independent of LP feasibility; numerical pricing is not a no-column proof.
"""
import os
for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMBA_NUM_THREADS'):os.environ[k]='1'
import argparse,json,math,time,hashlib,sys
from pathlib import Path
from fractions import Fraction as F
import numpy as np
from scipy import sparse
from scipy.optimize import differential_evolution
from unified_measure import primitive_key
from unified_geometry import matrix,expand_primitives
from unified_grid_search import solve_matrix
from radial_measure import variable_matrix

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--config',required=True);args=ap.parse_args()
    config_path=Path(args.config).resolve();cfg=json.loads(config_path.read_text())
    root=Path(cfg['root']);out=root/cfg['out'];out.mkdir(parents=True,exist_ok=True)
    progress=[];started=time.perf_counter()
    def write(name,data):(out/name).write_text(json.dumps(data,indent=2)+'\n')
    def log(**kw):
        kw['elapsed']=time.perf_counter()-started;progress.append(kw);write('progress.json',dict(records=progress));print(kw,flush=True)
    try:
        source=root/cfg['parent'];z=np.load(source);L=float(F(cfg['L']));B=float(z['B']);rhs=float(z['rhs'])
        assert L==float(z['L'])
        write('manifest.json',dict(config=cfg,parent_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
            source_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in Path(__file__).parent.glob('*radial*.py')}))
        unified=cfg.get('parent_format')=='unified'
        if unified:
            poses=z['poses'];rects=json.loads(str(z['primitives_json']))
        else:
            p=z['poses'];theta=p[:,2]*np.pi/4;e=(L-B*(np.cos(theta)+np.sin(theta)))/2
            poses=np.column_stack((L/2+p[:,0]*e,L/2+p[:,1]*e,np.tan(theta/2)))
            rects=[dict(kind='rectangle',geometry=list(map(str,r))) for r in z['rectangles']]
        pilot=json.loads((root/cfg['pilot']).read_text());centers=pilot['centers'];controls=[]
        keys={primitive_key(p['kind'],p['geometry'],F(str(L))) for p in rects}
        def add(kind,g,output):
            # Matched controls fit inside the container; radial supports may
            # extend outside, in which case their full-plane cost is retained.
            if not all(0<=x<=L for x in g):return
            key=primitive_key(kind,list(map(str,g)),F(str(L)))
            if key not in keys:keys.add(key);output.append(dict(kind=kind,geometry=list(map(str,g))))
        for x,y in ([] if unified else centers):
            for R in (.03,.15,.35):
                for kind,g in [('point',(x,y)),('segment',(x-R,y,x+R,y)),('rectangle',(x-R,y-R,x+R,y+R))]:add(kind,g,controls)
        primitives=rects+controls
        def build(prims):
            atoms=expand_primitives(prims,F(str(L)));parts=[]
            for i in range(0,len(poses),128):
                block=matrix(poses[i:i+128],B,atoms);block[abs(block)<=1e-12]=0;parts.append(sparse.csr_matrix(block))
            return sparse.vstack(parts,format='csr')
        def solve(A,dual,label,it):
            sol,report=solve_matrix(A,poses,rhs,dual)
            log(operation='lp',iteration=it,label=label,mass=sol.mass,rows=A.shape[0],columns=A.shape[1],
                seconds=sol.seconds,minimum=sol.min_coverage,dual_violation=sol.dual_violation,gap=sol.duality_gap,
                working_rows=report['working_rows'],rounds=report['rounds'])
            return sol
        A=build(primitives)
        log(operation='matrix',rows=A.shape[0],columns=A.shape[1],nnz=A.nnz,csr_bytes=A.data.nbytes+A.indices.nbytes+A.indptr.nbytes)
        sol=solve(A,np.where(z['dual']>1e-8,z['dual'],0.),'point_line_rectangle_baseline',0)
        baseline=sol;np.savez_compressed(out/'baseline.npz',weights=sol.weights,dual=sol.dual,poses=poses)
        positive=np.flatnonzero(sol.dual>1e-12);ps=poses[positive];ds=sol.dual[positive]
        discarded=float(sol.dual.sum()-ds.sum());nodes,weights=np.polynomial.legendre.leggauss(32)
        # Warm compile separately. No parallel optimizers or BLAS threads.
        variable_matrix(ps[:1],B,np.array([[0.,1.,1.,.1,0.]]),L,nodes,weights)
        archive=[];searches=[]
        for kind in (0,1,2):
            for seed in cfg.get('seeds',[20260927,20260928]):
                calls=[0];best=[-1.];start=time.perf_counter()
                def unpack(v):
                    y=L/2*v[0];x=y*v[1];R=math.exp(v[2]);q=v[3] if kind==2 else 0.
                    return [float(kind),x,y,R,q]
                def objective(v):
                    k=unpack(v);value=float(variable_matrix(ps,B,np.array([k]),L,nodes,weights)[:,0]@ds)
                    calls[0]+=1;best[0]=max(best[0],value)
                    if value>1+cfg['pricing_margin']:archive.append((value,k))
                    return -value
                def callback(x,convergence):
                    if calls[0]%320<40:log(operation='pricing_progress',kind=kind,seed=seed,evaluations=calls[0],best=best[0])
                r0,r1=cfg.get('radius_bounds',[.003,.9])
                bounds=[(.005,1.),(.005,1.),(math.log(r0),math.log(r1))]
                if kind==2:bounds.append(tuple(cfg.get('annulus_ratio_bounds',[0.,.98])))
                result=differential_evolution(objective,bounds,popsize=8,maxiter=cfg['pricing_iterations'],
                    seed=seed,polish=False,workers=1,tol=1e-7,atol=1e-8,callback=callback)
                # Retain even an unsuccessful/no-improvement best as evidence.
                searches.append(dict(kind=kind,seed=seed,score=-float(result.fun),kernel=unpack(result.x),evaluations=calls[0],seconds=time.perf_counter()-start))
                log(operation='pricing',**searches[-1])
        candidates=[]
        for value,k in sorted(archive,reverse=True):
            if any(k[0]==a[0] and np.linalg.norm(np.array(k[1:3])-a[1:3])<.025 and abs(math.log(k[3]/a[3]))<.3 and abs(k[4]-a[4])<.1 for a in candidates):continue
            candidates.append(k)
            if len(candidates)>=cfg['max_candidates']:break
        write('pricing.json',dict(searches=searches,positive_dual_rows=len(positive),discarded_dual_mass=discarded,
            selected=candidates,pricing_margin=cfg['pricing_margin'],no_global_optimality_claim=True))
        if not candidates:log(operation='finish',status='SAVED_NO_PRICED_CANDIDATES',certified=False);return
        kernels=np.array(candidates);q64=np.polynomial.legendre.leggauss(64);q128=np.polynomial.legendre.leggauss(128)
        C64=variable_matrix(poses,B,kernels,L,*q64);C128=variable_matrix(poses,B,kernels,L,*q128)
        delta=float(abs(C64-C128).max());refined=C128.T@baseline.dual
        log(operation='refinement',columns=len(kernels),max_coefficient_change=delta,minimum_priced_score=float(refined.min()),maximum_priced_score=float(refined.max()))
        # Reject candidates whose apparent improvement disappears on refinement.
        keep=np.flatnonzero(refined>1+cfg['pricing_margin']);kernels=kernels[keep];C=C128[:,keep]
        if not len(kernels):log(operation='finish',status='SAVED_QUADRATURE_REVIEW',certified=False);return
        matched=[]
        for _,x,y,R,q in kernels:
            add('point',(x,y),matched)
            for h in (R/5,R):
                add('rectangle',(x-h,y-h,x+h,y+h),matched)
                add('segment',(x-h,y,x+h,y),matched)
                h/=math.sqrt(2)
                add('segment',(x-h,y-h,x+h,y+h),matched)
                add('segment',(x-h,y+h,x+h,y-h),matched)
        M=build(matched);rad=sparse.csr_matrix(C)
        radialA=sparse.hstack((A,rad),format='csr');matchedA=sparse.hstack((A,M),format='csr');joint=sparse.hstack((matchedA,rad),format='csr')
        radial=solve(radialA,baseline.dual,'plus_priced_radial',1)
        control=solve(matchedA,baseline.dual,'plus_matched_centers',2)
        both=solve(joint,control.dual,'matched_and_radial',3)
        write('comparison.json',dict(certified=False,rows=len(poses),baseline_mass=baseline.mass,radial_mass=radial.mass,
            matched_mass=control.mass,joint_mass=both.mass,radial_support_mass=float(radial.weights[-len(kernels):].sum()),
            joint_radial_support_mass=float(both.weights[-len(kernels):].sum()),radial_columns=len(kernels),matched_columns=len(matched),
            max_coefficient_change=delta,warning='All saved rows checked numerically; no continuous placement coverage proof. Matched controls share centers but not column counts. Pricing is heuristic.'))
        np.savez_compressed(out/'resume-state.npz',poses=poses,L=L,B=B,rhs=rhs,kernels=kernels,
            primitives_json=json.dumps(primitives+matched),weights=both.weights,dual=both.dual,
            baseline_weights=baseline.weights,radial_weights=radial.weights,control_weights=control.weights)
        sparse.save_npz(out/'finite-matrix.npz',joint)
        write('manifest.json',dict(config=cfg,parent_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
            source_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in Path(__file__).parent.glob('*radial*.py')}))
        log(operation='finish',status='SAVED_PRICING_REVIEW',certified=False)
    except Exception as exc:
        log(operation='error',status='ERROR',error=repr(exc));raise

if __name__=='__main__':main()
