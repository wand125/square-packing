"""Probe unresolved boxes, using floats only to select exact rational checks."""
from pathlib import Path
from fractions import Fraction as F
from math import lcm
import argparse,json,hashlib
import numpy as np
from collections import Counter
from probe_external_integer_bridge import read
from score import square,contains

def run(config,out):
 c=json.loads(config.read_text());cert=Path(c['parent']);assert hashlib.sha256(cert.read_bytes()).hexdigest()==c['candidate_sha256'];L,span,W,pts=read(cert)
 xy=np.array([(float(F(x)*L/span),float(F(y)*L/span)) for x,y,w in pts]);weights=np.array([w/W for x,y,w in pts]);rows=[json.loads(l) for l in (Path(c['output'])/'roots.jsonl').read_text().splitlines()];expected=len(json.loads(Path(c['frontier']).read_text())['pending']) if 'frontier' in c else c['grid']**2*c['ubins'];assert len(rows)==expected;stats=Counter();violations=[];sampled=0;verified=0;seen=set()
 for index,row in enumerate(rows):
  if index and index%500==0:print('probe',index,'/',len(rows),'poses',sampled,'violations',len(violations),flush=True)
  assert row['index']==index and row['config_sha256']==hashlib.sha256(config.read_bytes()).hexdigest();stats.update(row['stats'])
  for box in row['uncertified']:
   x0,x1,y0,y1,a,b=map(F,box)
   for t in (a,(a+b)/2,b):
    co,si=(1-t*t)/(1+t*t),2*t/(1+t*t);h=(co+si)/2;lo=max(x0,h);hi=min(x1,L-h);bottom=max(y0,h);top=min(y1,L-h)
    if lo>hi or bottom>top:continue
    for x,y in [((lo+hi)/2,(bottom+top)/2),(lo,bottom),(hi,top)]:
     key=(x,y,t)
     if key in seen:continue
     seen.add(key);sampled+=1;dx=xy[:,0]-float(x);dy=xy[:,1]-float(y);mask=(np.abs(float(co)*dx+float(si)*dy)<=.5+1e-12)&(np.abs(float(co)*dy-float(si)*dx)<=.5+1e-12);v=weights[mask].sum()
     if v>=1+1e-9:continue
     verified+=1;poly=square(x,y,F(1),t);assert all(0<=px<=L and 0<=py<=L for px,py in poly)
     exact=sum((F(w,W) for px,py,w in pts if contains(poly,(F(px)*L/span,F(py)*L/span))),F(0))
     if exact<1:violations.append(dict(root_index=index,cx=str(x),cy=str(y),t=str(t),score=str(exact)))
 result=dict(candidate_sha256=c['candidate_sha256'],root_count=len(rows),leaf_counts={k:v for k,v in stats.items() if k not in ['maxdepth','boxes']},boxes=stats['boxes'],sampled=sampled,exact_checked=verified,violations=violations,all_samples_exact=False,general_coverage_verified=False)
 out.write_text(json.dumps(result,indent=2));print({k:v for k,v in result.items() if k!='violations'},'violations',len(violations),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('config',type=Path);p.add_argument('out',type=Path);a=p.parse_args();assert not a.out.exists();run(a.config,a.out)
