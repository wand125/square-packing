"""One common violated-row repair, then recheck every saved pose."""
import argparse,json
from time import perf_counter
import numpy as np
from expanded_search_pilot import ROOT,load,Geometry,columns,solve,capture
from fractions import Fraction as F

def run(n, previous=None, output_name="repair"):
    start=perf_counter();out=ROOT/f'n{n}';d=json.loads((out/'results.json').read_text());z=np.load(out/(previous+'-replay.npz' if previous else 'replay.npz'))
    path,rects,allposes,L,B,rhs,_=load(n);r=len(rects);p=d['point_columns']
    bad=set()
    for name in ('rectangles','plus_points'):
        v=z['coverage_'+name] if previous else np.load(out/('saved_coverage_'+name+'.npy'))
        bad.update(np.flatnonzero(v<rhs-1e-7).tolist())
    extra=np.array(sorted(bad-set(z['row_ids'].tolist())),int)
    rules=d['rules']
    for rule in rules:rule['sites']=[tuple(map(F,q)) for q in rule['sites']]
    pc,rc,mapping=columns(allposes[extra],rules,L,B)
    a=np.vstack([z['matrix'],np.hstack([Geometry(L,B,rects).matrix(allposes[extra]),pc,rc])])
    result=dict(n=n,added_rows=len(extra),rows=len(a),models={});saved={}
    for name,end in [('rectangles',r),('plus_points',r+p),('plus_rules',a.shape[1])]:
        fit,stat=solve(a[:,:end],rhs);w=fit.x;active=np.flatnonzero(w[:r]>0)
        values=[]
        for lo in range(0,len(allposes),1024):
            batch=allposes[lo:lo+1024];v=Geometry(L,B,rects[active]).matrix(batch)@w[active]
            if end>r:
                # Full point/rule blocks also exercise rules after the repaired LP.
                pc,rc,_=columns(batch,rules,L,B)
                v+=pc@w[r:r+p]
                if end>r+p:v+=rc@w[r+p:]
            values.extend(v)
        values=np.array(values);deficit=np.maximum(rhs-values,0)
        stat.update(full_saved_minimum=float(min(values)),full_saved_deficit_sum=float(sum(deficit)),full_saved_violations_1e7=int(sum(deficit>1e-7)),new_point_mass=float(sum(w[r:min(end,r+p)])),new_rule_mass=float(sum(w[r+p:])))
        result['models'][name]=stat;saved['weights_'+name]=w;saved['coverage_'+name]=values
        print(json.dumps(dict(n=n,model=name,**stat)),flush=True)
    result.update(seconds=perf_counter()-start,scope='One common row-repair on frozen supports/rules. Full saved-pose audit is numerical and finite, not all-domain verification.')
    np.savez_compressed(out/(output_name+'-replay.npz'),matrix=a,rhs=rhs,row_ids=np.r_[z['row_ids'],extra],**saved)
    (out/(output_name+'.json')).write_text(json.dumps(result,indent=2));print(json.dumps(dict(n=n,seconds=result['seconds'],added_rows=len(extra))),flush=True)
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--n',type=int,required=True);ap.add_argument('--previous');ap.add_argument('--output-name',default='repair');args=ap.parse_args();run(args.n,args.previous,args.output_name)
