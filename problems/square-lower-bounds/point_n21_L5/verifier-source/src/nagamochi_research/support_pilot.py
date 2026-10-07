"""Finite support refinement scout. No global or integer-endpoint certificate.

D4-invariant piecewise line densities and point orbits, with original central
area. Independent holdouts include both signs of rotation and smaller deltas.
Selected LP duals are replayed with rational geometry to bound this finite basis.
"""
import os
for name in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS'):
    os.environ[name]='1'
import argparse, json, math
from fractions import Fraction as F
from pathlib import Path
from time import perf_counter
import numpy as np
from scipy.optimize import linprog
from pilot import samples
from score import square, clip, area, contains, segment_length


def orbit(k, points):
    out=set()
    for swap in (False,True):
        for sx in (False,True):
            for sy in (False,True):
                ps=[]
                for x,y in points:
                    if swap: x,y=y,x
                    ps.append((k-x if sx else x,k-y if sy else y))
                out.add(tuple(sorted(ps)))
    return sorted(out)


def basis(k, expanded=False, interior=False):
    cols=[dict(kind='area',support=[],cost=F((k-2)**2))]
    seen=set()
    for r in ([F(4,5),F(9,10),F(19,20)] if expanded else [F(9,10)]):
        knots=sorted({r,k-r}|{F(j,2) for j in range(2,2*k-1) if r<F(j,2)<k-r})
        for a,b in zip(knots,knots[1:]):
            support=orbit(k,[(a,F(1)),(b,F(1))])
            key=('line',tuple(support))
            if key in seen: continue
            seen.add(key)
            cost=sum(abs(v[0]-u[0])+abs(v[1]-u[1]) for u,v in support)
            cols.append(dict(kind='line',support=support,cost=cost))
        points=[(r,F(1))]+[(F(i),r) for i in range(2,k-1)]
        if expanded:
            points += [(F(j,2),r) for j in range(2,2*k-1)]
        for pt in points:
            support=orbit(k,[pt]);key=('point',tuple(support))
            if key in seen: continue
            seen.add(key)
            cols.append(dict(kind='point',support=support,cost=F(len(support))))
    if interior:
        # Unit tiles of the central region, and interior half-grid point orbits.
        # Keep the original area column so the richer model includes the baseline.
        for i in range(1,k-1):
            for j in range(1,k-1):
                support=orbit(k,[(F(i),F(j)),(F(i+1),F(j)),(F(i),F(j+1)),(F(i+1),F(j+1))])
                key=('tile',tuple(support))
                if key in seen: continue
                seen.add(key);cols.append(dict(kind='tile',support=support,cost=F(len(support))))
        for i in range(2,2*k-1):
            for j in range(2,2*k-1):
                support=orbit(k,[(F(i,2),F(j,2))]);key=('point',tuple(support))
                if key in seen: continue
                seen.add(key);cols.append(dict(kind='point',support=support,cost=F(len(support))))
    return cols


def exact_row(k,cols,pose):
    poly=square(pose['cx'],pose['cy'],1+pose['delta'],pose['t'])
    central=poly
    for axis in (0,1):
        central=clip(central,axis,F(1),True)
        central=clip(central,axis,F(k-1),False)
    row=[area(central)]
    for col in cols[1:]:
        if col['kind']=='point':
            row.append(F(sum(contains(poly,s[0]) for s in col['support'])))
        elif col['kind']=='line':
            row.append(sum(segment_length(poly,*s) for s in col['support']))
        else:
            total=F(0)
            for tile in col['support']:
                part=poly
                for axis in (0,1):
                    part=clip(part,axis,min(v[axis] for v in tile),True)
                    part=clip(part,axis,max(v[axis] for v in tile),False)
                total+=area(part)
            row.append(total)
    return row


def matrix(k,cols,poses):
    # Vectorized square-local slab tests; rational replay handles active witnesses.
    cx=np.array([float(p['cx']) for p in poses]);cy=np.array([float(p['cy']) for p in poses])
    t=np.array([float(p['t']) for p in poses]);h=np.array([float(1+p['delta'])/2 for p in poses])
    c=(1-t*t)/(1+t*t);s=2*t/(1+t*t)
    def local(x,y):
        dx=x-cx;dy=y-cy
        return c*dx+s*dy,-s*dx+c*dy
    out=np.zeros((len(poses),len(cols)));polys=[]
    for i,p in enumerate(poses):
        poly=square(p['cx'],p['cy'],1+p['delta'],p['t'])
        poly=[tuple(map(float,v)) for v in poly]
        polys.append(poly)
        for axis in (0,1):
            poly=clip(poly,axis,1.,True);poly=clip(poly,axis,float(k-1),False)
        out[i,0]=float(area(poly))
    for j,col in enumerate(cols[1:],1):
        for primitive in col['support']:
            if col['kind']=='point':
                x,y=local(*map(float,primitive[0]))
                out[:,j]+=(np.abs(x)<=h+1e-13)&(np.abs(y)<=h+1e-13)
            elif col['kind']=='tile':
                lower=np.min(primitive,axis=0).astype(float);upper=np.max(primitive,axis=0).astype(float)
                radius=h*(np.abs(c)+np.abs(s))
                selected=np.flatnonzero((cx+radius>lower[0])&(cx-radius<upper[0])&
                                        (cy+radius>lower[1])&(cy-radius<upper[1]))
                for i in selected:
                    part=polys[i]
                    for axis in (0,1):
                        part=clip(part,axis,lower[axis],True);part=clip(part,axis,upper[axis],False)
                    out[i,j]+=float(area(part))
            else:
                a,b=np.array(primitive,dtype=float);u,v=local(*a)
                dx,dy=b-a;du=c*dx+s*dy;dv=-s*dx+c*dy
                lo=np.zeros(len(poses));hi=np.ones(len(poses))
                for start,direction in ((u,du),(v,dv)):
                    moving=np.abs(direction)>1e-15
                    low=np.full(len(poses),-np.inf);high=np.full(len(poses),np.inf)
                    low[moving]=(-h[moving]-start[moving])/direction[moving]
                    high[moving]=(h[moving]-start[moving])/direction[moving]
                    lo=np.maximum(lo,np.minimum(low,high));hi=np.minimum(hi,np.maximum(low,high))
                    hi[(~moving)&(np.abs(start)>h+1e-13)]=-1
                out[:,j]+=np.maximum(0,hi-lo)*np.abs(b-a).sum()
    return out


