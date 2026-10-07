"""Fresh numerical root or sieve replay, including every added repair."""
from pathlib import Path
from fractions import Fraction as F
from collections import Counter
import argparse,json,time,os
from frontier import ROOT,R,sha,load,boxkey
from compile_box_capture_rows import geometry,validate_partition
from physical_pose_enclosure import enclose,replay_partition
from replay_physical_point_witness import replay as witness_replay
from point_box_sieve import replay as sieve_replay
from stratified_box_cover import verify as cover_replay
from verify_angle_clip import verify as clip_replay
from checkpoint_external_cover import atomic
ap=argparse.ArgumentParser();ap.add_argument('--stage',choices=['root','sieve'],required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();out=a.out;out.mkdir(exist_ok=False);(out/'proofs').mkdir();candidate=R/'n21_L5_refit29_counterexample_trial/refit/candidate.txt';expected=sha(candidate);L,c,w,_=geometry(candidate);q=F(249987,250000);assert L==5 and all(x>=0 for x in w) and sum(w,F())<21*q
bindings={str(p):sha(p) for p in list((ROOT/'src/nagamochi_research').glob('*.py'))+list(Path(__file__).resolve().parent.glob('*.py'))+[candidate]}
def read(p,h=None):
 p=Path(p);p=p if p.is_absolute() else ROOT/p;d=load(p,h);bindings[str(p)]=sha(p);return d
folder=R/f'n21_L5_refit29_{a.stage}_transfer_trial';front=read(folder/'frontier-output.json');assert front['candidate_sha256']==expected;assembly=read(R/'n21_L5_refit29_additional_assembly_trial/manifest.json');assert assembly['candidate_sha256']==expected;repairs={e['additional_index']:e for e in assembly['entries'] if e['stage']==a.stage};assert set(repairs)==set(range(len(front['additional_pending'])))
def repair(i):
 entry=repairs[i];box=front['additional_pending'][i]['box'];assert boxkey(entry['box'])==boxkey(box);proof=read(entry['path'],entry['sha256']);assert proof['candidate_sha256']==expected;checked=replay_partition(candidate,box,proof['records'],expected);assert checked['lower'] is None or F(checked['lower'])>=q;return checked
pending=[];counts=dict(witnesses=0,empty=0,repairs=0,clips=0,strata=0);start=time.monotonic()
if a.stage=='root':
 cfg=read(R/'n21_L5_refit27_root_independent_m1_trial/n21_L5_refit27_root_independent_m1_trial.json');additional={(z['parent_index'],z['source_leaf']):i for i,z in enumerate(front['additional_pending'])};assert len(additional)==len(repairs)
 for i in range(5000):
  sourcepath=R/'n21_L5_refit27_root_replay_m1_trial/proofs'/f'{i:06d}.json.gz';source=read(sourcepath,cfg['proof_sha256'][sourcepath.name]);saved=read(folder/'proofs'/f'{i:06d}.json');assert saved['new_candidate_sha256']==expected and saved['source_proof_sha256']==sha(sourcepath)
  x,z=divmod(i,200);y,t=divmod(z,8);root=[F(x,10),F(x+1,10),F(y,10),F(y+1,10),F(t,16),F(t+1,16)];assert source['index']==i and boxkey(source['root'])==tuple(root)
  witnesses={z['leaf']:z for z in saved['witnesses']};assert len(witnesses)==len(saved['witnesses']);closed=[];opened=[];used=set();results=[]
  for j,(box,kind,_) in enumerate(source['success_leaves']):
   closed.append(box)
   if kind=='EMPTY':assert enclose(L,box)['enclosing_box'] is None and j not in witnesses;counts['empty']+=1
   elif j in witnesses:
    assert kind=='ADM';z=witnesses[j];assert boxkey(z['box'])==boxkey(box);value=witness_replay(c,w,L,box,z['indices']);assert value>=q;used.add(j);counts['witnesses']+=1
   else:
    assert kind=='ADM' and (i,j) in additional;k=additional[(i,j)];assert boxkey(front['additional_pending'][k]['box'])==boxkey(box);results.append(repair(k));counts['repairs']+=1
  assert used==set(witnesses)
  for event in source['clip_events']:
   fresh=clip_replay(L,event['original'],event['cut']);assert fresh['clipped'] and fresh['lower_open'];b=event['original'].copy();b[4]=event['cut'];opened.append(b);counts['clips']+=1
  closed.extend(source['uncertified']);coverage=cover_replay(root,closed,opened);counts['strata']+=coverage['strata_checked'];pending.extend(dict(parent_index=i,box=b) for b in source['uncertified']);atomic(out/'proofs'/f'{i:06d}.json',dict(index=i,root=list(map(str,root)),coverage=coverage,repairs=results,local_parts_numerically_replayed=True))
  if i%100==0:atomic(out/'progress.json',dict(status='RUNNING',pid=os.getpid(),done=i+1,total=5000,seconds=time.monotonic()-start,counts=counts));print(i+1,counts,flush=True)
 assert pending==front['inherited_pending'] and counts['repairs']==12
else:
 incoming=read(R/'n21_L5_refit29_root_transfer_trial/frontier-output.json')['inherited_pending'];additional={(z['frontier_index'],z['source_leaf']):i for i,z in enumerate(front['additional_pending'])};assert len(additional)==len(repairs);recordpath=folder/'records.jsonl';bindings[str(recordpath)]=sha(recordpath);count=0
 with recordpath.open() as stream:
  for i,line in enumerate(stream):
   row=json.loads(line);parent=incoming[i];assert row['index']==i and row['candidate_sha256']==expected and row['parent_index']==parent['parent_index'] and boxkey(row['root'])==boxkey(parent['box']);validate_partition(parent['box'],[z['enclosure']['original_box'] for z in row['leaves']]);results=[]
   for j,z in enumerate(row['leaves']):
    enclosure=enclose(L,z['enclosure']['original_box']);assert enclosure==z['enclosure'];box=enclosure['enclosing_box'];proof=z['proof']
    if box is None:assert proof is None;counts['empty']+=1
    elif proof is not None:
     value=sieve_replay(c,w,box,proof);counts['witnesses']+=1
    elif (i,j) in additional:
     k=additional[(i,j)];assert boxkey(front['additional_pending'][k]['box'])==boxkey(enclosure['original_box']);results.append(repair(k));counts['repairs']+=1
    else:pending.append(dict(parent_index=parent['parent_index'],frontier_index=i,box=enclosure['original_box']))
   atomic(out/'proofs'/f'{i:06d}.json',dict(index=i,parent=parent['box'],repairs=results,partition_recomputed=True,local_parts_numerically_replayed=True));count+=1
   if i%100==0:atomic(out/'progress.json',dict(status='RUNNING',pid=os.getpid(),done=count,total=len(incoming),seconds=time.monotonic()-start,counts=counts));print(count,counts,flush=True)
 assert count==len(incoming)==8758 and pending==front['inherited_pending'] and counts['repairs']==104
assert all(sha(p)==h for p,h in bindings.items());atomic(out/'inputs.json',dict(candidate_sha256=expected,stage=a.stage,bindings=bindings));atomic(out/'result.json',dict(candidate_sha256=expected,threshold=str(q),stage=a.stage,counts=counts,pending=pending,seconds=time.monotonic()-start,local_parts_numerically_replayed=True,complete_stage_partition_verified=True,general_coverage_verified=False));atomic(out/'progress.json',dict(status='COMPLETED',pid=os.getpid(),counts=counts));print(a.stage,'COMPLETED',counts,flush=True)
