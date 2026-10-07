"""Finite constraint exchange with disjoint fresh validation seeds."""
import argparse,json
from pathlib import Path
from fractions import Fraction as F
from repair_lemma_measure import np,coefficients,expand_primitives,poses,export,bounded_weights,expand,evaluate


def run(candidate,prior,out,rounds=4):
    out.mkdir(parents=True,exist_ok=False);d=json.loads(candidate.read_text());base=expand(d);L=base[0];B=F(999999,1000000)
    primitives=[dict(kind='rectangle',geometry=r['rectangle']) for r in d['rectangles']]+[dict(kind='point',geometry=r['point']) for r in d['points']]
    w0=np.array([float(F(r['mass'])) for r in d['rectangles']+d['points']]);expanded=expand_primitives(primitives,L)
    p=json.loads((prior/'poses.json').read_text());train=[tuple(map(F,x)) for x in p['train']+p['held']]
    # The previous held-out set is now explicitly training data.
    train=list(dict.fromkeys(train));keys=set(train);A=coefficients(train,B,expanded,L);records=[]
    for iteration in range(rounds):
        w,minimum=bounded_weights(A,w0,0.,5.)
        scan=poses(L,2048,9271300+iteration);H=coefficients(scan,B,expanded,L);v=H@w
        record=dict(iteration=iteration,training_rows=len(train),training_minimum=minimum,
                    scan_seed=9271300+iteration,scan_minimum=float(min(v)),scan_below_one=int(sum(v<1)))
        new=[]
        if iteration+1<rounds:
            for i in np.argsort(v):
                if v[i]>=minimum-1e-8:break
                pose=scan[int(i)]
                if pose not in keys:keys.add(pose);new.append(pose)
                if len(new)>=128:break
        record['added']=len(new);records.append(record)
        (out/'progress.json').write_text(json.dumps(records,indent=2));print(record,flush=True)
        if new:A=np.vstack([A,coefficients(new,B,expanded,L)]);train.extend(new)
    candidate_data=export(d,primitives,w,B);model=expand(candidate_data)
    (out/'candidate.json').write_text(json.dumps(candidate_data,indent=2))
    held=poses(L,4096,9271400);H=coefficients(held,B,expanded,L);values=H@w;original=H@w0
    checks=[evaluate(model,*held[int(i)]) for i in np.argsort(values)[:16]]
    known=[tuple(map(F,x)) for x in p['train'][:220]]
    exact_known=[evaluate(model,*x) for x in known]
    result=dict(status='FINITE_EXCHANGE_NOT_CERTIFIED',records=records,final_training_rows=len(train),
                final_seed=9271400,final_held_minimum=float(min(values)),original_held_minimum=float(min(original)),
                final_held_below_one=int(sum(values<1)),exact_held_checks=checks,
                exact_known_minimum=str(min(F(x['score']) for x in exact_known)),mass=str(model[4]),general_packing_exclusion=False)
    (out/'results.json').write_text(json.dumps(result,indent=2))
    (out/'poses.json').write_text(json.dumps(dict(train=[list(map(str,p)) for p in train],held=[list(map(str,p)) for p in held]),indent=2))
    np.savez_compressed(out/'state.npz',weights=w,reference_weights=w0,matrix=A)
    print({k:v for k,v in result.items() if k not in ('records','exact_held_checks')},flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for name in ('candidate','prior','out'):p.add_argument(name,type=Path)
    a=p.parse_args();run(a.candidate,a.prior,a.out)
