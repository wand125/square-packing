"""Resume local exchange while preserving every saved priced basis column."""
import argparse,json,hashlib,time
from pathlib import Path
from fractions import Fraction as F
from repair_lemma_measure import np,expand_primitives,coefficients,export,poses,expand,evaluate
from local_exchange_lemma_measure import unrestricted_weights,separate


def informative_local(row, minimum):
    score=F(row['score']);gamma=F(str(minimum))
    # Numerical row generation only. Keep genuine sub-unit violations even
    # near gamma=1; above one, ignore noise at the same scale as scan cuts.
    return score<min(F(1),gamma) or score<gamma-F(1,10**8)


def run(base,prior,out,mode='points',seed=9272100,rounds=4,extra_witnesses=None,lp_method='highs',local_starts=8,local_bins=0):
    if rounds<1:raise ValueError('Positive rounds required')
    if local_starts<1 or local_bins<0 or (local_bins and local_starts%local_bins):
        raise ValueError('Positive starts divisible by the nonnegative angle-bin count required')
    out.mkdir(parents=True,exist_ok=False);data=json.loads(base.read_text());L=F(data['L']);B=F(999999,1000000);M=F(data['total_mass'])
    state=prior/'state.npz' if (prior/'state.npz').exists() else prior/f'{mode}-state.npz';z=np.load(state);primitives=json.loads(str(z['primitives_json']));ex=expand_primitives(primitives,L)
    p=json.loads((prior/'poses.json').read_text());old=[tuple(map(F,x)) for x in p['train']];A=z['matrix']
    if A.shape!=(len(old),len(primitives)):raise ValueError('Saved matrix/basis/pose mismatch')
    ids=sorted({0,len(old)//2,len(old)-1})
    if np.max(np.abs(coefficients([old[i] for i in ids],B,ex,L)-A[ids]))>1e-8:raise ValueError('Saved matrix order mismatch')
    source_results=json.loads((prior/'results.json').read_text());record=source_results if isinstance(source_results,dict) else next(r for r in source_results if r['mode']==mode)
    extra=[tuple(map(F,x)) for x in p['held']]+[tuple(F(x[k]) for k in ('cx','cy','t')) for x in record['local_witnesses']]
    inherited_pending=0
    if (prior/'pending-poses.json').exists():
        from pending_lemma_poses import validate
        bundle=json.loads((prior/'pending-poses.json').read_text())
        if F(bundle['L'])!=L or F(bundle['B'])!=B:raise ValueError('Pending pose domain mismatch')
        pending=validate([tuple(map(F,q)) for q in bundle['poses']],L)
        extra.extend(pending);inherited_pending=len(pending)
    recovered_last_local=0;recovered_last_scan=0
    if record.get('records'):
        last=record['records'][-1]
        pending_local=[tuple(F(x[k]) for k in ('cx','cy','t')) for x in last['local_witnesses']]
        extra.extend(pending_local);recovered_last_local=len(pending_local)
        # The last loop iteration does not append its scan cuts before saving.
        # Reconstruct that deterministic scan, including legacy outputs which
        # predate scan_count (this runner used 2048 throughout).
        pending_scan=poses(L,last.get('scan_count',2048),last['scan_seed'])
        pending_values=coefficients(pending_scan,B,ex,L)@z['weights']
        pending_ids=[int(i) for i in np.argsort(pending_values)[:128]
                     if pending_values[i]<last['training_minimum']-1e-8]
        extra.extend(pending_scan[i] for i in pending_ids);recovered_last_scan=len(pending_ids)
    if extra_witnesses is not None:
        witness_report=json.loads(extra_witnesses.read_text())
        candidate_path=prior/'candidate.json' if (prior/'candidate.json').exists() else prior/f'{mode}-candidate.json'
        if witness_report['candidate_sha256']!=hashlib.sha256(candidate_path.read_bytes()).hexdigest():
            raise ValueError('Extra witnesses belong to another candidate')
        prior_model=expand(json.loads(candidate_path.read_text()))
        for row in witness_report['local_witnesses']:
            pose=tuple(F(row[k]) for k in ('cx','cy','t'));t=abs(pose[2]);h=(1-t*t+2*t)/(2*(1+t*t))
            if t>1 or not all(h<=v<=L-h for v in pose[:2]):raise ValueError('Nonphysical extra witness')
            if F(evaluate(prior_model,*pose)['score'])!=F(row['score']):raise ValueError('Wrong extra witness score')
            extra.append(pose)
    keys=set(old);new=[]
    for pose in extra:
        if pose not in keys:keys.add(pose);new.append(pose)
    train=old+new;A=np.vstack([A,coefficients(new,B,ex,L)]);reference=np.full(len(primitives),float(M)/len(primitives));records=[]
    for iteration in range(rounds):
        started=time.perf_counter()
        lp_check=None
        reused=iteration>0 and records[-1]['added']==0
        if reused:
            lp_check=records[-1].get('working_lp_check')
        elif lp_method=='working-ipm':
            from working_measure_lp import solve
            raw,lp_check=solve(A,z['weights'] if iteration==0 else w)
            w=raw*float(M)/sum(raw);minimum=float(min(A@w))
        else:w,minimum=unrestricted_weights(A,reference,method=lp_method)
        lp_seconds=0. if reused else time.perf_counter()-started
        candidate=export(data,primitives,w,B);model=expand(candidate)
        scan=poses(L,2048,seed+iteration);v=coefficients(scan,B,ex,L)@w
        local_started=time.perf_counter()
        if local_bins:
            from stratified_lemma_probe import angle_starts
            selected,_=angle_starts(scan,v,bins=local_bins,per_bin=local_starts//local_bins)
            local=separate(model,ex,w,[scan[i] for i in selected],v[selected],starts=len(selected))
        else:local=separate(model,ex,w,scan,v,starts=local_starts)
        local_seconds=time.perf_counter()-local_started
        new=[]
        if iteration+1<rounds:
            options=[tuple(F(x[k]) for k in ('cx','cy','t')) for x in local if informative_local(x,minimum)]
            options += [scan[int(i)] for i in np.argsort(v)[:128] if v[i]<minimum-1e-8]
            for pose in options:
                if pose not in keys:keys.add(pose);new.append(pose)
        rec=dict(iteration=iteration,rows=len(train),columns=len(primitives),training_minimum=minimum,lp_seconds=lp_seconds,lp_reused=reused,
                 implied_minimum_mass=float(M)/minimum,scan_seed=seed+iteration,scan_count=len(scan),scan_minimum=float(min(v)),
                 scan_below_one=int(sum(v<1)),local_minimum=str(min(F(x['score']) for x in local)),local_witnesses=local,added=len(new))
        rec['local_tiny_skipped']=sum(F(x['score'])<F(str(minimum)) and not informative_local(x,minimum) for x in local)
        rec.update(local_starts=len(local),local_bins=local_bins,local_seconds=local_seconds)
        if lp_check is not None:rec['working_lp_check']=lp_check
        records.append(rec);(out/'progress.json').write_text(json.dumps(records,indent=2));print({k:v for k,v in rec.items() if k not in ('local_witnesses','local_minimum','working_lp_check')},flush=True)
        if new:A=np.vstack([A,coefficients(new,B,ex,L)]);train.extend(new)
    (out/'candidate.json').write_text(json.dumps(candidate,indent=2));held=poses(L,4096,seed+100);H=coefficients(held,B,ex,L);v=H@w;before=H@z['weights'];local=separate(model,ex,w,held,v)
    exact=[evaluate(model,*held[int(i)]) for i in np.argsort(v)[:16]]
    result=dict(status='FINITE_PRICED_BASIS_EXCHANGE_NOT_CERTIFIED',mode=mode,lp_method=lp_method,source_state_sha256=hashlib.sha256(state.read_bytes()).hexdigest(),records=records,
                recovered_last_local=recovered_last_local,recovered_last_scan=recovered_last_scan,
                inherited_pending=inherited_pending,local_starts=local_starts,local_bins=local_bins,
                final_seed=seed+100,held_minimum=float(min(v)),previous_candidate_held_minimum=float(min(before)),held_below_one=int(sum(v<1)),
                previous_candidate_held_below_one=int(sum(before<1)),exact_held_checks=exact,local_witnesses=local,
                local_minimum=str(min(F(x['score']) for x in local)),mass=str(model[4]),general_packing_exclusion=False)
    if extra_witnesses is not None:result['extra_witnesses_sha256']=hashlib.sha256(extra_witnesses.read_bytes()).hexdigest()
    (out/'results.json').write_text(json.dumps(result,indent=2));(out/'poses.json').write_text(json.dumps(dict(train=[list(map(str,p)) for p in train],held=[list(map(str,p)) for p in held]),indent=2))
    np.savez_compressed(out/'state.npz',weights=w,matrix=A,primitives_json=json.dumps(primitives))
    print({k:v for k,v in result.items() if k not in ('records','exact_held_checks','local_witnesses')},flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for k in ('base','prior','out'):p.add_argument(k,type=Path)
    p.add_argument('--mode',default='points');p.add_argument('--seed',type=int,default=9272100);p.add_argument('--rounds',type=int,default=4)
    p.add_argument('--extra-witnesses',type=Path);p.add_argument('--lp-method',choices=['highs','highs-ipm','highs-ds','working-ipm'],default='highs')
    p.add_argument('--local-starts',type=int,default=8);p.add_argument('--local-bins',type=int,default=0);a=p.parse_args()
    run(a.base,a.prior,a.out,a.mode,a.seed,a.rounds,a.extra_witnesses,a.lp_method,a.local_starts,a.local_bins)
