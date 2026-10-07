"""Rigorous axis-wide verifier: exact event cells, integer lower-bound sums.
Success is ONLY net angle zero, never a full packing certificate.
"""
import argparse,json,math,hashlib
from fractions import Fraction as F
from pathlib import Path
from time import perf_counter
import numpy as np
from mixed_density_check import expand,evaluate
from mixed_net_audit import symmetry,net_certificate,candidate_net
from mixed_axis_cells import axis_cell_lower


def lattice(model):
    L,B,rs,ps,total,digest=model;lo=L/2;hi=L-F(1,2)
    if lo>=hi:raise ValueError('Empty centre domain')
    axes=[]
    for dim in (0,1):
        values={lo,hi}
        values.update(v+s*B/2 for r in rs for v in (r[dim],r[dim+2]) for s in (-1,1) if lo<v+s*B/2<hi)
        values.update(p[dim]+s*B/2 for p,w in ps for s in (-1,1) if lo<p[dim]+s*B/2<hi)
        axes.append(sorted(values))
    return axes


def tables(model,axes,fraction_bits=17,weight_bits=24):
    L,B,rs,ps,total,digest=model
    coords=[B/2]+[v for axis in axes for v in axis]+[v for r in rs for v in r[:4]]+[v for p,w in ps for v in p]
    D=math.lcm(*(v.denominator for v in coords));h=int(B/2*D)
    ir=[[int(v*D) for v in r[:4]] for r in rs];ip=[[int(v*D) for v in p] for p,w in ps]
    weights=[r[4]*(r[2]-r[0])*(r[3]-r[1]) for r in rs]
    W=1<<weight_bits;wi=np.array([int(w*W) for w in weights],dtype=np.int64);pi=np.array([int(w*W) for p,w in ps],dtype=np.int64)
    S=1<<fraction_bits
    # All factors are nonnegative; this bounds EVERY product and partial sum.
    while (sum(map(int,wi))+sum(map(int,pi)))*S*S>=2**63:
        fraction_bits-=1;S=1<<fraction_bits
        if fraction_bits<1:raise ValueError('Integer accumulator would overflow')
    intervals=[];hits=[]
    for dim,axis in enumerate(axes):
        values=[int(v*D) for v in axis]
        f=np.empty((len(values),len(rs)),dtype=np.int64)
        for i,x in enumerate(values):
            for j,r in enumerate(ir):
                a,b=r[dim],r[dim+2]
                f[i,j]=max(0,min(b,x+h)-max(a,x-h))*S//(b-a)
        # Twice the midpoint stays integer even if the midpoint is off lattice.
        atom=np.array([[int(abs(2*p[dim]-a-b)<=2*h) for p in ip] for a,b in zip(values,values[1:])],dtype=np.int64)
        intervals.append(f);hits.append(atom)
    return intervals,hits,wi,pi,W*S*S,dict(coordinate_denominator=str(D),fraction_bits=fraction_bits,weight_bits=weight_bits)


def verify(candidate,out,gamma=F(10001,10000),exact_limit=32):
    start=perf_counter();data=json.loads(candidate.read_text());model=expand(data);symmetry(model);net_certificate(model[1],*candidate_net(data));axes=lattice(model)
    if gamma<=0 or model[-2]>=data['n']*gamma:raise ValueError('Invalid mixed proof budget/threshold')
    f,h,wi,pi,den,meta=tables(model,axes)
    density=(f[0]*wi)@f[1].T
    corner=np.minimum(np.minimum(density[:-1,:-1],density[1:,:-1]),np.minimum(density[:-1,1:],density[1:,1:]))
    point=(h[0]*pi)@h[1].T
    S=1<<meta['fraction_bits'];lower=corner+point*S*S
    threshold=-((-gamma.numerator*den)//gamma.denominator)
    unresolved=np.argwhere(lower<threshold);patches=[];witness=None
    # Integer lower bound may be pessimistic. A failed lower bound is NOT a hole.
    for i,j in sorted(map(tuple,unresolved.tolist()),key=lambda ij:int(lower[ij]))[:exact_limit]:
        box=(axes[0][i],axes[0][i+1],axes[1][j],axes[1][j+1])
        lb=axis_cell_lower(model,*box)
        if lb>=gamma:patches.append(dict(i=i,j=j,lower=str(lb)));continue
        # A centre or a point sufficiently near the minimum-density corner can
        # witness a strict failure. Keep UNRESOLVED if this bounded search fails.
        x0,x1,y0,y1=box
        for power in range(1,14):
            u=F(1,2**power)
            for xx,yy in ((u,u),(u,1-u),(1-u,u),(1-u,1-u)):
                w=evaluate(model,x0+xx*(x1-x0),y0+yy*(y1-y0),F(0))
                if F(w['score'])<gamma:witness=w;break
            if witness:break
        if witness:break
    passed=len(unresolved)==len(patches)
    status='AXIS_VERIFIED' if passed else ('AXIS_BELOW_GAMMA' if witness else 'AXIS_UNRESOLVED')
    out.mkdir(parents=True,exist_ok=False)
    np.savez_compressed(out/'integer-tables.npz',fx=f[0],fy=f[1],hx=h[0],hy=h[1],density_weights=wi,point_weights=pi)
    result=dict(status=status,candidate=str(candidate),digest=model[-1],net_index=0,gamma=str(gamma),mass=str(model[-2]),axes=[[str(v) for v in a] for a in axes],table_metadata=meta,denominator=str(den),cells=int(lower.size),integer_minimum=str(F(int(lower.min()),den)),integer_unresolved=len(unresolved),exact_patches=patches,witness=witness,seconds=perf_counter()-start,
                scope='Complete centre domain for net angle zero only. D4 checked. Integer floors are one-sided; boundary atoms use the open-cell mask. No other angle is certified.')
    result['proof_spec']=dict(version='mixed-axis-integer-v1',candidate_digest=model[-1],gamma=str(gamma),net_index=0,net_step=str(candidate_net(data)[0]),net_last=candidate_net(data)[1],centre_domain='D4 quarter of unit-bin centre domain')
    result['proof_digest']=hashlib.sha256(json.dumps(result['proof_spec'],sort_keys=True,separators=(',',':')).encode()).hexdigest()
    (out/'result.json').write_text(json.dumps(result,indent=2))
    print(json.dumps({k:v for k,v in result.items() if k not in ('axes','exact_patches','witness','candidate','digest','mass','denominator')}),flush=True)
    return result

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('candidate',type=Path);ap.add_argument('--out',type=Path,required=True);args=ap.parse_args();verify(args.candidate,args.out)
