"""Search the explicitly listed residual fixed-epsilon target sets."""
import argparse,hashlib,json,os,time
from pathlib import Path
from fractions import Fraction as F
from direct_fixed_epsilon import run,verify
from normalized_axis_cells import geometry


def campaign(source,subsets,out,epsilon,shard,shards,nodes):
    base=json.loads(source.read_text());cfg=base['config'];e=str(F(epsilon))
    assert 0<F(e)<=F(cfg['eps_max'])
    raw=subsets.read_bytes();sets=json.loads(raw);_,pieces=geometry(cfg,[])
    target=base['n']-(cfg['k']-1)**2
    assert len({tuple(c) for c in sets})==len(sets)
    assert all(len(c)==target and c==sorted(set(c)) and all(type(i) is int and 0<=i<len(pieces) for i in c) for c in sets)
    selected=sets[shard::shards];out.mkdir(parents=True,exist_ok=True);start=time.monotonic()
    summary=dict(status='RUNNING',worker_pid=os.getpid(),config=cfg,fixed_epsilon=e,
                 subsets=str(subsets),subsets_sha256=hashlib.sha256(raw).hexdigest(),
                 shard=shard,shards=shards,total=len(selected),cases=[],
                 limitation='Only listed target sets, fixed epsilon and specified angle/occupancy scope.')
    def save():
        summary['seconds']=time.monotonic()-start
        tmp=out/'summary.tmp';tmp.write_text(json.dumps(summary,indent=2));tmp.replace(out/'summary.json')
    save()
    for chosen in selected:
        path=out/('case-'+'-'.join(map(str,chosen))+'.json')
        if path.exists():
            q=json.loads(path.read_text());assert q['config']==cfg and q['fixed_epsilon']==e and q['chosen']==chosen and q['missing']==[]
            assert verify(q)==q['verified']
        else:
            q=run(cfg,[],chosen,e,nodes);tmp=path.with_suffix('.tmp')
            tmp.write_text(json.dumps(q,indent=2));tmp.replace(path)
        item=dict(chosen=chosen,status=q['status'],verified=q['verified'],nodes=q['nodes'],path=path.name)
        summary['cases'].append(item);save();print(item,flush=True)
    summary['status']='SUBSET_PILOT_FINISHED';save()


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('subsets',type=Path);p.add_argument('out',type=Path)
    p.add_argument('--epsilon',required=True);p.add_argument('--shard',type=int,required=True)
    p.add_argument('--shards',type=int,default=2);p.add_argument('--nodes',type=int,default=300)
    a=p.parse_args();assert 0<=a.shard<a.shards and a.nodes>0
    campaign(a.source,a.subsets,a.out,a.epsilon,a.shard,a.shards,a.nodes)
