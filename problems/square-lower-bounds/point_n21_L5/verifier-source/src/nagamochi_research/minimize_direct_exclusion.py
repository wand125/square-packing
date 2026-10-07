"""Greedily shrink a replayed exclusion; unresolved trials never remove boxes."""
import argparse,json,time
from pathlib import Path
from direct_normalized_search import run,verify


def minimize(source,out,nodes):
    original=json.loads(source.read_text());assert verify(original)
    best=original;out.mkdir(parents=True,exist_ok=True);attempts=[];start=time.monotonic()
    for removed in original['chosen']:
        chosen=[i for i in best['chosen'] if i!=removed]
        if not chosen:continue
        q=run(best['config'],best['missing'],chosen,nodes)
        name='without-%d.json'%removed;(out/name).write_text(json.dumps(q,indent=2))
        attempts.append(dict(removed=removed,chosen=chosen,verified=q['verified'],nodes=q.get('nodes'),path=name))
        if q['verified']:best=q
        summary=dict(status='RUNNING',best_chosen=best['chosen'],attempts=attempts,seconds=time.monotonic()-start)
        tmp=out/'summary.tmp';tmp.write_text(json.dumps(summary,indent=2));tmp.replace(out/'summary.json')
        print(attempts[-1],flush=True)
    assert verify(best)
    (out/'best.json').write_text(json.dumps(best,indent=2))
    summary.update(status='GREEDY_SHRINK_FINISHED',limitation='Not guaranteed inclusion-minimal: unresolved removals retain boxes.')
    (out/'summary.json').write_text(json.dumps(summary,indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('out',type=Path)
    p.add_argument('--nodes',type=int,default=300);a=p.parse_args();assert a.nodes>0
    minimize(a.source,a.out,a.nodes)
