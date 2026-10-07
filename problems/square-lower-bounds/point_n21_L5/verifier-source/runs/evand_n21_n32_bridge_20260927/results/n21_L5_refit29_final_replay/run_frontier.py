from pathlib import Path
import argparse,json,time,os,hashlib
from frontier import Checker,ROOT,sha
from checkpoint_external_cover import atomic
ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);ap.add_argument('--indices',type=int,nargs='+');ap.add_argument('--shard',type=int,default=0);ap.add_argument('--shards',type=int,default=1);a=ap.parse_args();assert 0<=a.shard<a.shards
out=a.out;out.mkdir(exist_ok=False);(out/'proofs').mkdir();checker=Checker();ids=a.indices if a.indices is not None else [i for i in sorted(checker.required) if i%a.shards==a.shard];assert len(ids)==len(set(ids)) and set(ids)<=checker.required
files=list((ROOT/'src/nagamochi_research').glob('*.py'))+list(Path(__file__).resolve().parent.glob('*.py'))+[checker.old,checker.new,checker.front]
bindings={str(p):sha(p) for p in files};atomic(out/'inputs.json',dict(indices=ids,candidate_sha256=checker.newsha,threshold=str(checker.q),bindings=bindings));start=time.monotonic();done=[]
for i in ids:
 atomic(out/'progress.json',dict(status='RUNNING',pid=os.getpid(),done=len(done),total=len(ids),current=i,seconds=time.monotonic()-start));record=checker.parent(i);atomic(out/'proofs'/f'{i:06d}.json',record);done.append(i);print(i,record['lower'],sorted(set(z['method'] for z in record['leaves'])),flush=True)
assert all(sha(p)==h for p,h in bindings.items());atomic(out/'result.json',dict(candidate_sha256=checker.newsha,threshold=str(checker.q),indices=done,total=len(done),seconds=time.monotonic()-start,numerically_replayed=True,general_coverage_verified=False));atomic(out/'progress.json',dict(status='COMPLETED',pid=os.getpid(),done=len(done),total=len(ids)))
