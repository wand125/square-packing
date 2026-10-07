"""Repair a full-angle scan, preserving every prior row/support and exact pose.
One density+point model, no discarded comparator constraints.
"""
import argparse,json,math
from pathlib import Path
from fractions import Fraction as F
from time import perf_counter
import numpy as np
from scipy.optimize import minimize
from expanded_search_pilot import ROOT,load,columns,Geometry,capture,solve
from mixed_density_check import expand,evaluate
from mixed_density_refit import export
from mixed_net_audit import symmetry,centre_domains,candidate_net


def collect(scan,out):
    data=json.loads((scan/'candidate.json').read_text());model=expand(data);symmetry(model);L,B=model[:2]
    rs=np.array([[float(F(x)) for x in r['rectangle']] for r in data['rectangles']]);rw=np.array([float(F(r['mass'])) for r in data['rectangles']]);ps=np.array([[float(F(x)) for x in p['point']] for p in data['points']]);pw=np.array([float(F(p['mass'])) for p in data['points']]);geo=Geometry(float(L),float(B),rs)
    rows={};failed=[]
    def add(x,y,t,origin):
        w=evaluate(model,x,y,t)
        if F(w['score'])>=1:return
        if t*t+2*t-1>0:x,y,t=y,x,(1-t)/(1+t);w=evaluate(model,x,y,t)
        reach=(L-B*(1+2*t-t*t)/(1+t*t))/2
        w['normalized_pose']=[float((x-L/2)/reach),float((y-L/2)/reach),2*math.atan(float(t))/(math.pi/4)];w['origin']=origin
        rows[tuple(map(str,(x,y,t)))]=w
    axis_path=scan/'axis/result.json'
    if axis_path.exists():
        ar=json.loads(axis_path.read_text())
        if ar['status']=='AXIS_BELOW_GAMMA' and ar.get('witness'):
            w=ar['witness'];add(F(w['cx']),F(w['cy']),F(0),str(axis_path));failed.append(0)
            # Use saved integer lower bounds only to prioritize candidate
            # cells. Every added centre is still re-evaluated rationally.
            with np.load(scan/'axis/integer-tables.npz') as table:
                f0,f1=table['fx'],table['fy'];h0,h1=table['hx'],table['hy']
                density=(f0*table['density_weights'])@f1.T
                lower=np.minimum.reduce([density[:-1,:-1],density[1:,:-1],density[:-1,1:],density[1:,1:]])
                lower+=(h0*table['point_weights'])@h1.T*(1<<(2*ar['table_metadata']['fraction_bits']))
            ax,ay=[[F(v) for v in axis] for axis in ar['axes']];selected=[]
            for index in np.argsort(lower,axis=None)[:256]:
                i,j=np.unravel_index(index,lower.shape)
                x,y=(ax[i]+ax[i+1])/2,(ay[j]+ay[j+1])/2
                canonical=tuple(sorted((x,y)))  # D4 exchange duplicates at t=0.
                if any(abs(float(canonical[0]-u))+abs(float(canonical[1]-v))<.000001 for u,v in selected):continue
                selected.append(canonical);add(x,y,F(0),'axis-batch:'+str(axis_path))
                e=F(1,4096)
                for u,v in ((e,e),(e,1-e),(1-e,e),(1-e,1-e)):
                    add(ax[i]+u*(ax[i+1]-ax[i]),ay[j]+v*(ay[j+1]-ay[j]),F(0),'axis-corner-batch:'+str(axis_path))
                if len(selected)>=16:break
    for path in sorted(scan.glob('net*/result.json')):
        result=json.loads(path.read_text())
        if result['status']=='ANGLE_VERIFIED':continue
        failed.append(result['manifest']['net_index']);ws=sorted(result['exact_witnesses'],key=lambda w:F(w['score']))
        selected=[]
        for w in ws:
            point=np.array([float(F(w[k])) for k in ('cx','cy')])
            if any(np.linalg.norm(point-p)<.002 for p in selected):continue
            selected.append(point);x,y,t=[F(w[k]) for k in ('cx','cy','t')];add(x,y,t,str(path))
            if len(selected)>=3:break
        # A failed interval lower bound is not a counterexample. Search its
        # unresolved cells numerically and replay the result exactly.
        seeds=ws[:1]
        if not seeds:
            E=F(result['manifest']['E']);tt=F(result['manifest']['t'])
            seeds=[dict(cx=str(L/2+F(z[0])*E),cy=str(L/2+F(z[1])*E),t=str(tt)) for z in result['frontier'][-3:]]
        for w in seeds:
            x,y,t=[F(w[k]) for k in ('cx','cy','t')]
            if t*t+2*t-1>0:x,y,t=y,x,(1-t)/(1+t)
            reach=(L-B*(1+2*t-t*t)/(1+t*t))/2;theta=2*math.atan(float(t))/(np.pi/4)
            high=F(result['manifest']['domain']['centre_high']);limit=float((high-L/2)/reach)
            def objective(z):
                pose=np.array([[z[0],z[1],min(1.,theta)]])
                return float((geo.matrix(pose)@rw+capture(pose,float(L),float(B),ps,shrink=0)@pw)[0])
            z=np.clip([float((x-L/2)/reach),float((y-L/2)/reach)],0,limit)
            fit=minimize(objective,z,method='Nelder-Mead',bounds=[(0,limit)]*2,options={'maxiter':160,'xatol':1e-9,'fatol':1e-10})
            u,v=[min((high-L/2)/reach,max(F(0),F(float(q)).limit_denominator(10**10))) for q in fit.x]
            add(L/2+u*reach,L/2+v*reach,t,'local-refinement:'+str(path))
    # Search beyond the first unresolved branch of each rigorous traversal.
    # This is only a source of exact counterexamples, never a coverage proof.
    rng=np.random.default_rng(926021)
    grid=np.array([(x,y) for x in np.linspace(0,1,19) for y in np.linspace(0,1,19)])
    broad_before=len(rows)
    for domain in centre_domains(L,B,*candidate_net(data)):
        t=F(domain['t']);high=F(domain['centre_high'])
        if t*t+2*t-1>0:t=(1-t)/(1+t)
        reach=(L-B*(1+2*t-t*t)/(1+t*t))/2;lim=(high-L/2)/reach
        theta=2*math.atan(float(t))/(np.pi/4)
        xy=np.vstack([grid,rng.random((256,2))])*float(lim)
        pp=np.column_stack([xy,np.full(len(xy),min(1.,theta))])
        vv=geo.matrix(pp)@rw+capture(pp,float(L),float(B),ps,shrink=0)@pw
        selected=[]
        for i in np.argsort(vv):
            if vv[i]>=1 or len(selected)>=4:break
            if any(np.linalg.norm(xy[i]-z)<.01 for z in selected):continue
            selected.append(xy[i])
        if vv.min()<1.004:
            def broad_objective(z):
                pose=np.array([[z[0],z[1],min(1.,theta)]])
                return float((geo.matrix(pose)@rw+capture(pose,float(L),float(B),ps,shrink=0)@pw)[0])
            fit=minimize(broad_objective,xy[np.argmin(vv)],method='Nelder-Mead',bounds=[(0,float(lim))]*2,options={'maxiter':160,'xatol':1e-9,'fatol':1e-10})
            selected.append(fit.x)
        for z in selected:
            u,v=[min(lim,max(F(0),F(float(q)).limit_denominator(10**10))) for q in z]
            add(L/2+u*reach,L/2+v*reach,t,'broad-net-search:'+str(domain['index']))
    print(json.dumps(dict(broad_exact_added=len(rows)-broad_before)),flush=True)
    from mixed_neighbor_search import search as neighbor_search
    neighbor_before=len(rows)
    neighbors,neighbor_records=neighbor_search(data,model,list(rows.values()))
    for w in neighbors:
        rows[tuple(w[k] for k in ('cx','cy','t'))]=w
    print(json.dumps(dict(neighbor_exact_added=len(rows)-neighbor_before,neighbor_searches=len(neighbor_records))),flush=True)
    pool=dict(candidate_digest=model[-1],source=str(scan),failed_angles=failed,witnesses=list(rows.values()),count=len(rows))
    pool['neighbor_search']=neighbor_records
    out.write_text(json.dumps(pool,indent=2));print(json.dumps(dict(failed_angles=len(failed),new_exact=len(rows))),flush=True);return pool


