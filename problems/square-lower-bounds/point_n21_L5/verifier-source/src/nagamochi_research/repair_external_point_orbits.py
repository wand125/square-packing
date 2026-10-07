"""Monotone exact repair of selected witness deficits using existing D4 orbits.
This is a finite repair, not an LP optimum or a global covering certificate.
"""
from pathlib import Path
from fractions import Fraction as F
from math import lcm,ceil
import argparse,json,hashlib
from probe_external_integer_bridge import read

def run(source,root,outdir,extra=None):
 outdir.mkdir(exist_ok=False);native,span,W,points=read(source);L=F(4999,1000);poses={}
 for name in ['n21-endpoint-probe.json','n21-rational-random4096.json']:
  data=json.loads((root/name).read_text())
  for row in data['records']:
   if F(row['L'])!=L:continue
   for w in row['violations']+[row['minimum']]:poses[tuple(F(w[k]) for k in ['cx','cy','t'])]=name
 for name in ['n21-L4999-refined-witness.json']:
  d=json.loads((root/name).read_text());w=d['minimum'];poses[tuple(F(w[k]) for k in ['cx','cy','t'])]=name
  for h in d['history']:poses[tuple(map(F,h['pose']))]=name
 if extra is not None:
  data=json.loads(extra.read_text());rows=data.get("violations",[])
  if "minimum" in data:rows=rows+[data["minimum"]]
  for w in rows:poses[tuple(F(w[k]) for k in ["cx","cy","t"])]=str(extra)
 poses=sorted(poses);groups={}
 for i,(x,y,w) in enumerate(points):
  key=tuple(sorted((min(x,span-x),min(y,span-y))));groups.setdefault(key,[]).append(i)
 orbits=list(groups.values());coeff=[]
 for cx,cy,t in poses:
  p,q=t.numerator,t.denominator;a=q*q-p*p;b=2*p*q;r=q*q+p*p;h=F(a+b,2*r);assert h<=cx<=L-h and h<=cy<=L-h
  H=lcm(L.denominator,cx.denominator,cy.denominator);A=int(L*H);X0=int(span*cx*H);Y0=int(span*cy*H);limit=r*span*H
  hits=[2*abs(a*(x*A-X0)+b*(y*A-Y0))<=limit and 2*abs(a*(y*A-Y0)-b*(x*A-X0))<=limit for x,y,w in points]
  coeff.append([sum(hits[i] for i in orbit) for orbit in orbits])
 weights=[F(w,W) for x,y,w in points];start_weights=weights[:];target=F(10001,10000)
 def score(row):return sum((F(c)*weights[o[0]] for o,c in zip(orbits,row)),F(0))
 assert all(len({weights[i] for i in o})==1 for o in orbits)
 initial=list(map(score,coeff));scores=initial[:];steps=[]
 while min(scores)<target:
  wi=min(range(len(scores)),key=scores.__getitem__);deficit=target-scores[wi];options=[]
  for j,o in enumerate(orbits):
   hit=coeff[wi][j]
   if not hit:continue
   delta=deficit/hit;cost=delta*len(o);benefit=sum((min(max(F(0),target-s),delta*row[j]) for s,row in zip(scores,coeff)),F(0))
   options.append((benefit/cost,F(hit,len(o)),-j,j,delta))
  *_,j,delta=max(options)
  for i in orbits[j]:weights[i]+=delta
  scores=list(map(score,coeff));steps.append(dict(orbit=j,point_indices=orbits[j],per_point_increment=str(delta),mass_increment=str(delta*len(orbits[j]))))
 D=span*L.denominator;coords=[(x*L.numerator,y*L.numerator) for x,y,w in points]
 if native==L:
  assert (F(span)/L).denominator==1
  D=int(F(span)/L);coords=[(x,y) for x,y,w in points]
 den=10**12;nums=[ceil(w*den) for w in weights]
 assert all(F(n,den)>=old for n,old in zip(nums,start_weights))
 output=outdir/'candidate.txt';output.write_text('\n'.join([f'{L.numerator} {L.denominator}',str(D),str(den),str(len(points))]+[f'{x} {y} {n}' for (x,y),n in zip(coords,nums)])+'\n')
 report=dict(status='FINITE_MONOTONE_REPAIR',source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),sha256=hashlib.sha256(output.read_bytes()).hexdigest(),L=str(L),original_mass=str(sum(start_weights)),total_mass=str(F(sum(nums),den)),target=str(target),orbits=len(orbits),steps=steps,witnesses=[dict(pose=list(map(str,p)),before=str(a),after=str(b)) for p,a,b in zip(poses,initial,scores)],pointwise_weights_nondecreasing=True,general_coverage_verified=False)
 (outdir/'repair.json').write_text(json.dumps(report,indent=2));print('mass',float(F(report['total_mass'])),'orbits',len(steps),'witnesses',len(poses),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('root',type=Path);p.add_argument('outdir',type=Path);p.add_argument('--extra',type=Path);a=p.parse_args();run(a.source,a.root,a.outdir,a.extra)
