"""Exact finite pose samples for diagnosis, never a continuous lower bound."""
import argparse,json,hashlib
from pathlib import Path
from fractions import Fraction as F
from mixed_density_check import expand,evaluate
from mixed_net_audit import symmetry
from pose_symmetry import images


def run(candidate,source,out,threshold,method=None):
    model=expand(json.loads(candidate.read_text()));symmetry(model);q=json.loads(source.read_text())
    if q['digest']!=model[-1]:raise ValueError('Candidate mismatch')
    groups={}
    for p,r in q['leaves'].items():
        if r['kind']=='OUTSIDE' or F(r['lower'])>=threshold:continue
        if method and r.get('bound_method',q.get('bound_method'))!=method:continue
        box=tuple(map(F,r['box']));groups.setdefault(images(box,model[0])[0],[]).append(p)
    rows=[];empty_angles=0
    for box,paths in groups.items():
        x0,x1,y0,y1,a,b=box
        for t in sorted({a,(a+b)/2,b}):
            u=abs(t);h=(1-u*u+2*u)/(2*(1+u*u));xl=max(x0,h);xh=min(x1,model[0]-h);yl=max(y0,h);yh=min(y1,model[0]-h)
            if xl>xh or yl>yh:empty_angles+=1;continue
            centres={(xl,yl),(xl,yh),(xh,yl),(xh,yh),((xl+xh)/2,(yl+yh)/2)}
            for x,y in sorted(centres):
                rec=evaluate(model,x,y,t);rec.update(source_paths=paths,canonical_box=list(map(str,box)))
                rows.append(rec)
    result=dict(status='EXACT_FINITE_PHYSICAL_POSE_SAMPLES',source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                candidate_sha256=hashlib.sha256(candidate.read_bytes()).hexdigest(),groups=len(groups),empty_angle_sections=empty_angles,
                samples=rows,general_packing_exclusion=False,continuous_lower_bound=False)
    out.write_text(json.dumps(result,indent=2));print(dict(groups=len(groups),samples=len(rows),minimum=float(min(F(r['score']) for r in rows)),below_one=sum(F(r['score'])<1 for r in rows)),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for name in ('candidate','source','out'):p.add_argument(name,type=Path)
    p.add_argument('--threshold',type=F,required=True);p.add_argument('--method');a=p.parse_args()
    run(a.candidate,a.source,a.out,a.threshold,a.method)