def repair(source,scan,out):
    start=perf_counter();out.mkdir(parents=True,exist_ok=False);pool=collect(scan,out/'new-witnesses.json')
    if not pool['witnesses']:raise RuntimeError('No exact deficit: refine verification instead of changing the LP')
    if (source/'model.json').exists():
        d=json.loads((source/'model.json').read_text());rects=np.array(d['rectangles']);L=d['L'];B=d['B'];rhs=d['rhs'];saved=range(d['base_pose_count'])
        (out/'model.json').write_text(json.dumps(d,indent=2))
    else:
        _,rects,saved,L,B,rhs,_=load(21);d=json.loads((ROOT/'n21/results.json').read_text())
    r=len(rects);p=d['point_columns'];rules=d['rules']
    for rule in rules:rule['sites']=[tuple(map(F,x)) for x in rule['sites']]
    ledger=json.loads((source/'cumulative-witnesses.json').read_text());new=pool['witnesses']
    with np.load(source/'replay.npz') as z:
        aa=z['matrix'].copy();ids=z['row_ids'].tolist();chosen=z['selected_rectangles'].copy();oldposes=z['poses'].copy()
    npnew=np.clip(np.array([w['normalized_pose'] for w in new]),[-1,-1,0],[1,1,1]);allposes=np.vstack([oldposes,npnew]);assert len(oldposes)==len(saved)+len(ledger)
    def block(pose):
        pc,_,mapping=columns(pose,rules,L,B)
        return np.hstack([Geometry(L,B,rects).matrix(pose),pc,Geometry(L,B,chosen).matrix(pose)]),mapping
    extra,mapping=block(npnew);aa=np.vstack([aa,extra]);ids+=list(range(len(oldposes),len(allposes)))
    def audit(w):
        ri=np.flatnonzero(w[:r]>0);ni=np.flatnonzero(w[r+p:]>0);dens=np.vstack([rects[ri],chosen[ni]]);dw=np.r_[w[ri],w[r+p:][ni]];pi=np.flatnonzero(w[r:r+p]>0);unique=sorted({i for j in pi for i in mapping['point_orbits'][j]});idx={v:k for k,v in enumerate(unique)};vals=[]
        for lo in range(0,len(allposes),1024):
            q=allposes[lo:lo+1024];v=Geometry(L,B,dens).matrix(q)@dw
            if unique:
                hit=capture(q,L,B,np.array([mapping['points'][i] for i in unique],float))
                for j in pi:v+=w[r+j]*hit[:,[idx[i] for i in mapping['point_orbits'][j]]].mean(axis=1)
            vals.extend(v)
        return np.array(vals)
    records=[]
    for iteration in range(12):
        fit,stat=solve(aa,rhs);w=fit.x;v=audit(w);bad=np.flatnonzero(v<rhs-1e-8);stat.update(iteration=iteration,rows=len(aa),all_min=float(v.min()),violations=len(bad));records.append(stat);print(json.dumps(stat),flush=True)
        if not len(bad):break
        missing=sorted(set(bad)-set(ids))
        if not missing:raise RuntimeError('Numerical disagreement on existing rows')
        extra,_=block(allposes[missing]);aa=np.vstack([aa,extra]);ids+=missing
    assert not len(bad),'Finite repair did not finish'
    # Preserve the whole LP before rational export: an over-budget solution
    # must remain usable for support pricing even when expand() rejects it.
    allw=ledger+new
    np.savez_compressed(out/'replay.npz',matrix=aa,row_ids=ids,selected_rectangles=chosen,poses=allposes,weights_added_density=w,coverage_added_density=v)
    (out/'cumulative-witnesses.json').write_text(json.dumps(allw,indent=2))
    mass=sum((F(str(x)) for x in w),F(0))
    budget=F(d.get('budget',str(F(d.get('n',21))-F(1,1000))))
    if mass>budget:
        result=dict(status='BUDGET_EXHAUSTED',source=str(source),scan=str(scan),records=records,total_poses=len(allposes),exact_count=len(allw),mass=str(mass),rational_replay='PENDING_AFTER_BUDGET_RECOVERY',seconds=perf_counter()-start)
        (out/'results.json').write_text(json.dumps(result,indent=2))
        print(json.dumps({k:v for k,v in result.items() if k!='records'}),flush=True)
        return
    ordered=np.r_[w[:r],w[r+p:],w[r:r+p]];candidate=export(out/'mixed-candidate.json',d,np.vstack([rects,chosen]),ordered,mapping);model=expand(candidate)
    rechecks=[evaluate(model,F(q['cx']),F(q['cy']),F(q['t'])) for q in allw];assert all(F(q['score'])>=1 for q in rechecks),'Rational replay failed'
    result=dict(status='FINITE_REPAIRED_NOT_CERTIFIED',source=str(source),scan=str(scan),records=records,total_poses=len(allposes),exact_count=len(allw),mass=str(model[-2]),exact_rechecks=rechecks,seconds=perf_counter()-start)
    (out/'results.json').write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items() if k not in ('records','exact_rechecks')}),flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--scan',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();repair(a.source,a.scan,a.out)
