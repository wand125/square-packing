"""All-row point/line/rectangle search with grid seeds and exact separation.

No original support or saved row is removed. Numerical LP/sampling cannot
certify. Only the exact full-centre/full-net verifier can emit CERTIFIED.
"""
import os
for name in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMBA_NUM_THREADS'):os.environ[name]='1'
import argparse,json,math,time,hashlib,sys
from pathlib import Path
from fractions import Fraction as F
import numpy as np
from scipy import sparse
from unified_measure import SCHEMA,RADIAL_SCHEMA,RADIAL_KINDS,primitive_key,validate,verify,region,score,net_check

def solve_matrix(A,poses,rhs,dual):
    """Adapter to the retained-row solver; rows are physical poses of all types."""
    import highspy
    from working_rows import solve_working_rows
    class Model:
        atoms=[]  # Point/line coefficients are already ordinary matrix columns.
        @staticmethod
        def _check(status):
            if status!=highspy.HighsStatus.kOk:raise RuntimeError(str(status))
    m=Model();m.A=A;m.poses=poses;m.rhs=rhs
    if A.shape[0]!=len(poses):raise ValueError('matrix/pose count mismatch')
    return solve_working_rows(m,dual)

def structured(L,k):
    """Multiple grid families plus off-grid repairs; no locked mass ratios."""
    L=F(str(L));out=[]
    def add(kind,g,family):out.append(dict(kind=kind,geometry=list(map(str,g)),family=family))
    for family,lines in [('scaled',[L*j/k for j in range(1,k)]),
                         ('wall',[1+j*(L-2)/(k-2) for j in range(k-1)])]:
        for x in lines:
            for y in lines:add('point',(x,y),family)
            # Split long lines into local segments so weights can vary by place.
            edges=[F(1,4)]+lines+[L-F(1,4)]
            for a,b in zip(edges,edges[1:]):
                if b<=a:continue
                add('segment',(x,a,x,b),family)
                for half in [F(1,200),F(1,50)]:add('rectangle',(x-half,a,x+half,b),family)
    for phase in [F(0),F(1,2),L/2-(L//2)]:
        lines=[F(i)+phase for i in range(math.ceil(float(L))) if F(1,1000)<i+phase<L-F(1,1000)]
        for x in lines:
            for y in lines:add('point',(x,y),'phase')
    return out

def repair_primitives(cx,cy,L):
    out=[];L=F(str(L));cx=F(cx);cy=F(cy);margin=F(1,1000)
    for x,y in [(cx,cy),(cx-F(1,4),cy),(cx+F(1,4),cy),(cx,cy-F(1,4)),(cx,cy+F(1,4))]:
        if not margin<x<L-margin or not margin<y<L-margin:continue
        out.append(dict(kind='point',geometry=list(map(str,(x,y))),family='repair'))
        for h in [F(1,100),F(1,20)]:
            if margin<x-h<x+h<L-margin and margin<y-h<y+h<L-margin:
                out.append(dict(kind='rectangle',geometry=list(map(str,(x-h,y-h,x+h,y+h))),family='repair'))
        for dx,dy in [(F(1,8),F(0)),(F(1,8),F(1,8)),(F(1,8),-F(1,8))]:
            g=(x-dx,y-dy,x+dx,y+dy)
            if all(margin<z<L-margin for z in g):out.append(dict(kind='segment',geometry=list(map(str,g)),family='repair'))
    return out

def shifted_controls(pool,existing,L):
    """Equal-count, equal-type/shape control; rigid translations only.
    D4 canonical duplicates are rejected without shrinking or changing type.
    """
    L=F(L);margin=F(1,1000);seen=set(existing);out=[]
    for i,p in enumerate(pool):
        g=list(map(F,p['geometry']));pts=[g] if p['kind']=='point' else [g[:2],g[2:]]
        low=[min(q[a] for q in pts) for a in (0,1)];high=[max(q[a] for q in pts) for a in (0,1)]
        room=[L-2*margin-high[a]+low[a] for a in (0,1)]
        if min(room)<=0:raise ValueError('control has no translation room')
        for attempt in range(1,101):
            shift=[margin+(low[a]-margin+L*F((173205 if a==0 else 271828)+attempt*7919+i*101,1000000))%room[a]-low[a] for a in (0,1)]
            translated=[q[a]+shift[a] for q in pts for a in (0,1)]
            key=primitive_key(p['kind'],translated,L)
            if key not in seen:
                seen.add(key);out.append(dict(kind=p['kind'],geometry=list(map(str,translated)),family='shifted_control'));break
        else:raise ValueError('could not match control count')
    return out

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--config',type=Path,required=True);a=ap.parse_args()
    cfg=json.loads(a.config.read_text());base=a.config.resolve().parent
    if cfg.get('radial_mode','rectangles') not in ('rectangles','native'):raise ValueError('invalid radial mode')
    sys.path.insert(0,str((base/cfg['code_dir']).resolve()));sys.path.insert(0,str((base/cfg['research_dir']).resolve()))
    from unified_geometry import expand_primitives,matrix
    from working_rows import solve_working_rows
    import highspy
    out=base/cfg['out'];out.mkdir(parents=True,exist_ok=False)
    records=[];started=time.monotonic()
    def emit(d):
        d['elapsed']=time.monotonic()-started;records.append(d)
        p=out/'progress.tmp';p.write_text(json.dumps(dict(records=records),indent=2));p.replace(out/'progress.json');print(json.dumps(d),flush=True)
    def write(name,d):
        p=out/(name+'.tmp');p.write_text(json.dumps(d,indent=2));p.replace(out/name)
    try:
        L=F(cfg['L']);B=F(cfg.get('B','0.9977'));n=cfg['n'];target=F(cfg['target']);rhs=1.001
        if not 0<target<n:raise ValueError('invalid target')
        net_check(dict(B=str(B),net=cfg.get('net',dict(step='83/40000',last=200))))
        if cfg.get('initial_state',False):
            if 'checkpoint' in cfg:raise ValueError('choose initial_state or checkpoint')
            from mixed_grid_pricing import initial_state,candidate_pool
            ps,qs,ws,ds=initial_state(L,B,rhs)
            # A uniform-only LP has a highly degenerate dual. Seed a spatially
            # diverse bounded dictionary before using dual-ranked additions.
            options=cfg.get('mixed_pricing',{})
            seed_pool=candidate_pool(L,cfg['k'],ps,ws,**{key:options[key] for key in ('per_kind','seed','grid_fraction') if key in options})
            if cfg.get('initial_grid_hint',False):
                seen={primitive_key(p['kind'],p['geometry'],L) for p in ps+seed_pool}
                hint_pool=[]
                for p in structured(L,cfg['k']):
                    g=list(map(F,p['geometry']));key=primitive_key(p['kind'],g,L)
                    if key not in seen and all(0<=z<=L for z in g):
                        seen.add(key);hint_pool.append(p)
                if cfg.get('initial_grid_hint_shifted',False):
                    existing={primitive_key(p['kind'],p['geometry'],L) for p in ps+seed_pool}
                    hint_pool=shifted_controls(hint_pool,existing,L)
                seed_pool+=hint_pool
            ps+=seed_pool;ws=np.pad(ws,(0,len(seed_pool)))
            path=out/'initial-state.npz'
            np.savez_compressed(path,primitives_json=json.dumps(ps),poses=qs,weights=ws,dual=ds,L=float(L),B=float(B),rhs=rhs,net_json=json.dumps(cfg.get('net',dict(step='83/40000',last=200))))
        else:path=base/cfg['checkpoint']
        data=np.load(path,allow_pickle=False)
        for key,value in [('L',L),('B',B),('rhs',F('1.001'))]:
            if key in data and abs(float(data[key])-float(value))>1e-13:raise ValueError('checkpoint geometry mismatch')
        resumed='primitives_json' in data
        primitives=json.loads(str(data['primitives_json'])) if resumed else [dict(kind='rectangle',geometry=[str(float(x)) for x in r],family='retained') for r in data['rectangles']]
        keys={primitive_key(p['kind'],p['geometry'],L) for p in primitives}
        original_count=len(primitives)
        def fresh(pool,commit=True):
            selected=[];seen=keys if commit else set(keys)
            for p in pool:
                g=list(map(F,p['geometry']))
                if not all(0<z<L for z in (g[:2] if p['kind'] in RADIAL_KINDS else g)):continue
                key=primitive_key(p['kind'],g,L)
                if key not in seen:seen.add(key);selected.append(p)
            return selected
        # Preserve saved physical poses: original normalization is based on core B.
        poses=[]
        if resumed:poses=data['poses'].tolist()
        else:
            for u,v,z in data['poses']:
                theta=float(z)*math.pi/4;t=math.tan(theta/2);e=(float(L)-float(B)*(math.cos(theta)+math.sin(theta)))/2
                poses.append([float(L)/2+float(u)*e,float(L)/2+float(v)*e,t])
        poses=np.asarray(poses);rowkeys={tuple(np.round(p,13)) for p in poses}
        def build(ps,cols):
            expanded=expand_primitives(cols,L);parts=[]
            for start in range(0,len(ps),128):
                block=matrix(np.asarray(ps[start:start+128],float),float(B),expanded)
                block[np.abs(block)<=1e-12]=0;parts.append(sparse.csr_matrix(block))
            return sparse.vstack(parts,format='csr') if parts else sparse.csr_matrix((0,len(cols)))
        class Model:
            atoms=[]
            @staticmethod
            def _check(status):
                if status!=highspy.HighsStatus.kOk:raise RuntimeError(str(status))
        m=Model();m.rhs=rhs;m.A=build(poses,primitives)
        dual=np.zeros(len(poses))
        if resumed:dual=np.where(data['dual']>1e-8,data['dual'],0.)
        if 'dual_seed' in cfg:
            seed=np.load(base/cfg['dual_seed'],allow_pickle=False)
            if not np.array_equal(seed['poses'],data['poses']) or not np.array_equal(seed['rectangles'],data['rectangles']):raise ValueError('seed mismatch')
            dual=np.where(seed['dual']>1e-8,seed['dual'],0.)
        manifest=dict(config=cfg,input_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
            source_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in Path(__file__).parent.glob('*.py') if p.name.startswith(('unified_','radial_','mixed_grid_')) or p.name=='score.py'},
            proof_condition='all net directions and full centre domains; exact mass < n')
        manifest['dependency_sha256']={name:dict(path=str(Path(sys.modules[name].__file__).resolve()),
            sha256=hashlib.sha256(Path(sys.modules[name].__file__).read_bytes()).hexdigest())
            for name in ('radial_numeric','fast_geometry','working_rows','master','score') if name in sys.modules}
        write('manifest.json',manifest)
        def solve(label):
            nonlocal dual
            sol,report=solve_matrix(m.A,poses,rhs,dual);dual=sol.dual.copy()
            emit(dict(operation='lp',label=label,mass=sol.mass,rows=m.A.shape[0],columns=m.A.shape[1],seconds=sol.seconds,
                      minimum=sol.min_coverage,dual_violation=sol.dual_violation,gap=sol.duality_gap,
                      working_rows=report['working_rows'],rounds=report['rounds']))
            return sol
        sol=solve('retained_dictionary_baseline')
        grid=fresh(structured(L,cfg['k'])) if cfg.get('compare_grid',True) else []
        control=shifted_controls(grid,keys,L)
        keys.update(primitive_key(p['kind'],p['geometry'],L) for p in control)
        # Include point/line versions of active old supports, including non-grid sites.
        support_pool=[]
        for p,w in zip(primitives,sol.weights):
            if w<=1e-8 or p['kind']!='rectangle':continue
            x0,y0,x1,y1=map(F,p['geometry']);x=(x0+x1)/2;y=(y0+y1)/2
            support_pool.extend([dict(kind='point',geometry=list(map(str,(x,y))),family='active_support'),
                dict(kind='segment',geometry=list(map(str,(x0,y,x1,y))),family='active_support'),
                dict(kind='segment',geometry=list(map(str,(x,y0,x,y1))),family='active_support')])
        common=fresh(support_pool) if cfg.get("compare_grid",True) else []
        extra=grid+control+common
        extra_matrix=build(poses,extra);allA=sparse.hstack([m.A,extra_matrix],format='csr');allprimitives=primitives+extra
        baseline_mass=sol.mass
        # Same rows and same original dictionary for each separate treatment.
        comparisons=[]
        treatments=[('common_offgrid',lambda i,p:i>=len(grid)+len(control)),
            ('grid_all_three',lambda i,p:i<len(grid) or i>=len(grid)+len(control)),
            ('shifted_all_three',lambda i,p:i>=len(grid)),
            ('grid_rectangles',lambda i,p:(i<len(grid) or i>=len(grid)+len(control)) and p['kind']=='rectangle'),
            ('points_rectangles',lambda i,p:(i<len(grid) or i>=len(grid)+len(control)) and p['kind'] in ('point','rectangle')),
            ('lines_rectangles',lambda i,p:(i<len(grid) or i>=len(grid)+len(control)) and p['kind'] in ('segment','rectangle')),
            ('all_three_union',lambda i,p:True)]
        s=sol
        if not cfg.get('compare_grid',True):treatments=[]
        for label,select in treatments:
            ids=list(range(original_count))+[original_count+i for i,p in enumerate(extra) if select(i,p)]
            m.A=allA[:,ids].tocsr();s=solve(label)
            if s.mass>baseline_mass+1e-4:raise RuntimeError('adding columns increased optimum')
            comparisons.append(dict(label=label,mass=s.mass,seconds=s.seconds,columns=len(ids)))
        write('comparison.json',dict(comparisons=comparisons,baseline_mass=baseline_mass,rows=len(poses),certified=False,
              grid_count=len(grid),shifted_count=len(control),common_count=len(common),
              limitations='One inherited row dictionary; controls preserve candidate counts/types/shapes, not independent initial histories. Solve timings are order-dependent warm starts.'))
        primitives=allprimitives;m.A=allA;sol=s
        mixed_calls=0
        def add_mixed(label):
            nonlocal sol,primitives,mixed_calls
            if not cfg.get('mixed_pricing'):return
            from mixed_grid_pricing import propose_mixed_grid
            options=dict(cfg['mixed_pricing'])
            if cfg.get('mixed_refresh_seed',False):options['seed']=options.get('seed',20260927)+mixed_calls
            mixed_calls+=1
            extra,report=propose_mixed_grid(poses,dual,L,B,primitives,sol.weights,k=cfg['k'],**options)
            extra=fresh(extra,commit=False)
            write(f'mixed-pricing-{label}.json',report);emit(dict(report,operation='pricing',label=label))
            if extra:
                keys.update(primitive_key(p['kind'],p['geometry'],L) for p in extra)
                m.A=sparse.hstack([m.A,build(poses,extra)],format='csr');primitives+=extra
                sol=solve(f'mixed-{label}')
        for step in range(cfg.get('initial_pricing_rounds',1)):add_mixed(f'initial-{step}')
        def add_radial(label):
            nonlocal sol,primitives
            if not cfg.get('radial_pricing'):return
            radial_dir=(base/cfg['radial_code_dir']).resolve() if 'radial_code_dir' in cfg else Path(__file__).resolve().parents[1]/'rectangle_budget_optimization'
            sys.path.insert(0,str(radial_dir))
            from radial_pricing import RadialOptions,search_radial,rectangle_seed_pool
            module=Path(sys.modules['radial_pricing'].__file__)
            manifest['dependency_sha256']['radial_pricing']=dict(path=str(module.resolve()),sha256=hashlib.sha256(module.read_bytes()).hexdigest())
            write('manifest.json',manifest)
            options=RadialOptions(**cfg['radial_pricing'])
            kernels,report=search_radial(poses,dual,float(L),float(B),options)
            if cfg.get('radial_mode')=='native':
                pool=fresh([dict(kind=('disk','bump','annulus')[int(k[0])],
                    geometry=[format(x,'.12g') for x in (k[1:] if k[0]==2 else k[1:4])],family='radial_native') for k in kernels],commit=False)
            else:
                pool=fresh([dict(kind='rectangle',geometry=list(map(str,r)),family='radial_seed')
                            for r in rectangle_seed_pool(kernels,float(L),options)],commit=False)
            positive=np.flatnonzero(dual>0)
            prices=np.asarray(build(poses[positive],pool).T@dual[positive]).ravel() if pool else np.array([])
            ids=[int(i) for i in np.argsort(-prices) if prices[i]>1+options.score_margin][:options.max_columns]
            extra=[pool[i] for i in ids]
            report.update(columns=len(extra),rectangle_evaluations=len(pool),selected_kernels=kernels,
                          selected_scores=[float(prices[i]) for i in ids],radial_measure_exported=cfg.get('radial_mode')=='native')
            write(f'radial-pricing-{label}.json',report);emit(dict(report,operation='pricing',label=label))
            if extra:
                keys.update(primitive_key(p['kind'],p['geometry'],L) for p in extra)
                m.A=sparse.hstack([m.A,build(poses,extra)],format='csr');primitives+=extra
                sol=solve('radial_native' if cfg.get('radial_mode')=='native' else 'radial_rectangle_seeds')
        add_radial('initial')
        def save_state():
            np.savez_compressed(out/'resume-state.tmp.npz',poses=poses,weights=sol.weights,dual=dual,
                primitives_json=json.dumps(primitives),L=float(L),B=float(B),rhs=rhs,net_json=json.dumps(cfg.get('net',dict(step='83/40000',last=200))))
            (out/'resume-state.tmp.npz').replace(out/'resume-state.npz');write('primitives.json',primitives)
        if cfg.get('initial_screen_rounds',0)>0:
            from mixed_grid_pricing import screening_poses
            rolling=cfg.get('initial_screen_refresh',False)
            catalog=None
            if cfg.get('initial_pose_catalog'):
                catalog_path=base/cfg['initial_pose_catalog']
                catalog=np.load(catalog_path,allow_pickle=False)['poses']
                if cfg.get('initial_catalog_normalized',False):
                    from radial_pricing import physical_poses
                    catalog=physical_poses(catalog,float(L),float(B))
                if catalog.ndim!=2 or catalog.shape[1]!=3 or not np.all(np.isfinite(catalog)):raise ValueError('invalid pose catalog')
                manifest['pose_catalog']=dict(sha256=hashlib.sha256(catalog_path.read_bytes()).hexdigest(),
                    rows=len(catalog),normalized=cfg.get('initial_catalog_normalized',False))
                write('manifest.json',manifest)
            for step in range(cfg['initial_screen_rounds']+1):
                seed=20261000+step if rolling else 20260928
                seed+=cfg.get('initial_screen_seed_offset',0)
                samples=screening_poses(L,B,count=cfg.get('initial_screen_samples',4096),seed=seed,
                    boundary_fraction=cfg.get('initial_boundary_fraction',0.))
                if catalog is not None:samples=np.vstack([samples,catalog])
                active=np.flatnonzero(sol.weights>0)
                values=build(samples,[primitives[i] for i in active])@sol.weights[active]
                if cfg.get('initial_adversarial_starts',0)>0:
                    from mixed_grid_pricing import refine_witnesses
                    def current_score(q):return build(q,[primitives[i] for i in active])@sol.weights[active]
                    refined,refined_values=refine_witnesses(samples,values,L,B,current_score,starts=cfg['initial_adversarial_starts'])
                    samples=np.vstack([samples,refined]);values=np.r_[values,refined_values]
                bad=np.flatnonzero(values<rhs-2e-7)
                emit(dict(operation='initial_screen',iteration=step,samples=len(samples),
                          minimum=float(values.min()),counterexamples=len(bad),mass=sol.mass,globally_verified=False))
                if step==cfg['initial_screen_rounds']:break
                if not len(bad):
                    if rolling:continue
                    break
                new=[]
                for i in bad[np.argsort(values[bad])]:
                    p=samples[i];key=tuple(np.round(p,13))
                    if key not in rowkeys:rowkeys.add(key);new.append(p)
                    if len(new)>=cfg['max_screen_rows']:break
                if not new:break
                m.A=sparse.vstack([m.A,build(new,primitives)],format='csr')
                poses=np.vstack([poses,new]);dual=np.pad(dual,(0,len(new)))
                if cfg.get('initial_witness_supports',False):
                    pool=[]
                    for x,y,t in new[:cfg.get('initial_witness_support_count',4)]:pool.extend(repair_primitives(str(x),str(y),L))
                    extra=fresh(pool)
                    if extra:
                        m.A=sparse.hstack([m.A,build(poses,extra)],format='csr');primitives+=extra
                sol=solve(f'initial-screen-{step}')
                if not cfg.get('initial_pricing_near_budget',False) or sol.mass>=float(target)*.9995:
                    for attempt in range(cfg.get('initial_pricing_per_screen',1)):add_mixed(f'initial-screen-{step}-{attempt}')
                if cfg.get('initial_radial_every',0)>0 and (step+1)%cfg['initial_radial_every']==0:add_radial(f'initial-screen-{step}')
                save_state()
        if cfg.get('pricing_only',False):
            quality_passed=None
            if cfg.get('initial_state',False) or cfg.get('initial_screen_rounds',0)>0:
                from mixed_grid_pricing import screening_poses,quality_metrics
                samples=screening_poses(L,B,count=cfg.get('holdout_samples',4096),seed=cfg.get('holdout_seed',20260929),
                    boundary_fraction=cfg.get('holdout_boundary_fraction',0.))
                active=np.flatnonzero(sol.weights>0)
                values=build(samples,[primitives[i] for i in active])@sol.weights[active]
                quality=dict(operation='holdout',samples=len(samples),minimum=float(values.min()),
                    below_one=int(np.count_nonzero(values<1)),mass=sol.mass,
                    minimum_at_target=float(values.min())*float(target)/sol.mass,globally_verified=False)
                quality.update(quality_metrics(values,sol.mass,float(target)))
                gate=cfg.get('initial_quality_gate')
                if gate is not None:
                    metrics=quality['target_mass']
                    quality_passed=(metrics['hole_fraction']<=gate['max_hole_fraction'] and metrics['max_deficit']<=gate['max_deficit'])
                    quality.update(quality_gate=gate,quality_passed=quality_passed)
                write('quality.json',quality);emit(quality)
            status='SAVED_INITIAL_QUALITY_INSUFFICIENT' if quality_passed is False else 'SAVED_FINITE_INITIAL'
            save_state();emit(dict(status=status,mass=sol.mass,quality_passed=quality_passed,globally_verified=False));return
        for iteration in range(cfg.get('repair_rounds',20)+1):
            save_state()
            if sol.mass>=float(target):emit(dict(status='BUDGET_EXHAUSTED',operation='terminal',iteration=iteration,globally_verified=False));return
            # Upward rational rounding preserves nonnegativity and numerical coverage.
            rounded=[F(math.ceil(float(w)*1e12),10**12) for w in sol.weights];total=sum(rounded,F(0))
            if total>target:emit(dict(status='SAVED_ROUNDING_BUDGET',operation='terminal',globally_verified=False));return
            factor=target/total
            candidate=dict(schema=RADIAL_SCHEMA if any(p['kind'] in RADIAL_KINDS for p in primitives) else SCHEMA,n=n,L=str(L),B=str(B),net=cfg.get('net',dict(step='83/40000',last=200)),
                primitives=[dict(kind=p['kind'],geometry=p['geometry'],mass=str(w*factor)) for p,w in zip(primitives,rounded) if w],total_mass=str(target))
            validate(candidate);write(f'candidate-{iteration:03}.json',candidate)
            # Broad, bounded numerical search; source rows remain untouched.
            samples=[]
            for j in range(0,201,10):
                t=F(83*j,40000);c=(1-t*t)/(1+t*t);ss=2*t/(1+t*t);e=(L-B*(c+ss))/2
                for u in range(-4,5):
                    for v in range(-4,5):samples.append([float(L/2+F(u,4)*e),float(L/2+F(v,4)*e),float(t)])
            values=build(samples,primitives)@np.asarray([float(w*factor) for w in rounded]);bad=np.flatnonzero(values<1.0001)
            order=bad[np.argsort(values[bad])[:cfg['max_screen_rows']]];witnesses=[samples[i] for i in order]
            emit(dict(operation='screen',iteration=iteration,samples=len(samples),counterexamples=len(bad),added_candidates=len(witnesses),globally_verified=False))
            if not witnesses:
                work=None
                while True:
                    work=verify(candidate,work=work,max_boxes=cfg.get('exact_chunk_boxes',64),checkpoint=lambda x:write(f'proof-{iteration:03}.json',x),
                        integral_subdivisions=cfg.get('integral_subdivisions',32),max_integral_subdivisions=cfg.get('max_integral_subdivisions',256))
                    emit(dict(operation='proof',iteration=iteration,status=work['status'],boxes=work['boxes'],directions_completed=work['directions_completed']))
                    if work['status']=='CERTIFIED':write('certificate.json',candidate);emit(dict(status='CERTIFIED',globally_verified=True));return
                    if work['status']=='UNCOVERED':
                        w=work['witness'];witnesses=[[float(F(w['cx'])),float(F(w['cy'])),float(F(w['t']))]];break
                    if work.get('reason')=='INTEGRAL_PRECISION':emit(dict(status='SAVED_INTEGRAL_REVIEW',globally_verified=False));return
                    if work['boxes']>=cfg.get('exact_review_boxes',20000):emit(dict(status='SAVED_EXACT_REVIEW',globally_verified=False));return
            new=[]
            for p in witnesses:
                key=tuple(np.round(p,13))
                if key not in rowkeys:rowkeys.add(key);new.append(p)
            if not new:emit(dict(status='SAVED_NO_NEW_ROWS',globally_verified=False));return
            m.A=sparse.vstack([m.A,build(new,primitives)],format='csr');poses=np.vstack([poses,new]);dual=np.pad(dual,(0,len(new)))
            pool=[]
            for x,y,t in new[:4]:pool.extend(repair_primitives(str(x),str(y),L))
            extra=fresh(pool)
            if extra:m.A=sparse.hstack([m.A,build(poses,extra)],format='csr');primitives+=extra
            sol=solve(f'repair-{iteration}')
            add_mixed(f'repair-{iteration}')
            if cfg.get('radial_every',0)>0 and (iteration+1)%cfg['radial_every']==0:add_radial(f'repair-{iteration}')
        save_state()
        emit(dict(status='ITERATIONS_EXHAUSTED',globally_verified=False))
    except Exception as e:emit(dict(status='ERROR',error=repr(e)));raise

if __name__=='__main__':main()
