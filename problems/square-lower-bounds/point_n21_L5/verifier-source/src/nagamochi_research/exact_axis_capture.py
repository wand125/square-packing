"""PL34: exact conservative capture on every axis-aligned physical pose."""
import argparse,bisect,hashlib,json,time
from fractions import Fraction as F
from pathlib import Path
import numpy as np
from mixed_density_check import expand


def floor(q):return q.numerator//q.denominator


def setup(data):
    model=expand(data);L,B,rects,points=model[:4]
    atoms={}
    for p,w in points:atoms[p]=atoms.get(p,F(0))+w
    atoms={p:w for p,w in atoms.items() if w}
    for (x,y),w in atoms.items():
        if any(atoms.get(p,F(0))!=w for p in ((L-x,y),(x,L-y),(y,x))):
            raise ValueError('Point measure is not D4 invariant')
    lo=F(1,2);hi=L/2;knots={lo,hi}
    for r in rects:
        if r[4]:
            for x in r[:4]:
                knots.update(x+sign*B/2 for sign in (-1,1) if lo<=x+sign*B/2<=hi)
    for p in atoms:
        for x in p:knots.update(x+sign*B/2 for sign in (-1,1) if lo<=x+sign*B/2<=hi)
    return model,sorted(knots)


def lower_grid(model,knots,ratio_bits=19,mass_bits=32,limb_bits=12):
    if not(1<=ratio_bits<=26 and 1<=mass_bits<=50 and 1<=limb_bits<=20):raise ValueError('Invalid precision')
    L,B,rects,points=model[:4];D=1<<ratio_bits;W=1<<mass_bits;limit=(1<<63)-1
    rects=[r for r in rects if r[4]];n=len(rects);size=len(knots)
    if n*D*D*((1<<limb_bits)-1)>limit:raise ValueError('Integer dot product can overflow')
    X=np.zeros((size,n),dtype=np.int64);Y=np.zeros_like(X);weights=[]
    for j,(x0,y0,x1,y1,rho) in enumerate(rects):
        weights.append(floor(rho*(x1-x0)*(y1-y0)*W))
        for i,x in enumerate(knots):
            X[i,j]=floor(max(F(0),min(x+B/2,x1)-max(x-B/2,x0))/(x1-x0)*D)
            Y[i,j]=floor(max(F(0),min(x+B/2,y1)-max(x-B/2,y0))/(y1-y0)*D)
    if sum(weights)>limit:raise ValueError('Mass integers exceed int64')
    point_weights=[floor(w*W) for _,w in points]
    if 4*sum(point_weights)>limit:raise ValueError('Point prefix sums can overflow')
    diff=np.zeros((size+1,size+1),dtype=np.int64)
    for ((x,y),_),q in zip(points,point_weights):
        # Strict capture at vertices is a lower bound for the adjacent cells.
        i=bisect.bisect_right(knots,x-B/2);j=bisect.bisect_left(knots,x+B/2)
        k=bisect.bisect_right(knots,y-B/2);ell=bisect.bisect_left(knots,y+B/2)
        if i>=j or k>=ell:continue
        diff[i,k]+=q;diff[j,k]-=q;diff[i,ell]-=q;diff[j,ell]+=q
    result=diff.cumsum(axis=0).cumsum(axis=1)[:-1,:-1].astype(object)*(D*D)
    mask=(1<<limb_bits)-1;maximum=max(weights,default=0)
    for shift in range(0,maximum.bit_length(),limb_bits):
        limb=np.array([(w>>shift)&mask for w in weights],dtype=np.int64)
        product=(X*limb)@Y.T
        result+=product.astype(object)*(1<<shift)
    return result,D*D*W


def calculate(data,ratio_bits=19,mass_bits=32,limb_bits=12):
    started=time.perf_counter();model,knots=setup(data)
    values,den=lower_grid(model,knots,ratio_bits,mass_bits,limb_bits)
    raw=min(map(int,values.flat));index=next(i for i,v in enumerate(values.flat) if v==raw)
    digest=hashlib.sha256()
    for row in values:digest.update((','.join(map(str,row))+'\n').encode())
    return dict(status='EXACT_AXIS_CONTINUOUS_LOWER_BOUND',lemma='PL34',L=str(model[0]),B=str(model[1]),
                ratio_bits=ratio_bits,mass_bits=mass_bits,knots=len(knots),vertices=len(values.flat),
                lower_bound=str(F(raw,den)),proves_capture_one=raw>=den,
                minimum_vertex=[str(knots[index//len(knots)]),str(knots[index%len(knots)])],
                knots_sha256=hashlib.sha256(json.dumps(list(map(str,knots))).encode()).hexdigest(),
                lower_grid_sha256=digest.hexdigest(),seconds=time.perf_counter()-started,
                scope='All physical t=0 centres in [1/2,L-1/2]^2, via verified D4 symmetry',
                general_packing_exclusion=False)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('candidate',type=Path);p.add_argument('out',type=Path)
    p.add_argument('--replay',type=Path);a=p.parse_args()
    data=json.loads(a.candidate.read_text());sha=hashlib.sha256(a.candidate.read_bytes()).hexdigest()
    old=json.loads(a.replay.read_text()) if a.replay else None
    if old and old['candidate_sha256']!=sha:raise ValueError('Candidate changed')
    result=calculate(data,ratio_bits=old['ratio_bits'] if old else 19,mass_bits=old['mass_bits'] if old else 32,limb_bits=8 if old else 12)
    result['candidate_sha256']=sha
    if old:
        for key in ('L','B','knots','vertices','lower_bound','proves_capture_one','knots_sha256','lower_grid_sha256'):
            if old[key]!=result[key]:raise ValueError('Replay mismatch: '+key)
        result['status']='EXACT_AXIS_LOWER_BOUND_REPLAYED'
    if a.out.exists():raise FileExistsError(a.out)
    a.out.write_text(json.dumps(result,indent=2));print(result,flush=True)
