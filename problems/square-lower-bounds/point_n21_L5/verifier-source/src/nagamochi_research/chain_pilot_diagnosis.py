"""Exact sampled scores and one-level subdivision of the fixed PL36 pilot.
Samples do not certify a region. Only bounds over all children certify it.
"""
import argparse,json,hashlib
from fractions import Fraction as F
from itertools import product
from pathlib import Path
from mixed_density_check import expand,evaluate,pose_lower_bound
from score import square

def run(candidate,pilot,out):
    if out.exists():raise FileExistsError(out)
    sha=hashlib.sha256(candidate.read_bytes()).hexdigest()
    prior=json.loads(pilot.read_text())
    if sha!=prior['candidate_sha256']:raise ValueError('Candidate differs from pilot')
    model=expand(json.loads(candidate.read_text()));L=model[0];rows=[]
    for row in prior['records']:
        box=list(map(F,row['box']));axes=[(box[i],(box[i]+box[i+1])/2,box[i+1]) for i in (0,2,4)]
        samples=[]
        for x,y,t in product(*axes):
            if all(0<=u<=L and 0<=v<=L for u,v in square(x,y,F(1),t)):
                samples.append(evaluate(model,x,y,t))
        child_bounds=[]
        for halves in product((0,1),repeat=3):
            child=[v for axis,h in zip(axes,halves) for v in (axis[h],axis[h+1])]
            child_bounds.append(dict(box=list(map(str,child)),lower=str(pose_lower_bound(model,*child))))
        minimum=min(samples,key=lambda r:F(r['score'])) if samples else None
        lower=max(F(row['chain_lower']),min(F(c['lower']) for c in child_bounds))
        record=dict(box=row['box'],pilot_lower=row['chain_lower'],subdivision_lower=str(lower),children=child_bounds,
                    admissible_samples=len(samples),sample_min=minimum,strict_counterexamples=[r for r in samples if F(r['score'])<1],
                    entire_box_certified=lower>=1)
        rows.append(record)
        print('DIAG',row['box'],'bounds',float(F(row['chain_lower'])),float(lower),'sample',float(F(minimum['score'])) if minimum else None,flush=True)
    out.write_text(json.dumps(dict(candidate_sha256=sha,records=rows,general_packing_exclusion=False),indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('candidate',type=Path);p.add_argument('pilot',type=Path);p.add_argument('out',type=Path);a=p.parse_args();run(a.candidate,a.pilot,a.out)
