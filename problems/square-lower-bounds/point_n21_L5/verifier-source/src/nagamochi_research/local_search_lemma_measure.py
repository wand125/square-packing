"""Local numerical separation with exact rational physical-pose replay."""
import argparse,json
from pathlib import Path
from fractions import Fraction as F
from scipy.optimize import minimize
from repair_lemma_measure import np,coefficients,expand_primitives,expand,evaluate


def physical(L,z):
    u,v,t=z;a=abs(t);h=(1-a*a+2*a)/(2*(1+a*a))
    return h+(L-2*h)*u,h+(L-2*h)*v,t


def run(base,experiment,out):
    d=json.loads(base.read_text());model=expand(json.loads((experiment/'candidate.json').read_text()));L=float(model[0]);B=model[1]
    primitives=[dict(kind='rectangle',geometry=r['rectangle']) for r in d['rectangles']]+[dict(kind='point',geometry=r['point']) for r in d['points']]
    ex=expand_primitives(primitives,model[0]);w=np.load(experiment/'state.npz')['weights'];report=json.loads((experiment/'results.json').read_text())
    def objective(z):return float((coefficients([physical(L,z)],B,ex,model[0])@w)[0])
    records=[];seen=set()
    for rec in report['exact_held_checks'][:12]:
        x,y,t=map(lambda k:float(F(rec[k])),('cx','cy','t'));a=abs(t);h=(1-a*a+2*a)/(2*(1+a*a));start=[(x-h)/(L-2*h),(y-h)/(L-2*h),t]
        fit=minimize(objective,start,method='Nelder-Mead',bounds=[(0,1),(0,1),(-.414,.414)],options={'maxiter':120,'xatol':1e-8,'fatol':1e-9})
        z=tuple(F(float(v)).limit_denominator(10**9) for v in fit.x);pose=physical(model[0],z)
        if pose in seen:continue
        seen.add(pose);checked=evaluate(model,*pose)
        # physical() maps the unit-square centre domain, not the smaller core domain.
        a=abs(pose[2]);radius=(1-a*a+2*a)/(2*(1+a*a))
        assert all(radius<=p<=model[0]-radius for p in pose[:2])
        checked.update(numeric_score=float(fit.fun),evaluations=int(fit.nfev),converged=bool(fit.success))
        records.append(checked);print(dict(score=float(F(checked['score'])),evaluations=int(fit.nfev)),flush=True)
    result=dict(status='EXACT_LOCAL_COUNTEREXAMPLES',candidate_digest=model[-1],records=records,general_packing_exclusion=False)
    out.write_text(json.dumps(result,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for k in ('base','experiment','out'):p.add_argument(k,type=Path)
    a=p.parse_args();run(a.base,a.experiment,a.out)
