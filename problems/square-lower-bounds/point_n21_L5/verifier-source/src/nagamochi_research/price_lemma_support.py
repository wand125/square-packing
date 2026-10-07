"""Price new D4 point/rectangle columns against a replayed rational dual."""
import argparse,json
from pathlib import Path
from fractions import Fraction as F
from scipy.optimize import linprog
from scipy.sparse import csr_matrix
from repair_lemma_measure import np,expand,expand_primitives,coefficients,export,poses,evaluate
from fixed_support_dual_audit import exact_columns
from local_exchange_lemma_measure import separate


def run(base,source,out,seed=9272000,resolution=128,working=False,rectangle_divisors=(2000,)):
    if resolution<2 or resolution%2:raise ValueError("Even positive grid resolution required")
    rectangle_divisors=tuple(dict.fromkeys(rectangle_divisors))
    if not rectangle_divisors or any(not isinstance(v,int) or v<=0 for v in rectangle_divisors):
        raise ValueError('Positive integer rectangle half-width divisors required')
    out.mkdir(parents=True,exist_ok=False);d=json.loads(base.read_text());L=F(d['L']);B=F(999999,1000000)
    cert=json.loads((source/'fixed-support-dual.json').read_text());dual_poses=[tuple(map(F,p)) for p in cert['poses']]
    scale=F(next(r['scale'] for r in cert['records'] if F(r['B'])==B));dual=[F(x)/scale for x in cert['unscaled_weights']]
    grid=[(L*i/resolution,L*j/resolution) for i in range(resolution//2+1) for j in range(i,resolution//2+1)]
    pg=[dict(kind='point',geometry=list(map(str,p))) for p in grid]
    loads=np.array(list(map(float,dual)))@coefficients(dual_poses,B,expand_primitives(pg,L),L)
    selected=[]
    for i in np.argsort(-loads):
        p=grid[int(i)]
        if loads[i]<=1.0001:break
        if any(sum((a-b)**2 for a,b in zip(p,q))<(L/64)**2 for q in selected):continue
        selected.append(p)
        if len(selected)==16:break
    additions=[];priced=[]
    for p in selected:
        additions.append(dict(kind='point',geometry=list(map(str,p))))
        x,y=p
        for divisor in rectangle_divisors:
            h=L/divisor
            if 0<x-h<x+h<L and 0<y-h<y+h<L:additions.append(dict(kind='rectangle',geometry=list(map(str,[x-h,y-h,x+h,y+h]))))
    for primitive in additions:
        tiny=dict(L=str(L),rectangles=[],points=[])
        tiny['rectangles' if primitive['kind']=='rectangle' else 'points']=[{('rectangle' if primitive['kind']=='rectangle' else 'point'):primitive['geometry']}]
        load=sum(w*exact_columns(tiny,p,B)[0] for w,p in zip(dual,dual_poses))
        priced.append(dict(**primitive,dual_load=str(load),improves_dual=load>1));print('PRICE',primitive['kind'],float(load),flush=True)
    (out/'pricing.json').write_text(json.dumps(dict(source_dual=str(source/'fixed-support-dual.json'),grid=len(grid),resolution=resolution,rectangle_divisors=rectangle_divisors,columns=priced),indent=2))
    saved=np.load(source/'state.npz')
    old=json.loads(str(saved['primitives_json'])) if 'primitives_json' in saved else [dict(kind='rectangle',geometry=r['rectangle']) for r in d['rectangles']]+[dict(kind='point',geometry=r['point']) for r in d['points']]
    p=json.loads((source/'poses.json').read_text());train=[tuple(map(F,x)) for x in p['train']];A=saved['matrix'];records=[]
    from pending_lemma_poses import collect,validate
    pending=validate(collect(p,json.loads((source/'results.json').read_text()),L),L)
    (out/'pending-poses.json').write_text(json.dumps(dict(L=str(L),B=str(B),source=str(source),poses=[list(map(str,q)) for q in pending]),indent=2))
    if A.shape!=(len(train),len(old)):raise ValueError('Saved basis/matrix mismatch')
    train_set=set(train)
    held=[p for p in poses(L,4096,seed) if p not in train_set]
    if not held:raise ValueError("Validation set overlaps training")
    for mode in ['points','points_rectangles']:
        added=[p for p in priced if p['improves_dual'] and (mode!='points' or p['kind']=='point')]
        primitives=old+added;matrix=np.hstack([A,coefficients(train,B,expand_primitives(added,L),L)])
        lp_check=None
        if working:
            from working_measure_lp import solve
            raw,lp_check=solve(matrix,np.concatenate([saved['weights'],np.zeros(len(added))]));mass=float(sum(raw))
        else:
            fit=linprog(np.ones(matrix.shape[1]),A_ub=-csr_matrix(matrix),b_ub=-np.ones(len(matrix)),bounds=(0,None),method='highs',options={'time_limit':45})
            if not fit.success:raise RuntimeError(fit.message)
            raw=fit.x;mass=float(fit.fun)
        w=raw*float(F(d['total_mass']))/sum(raw);candidate=export(d,primitives,w,B);model=expand(candidate)
        (out/f'{mode}-candidate.json').write_text(json.dumps(candidate,indent=2));ex=expand_primitives(primitives,L);v=coefficients(held,B,ex,L)@w
        local=separate(model,ex,w,held,v);checks=[evaluate(model,*held[int(i)]) for i in np.argsort(v)[:8]]
        rec=dict(mode=mode,held_seed=seed,held_count=len(held),added=len(added),lp_mass=mass,training_minimum=float(min(matrix@w)),held_minimum=float(min(v)),held_below_one=int(sum(v<1)),local_minimum=str(min(F(x['score']) for x in local)),exact_held_checks=checks,local_witnesses=local,general_packing_exclusion=False)
        if lp_check is not None:rec['working_lp_check']=lp_check
        records.append(rec);(out/'results.json').write_text(json.dumps(records,indent=2));np.savez_compressed(out/f'{mode}-state.npz',weights=w,matrix=matrix,primitives_json=json.dumps(primitives))
        print({k:v for k,v in rec.items() if k not in ('local_witnesses','exact_held_checks','working_lp_check')},flush=True)
    (out/'poses.json').write_text(json.dumps(dict(train=[list(map(str,p)) for p in train],held=[list(map(str,p)) for p in held]),indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for k in ('base','source','out'):p.add_argument(k,type=Path)
    p.add_argument('--seed',type=int,default=9272000);p.add_argument('--grid',type=int,default=128);p.add_argument('--working',action='store_true')
    p.add_argument('--rectangle-divisors',type=int,nargs='+',default=[2000]);a=p.parse_args();run(a.base,a.source,a.out,a.seed,a.grid,a.working,a.rectangle_divisors)
