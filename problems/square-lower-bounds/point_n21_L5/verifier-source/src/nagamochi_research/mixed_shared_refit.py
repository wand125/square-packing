"""Repair both fixed support models on one shared exact-deficit pool.

All prior LP rows/supports are retained; every saved pose is re-audited.
Numerical finite feasibility is followed by rational replay, not certification.
"""
import json, hashlib, argparse
from fractions import Fraction as F
from pathlib import Path
from time import perf_counter
import numpy as np
from expanded_search_pilot import ROOT,load,Geometry,columns,capture,solve
from mixed_density_refit import export
from mixed_density_check import expand,evaluate


def run(source=None,pool_path=None,out=None):
    started=perf_counter();root=ROOT/'n21';previous=root/'exact-refit-5';source=Path(source) if source else previous/'targeted-pricing-polished'
    out=Path(out) if out else root/'shared-net-refit-1';out.mkdir(exist_ok=False)
    pool_path=Path(pool_path) if pool_path else Path('runs/mixed_rotated_full_20260926/shared-repair-pool.json');pool=json.loads(pool_path.read_text())['witnesses']
    models={name:expand(json.loads((source/file).read_text())) for name,file in [('fixed_mixed','fixed-candidate.json'),('added_density','mixed-candidate.json')]}
    for w in pool:
        for name,m in models.items():
            checked=evaluate(m,F(w['cx']),F(w['cy']),F(w['t']))
            assert checked==w['evaluations'][name]
    d=json.loads((root/'results.json').read_text());_,rects,saved,L,B,rhs,_=load(21);r=len(rects);p=d['point_columns'];rules=d['rules']
    for rule in rules:rule['sites']=[tuple(map(F,v)) for v in rule['sites']]
    ledger=json.loads((source/'cumulative-witnesses.json').read_text()) if (source/'cumulative-witnesses.json').exists() else json.loads((previous/'cumulative-witnesses.json').read_text())+json.loads((previous/'fresh-separation.json').read_text())['witnesses']
    def poses(ws):
        a=np.array([w['normalized_pose'] for w in ws]);b=np.clip(a,[-1,-1,0],[1,1,1]);assert np.max(abs(a-b))<1e-10;return b
    oldposes=np.vstack([saved,poses(ledger)]);allposes=np.vstack([oldposes,poses(pool)])
    with np.load(source/'replay.npz') as z:
        chosen=z['selected_rectangles'].copy();aa=z['matrix'].copy();ids=z['row_ids'].tolist()
        if 'poses' in z:assert np.array_equal(z['poses'],oldposes)
    assert aa.shape==(len(ids),r+p+len(chosen)) and max(ids)<len(oldposes)
    def block(ps):
        pc,_,mapping=columns(ps,rules,L,B)
        return np.hstack([Geometry(L,B,rects).matrix(ps),pc,Geometry(L,B,chosen).matrix(ps)]),mapping
    more,mapping=block(poses(pool));aa=np.vstack([aa,more]);ids+=list(range(len(oldposes),len(allposes)))
    def audit(w):
        oldids=np.flatnonzero(w[:r]>0);nw=w[r+p:];newids=np.flatnonzero(nw>0)
        densities=np.vstack([rects[oldids],chosen[newids]]) if len(newids) else rects[oldids]
        dw=np.r_[w[oldids],nw[newids]];activep=np.flatnonzero(w[r:r+p]>0)
        unique=sorted({i for j in activep for i in mapping['point_orbits'][j]});index={i:j for j,i in enumerate(unique)};values=[]
        for lo in range(0,len(allposes),1024):
            ps=allposes[lo:lo+1024];v=Geometry(L,B,densities).matrix(ps)@dw
            if unique:
                hits=capture(ps,L,B,np.array([mapping['points'][i] for i in unique],float))
                for j in activep:v+=w[r+j]*hits[:,[index[i] for i in mapping['point_orbits'][j]]].mean(axis=1)
            values.extend(v)
        return np.array(values)
    records=[];weights={};coverages={}
    for iteration in range(6):
        record=dict(iteration=iteration,rows=len(aa),models={});bad=set()
        for name,end in [('fixed_mixed',r+p),('added_density',r+p+len(chosen))]:
            fit,stat=solve(aa[:,:end],rhs);w=fit.x;v=audit(w);violations=np.flatnonzero(v<rhs-1e-8);bad.update(violations.tolist())
            stat.update(full_minimum=float(v.min()),full_violations=len(violations),point_mass=float(sum(w[r:r+p])),new_density_mass=float(sum(w[r+p:])))
            record['models'][name]=stat;weights[name]=w;coverages[name]=v
        records.append(record);print(json.dumps(record),flush=True)
        missing=sorted(bad-set(ids))
        if not missing or iteration==5:break
        more,_=block(allposes[missing]);aa=np.vstack([aa,more]);ids+=missing
    allw=ledger+pool;rechecks={}
    for name,file in [('fixed_mixed','fixed-candidate.json'),('added_density','mixed-candidate.json')]:
        w=weights[name]
        rr=rects if name=='fixed_mixed' else np.vstack([rects,chosen]);ww=w if name=='fixed_mixed' else np.r_[w[:r],w[r+p:],w[r:r+p]]
        model=expand(export(out/file,d,rr,ww,mapping))
        rechecks[name]=[evaluate(model,F(q['cx']),F(q['cy']),F(q['t'])) for q in allw]
    np.savez_compressed(out/'replay.npz',matrix=aa,row_ids=ids,selected_rectangles=chosen,poses=allposes,**{'weights_'+k:v for k,v in weights.items()},**{'coverage_'+k:v for k,v in coverages.items()})
    (out/'cumulative-witnesses.json').write_text(json.dumps(allw,indent=2))
    ok=all(v['full_violations']==0 for v in records[-1]['models'].values()) and all(F(q['score'])>=F(10001,10000) for checks in rechecks.values() for q in checks)
    result=dict(status='FINITE_REPAIRED_NOT_CERTIFIED' if ok else 'REPAIR_INCOMPLETE',source=str(source),pool_sha256=hashlib.sha256(pool_path.read_bytes()).hexdigest(),total_poses=len(allposes),prior_exact_count=len(ledger),new_exact_count=len(pool),records=records,exact_rechecks=rechecks,seconds=perf_counter()-started)
    (out/'results.json').write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items() if k not in ('records','exact_rechecks')}),flush=True)
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--source');ap.add_argument('--pool');ap.add_argument('--out');a=ap.parse_args();run(a.source,a.pool,a.out)
