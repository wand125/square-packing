"""Optional paired mixed branch from a saved rectangle ladder; never auto-promotes proofs."""
import os
for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMBA_NUM_THREADS'):
    os.environ[key]='1'
import argparse,json,time,hashlib,sys,platform,resource,io
from pathlib import Path
from fractions import Fraction as F
from types import SimpleNamespace as NS
from collections import Counter
ROOT=Path(__file__).resolve().parent
import numpy as np
from scipy import sparse
from mixed_aux_policy import choose_branch

def load_backend(code_dir,research_dir):
    sys.path[:0]=[str(ROOT),str(research_dir),str(code_dir)]
    global expand_primitives,matrix,solve_matrix,primitive_key,validate,verify,SCHEMA,RADIAL_SCHEMA
    global propose_mixed_grid,screening_poses,quality_metrics,Geometry,rectangle_key,propose_edges,propose_resize
    from unified_geometry import expand_primitives,matrix
    from unified_grid_search import solve_matrix
    from unified_measure import primitive_key,validate,verify,SCHEMA,RADIAL_SCHEMA
    from mixed_grid_pricing import propose_mixed_grid,screening_poses,quality_metrics
    from geometry import Geometry,rectangle_key
    from edge_pricing import propose_edges
    from additive_resize_pricing import propose as propose_resize

def physical(q,L,B):
    theta=q[:,2]*np.pi/4;t=np.tan(theta/2)
    e=(L-B*(np.cos(theta)+np.sin(theta)))/2
    return np.c_[L/2+q[:,:2]*e[:,None],t]

def normalized(q,L,B):
    t=q[:,2];theta=2*np.arctan(t);e=(L-B*((1-t*t+2*t)/(1+t*t)))/2
    result=np.c_[(q[:,:2]-L/2)/e[:,None],theta/(np.pi/4)]
    if np.any(result<np.array([-1,-1,0])-1e-12) or np.any(result>1+1e-12):
        raise ValueError('physical pose outside legacy domain')
    return np.clip(result,[-1,-1,0],[1,1,1])

def build(q,ps,L,B):
    expanded=expand_primitives(ps,F(str(L)));blocks=[]
    for start in range(0,len(q),128):
        a=matrix(q[start:start+128],B,expanded);a[np.abs(a)<=1e-12]=0
        blocks.append(sparse.csr_matrix(a))
    return sparse.vstack(blocks,format='csr') if blocks else sparse.csr_matrix((0,len(ps)))

def rect_model(ps,q,L,B):
    ids=np.array([i for i,p in enumerate(ps) if p['kind']=='rectangle'],int)
    rs=np.array([[float(F(x)) for x in ps[i]['geometry']] for i in ids])
    return NS(L=L,B=B,poses=normalized(q,L,B),rectangles=rs,rect_cols=ids,
              rect_keys={rectangle_key(r,L) for r in rs},atoms=[])

