"""Checkpointed exhaustive D4 root diagnosis using a pinned upstream checker."""
from pathlib import Path
from fractions import Fraction as F
import argparse,json,hashlib,importlib.util,time,os,fcntl,traceback
from probe_external_integer_bridge import read

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def atomic(p,data):
 tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(data,indent=2));tmp.replace(p)
def ledger(status,job):
 with Path('runs/mother_owned.jsonl').open('a') as f:
  fcntl.flock(f,fcntl.LOCK_EX);f.write(json.dumps(dict(owner='codex',pid=os.getpid(),job=job,status=status))+'\n');f.flush()
def run(config,workers):
 c=json.loads(config.read_text());assert workers==1;cand=Path(c['parent']);checker=Path(c['checker']);out=Path(c['output']);out.mkdir(exist_ok=True)
 assert digest(cand)==c['candidate_sha256'] and digest(checker)==c['checker_sha256'];m,span,W,pts=read(cand);assert m==F(c['L']);assert F(sum(w for x,y,w in pts),W)<c['n']
 spec=importlib.util.spec_from_file_location('pinned_zm',checker);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
 side,points,weights=mod.read_cert(str(cand));chk=mod.Checker(side,points,weights,max_depth=c['depth'],use_chain=c['chain'],theta_bias=4);assert chk.symmetric_d4()
 if 'frontier' in c:
  from inherit_monotone_cover_roots import run as replay_inheritance
  frontier=Path(c['frontier']);assert digest(frontier)==c['frontier_sha256']
  replay_file=out/'inheritance.replayed.json'
  if replay_file.exists():replay_file.unlink()
  replay_inheritance(Path(c['predecessor_config']),cand,Path(c['repair']),replay_file)
  inherited=json.loads(frontier.read_text());assert json.loads(replay_file.read_text())==inherited
  roots=[tuple(map(F,row['box'])) for row in inherited['pending']]
 else:
  roots=mod.d4_roots(side,side/(2*c['grid']),c['ubins']);assert len(roots)==c['grid']**2*c['ubins']
 frontier_indices=list(range(len(roots)))
 if c.get('pilot_count'):
  n=min(c['pilot_count'],len(roots));frontier_indices=[i*len(roots)//n for i in range(n)];roots=[roots[i] for i in frontier_indices]
 chain_checker=mod.Checker(side,points,weights,max_depth=0,use_chain=True,theta_bias=4,chain_from=0) if c.get('hybrid') else None
 rows=out/'roots.jsonl';done=[]
 if rows.exists():
  for line in rows.read_text().splitlines():
   r=json.loads(line);assert r['index']==len(done) and r['root']==list(map(str,roots[len(done)]));assert r['config_sha256']==digest(config);done.append(r)
 start=time.monotonic();job=c['id'];ledger('RUNNING',job)
 def progress(status):
  unc=sum(r['stats']['UNCERT'] for r in done);record=dict(operation='proof_roots',status=status,roots_done=len(done),roots_total=len(roots),roots_certified=sum(r['stats']['UNCERT']==0 for r in done),uncertified_leaves=unc,pid=os.getpid(),elapsed_this_run=time.monotonic()-start)
  atomic(out/'progress.json',dict(records=[record]));return record
 try:
  progress('RUNNING')
  with rows.open('a') as f:
   for index in range(len(done),len(roots)):
    root=roots[index];t=time.monotonic();chk.fast='check' if c.get('selfcheck_all') or index%100==0 else True;stats,unc,leaves=chk.run_box(root)
    split_seconds=time.monotonic()-t;split_stats=dict(stats);chain_stats=None;chain_seconds=0
    if unc and chain_checker is not None:
     chain_checker.fast=chk.fast;ct=time.monotonic();chain_stats,chain_unc,_=chain_checker.run_box(root);chain_seconds=time.monotonic()-ct
     if not chain_unc:stats,unc=chain_stats,[]
    r=dict(index=index,frontier_index=frontier_indices[index],root=list(map(str,root)),config_sha256=digest(config),stats=stats,uncertified=[list(map(str,b)) for b in unc],selfcheck=chk.fast=='check',seconds=time.monotonic()-t,split_seconds=split_seconds,split_stats=split_stats,chain_seconds=chain_seconds,chain_stats=chain_stats)
    f.write(json.dumps(r)+'\n');f.flush();done.append(r)
    if len(done)%c.get('progress_every',100)==0:print(json.dumps(progress('RUNNING')),flush=True)
  result=progress('SAVED_ROOT_DIAGNOSIS');result.update(candidate_sha256=digest(cand),checker_sha256=digest(checker),full_domain_roots_visited='frontier' not in c,frontier_visited='frontier' in c and not c.get('pilot_count'),general_coverage_verified=not c.get('pilot_count') and not any(r['stats']['UNCERT'] for r in done),independent_replay=False);atomic(out/'result.json',result);ledger('COMPLETED',job);print(json.dumps(result),flush=True)
 except BaseException:
  progress('ERROR');ledger('FAILED',job);raise
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('config',type=Path);p.add_argument('--workers',type=int,default=1);a=p.parse_args();run(a.config,a.workers)
