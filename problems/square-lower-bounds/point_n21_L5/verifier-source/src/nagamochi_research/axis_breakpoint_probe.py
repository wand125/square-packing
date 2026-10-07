"""Finite axis-aligned translation probe, with exact checked witnesses.

Rectangle overlap at t=0 is a product of one-dimensional overlaps. This
permits a dense translation grid without a pose-by-basis tensor. No claim
of an all-angle or continuous-domain certificate is made here.
"""
import argparse,json,hashlib,time
from pathlib import Path
from fractions import Fraction as F
from repair_lemma_measure import np,expand,evaluate


def grid(model):
    L,B,rects,points=model[:4];lo=F(1,2);hi=L/2
    knots={lo,hi}
    for r in rects:
        if r[4]:
            for x in r[:4]:
                knots.update(x+sign*B/2 for sign in (-1,1) if lo<=x+sign*B/2<=hi)
    for point,w in points:
        if w:
            for x in point:knots.update(x+sign*B/2 for sign in (-1,1) if lo<=x+sign*B/2<=hi)
    knots=sorted(knots);result=set(knots)
    for a,b in zip(knots,knots[1:]):
        eps=min(F(1,10**7),(b-a)/10000)
        result.update((a+eps,b-eps))
    return sorted(result),len(knots)


def scores(model,xs,ys):
    L,B,rects,points=model[:4];h=float(B)/2;x=np.array(xs,float);y=np.array(ys,float)
    r=np.array([list(map(float,q)) for q in rects if q[4]],float)
    if len(r):
        ox=np.maximum(0,np.minimum(x[:,None]+h,r[:,2])-np.maximum(x[:,None]-h,r[:,0]))
        oy=np.maximum(0,np.minimum(y[:,None]+h,r[:,3])-np.maximum(y[:,None]-h,r[:,1]))
        result=(ox*r[:,4])@oy.T
    else:result=np.zeros((len(x),len(y)))
    diff=np.zeros((len(x)+1,len(y)+1))
    for (px,py),w in points:
        i=np.searchsorted(x,float(px-B/2),side='left')
        j=np.searchsorted(x,float(px+B/2),side='right')
        k=np.searchsorted(y,float(py-B/2),side='left');ell=np.searchsorted(y,float(py+B/2),side='right')
        diff[i,k]+=float(w);diff[j,k]-=float(w);diff[i,ell]-=float(w);diff[j,ell]+=float(w)
    return result+diff.cumsum(axis=0).cumsum(axis=1)[:-1,:-1]


def run(prior,out,grid_source=None):
    if out.exists():raise FileExistsError(out)
    candidate=prior/'candidate.json';model=expand(json.loads(candidate.read_text()));started=time.perf_counter()
    source_model=expand(json.loads(grid_source.read_text())) if grid_source else model
    if source_model[:2]!=model[:2]:raise ValueError('Grid source domain mismatch')
    xs,knots=grid(source_model)
    if len(xs)>4000:raise ValueError('Grid exceeds diagnostic memory limit')
    values=scores(model,xs,xs);flat=values.ravel();ids=set(map(int,np.argpartition(flat,min(63,len(flat)-1))[:64]))
    bad=np.flatnonzero(flat<1);diverse=[];separation=float(model[0])/64
    for i in bad[np.argsort(flat[bad])]:
        point=(float(xs[int(i)//len(xs)]),float(xs[int(i)%len(xs)]))
        if any((point[0]-q[0])**2+(point[1]-q[1])**2<separation**2 for q in diverse):continue
        diverse.append(point);ids.add(int(i))
        if len(diverse)==64:break
    checks=[]
    for i in sorted(ids,key=lambda i:flat[i]):
        row=evaluate(model,xs[int(i)//len(xs)],xs[int(i)%len(xs)],F(0));row['numeric_score']=float(flat[i]);checks.append(row)
    report=dict(status='FINITE_AXIS_BREAKPOINT_PROBE',candidate_sha256=hashlib.sha256(candidate.read_bytes()).hexdigest(),
                domain='t=0, centres in [1/2,L/2]^2; finite breakpoint and one-sided probes',
                knots=knots,axis_samples=len(xs),poses=len(flat),seconds=time.perf_counter()-started,
                numeric_subunit_grid_points=len(bad),diverse_starts=len(diverse),checked=len(checks),
                numeric_minimum=float(min(flat)),exact_minimum=str(min(F(x['score']) for x in checks)),
                max_checked_error=max(abs(float(F(x['score']))-x['numeric_score']) for x in checks),
                local_witnesses=checks,general_packing_exclusion=False)
    if grid_source:report['grid_source_sha256']=hashlib.sha256(grid_source.read_bytes()).hexdigest()
    out.write_text(json.dumps(report,indent=2));print({k:v for k,v in report.items() if k!='local_witnesses'},flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('prior',type=Path);p.add_argument('out',type=Path);p.add_argument('--grid-source',type=Path);a=p.parse_args();run(a.prior,a.out,a.grid_source)