def rectangle_columns(proposals,family):
    return [dict(kind='rectangle',geometry=list(map(str,p['rectangle'])),family=family) for p in proposals]

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--config',type=Path,required=True)
    args=ap.parse_args();cfg=json.loads(args.config.read_text());base=args.config.resolve().parent
    n=int(cfg['n']);source_L=float(F(str(cfg['source_L'])));target=float(F(str(cfg['target'])))
    levels=[float(F(str(x))) for x in cfg['L_values']]
    if not 0<target<n or not levels or len(set(levels))!=len(levels) or min(levels+[source_L])<=2:
        raise ValueError('invalid geometry/budget')
    for key,default in [('rounds',3),('screen_samples',16384),('holdout_samples',65536),('max_new_rows',256)]:
        if not isinstance(cfg.get(key,default),int) or cfg.get(key,default)<1:raise ValueError('invalid '+key)
    if cfg.get('auxiliary_kind','mixed') not in ('mixed','rectangles'):raise ValueError('invalid auxiliary kind')
    green=cfg.get('green_phases')
    if green is not None:
        if not isinstance(green,dict) or set(green)-{'phase_count','reserved_columns'}:raise ValueError('invalid green phase options')
        if int(cfg.get('k',0))**2+1!=n:raise ValueError('green phases require n=k*k+1')
        if not 1<=green.get('reserved_columns',16)<=24:raise ValueError('invalid green reserved columns')
        if not 1<=green.get('phase_count',12)<=24:raise ValueError('invalid phase count')
    training_seed=int(cfg.get('training_seed',20281100));holdout_seed=int(cfg['holdout_seed'])
    if training_seed<=holdout_seed<training_seed+cfg.get('rounds',3):raise ValueError('holdout seed overlaps training')
    code_dir=(base/cfg['code_dir']).resolve();research_dir=(base/cfg['research_dir']).resolve()
    load_backend(code_dir,research_dir)
    args.out=(base/cfg['out']).resolve()
    args.out.mkdir(parents=True,exist_ok=False);started=time.monotonic();records=[]
    def write(name,d):
        p=args.out/(name+'.tmp');p.write_text(json.dumps(d,indent=2)+'\n');p.replace(args.out/name)
    def emit(d):
        d.update(elapsed=time.monotonic()-started,loadavg=os.getloadavg(),maxrss=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        records.append(d);write('progress.json',dict(records=records));print(json.dumps(d),flush=True)
    source=(base/cfg['checkpoint']).resolve();source_bytes=source.read_bytes()
    z=np.load(io.BytesIO(source_bytes),allow_pickle=False)
    (args.out/'input.npz').write_bytes(source_bytes)
    if 'primitives_json' in z or 'core_json' in z or 'atoms' in z or 'points' in z:
        raise ValueError('requires a legacy rectangle-only checkpoint')
    for key,want in [('L',source_L),('B',.9977),('rhs',1.001)]:
        if key in z and abs(float(z[key])-want)>1e-13:raise ValueError('checkpoint mismatch: '+key)
    if 'net_json' in z and json.loads(str(z['net_json']))!=dict(step='83/40000',last=200):
        raise ValueError('unsupported angle net')
    write('manifest.json',dict(host=platform.node(),source_sha256=hashlib.sha256(source_bytes).hexdigest(),
        config=cfg,threads=1,target=str(cfg['target']),n=n,B='.9977',rhs=1.001,
        source_code_sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for folder in (ROOT,research_dir,code_dir) for p in folder.glob('*.py')},
        auxiliary_kind=cfg.get('auxiliary_kind','mixed'),
        comparison='Shared inherited and union-repair rows; existing edge pricing versus edge+native mixed pricing; equal 32-column cap. Common transfer initialization. Not an end-to-end legacy-runner speed comparison.',
        retained_rows=len(z['poses']),retained_columns=len(z['rectangles']),
        timings='Common initialization charged separately; sequential alternating arm order on one host; other host jobs remain active.'))
    summary=[]
    for level_index,L in enumerate(levels):
        B=.9977
        raw=z['poses']
        poses=physical(raw,L,B);original_rows=len(poses)
        ps=rectangle_columns([dict(rectangle=r*(L/source_L)) for r in z['rectangles']],'retained')
        original_count=len(ps);t=time.monotonic();A=build(poses,ps,L,B)
        # Cross-check physical mixed coefficients against the production rectangle engine.
        ids=np.linspace(0,len(ps)-1,16,dtype=int);qs=np.linspace(0,len(poses)-1,16,dtype=int)
        legacy=Geometry(L,B,np.array([[float(F(x)) for x in ps[i]['geometry']] for i in ids])).matrix(raw[qs])
        discrepancy=float(np.max(np.abs(legacy-A[qs][:,ids].toarray())))
        if discrepancy>2e-9:raise RuntimeError(f'coefficient mismatch {discrepancy}')
        sol,rep=solve_matrix(A,poses,1.001,np.zeros(len(poses)))
        emit(dict(operation='baseline',L=L,mass=sol.mass,seconds=time.monotonic()-t,coefficient_difference=discrepancy,rows=len(poses),columns=len(ps)))
        m=rect_model(ps,poses,L,B);extra,report=propose_resize(m,sol,source_L=source_L)
        extra=rectangle_columns(extra,'resize_common')
        if extra:
            A=sparse.hstack([A,build(poses,extra,L,B)],format='csr');ps+=extra
            sol,rep=solve_matrix(A,poses,1.001,sol.dual)
        emit(dict(operation='common_resize',L=L,mass=sol.mass,columns=len(ps),report=report,common_initialization_seconds=time.monotonic()-t))
        arms={name:dict(ps=list(ps),A=A.copy(),sol=sol,seconds=0.) for name in ('normal','auxiliary')}
        rowkeys={tuple(np.round(q,13)) for q in poses}
        for iteration in range(cfg.get('rounds',3)):
            order=['normal','auxiliary'] if (iteration+level_index)%2==0 else ['auxiliary','normal']
            for name in order:
                arm=arms[name];t=time.monotonic();m=rect_model(arm['ps'],poses,L,B)
                green_arm=name=='auxiliary' and green is not None
                mixed_arm=name=='auxiliary' and cfg.get('auxiliary_kind','mixed')=='mixed' and not green_arm
                edge_cap=32-green.get('reserved_columns',16) if green_arm else (16 if mixed_arm else 32)
                edge_options=cfg.get('edge_options',{}) if name=='normal' else cfg.get('auxiliary_edge_options',cfg.get('edge_options',{}))
                if name=='auxiliary' and cfg.get('multiscale_edges'):
                    from multiscale_edge_pricing import propose_multiscale
                    proposals,pr=propose_multiscale(m,arm['sol'],max_columns=edge_cap,
                        **edge_options,**cfg['multiscale_edges'])
                else:
                    proposals,pr=propose_edges(m,arm['sol'],max_columns=edge_cap,**edge_options)
                extra=rectangle_columns(proposals,'standard_edges');mr=None
                if mixed_arm:
                    mixed,mr=propose_mixed_grid(poses,arm['sol'].dual,F(str(L)),F(str(B)),arm['ps'],arm['sol'].weights,
                        k=cfg.get('k',round(n**.5)),max_columns=32-len(extra),seed=cfg.get('pricing_seed',20280927)+iteration,
                        **dict(dict(per_kind=64,refinement_per_kind=64),**cfg.get('mixed_options',{})))
                    extra+=mixed
                if green_arm:
                    from green_phase_pricing import propose_green
                    green_columns,mr=propose_green(poses,arm['sol'].dual,F(str(L)),F(str(B)),arm['ps'],
                        k=cfg['k'],max_columns=32-len(extra),phase_count=green.get('phase_count',12),
                        kinds=('rectangle',) if cfg.get('auxiliary_kind')=='rectangles' else ('rectangle','point'))
                    extra+=green_columns
                keys={primitive_key(p['kind'],p['geometry'],F(str(L))) for p in arm['ps']};fresh=[]
                for p in extra:
                    key=primitive_key(p['kind'],p['geometry'],F(str(L)))
                    if key not in keys:keys.add(key);fresh.append(p)
                before=arm['sol'].mass
                if fresh:
                    arm['A']=sparse.hstack([arm['A'],build(poses,fresh,L,B)],format='csr');arm['ps']+=fresh
                    arm['sol'],rep=solve_matrix(arm['A'],poses,1.001,arm['sol'].dual)
                if arm['sol'].mass>before+1e-4:raise RuntimeError('added columns increased mass')
                elapsed=time.monotonic()-t;arm['seconds']+=elapsed
                emit(dict(operation='pricing_lp',L=L,arm=name,iteration=iteration,before=before,mass=arm['sol'].mass,
                    seconds=elapsed,added=len(fresh),added_kinds=dict(Counter(p['kind'] for p in fresh)),edge_report=pr,mixed_report=mr,
                    minimum=arm['sol'].min_coverage,dual_violation=arm['sol'].dual_violation,gap=arm['sol'].duality_gap))
            # Both arms receive the identical union of their fresh training counterexamples.
            samples=screening_poses(L,B,count=cfg.get('screen_samples',16384),seed=training_seed+iteration,boundary_fraction=.25)
            new=[]
            for name,arm in arms.items():
                t=time.monotonic();active=np.flatnonzero(arm['sol'].weights>0)
                values=build(samples,[arm['ps'][i] for i in active],L,B)@arm['sol'].weights[active]
                arm['seconds']+=time.monotonic()-t
                bad=np.flatnonzero(values<1.001-2e-7)
                np.savez_compressed(args.out/f'L{L}-{name}-training-{iteration}.npz',poses=samples,values=values,bad_indices=bad)
                emit(dict(operation='training_screen',L=L,arm=name,iteration=iteration,quality=quality_metrics(values,arm['sol'].mass,target)))
                for i in bad[np.argsort(values[bad])][:cfg.get('max_new_rows',256)]:
                    key=tuple(np.round(samples[i],13))
                    if key not in rowkeys:rowkeys.add(key);new.append(samples[i])
            if new:
                new=np.array(new);oldlen=len(poses);poses=np.vstack([poses,new])
                for name in order:
                    arm=arms[name];t=time.monotonic()
                    arm['A']=sparse.vstack([arm['A'],build(new,arm['ps'],L,B)],format='csr')
                    arm['sol'],rep=solve_matrix(arm['A'],poses,1.001,np.pad(arm['sol'].dual,(0,len(new))))
                    elapsed=time.monotonic()-t;arm['seconds']+=elapsed
                    emit(dict(operation='shared_repair',L=L,arm=name,iteration=iteration,rows=len(poses),added=len(new),mass=arm['sol'].mass,seconds=elapsed))
        for name,arm in arms.items():
            assert arm['ps'][:original_count]==ps[:original_count]
            assert np.array_equal(poses[:original_rows],physical(raw,L,B))
            stem=f'L{L}-{name}';active=np.flatnonzero(arm['sol'].weights>0)
            np.savez_compressed(args.out/(stem+'.npz'),poses=poses,primitives_json=json.dumps(arm['ps']),weights=arm['sol'].weights,
                dual=arm['sol'].dual,L=L,B=B,rhs=1.001,net_json=json.dumps(dict(step='83/40000',last=200)))
            held=screening_poses(L,B,count=cfg.get('holdout_samples',65536),seed=holdout_seed,boundary_fraction=.25)
            t=time.monotonic();values=build(held,[arm['ps'][i] for i in active],L,B)@arm['sol'].weights[active]
            np.savez_compressed(args.out/(stem+'-holdout.npz'),poses=held,values=values)
            result=dict(operation='holdout',L=L,arm=name,quality=quality_metrics(values,arm['sol'].mass,target),
                search_seconds=arm['seconds'],audit_seconds=time.monotonic()-t,rows=len(poses),columns=len(arm['ps']),
                active_kinds=dict(Counter(arm['ps'][i]['kind'] for i in active)),certified=False)
            emit(result);summary.append(result);write('summary.json',summary)
            if arm['sol'].mass<target:
                rounded=[F(int(np.ceil(float(w)*1e12)),10**12) for w in arm['sol'].weights];total=sum(rounded,F(0))
                if total>F(str(target)):continue
                candidate=dict(schema=RADIAL_SCHEMA if any(p['kind'] in ('disk','bump','annulus') for p in arm['ps']) else SCHEMA,
                    n=n,L=str(L),B=str(B),net=dict(step='83/40000',last=200),total_mass=str(target),
                    primitives=[dict(kind=p['kind'],geometry=p['geometry'],mass=str(w*F(str(target))/total)) for p,w in zip(arm['ps'],rounded) if w])
                validate(candidate);write(stem+'-candidate.json',candidate)
        # Proof is a bounded diagnostic after both numerical arms complete.
    if cfg.get('exact_probe_boxes',8)>0:
        for path in sorted(args.out.glob('*-candidate.json')):
            t=time.monotonic();candidate=json.loads(path.read_text());filename=path.stem.replace('-candidate','-proof')+'.json'
            work=verify(candidate,max_boxes=cfg.get('exact_probe_boxes',8),checkpoint=lambda w:write(filename,w))
            write(filename,work);emit(dict(operation='exact_probe',candidate=path.name,status=work['status'],boxes=work['boxes'],seconds=time.monotonic()-t))
    decisions=[]
    for L in levels:
        reports={x['arm']:x for x in summary if x['L']==L}
        decision=choose_branch(reports['normal'],reports['auxiliary']);decision['L']=L
        decision['checkpoint']=f"L{L}-{decision['recommended']}.npz"
        decision['candidates_retained']=[f'L{L}-normal.npz',f'L{L}-auxiliary.npz']
        decisions.append(decision)
        for arm in ('normal','auxiliary'):
            continuation=dict(n=n,L=str(L),target=str(cfg['target']),k=cfg.get('k',round(n**.5)),
                checkpoint=f'L{L}-{arm}.npz',code_dir=str(code_dir),research_dir=str(research_dir),
                out=f'continue-L{L}-{arm}',exact_chunk_boxes=8,exact_review_boxes=20000,
                repair=dict(compare_grid=False,initial_pricing_rounds=1,repair_rounds=12,max_screen_rows=256,
                    mixed_pricing=dict(per_kind=64,max_columns=24,refinement_per_kind=64)))
            continuation['purpose']='Explicit native mixed continuation; original rectangle production branch remains separate'
            write(f'continue-L{L}-{arm}.json',continuation)
    write('selection.json',dict(decisions=decisions,auto_promote=False,certified=False,
        next_step='Both native states retained. Selection is numerical only; use a new audit seed after further tuning and exact verification before any bound claim.'))
    emit(dict(status='AUXILIARY_COMPARISON_COMPLETE',certified=False))

if __name__=='__main__':main()
