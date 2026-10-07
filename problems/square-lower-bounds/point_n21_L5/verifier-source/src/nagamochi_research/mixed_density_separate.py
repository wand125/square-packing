"""Numerical new-pose search followed by exact rational counterexample replay."""
import argparse,json,math
from fractions import Fraction as F
from pathlib import Path
from time import perf_counter
import numpy as np
from scipy.optimize import minimize
from expanded_search_pilot import ROOT,Geometry,capture
from mixed_density_check import expand,evaluate


def run(candidate,output,seed=926210):
    started=perf_counter();data=json.loads(candidate.read_text());model=expand(data)
    L,B=float(model[0]),float(model[1]);rects=np.array([[float(F(x)) for x in r['rectangle']] for r in data['rectangles']]);rw=np.array([float(F(r['mass'])) for r in data['rectangles']]);pts=np.array([[float(F(x)) for x in r['point']] for r in data['points']]);pw=np.array([float(F(r['mass'])) for r in data['points']])
    geo=Geometry(L,B,rects)
    def score(ps):return geo.matrix(np.atleast_2d(ps))@rw+capture(np.atleast_2d(ps),L,B,pts,shrink=0)@pw
    rng=np.random.default_rng(seed);ps=rng.random((6000,3));ps[:600,2]=0
    vals=score(ps);candidates=[(float(vals[i]),ps[i]) for i in np.argsort(vals)[:30]]
    for _,p in candidates[:6]:
        fit=minimize(lambda x:float(score(x)[0]),p,method='Nelder-Mead',bounds=[(0,1)]*3,options={'maxiter':100,'xatol':1e-6})
        candidates.append((float(fit.fun),fit.x))
    witnesses=[];used=[]
    for value,p in sorted(candidates,key=lambda z:z[0]):
        if value>=1:continue
        if any(np.linalg.norm(p-q)<.015 for q in used):continue
        t=F(float(np.tan(p[2]*np.pi/8))).limit_denominator(10**7)
        c=(1-t*t)/(1+t*t);s=2*t/(1+t*t);r=(model[0]-model[1]*(c+s))/2
        x=model[0]/2+F(float(p[0])).limit_denominator(10**7)*r
        y=model[0]/2+F(float(p[1])).limit_denominator(10**7)*r
        w=evaluate(model,x,y,t)
        if F(w['score'])<1:
            # Rebuild numerical pose from the exact witness for the LP adapter.
            theta=2*math.atan(float(t));reach=(L-B*(math.cos(theta)+math.sin(theta)))/2
            w['normalized_pose']=[(float(x)-L/2)/reach,(float(y)-L/2)/reach,theta/(np.pi/4)]
            witnesses.append(w);used.append(p)
        if len(witnesses)>=8:break
    result=dict(seed=seed,status='EXACT_LOCAL_DEFICITS' if witnesses else 'NO_DEFICIT_FOUND_NOT_PROOF',candidate=str(candidate),digest=model[-1],random_poses=len(ps),numerical_minimum=min(v for v,p in candidates),witnesses=witnesses,seconds=perf_counter()-started,scope='Each witness is exact for the rational candidate/core. No all-angle or global certification.')
    output.write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items() if k!='witnesses'}),flush=True)
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--candidate',type=Path,default=ROOT/'n21/mixed-candidate.json');ap.add_argument('--out',type=Path,default=ROOT/'n21/new-separation.json');ap.add_argument('--seed',type=int,default=926210);args=ap.parse_args();run(args.candidate,args.out,args.seed)
