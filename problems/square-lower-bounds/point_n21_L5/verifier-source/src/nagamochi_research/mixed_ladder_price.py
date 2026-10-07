"""Add rectangle supports to a transferred mixed model, retaining all rows."""
import argparse,json,sys,shutil
from pathlib import Path
from fractions import Fraction as F
from types import SimpleNamespace
import numpy as np
from expanded_search_pilot import Geometry,columns,capture,solve
from mixed_density_refit import export
from mixed_density_check import expand,evaluate
from geometry import rectangle_key
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'rectangle_budget_optimization'))
from edge_pricing import propose_edges


def pricing_dual(marginals):
    """Sanitize roundoff for the heuristic oracle only, never a proof bound."""
    dual = -np.asarray(marginals, dtype=float)
    if not np.isfinite(dual).all() or np.any(dual < -1e-9):
        raise ValueError('Invalid pricing dual beyond roundoff tolerance')
    return np.maximum(dual, 0)


def run(source,out,rounds,target=F('20.999')):
    assert 0<target<=F('20.999')
    out.mkdir(parents=True,exist_ok=False)
    raw=json.loads((source/'model.json').read_text());d=json.loads(json.dumps(raw))
    L,B,rhs=d['L'],d['B'],d['rhs'];rects=np.array(d['rectangles']);r=len(rects);p=d['point_columns']
    rules=d['rules']
    for rule in rules:rule['sites']=[tuple(map(F,v)) for v in rule['sites']]
    ledger=json.loads((source/'cumulative-witnesses.json').read_text())
    with np.load(source/'replay.npz') as z:
        aa=z['matrix'].copy();ids=z['row_ids'].tolist();chosen=z['selected_rectangles'].copy();poses=z['poses'].copy()
    _,_,mapping=columns(poses[:1],rules,L,B)
    def block(q):
        pc,_,_=columns(q,rules,L,B)
        return np.hstack([Geometry(L,B,rects).matrix(q),pc,Geometry(L,B,chosen).matrix(q)])
    def audit(w):
        ri=np.flatnonzero(w[:r]>0);ni=np.flatnonzero(w[r+p:]>0);pi=np.flatnonzero(w[r:r+p]>0)
        density=np.vstack([rects[ri],chosen[ni]]);dw=np.r_[w[ri],w[r+p:][ni]]
        unique=sorted({i for j in pi for i in mapping['point_orbits'][j]});lookup={v:k for k,v in enumerate(unique)};vals=[]
        for lo in range(0,len(poses),1024):
            q=poses[lo:lo+1024];v=Geometry(L,B,density).matrix(q)@dw
            if unique:
                hits=capture(q,L,B,np.array([mapping['points'][i] for i in unique],float))
                for j in pi:v+=w[r+j]*hits[:,[lookup[i] for i in mapping['point_orbits'][j]]].mean(axis=1)
            vals.extend(v)
        return np.array(vals)
    history=[]
    for step in range(rounds+1):
        comparison=None
        while True:
            fit,stat=solve(aa,rhs);w=fit.x;vals=audit(w);bad=np.flatnonzero(vals<rhs-1e-8)
            stat.update(step=step,rows=len(aa),supports=aa.shape[1],all_min=float(vals.min()),violations=len(bad))
            history.append(stat);print(json.dumps(stat),flush=True)
            if not len(bad) and sum((F(str(x)) for x in w),F(0))<=target:
                cols=np.r_[np.arange(r),np.arange(r+p,aa.shape[1])]
                pure,comparison=solve(aa[:,cols],rhs);pw=np.zeros_like(w);pw[cols]=pure.x
                pv=audit(pw);bad=np.flatnonzero(pv<rhs-1e-8)
                comparison.update(model='rectangles',all_min=float(pv.min()),violations=len(bad),same_supports=True,total_poses=len(poses))
                print(json.dumps(comparison),flush=True)
            if not len(bad):break
            missing=sorted(set(bad)-set(ids));assert missing,'LP/full audit disagreement'
            aa=np.vstack([aa,block(poses[missing])]);ids+=missing
        folder=out/f'step{step}';folder.mkdir()
        (folder/'model.json').write_text(json.dumps(raw,indent=2))
        shutil.copyfile(source/'cumulative-witnesses.json',folder/'cumulative-witnesses.json')
        np.savez_compressed(folder/'replay.npz',matrix=aa,row_ids=ids,selected_rectangles=chosen,poses=poses,weights_added_density=w,coverage_added_density=vals)
        mass=sum((F(str(x)) for x in w),F(0));result=dict(status='BUDGET_EXHAUSTED' if mass>F('20.999') else 'FINITE_NUMERICAL_ONLY',mass=str(mass),L=str(L),step=step,total_poses=len(poses),history=history)
        result['rectangle_comparison']=comparison
        (folder/'results.json').write_text(json.dumps(result,indent=2))
        (out/'status.json').write_text(json.dumps(dict(status=result['status'],step=step,mass=str(mass),latest=str(folder.resolve())),indent=2))
        # Intermediate LP checkpoints are never offered as verified candidates.
        # Replay all exact poses once, on the candidate actually sent to proof.
        if mass<=F('20.999') and (mass<=target or step==rounds):
            data=export(folder/'mixed-candidate.json',d,np.vstack([rects,chosen]),np.r_[w[:r],w[r+p:],w[r:r+p]],mapping)
            model=expand(data);checks=[evaluate(model,F(q['cx']),F(q['cy']),F(q['t'])) for q in ledger]
            assert all(F(q['score'])>=1 for q in checks),'Exact transferred witness failed'
            (folder/'exact-rechecks.json').write_text(json.dumps(checks,indent=2))
            result.update(status='FINITE_REPAIRED_NOT_CERTIFIED',exact_rechecks=len(checks))
            (folder/'results.json').write_text(json.dumps(result,indent=2))
            (out/'status.json').write_text(json.dumps(dict(status=result['status'],step=step,mass=str(mass),latest=str(folder.resolve())),indent=2))
            print(json.dumps(dict(status='READY_FOR_FULL_VERIFICATION',source=str(folder))),flush=True)
            if mass<=target:return
        if step==rounds:return
        density=np.vstack([rects,chosen]);dw=np.r_[w[:r],w[r+p:]]
        # The pricing oracle only proposes density columns; its dual is from
        # the full mixed LP. Existing point columns remain in every re-solve.
        master=SimpleNamespace(L=L,B=B,rectangles=density,poses=poses[ids],rect_cols=np.arange(len(density)),rect_keys={rectangle_key(q,L) for q in density},atoms=[])
        solution=SimpleNamespace(weights=dw,dual=pricing_dual(fit.ineqlin.marginals))
        proposals,report=propose_edges(master,solution,max_columns=64,seed_count=96,local_starts=12,max_evaluations=180,min_side=.0001)
        (folder/'pricing.json').write_text(json.dumps(dict(report=report,proposals=proposals),indent=2));print(json.dumps(report),flush=True)
        if not proposals:raise RuntimeError('Heuristic pricing found no columns; not a proof of impossibility')
        added=np.array([q['rectangle'] for q in proposals]);aa=np.hstack([aa,Geometry(L,B,added).matrix(poses[ids])]);chosen=np.vstack([chosen,added])

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--rounds',type=int,default=4);p.add_argument('--target-mass',type=F,default=F('20.999'));a=p.parse_args();run(a.source,a.out,a.rounds,a.target_mass)
