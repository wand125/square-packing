"""Resume high-impact direct exclusions, preserving and replaying old trees."""
import argparse,hashlib,json,os,time
from pathlib import Path
from direct_normalized_search import reconstruct,verify
from resume_disjunctive import resume_model


def campaign(tasks,out,shard,shards,nodes):
    selected=json.loads(tasks.read_text())[shard::shards]
    out.mkdir(parents=True,exist_ok=True);start=time.monotonic()
    summary=dict(status='RUNNING',worker_pid=os.getpid(),total=len(selected),cases=[])
    def save():
        summary['seconds']=time.monotonic()-start
        tmp=out/'summary.tmp';tmp.write_text(json.dumps(summary,indent=2));tmp.replace(out/'summary.json')
    save()
    for task in selected:
        source=Path(task['source']);raw=source.read_bytes()
        assert hashlib.sha256(raw).hexdigest()==task['sha256']
        old=json.loads(raw);assert old['chosen']==task['chosen']
        data=reconstruct(old);index=len(data[0][0])-1
        result=resume_model(data,old['tree'],nodes,positive_index=index)
        q=dict(old);q.update(result,source=str(source),source_sha256=task['sha256'],additional_node_limit=nodes)
        assert q['verified']==verify(q)
        name='case-'+'-'.join(map(str,q['chosen']))+'.json'
        tmp=out/(name+'.tmp');tmp.write_text(json.dumps(q,indent=2));tmp.replace(out/name)
        entry=dict(chosen=q['chosen'],status=q['status'],verified=q['verified'],nodes=q['nodes'],
                   reused_subtrees=q['reused_subtrees'],covered_targets=task['covered_targets'],path=name)
        summary['cases'].append(entry);save();print(entry,flush=True)
    summary['status']='RESEARCH_RESUME_FINISHED';save()


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('tasks',type=Path);p.add_argument('out',type=Path)
    p.add_argument('--shard',type=int,required=True);p.add_argument('--shards',type=int,default=2)
    p.add_argument('--nodes',type=int,default=500);a=p.parse_args()
    assert 0<=a.shard<a.shards and a.nodes>0
    campaign(a.tasks,a.out,a.shard,a.shards,a.nodes)
