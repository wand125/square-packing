"""Broaden local counterexample search on an unchanged saved measure."""
import argparse,json,hashlib,time
from pathlib import Path
from fractions import Fraction as F
from repair_lemma_measure import np,expand,expand_primitives,coefficients
from local_exchange_lemma_measure import separate


def run(prior,out,starts=64):
    if starts<1:raise ValueError('Positive start count required')
    if out.exists():raise FileExistsError(out)
    candidate=prior/'candidate.json';model=expand(json.loads(candidate.read_text()))
    z=np.load(prior/'state.npz');primitives=json.loads(str(z['primitives_json']))
    ex=expand_primitives(primitives,model[0]);held=[tuple(map(F,p)) for p in json.loads((prior/'poses.json').read_text())['held']]
    values=coefficients(held,model[1],ex,model[0])@z['weights']
    started=time.perf_counter();rows=separate(model,ex,z['weights'],held,values,starts=starts)
    before=json.loads((prior/'results.json').read_text())
    report=dict(status='FINITE_MULTISTART_EXACT_WITNESSES',candidate_sha256=hashlib.sha256(candidate.read_bytes()).hexdigest(),
                starts=len(rows),seconds=time.perf_counter()-started,held_count=len(held),held_seed=before['final_seed'],
                source_local_minimum=before['local_minimum'],exact_minimum=str(min(F(r['score']) for r in rows)),
                below_one=sum(F(r['score'])<1 for r in rows),local_witnesses=rows,general_packing_exclusion=False)
    out.write_text(json.dumps(report,indent=2));print({k:v for k,v in report.items() if k!='local_witnesses'},flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('prior',type=Path);p.add_argument('out',type=Path);p.add_argument('--starts',type=int,default=64)
    a=p.parse_args();run(a.prior,a.out,a.starts)
