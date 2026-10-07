"""Finite exact-incidence L1 refit with both increases and decreases permitted.
Rounded weights are checked on every training row; held-out tests remain separate.
"""
from pathlib import Path
from fractions import Fraction as F
from math import lcm,ceil
import os,json,hashlib,random,time,argparse
for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS'):os.environ[k]='1'
import numpy as np
from scipy.optimize import linprog
from scipy.sparse import csr_matrix,hstack,vstack,eye
from probe_external_integer_bridge import read

def exact_hits(pts,L,span,pose):
 cx,cy,t=map(F,pose);p,q=t.numerator,t.denominator;a=q*q-p*p;b=2*p*q;r=q*q+p*p;h=F(abs(a)+abs(b),2*r)
 if not h<=cx<=L-h or not h<=cy<=L-h:raise ValueError('Physical square outside container')
 H=lcm(L.denominator,cx.denominator,cy.denominator);A=int(L*H);X0=int(span*cx*H);Y0=int(span*cy*H);limit=r*span*H
 return np.array([2*abs(a*(x*A-X0)+b*(y*A-Y0))<=limit and 2*abs(a*(y*A-Y0)-b*(x*A-X0))<=limit for x,y,w in pts])


def train_poses(L,count,seed):
 rng=random.Random(seed);poses=[]
 for i in range(count):
  t=F(0) if i%10==0 else (F(rng.randrange(1,101),10**rng.randrange(4,8)) if i%3==0 else F(rng.randrange(500001),1000000))
  h=(1-t*t+2*t)/(2*(1+t*t));reach=L-2*h;u,v=F(rng.randrange(1000001),1000000),F(rng.randrange(1000001),1000000)
  if i%5==0:u=F(0)
  elif i%5==1:v=F(0)
  poses.append((h+reach*u,h+reach*v,t))
 return poses

def solve_weights(A,original,sizes,budget,target,tiebreak='none',predicate_blocks=()):
 if tiebreak not in ('none','point_linf'):raise ValueError('Unknown tie break')
 n=len(original);zero=csr_matrix(A.shape);identity=eye(n,format='csr');massrow=csr_matrix(np.ones((1,n)))
 Aub=vstack([hstack([-A,zero]),hstack([identity,-identity]),hstack([-identity,-identity]),hstack([massrow,csr_matrix((1,n))])],format='csr');rhs=np.r_[-np.broadcast_to(np.asarray(target,dtype=float),(A.shape[0],)),original,-original,float(budget)]
 extra=sum(block['variables']-n for block in predicate_blocks)
 if extra:
  Aub=hstack([Aub,csr_matrix((Aub.shape[0],extra))],format='csr')
  rr=[];cc=[];vv=[];bb=[];offset=2*n
  for block in predicate_blocks:
   if block['orbit_variables']!=n:raise ValueError('Predicate orbit count mismatch')
   for terms,bound in block['rows']:
    k=len(bb);bb.append(-float(bound))
    for j,value in terms.items():
     rr.append(k);cc.append(j if j<n else offset+j-n);vv.append(-float(value))
   offset+=block['variables']-n
  rows=csr_matrix((vv,(rr,cc)),shape=(len(bb),2*n+extra))
  Aub=vstack([Aub,rows],format='csr');rhs=np.r_[rhs,bb]
 objective=np.r_[np.zeros(n),np.ones(n),np.zeros(extra)]
 sol=linprog(objective,A_ub=Aub,b_ub=rhs,bounds=(0,None),method='highs',options={'threads':1});assert sol.success,sol.message
 first=float(sol.fun);secondary=None
 if tiebreak=='point_linf':
  # d_j bounds the change of TOTAL orbit mass, so divide by orbit size.
  cap=csr_matrix(np.r_[objective,0].reshape(1,-1))
  deviation=hstack([csr_matrix((n,n)),identity,csr_matrix((n,extra)),csr_matrix(-sizes.reshape(-1,1))])
  constraints=vstack([hstack([Aub,csr_matrix((Aub.shape[0],1))]),cap,deviation],format='csr')
  sol=linprog(np.r_[np.zeros(2*n+extra),1.],A_ub=constraints,b_ub=np.r_[rhs,first+1e-8,np.zeros(n)],bounds=(0,None),method='highs',options={'threads':1});assert sol.success,sol.message
  secondary=float(sol.fun)
 return sol,first,secondary


