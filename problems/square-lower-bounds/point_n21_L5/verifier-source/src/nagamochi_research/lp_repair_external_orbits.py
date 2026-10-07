"""Small monotone LP on known witnesses; rounded candidate audited exactly."""
from pathlib import Path
from fractions import Fraction as F
from math import lcm,ceil,floor
import json,hashlib,argparse
import os
for name in ("OMP_NUM_THREADS","OPENBLAS_NUM_THREADS","MKL_NUM_THREADS"):os.environ[name]="1"
import numpy as np
from scipy.optimize import linprog
from probe_external_integer_bridge import read

def run(source,witnesses,out):
 out.mkdir(exist_ok=False);data=json.loads(witnesses.read_text());assert hashlib.sha256(source.read_bytes()).hexdigest()==data['source_sha256'];L,span,W,pts=read(source);target=F(data['target']);groups={}
 for i,(x,y,w) in enumerate(pts):groups.setdefault(tuple(sorted((min(x,span-x),min(y,span-y)))),[]).append(i)
 orbits=list(groups.values());sizes=np.array(list(map(len,orbits)));matrix=[];base=[]
 for row in data['witnesses']:
  cx,cy,t=map(F,row['pose']);p,q=t.numerator,t.denominator;a=q*q-p*p;b=2*p*q;r=q*q+p*p;h=F(a+b,2*r);assert h<=cx<=L-h and h<=cy<=L-h
  H=lcm(L.denominator,cx.denominator,cy.denominator);A=int(L*H);X0=int(span*cx*H);Y0=int(span*cy*H);limit=r*span*H
  hits=[2*abs(a*(x*A-X0)+b*(y*A-Y0))<=limit and 2*abs(a*(y*A-Y0)-b*(x*A-X0))<=limit for x,y,w in pts]
  counts=[sum(hits[i] for i in orbit) for orbit in orbits];score=F(sum(w for hit,(x,y,w) in zip(hits,pts) if hit),W);assert score==F(row['before']);matrix.append(counts);base.append(score)
 coefficient=np.array(matrix,float)/sizes;rhs=np.array([float(max(F(0),target-s)) for s in base]);sol=linprog(np.ones(len(orbits)),A_ub=-coefficient,b_ub=-rhs,bounds=(0,None),method='highs');assert sol.success,sol.message
 dual=[F(floor(max(0,-float(v))*10**9),10**9) for v in sol.ineqlin.marginals]
 loads=[sum((dual[i]*F(matrix[i][j],len(orbits[j])) for i in range(len(base))),F(0)) for j in range(len(orbits))]
 scale=max(F(1),max(loads));dual=[v/scale for v in dual]
 lower=sum((v*max(F(0),target-b) for v,b in zip(dual,base)),F(0))
 lower_one=sum((v*max(F(0),F(1)-b) for v,b in zip(dual,base)),F(0))
 audit=dict(scope='Fixed existing D4 support and only nonnegative increments above the source weights; finite witness constraints.',multipliers=list(map(str,dual)),max_column_load=str(max(loads)/scale),all_columns_checked=len(orbits),increment_lower=str(lower),increment_lower_at_capture_one=str(lower_one),general_packing_exclusion=False)
 (out/'dual.json').write_text(json.dumps(audit,indent=2));print('exact incremental lower',str(lower),'at capture one',str(lower_one),flush=True)

 denominator=10**12;extra=[ceil(max(0,float(z))*denominator/int(k)) for z,k in zip(sol.x,sizes)];nums=[ceil(F(w,W)*denominator) for x,y,w in pts]
 for o,d in zip(orbits,extra):
  for i in o:nums[i]+=d
 scores=[s+sum((F(k*d,denominator) for k,d in zip(row,extra)),F(0)) for s,row in zip(base,matrix)];assert all(s>=target for s in scores)
 D=int(F(span)/L);cert=out/'candidate.txt';cert.write_text('\n'.join([f'{L.numerator} {L.denominator}',str(D),str(denominator),str(len(pts))]+[f'{x} {y} {m}' for (x,y,w),m in zip(pts,nums)])+'\n');read(cert)
 report=dict(status='FINITE_MONOTONE_LP_REPAIR',source_sha256=data['source_sha256'],sha256=hashlib.sha256(cert.read_bytes()).hexdigest(),L=str(L),original_mass=str(F(sum(w for x,y,w in pts),W)),total_mass=str(F(sum(nums),denominator)),target=str(target),orbits=len(orbits),changed_orbits=sum(d>0 for d in extra),numerical_increment=float(sol.fun),increments=[dict(orbit=i,per_point=str(F(d,denominator)),size=len(orbits[i])) for i,d in enumerate(extra) if d],witnesses=[dict(pose=row['pose'],before=str(a),after=str(b)) for row,a,b in zip(data['witnesses'],base,scores)],pointwise_weights_nondecreasing=True,general_coverage_verified=False)
 (out/'repair.json').write_text(json.dumps(report,indent=2));print('mass',float(F(report['total_mass'])),'changed orbits',report['changed_orbits'])
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('witnesses',type=Path);p.add_argument('out',type=Path);a=p.parse_args();run(a.source,a.witnesses,a.out)
