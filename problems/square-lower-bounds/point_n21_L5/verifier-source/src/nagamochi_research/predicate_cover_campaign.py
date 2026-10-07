"""Checkpointed, disjoint shards of exact local predicate-cover proofs.

Every saved gzip proof is read back and replayed. Resuming replays existing
artifacts; it never trusts a progress counter as evidence of certification.
This campaign covers only its supplied frontier, never the full container.
"""
import argparse
import fcntl
import gzip
import hashlib
import json
import os
from pathlib import Path
from time import monotonic
from fractions import Fraction as F
from adaptive_predicate_cover import cover
from compile_box_capture_rows import geometry
from physical_pose_enclosure import replay_partition
from checkpoint_external_cover import atomic, ledger

POLICY_KEYS = ('max_depth','max_cuts','branch_depth','branch_nodes','physical_cuts')


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def code_hashes(directory):
    return {p.name:digest(p) for p in sorted(Path(directory).glob('*.py'))}


def assigned_indices(count, shard, shards):
    if type(shard) is not int or type(shards) is not int or shards < 1 or not 0 <= shard < shards:
        raise ValueError('Invalid shard')
    return list(range(shard, count, shards))


def save_gzip(path, value):
    payload=json.dumps(value,separators=(',',':')).encode()
    tmp=path.with_suffix(path.suffix+'.tmp')
    tmp.write_bytes(gzip.compress(payload,compresslevel=6,mtime=0))
    tmp.replace(path)


def run(config_path, workers=1, *, track_ledger=True):
    if workers != 1:
        raise ValueError('Each campaign shard must use one worker')
    config_path=Path(config_path)
    config_digest=digest(config_path)
    c=json.loads(config_path.read_text())
    candidate=Path(c['parent']);frontier=Path(c['frontier']);out=Path(c['output'])
    if digest(candidate)!=c['candidate_sha256'] or digest(frontier)!=c['frontier_sha256']:
        raise ValueError('Changed candidate or frontier')
    if code_hashes(Path(__file__).parent)!=c['code_sha256']:
        raise ValueError('Changed implementation')
    data=json.loads(frontier.read_text())
    if data['candidate_sha256']!=c['candidate_sha256']:
        raise ValueError('Frontier candidate mismatch')
    L,coords,weights,_=geometry(candidate)
    if L!=F(c['L']) or not sum(weights,F(0)) <= F(c['target']) < c['n']:
        raise ValueError('Invalid candidate side or mass budget')
    points=[(*p,w) for p,w in zip(coords,weights)]
    indices=assigned_indices(len(data['pending']),c['shard'],c['shards'])
    if 'pilot_indices' in c:
        requested=c['pilot_indices']
        if len(set(requested))!=len(requested) or any(type(i) is not int or i not in indices for i in requested):
            raise ValueError('Invalid pilot subset')
        indices=requested
    out.mkdir(parents=True,exist_ok=True)
    artifacts=out/'proofs';artifacts.mkdir(exist_ok=True)
    lock=(out/'run.lock').open('a')
    try:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    except BlockingIOError:
        lock.close();raise RuntimeError('Campaign shard already running')
    start=monotonic();summaries=[];pending=[]
    def status(state):
        row=dict(operation='predicate_cover_campaign',status=state,pid=os.getpid(),
                 shard=c['shard'],shards=c['shards'],done=len(summaries),total=len(indices),
                 certified=sum(r['certified'] for r in summaries),
                 unresolved=len(pending),resumed=sum(r['resumed'] for r in summaries),
                 seconds=monotonic()-start)
        atomic(out/'progress.json',dict(records=[row]));return row
    try:
        if track_ledger:ledger('RUNNING',c['id'])
        status('RUNNING')
        # The journal is derived state. Proof artifacts remain authoritative
        # and survive a crash between artifact replacement and journal writes.
        with (out/'summary.jsonl').open('w') as journal:
            for index in indices:
                item=data['pending'][index];path=artifacts/f'{index:06d}.json.gz'
                context=dict(config_sha256=config_digest,candidate_sha256=c['candidate_sha256'],
                             frontier_sha256=c['frontier_sha256'],global_leaf_index=index,
                             input=item,L=str(L))
                begun=monotonic();resumed=path.exists()
                if not resumed:
                    result=cover(points,L,item['box'],**{k:c[k] for k in POLICY_KEYS})
                    save_gzip(path,dict(context=context,proof=result))
                saved=json.loads(gzip.decompress(path.read_bytes()))
                if saved['context']!=context:
                    raise ValueError('Saved proof input/configuration mismatch')
                proof=saved['proof']
                checked=replay_partition(candidate,item['box'],proof['records'],c['candidate_sha256'])
                certified=checked['certified_unit_capture']
                row=dict(global_leaf_index=index,certified=certified,lower=checked['lower'],
                         seconds=monotonic()-begun,resumed=resumed,bytes=path.stat().st_size,
                         proof_sha256=digest(path),leaves=len(proof['records']),nodes=len(proof['events']),
                         config_sha256=config_digest)
                summaries.append(row)
                if not certified:pending.append(dict(item,global_leaf_index=index))
                journal.write(json.dumps(row)+'\n');journal.flush()
                status('RUNNING')
                if len(summaries)%25==0:
                    print({'done':len(summaries),'total':len(indices),'certified':len(summaries)-len(pending),'shard':c['shard']},flush=True)
        result=status('SAVED_FRONTIER_SHARD')
        result.update(candidate_sha256=c['candidate_sha256'],frontier_sha256=c['frontier_sha256'],
                      config_sha256=config_digest,complete_assigned_frontier=not pending,
                      pilot='pilot_indices' in c,general_coverage_verified=False)
        atomic(out/'frontier-output.json',dict(candidate_sha256=c['candidate_sha256'],pending=pending,
                                               shard=c['shard'],general_coverage_verified=False))
        atomic(out/'result.json',result)
        if track_ledger:ledger('COMPLETED',c['id'])
        return result
    except BaseException:
        status('ERROR')
        if track_ledger:ledger('FAILED',c['id'])
        raise
    finally:
        lock.close()


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('config',type=Path)
    parser.add_argument('--workers',type=int,default=1);args=parser.parse_args()
    print(json.dumps(run(args.config,args.workers)),flush=True)