def round_to_row_targets(counts,nums,thresholds):
 """Upward rational rescaling for heterogeneous capture thresholds."""
 captures=counts.astype(np.int64)@nums
 assert len(captures)==len(thresholds) and np.all(captures>0) and np.all(thresholds>0)
 factor=max([F(1)]+[F(int(t),int(v)) for t,v in zip(thresholds,captures)])
 if factor>1:
  nums=np.array([ceil(int(z)*factor) for z in nums],dtype=np.int64)
  captures=counts.astype(np.int64)@nums
 assert np.all(captures>=thresholds)
 return nums,captures


def run(source,witnesses,out,count=8192,seed=9280200,capture_target=F(10001,10000),tiebreak='none',proof_rows=None,predicate_proofs=None):
 out.mkdir(exist_ok=False);started=time.monotonic();native,span,W,pts=read(source);data=json.loads(witnesses.read_text());assert hashlib.sha256(source.read_bytes()).hexdigest()==data['source_sha256'];L=F(data['L']);assert L==native;poses=sorted(set(train_poses(L,count,seed)+[tuple(map(F,r['pose'])) for r in data['witnesses']]))
 groups={}
 for i,(x,y,w) in enumerate(pts):groups.setdefault(tuple(sorted((min(x,span-x),min(y,span-y)))),[]).append(i)
 orbits=list(groups.values());sizes=np.array(list(map(len,orbits)));ids=np.zeros(len(pts),int)
 for j,o in enumerate(orbits):ids[o]=j;assert len({pts[i][2] for i in o})==1
 original=np.array([sum(pts[i][2] for i in o)/W for o in orbits]);counts=np.empty((len(poses),len(orbits)),dtype=np.uint8)
 for index,(cx,cy,t) in enumerate(poses):
  hit=exact_hits(pts,L,span,(cx,cy,t));counts[index]=np.bincount(ids[hit],minlength=len(orbits))
  if (index+1)%2048==0:print('exact rows',index+1,'/',len(poses),flush=True)
 np.savez_compressed(out/'incidence.npz',counts=counts,sizes=sizes,orbit_ids=ids);(out/'poses.json').write_text(json.dumps([list(map(str,p)) for p in poses]))
 n=len(orbits);budget=F(209989,10000);target=F(capture_target);assert target>=1
 proof_count=0;all_counts=counts;targets=[target]*len(poses);proof_digest=None
 if proof_rows is not None:
  from compile_box_capture_rows import replay_rows
  proof_digest=hashlib.sha256(proof_rows.read_bytes()).hexdigest();proof=json.loads(proof_rows.read_text())
  replay_rows(proof_rows,source) # geometry/partition replay; source masses may be below target
  proof_counts=np.array([np.bincount(ids[row['indices']],minlength=n) for row in proof['rows']],dtype=np.int64)
  assert proof_counts.ndim==2 and proof_counts.shape[1]==n and np.all(proof_counts<=sizes)
  proof_count=len(proof_counts);assert proof_count>0
  all_counts=np.vstack([counts,proof_counts]);targets += [F(1)]*proof_count
  np.savez_compressed(out/'proof-incidence.npz',counts=proof_counts,sizes=sizes,orbit_ids=ids)
  (out/'proof-rows.json').write_text(json.dumps(proof,indent=2))
 predicate_models=[];predicate_blocks=[];predicate_labels=[];predicate_digest=None
 if predicate_proofs is not None:
  from predicate_weight_rows import compile_model,evaluate,weight_rows
  from compile_box_capture_rows import geometry
  predicate_data=json.loads(predicate_proofs.read_text())
  if predicate_data['candidate_sha256']!=data['source_sha256']:raise ValueError('Predicate proof source mismatch')
  _,coordinates,weights,_=geometry(source);source_points=[(*p,w) for p,w in zip(coordinates,weights)]
  predicate_digest=hashlib.sha256(predicate_proofs.read_bytes()).hexdigest()
  for record in predicate_data['records']:
   # Only preserve demonstrated guarantees; failed bounds are not inherited.
   if F(record['lower'])<1:continue
   model=compile_model(source_points,record['box'],record)
   if evaluate(model,source_points)<1:raise ValueError('Source predicate guarantee failed')
   predicate_models.append(model);predicate_labels.append(record['label'])
   predicate_blocks.append(weight_rows(model,list(map(int,ids)),list(map(int,sizes)),F(1)+F(1,10**9)))
  if not predicate_models:raise ValueError('No successful predicate proofs')
  (out/'predicate-source-proofs.json').write_text(json.dumps(predicate_data,indent=2))
 A=csr_matrix(all_counts.astype(float)/sizes)
 sol,primary_objective,secondary_objective=solve_weights(A,original,sizes,budget,list(map(float,targets)),tiebreak,predicate_blocks)
 den=10**12;nums=np.array([ceil(max(0,float(z))*den/int(k)) for z,k in zip(sol.x[:n],sizes)],dtype=np.int64);assert int(nums@sizes)<2**63 and np.all(all_counts<=sizes)
 thresholds=np.array([ceil(t*den) for t in targets],dtype=np.int64)
 nums,all_captures=round_to_row_targets(all_counts,nums,thresholds)
 predicate_bounds=[]
 if predicate_models:
  rounded_points=[(*p,F(int(nums[ids[i]]),den)) for i,p in enumerate(coordinates)]
  predicate_bounds=[evaluate(model,rounded_points) for model in predicate_models]
  if any(bound<1 for bound in predicate_bounds):raise ValueError('Rounded predicate guarantee failed')
 captures=all_captures[:len(poses)];total=F(int(nums@sizes),den);assert total<F(20999,1000),str(total)
 outnums=[int(nums[ids[i]]) for i in range(len(pts))];D=int(F(span)/L);cert=out/'candidate.txt';cert.write_text('\n'.join([f'{L.numerator} {L.denominator}',str(D),str(den),str(len(pts))]+[f'{x} {y} {w}' for (x,y,_),w in zip(pts,outnums)])+'\n');read(cert)
 old=[F(sum(pts[i][2] for i in o),W) for o in orbits];new=[F(int(z)*int(k),den) for z,k in zip(nums,sizes)];delta=[a-b for a,b in zip(new,old)]
 result=dict(status='FINITE_L1_REFIT_EXACT_ROWS_PASSED',source_sha256=data['source_sha256'],sha256=hashlib.sha256(cert.read_bytes()).hexdigest(),L=str(L),total_mass=str(total),training_rows=len(poses),orbits=n,seed=seed,capture_target=str(target),lp_objective=primary_objective,tiebreak=tiebreak,secondary_objective=secondary_objective,primary_numerical_allowance=1e-8 if tiebreak!='none' else 0,actual_max_point_change=str(max(abs(d)/int(k) for d,k in zip(delta,sizes))),actual_l1_change=str(sum(map(abs,delta))),increased_orbits=sum(d>0 for d in delta),decreased_orbits=sum(d<0 for d in delta),training_minimum=str(F(int(captures.min()),den)),training_worst_pose=list(map(str,poses[int(captures.argmin())])),seconds=time.monotonic()-started,previous_proofs_inherited=False,general_coverage_verified=False)
 if proof_rows is not None:
  replay=replay_rows(out/'proof-rows.json',cert);assert replay['passed_rows']==proof_count
  assert replay['row_captures']==list(map(lambda v:str(F(int(v),den)),all_captures[len(poses):]))
  (out/'proof-replay.json').write_text(json.dumps(replay,indent=2))
  result.update(proof_rows=proof_count,proof_rows_sha256=proof_digest,proof_target='1',certified_regions_preserved=len(replay['retained_roots']),proof_minimum=str(F(int(all_captures[len(poses):].min()),den)))
 if predicate_models:
  replay=dict(source_proofs_sha256=predicate_digest,labels=predicate_labels,lower_bounds=list(map(str,predicate_bounds)),all_passed=True,model='fixed source geometry and multipliers',general_coverage_verified=False)
  (out/'predicate-replay.json').write_text(json.dumps(replay,indent=2))
  result.update(predicate_regions_preserved=len(predicate_models),predicate_minimum=str(min(predicate_bounds)),predicate_proofs_sha256=predicate_digest)
 (out/'result.json').write_text(json.dumps(result,indent=2));print(result,flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('witnesses',type=Path);p.add_argument('out',type=Path);p.add_argument('--count',type=int,default=8192);p.add_argument('--capture-target',default='10001/10000');p.add_argument('--tiebreak',choices=['none','point_linf'],default='none');p.add_argument('--proof-rows',type=Path);p.add_argument('--predicate-proofs',type=Path);a=p.parse_args();run(a.source,a.witnesses,a.out,a.count,capture_target=F(a.capture_target),tiebreak=a.tiebreak,proof_rows=a.proof_rows,predicate_proofs=a.predicate_proofs)