def holdout(k,seed):
    rng=np.random.default_rng(seed);poses=[]
    # New angles, both chiralities, random positions and contacts with grid/support.
    for i in range(1800):
        delta=[F(1,10**8),F(1,10**5),F(3,1000)][i%3]
        t=F(int(rng.integers(-414,415)),1000)
        radius=(1+delta)*(1-t*t+2*abs(t))/(2*(1+t*t))
        xy=[]
        for axis in (0,1):
            mode=int(rng.integers(0,4))
            if mode==0: z=radius+int(rng.integers(0,3))*delta
            elif mode==1: z=F(int(rng.integers(1,2*k)),2)+int(rng.integers(-2,3))*delta
            else: z=radius+(k-2*radius)*F(int(rng.integers(0,100001)),100000)
            xy.append(min(k-radius,max(radius,z)))
        poses.append(dict(k=k,delta=delta,t=t,cx=xy[0],cy=xy[1]))
    # Axis-aligned placements translated throughout each boundary cell.
    for delta in (F(1,10**8),F(1,10**5)):
        for j in range(5,10*k-4):
            for shift in (-delta,delta):
                x=F(j,10)+shift;y=(1+delta)/2
                if y<=x<=k-y:
                    poses.append(dict(k=k,delta=delta,t=F(0),cx=x,cy=y))
    return poses


def dual_certificate(k,cols,poses,lp):
    raw=-lp.ineqlin.marginals;ids=np.flatnonzero(raw>1e-9)
    rows=[exact_row(k,cols,poses[int(i)]) for i in ids]
    weights=[F(math.floor(float(raw[i])*10**10),10**10) for i in ids]
    costs=[col['cost'] for col in cols]
    loads=[sum(y*row[j] for y,row in zip(weights,rows)) for j in range(len(cols))]
    scale=max([F(1)]+[v/c for v,c in zip(loads,costs)])
    weights=[y/scale for y in weights]
    assert all(sum(y*row[j] for y,row in zip(weights,rows))<=costs[j] for j in range(len(cols)))
    return dict(bound=sum(weights),witnesses=[dict(pose=poses[int(i)],dual_weight=y) for i,y in zip(ids,weights)])


def run(k,expanded,interior=False):
    start=perf_counter();cols=basis(k,expanded,interior)
    poses=[p for p,_ in samples(k)];a=matrix(k,cols,poses);history=[]
    costs=np.array([float(c['cost']) for c in cols])
    for iteration in range(4):
        lp=linprog(costs,A_ub=-a,b_ub=-np.ones(len(a)),bounds=(0,None),method='highs',
                   options={'primal_feasibility_tolerance':1e-9,'dual_feasibility_tolerance':1e-9})
        if not lp.success: raise RuntimeError(lp.message)
        checks=holdout(k,20260926+iteration);b=matrix(k,cols,checks);scores=b@lp.x
        bad=np.flatnonzero(scores<1-1e-7)
        worst=int(np.argmin(scores))
        # Replay the worst holdout with exact geometry and rationalized primal weights.
        rational_weights=[F(str(w)) for w in lp.x]
        exact_score=sum(v*w for v,w in zip(exact_row(k,cols,checks[worst]),rational_weights))
        history.append(dict(iteration=iteration,mass=float(lp.fun),training=len(poses),
                            holdout=len(checks),violations=len(bad),minimum=float(scores[worst]),
                            worst_pose=checks[worst],worst_score_exact=exact_score))
        if iteration==3 or not len(bad): break
        poses.extend(checks[i] for i in bad);a=np.vstack([a,b[bad]])
    certificate=dual_certificate(k,cols,poses,lp)
    return dict(k=k,model='interior' if interior else 'expanded' if expanded else 'refined',columns=len(cols),history=history,
                basis=cols,weights=lp.x.tolist(),dual=certificate,seconds=perf_counter()-start,
                scope='Exact lower bound only for this finite support basis; holdout passage is not a proof.')


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--ks',nargs='+',type=int,default=list(range(4,11)))
    ap.add_argument('--models',nargs='+',choices=['refined','expanded','interior'],default=['refined','expanded'])
    ap.add_argument('--out',type=Path,required=True);args=ap.parse_args();args.out.mkdir(parents=True,exist_ok=False)
    for k in args.ks:
        for model in args.models:
            result=run(k,model!='refined',model=='interior')
            (args.out/f"k{k}-{result['model']}.json").write_text(json.dumps(result,default=str,indent=2))
            print(json.dumps({key:result[key] for key in ('k','model','columns','history','seconds')},default=str),flush=True)


if __name__=='__main__': main()
