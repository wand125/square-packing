"""Compare new density supports near exact holes on common cumulative rows."""
import json,argparse
from fractions import Fraction as F
from time import perf_counter
import numpy as np
from expanded_search_pilot import ROOT,load,Geometry,columns,capture,solve
from mixed_density_refit import export
from geometry import rectangle_key


def run(out_name='targeted-pricing',repair_rounds=5):
    start=perf_counter();root=ROOT/'n21';source=root/'exact-refit-5';out=source/out_name;out.mkdir(exist_ok=False)
    d=json.loads((root/'results.json').read_text());_,rects,saved,L,B,rhs,_=load(21);r=len(rects);p=d['point_columns'];rules=d['rules']
    for rule in rules:rule['sites']=[tuple(map(F,v)) for v in rule['sites']]
    ledger=json.loads((source/'cumulative-witnesses.json').read_text());fresh=json.loads((source/'fresh-separation.json').read_text())['witnesses'];z=np.load(source/'replay.npz')
    historical=np.clip(np.array([v['normalized_pose'] for v in ledger]),[-1,-1,0],[1,1,1]);new=np.clip(np.array([v['normalized_pose'] for v in fresh]),[-1,-1,0],[1,1,1]);allposes=np.vstack([saved,historical,new])
    ids=z['row_ids'].tolist()+list(range(len(saved)+len(ledger),len(allposes)))
    def baseblock(ps):
        pc,_,mapping=columns(ps,rules,L,B)
        return np.hstack([Geometry(L,B,rects).matrix(ps),pc]),mapping
    extra,mapping=baseblock(new);a=np.vstack([z['matrix'],extra]);base,bstat=solve(a,rhs);dual=-base.ineqlin.marginals
    # Search density supports at and near the newest exact-deficit centres.
    known={rectangle_key(row,L) for row in rects};candidates=[]
    for w in fresh:
        x,y,t=map(lambda k:float(F(w[k])),('cx','cy','t'));c=(1-t*t)/(1+t*t);s=2*t/(1+t*t)
        for u,v in [(0,0),(.35,0),(-.35,0),(0,.35),(0,-.35),(.35,.35),(-.35,.35),(.35,-.35),(-.35,-.35)]:
            cx=x+c*u-s*v;cy=y+s*u+c*v
            for hx,hy in [(.01,.01),(.04,.04),(.125,.125),(.35,.35),(.02,.20),(.20,.02)]:
                row=[max(.0001,cx-hx),max(.0001,cy-hy),min(L-.0001,cx+hx),min(L-.0001,cy+hy)]
                if row[2]<=row[0] or row[3]<=row[1]:continue
                key=rectangle_key(row,L)
                if key not in known:known.add(key);candidates.append(row)
    cand=np.array(candidates);ca=Geometry(L,B,cand).matrix(allposes[ids]);loads=ca.T@dual
    selected=[int(i) for i in np.argsort(-loads) if loads[i]>1+1e-5][:16]
    chosen=cand[selected];aa=np.hstack([a,ca[:,selected]])
    records=[];weights={};coverages={}
    def audit(w):
        oldids=np.flatnonzero(w[:r]>0);neww=w[r+p:];newids=np.flatnonzero(neww>0)
        densities=np.vstack([rects[oldids],chosen[newids]]) if len(newids) else rects[oldids]
        dw=np.r_[w[oldids],neww[newids]];activep=np.flatnonzero(w[r:r+p]>0)
        unique=sorted({i for j in activep for i in mapping['point_orbits'][j]});index={i:j for j,i in enumerate(unique)};values=[]
        for lo in range(0,len(allposes),1024):
            ps=allposes[lo:lo+1024];v=Geometry(L,B,densities).matrix(ps)@dw
            if unique:
                hits=capture(ps,L,B,np.array([mapping['points'][i] for i in unique],float))
                for j in activep:v+=w[r+j]*hits[:,[index[i] for i in mapping['point_orbits'][j]]].mean(axis=1)
            values.extend(v)
        return np.array(values)
    for iteration in range(repair_rounds):
        row=dict(iteration=iteration,rows=len(aa),models={});bad=set()
        for name,end in [('fixed_mixed',r+p),('added_density',aa.shape[1])]:
            fit,stat=solve(aa[:,:end],rhs);w=fit.x;v=audit(w)
            violations=np.flatnonzero(v<rhs-1e-8);bad.update(violations.tolist())
            stat.update(full_minimum=float(min(v)),full_violations=len(violations),deficit_sum=float(np.maximum(rhs-v,0).sum()),new_density_mass=float(sum(w[r+p:])))
            row['models'][name]=stat;weights[name]=w;coverages[name]=v
        records.append(row);print(json.dumps(row),flush=True)
        missing=sorted(bad-set(ids))
        if iteration==repair_rounds-1 or not missing:break
        more,_=baseblock(allposes[missing]);aa=np.vstack([aa,np.hstack([more,Geometry(L,B,chosen).matrix(allposes[missing])])]);ids+=missing
    # Reorder support columns for the existing rational mixed-candidate exporter.
    w=weights['added_density'];ordered=np.r_[w[:r],w[r+p:],w[r:r+p]]
    export(out/'fixed-candidate.json',d,rects,weights['fixed_mixed'],mapping)
    candidate=export(out/'mixed-candidate.json',d,np.vstack([rects,chosen]),ordered,mapping)
    np.savez_compressed(out/'replay.npz',matrix=aa,row_ids=ids,selected_rectangles=chosen,**{'weights_'+k:v for k,v in weights.items()},**{'coverage_'+k:v for k,v in coverages.items()})
    result=dict(candidate_count=len(cand),selected_count=len(chosen),selected_loads=[float(loads[i]) for i in selected],candidate_rectangles=candidates,selected_indices=selected,records=records,seconds=perf_counter()-start,scope='Numerical pricing and finite common-row repair; no global proof. All original supports retained.')
    (out/'results.json').write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items() if k not in ('records','candidate_rectangles')}),flush=True)
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--output-subdir',default='targeted-pricing');args=ap.parse_args();run(args.output_subdir)
