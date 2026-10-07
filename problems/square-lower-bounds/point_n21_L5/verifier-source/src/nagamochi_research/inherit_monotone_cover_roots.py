"""Carry local cover proofs across pointwise weight increases at identical L.
No new geometric proof is claimed; trust remains that of the source checker.
"""
from pathlib import Path
from fractions import Fraction as F
from collections import defaultdict
import json,hashlib,argparse
from probe_external_integer_bridge import read
from score import square,contains

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def measure(path):
 L,span,W,pts=read(path);out=defaultdict(F)
 for x,y,w in pts:out[F(x)*L/span,F(y)*L/span]+=F(w,W)
 return L,out

def validate(config,new_candidate,repair):
 c=json.loads(config.read_text());old=Path(c['parent']);assert digest(old)==c['candidate_sha256'];L,before=measure(old);L2,after=measure(new_candidate);assert L==L2 and set(before)==set(after);assert all(after[p]>=w for p,w in before.items());assert sum(after.values())<c['n']
 rowsfile=Path(c['output'])/'roots.jsonl';rows=[json.loads(l) for l in rowsfile.read_text().splitlines()];g=c['grid'];u=c['ubins'];inherited=[];pending=[]
 if 'frontier' in c:
  previous=Path(c['frontier']);assert digest(previous)==c['frontier_sha256']
  prior=validate(Path(c['predecessor_config']),old,Path(c['repair']))
  assert prior==json.loads(previous.read_text())
  inputs=prior['pending'];inherited=list(prior['inherited_root_indices'])
 else:
  inputs=[]
  for index in range(g*g*u):
   i=index//(g*u);j=(index//u)%g;k=index%u
   inputs.append(dict(parent_index=index,box=list(map(str,(L*i/(2*g),L*(i+1)/(2*g),L*j/(2*g),L*(j+1)/(2*g),F(k,2*u),F(k+1,2*u))))))
 assert len(rows)==len(inputs);failed=set()
 for index,(r,entry) in enumerate(zip(rows,inputs)):
  assert r['index']==index and r['config_sha256']==digest(config);expected=tuple(map(F,entry['box']));assert tuple(map(F,r['root']))==expected
  assert len(r['uncertified'])==r['stats']['UNCERT']
  if r['uncertified']:failed.add(entry['parent_index'])
  for b in r['uncertified']:
   box=tuple(map(F,b));assert all(expected[d]<=box[d]<=box[d+1]<=expected[d+1] for d in (0,2,4));pending.append(dict(parent_index=entry['parent_index'],box=b))
 inherited=sorted(set(inherited)|({p['parent_index'] for p in inputs}-failed))
 data=json.loads(repair.read_text());assert data['sha256']==digest(new_candidate);witnesses=[]
 for r in data['witnesses']:
  x,y,t=map(F,r['pose']);poly=square(x,y,F(1),t);assert all(0<=px<=L and 0<=py<=L for px,py in poly)
  score=sum((w for p,w in after.items() if contains(poly,p)),F(0));assert score>=F(data['target']);witnesses.append(dict(pose=r['pose'],score=str(score)))
 result=dict(status='MONOTONE_ROOT_INHERITANCE_CHECKED',old_sha256=digest(old),new_sha256=digest(new_candidate),roots_sha256=digest(rowsfile),config_sha256=digest(config),same_container=True,pointwise_nondecrease=True,total_mass=str(sum(after.values())),inherited_root_indices=inherited,pending=pending,replayed_witnesses=witnesses,source_checker_independently_replayed=False,general_coverage_verified=False)
 if 'frontier' in c:result['prior_inheritance_sha256']=c['frontier_sha256']
 return result

def run(config,new_candidate,repair,out):
 assert not out.exists();result=validate(config,new_candidate,repair);out.write_text(json.dumps(result,indent=2));print('inherited',len(result['inherited_root_indices']),'pending leaves',len(result['pending']),'mass',float(F(result['total_mass'])),'witnesses',len(result['replayed_witnesses']))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('config',type=Path);p.add_argument('candidate',type=Path);p.add_argument('repair',type=Path);p.add_argument('out',type=Path);a=p.parse_args();run(a.config,a.candidate,a.repair,a.out)
