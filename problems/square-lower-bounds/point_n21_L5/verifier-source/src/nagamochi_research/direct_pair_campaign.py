"""Sharded direct-domain pair pilot with exact replay and atomic checkpoints."""
import argparse
import json
import os
import time
from itertools import combinations
from pathlib import Path
from direct_normalized_search import run, verify
from normalized_axis_cells import geometry


def campaign(source, out, shard, shards, nodes, subsets=None):
    cfg = json.loads(source.read_text())['config']
    _, pieces = geometry(cfg, [])
    all_sets = list(combinations(range(len(pieces)), 2)) if subsets is None else json.loads(subsets.read_text())
    assert len({tuple(c) for c in all_sets}) == len(all_sets)
    assert all(c and list(c)==sorted(set(c)) and all(type(i) is int and 0<=i<len(pieces) for i in c) for c in all_sets)
    selected = all_sets[shard::shards]
    out.mkdir(parents=True, exist_ok=True)
    summary = dict(status='RUNNING', worker_pid=os.getpid(), config=cfg,
                   shard=shard, shards=shards, nodes_per_case=nodes,
                   total=len(selected), cases=[],
                   limitation='Saturated axis cells; one fixed rotor band; no global bound.')
    start = time.monotonic()
    def save():
        summary['seconds'] = time.monotonic()-start
        tmp = out/'summary.tmp'
        tmp.write_text(json.dumps(summary, indent=2)); tmp.replace(out/'summary.json')
    save()
    for pair in selected:
        path = out/('pair-'+'-'.join(map(str,pair))+'.json')
        try:
            if path.exists():
                q = json.loads(path.read_text())
                assert q['config'] == cfg and q['missing'] == [] and q['chosen'] == list(pair)
                q['verified'] = verify(q)
            else:
                q = run(cfg, [], pair, nodes)
                tmp = path.with_suffix('.tmp')
                tmp.write_text(json.dumps(q, indent=2)); tmp.replace(path)
            entry = dict(chosen=list(pair), status=q['status'], verified=q['verified'],
                         nodes=q.get('nodes'), path=path.name)
        except Exception as e:
            entry = dict(chosen=list(pair), status='ERROR', verified=False, error=repr(e))
        summary['cases'].append(entry); save(); print(entry, flush=True)
    summary['status'] = 'PAIR_PILOT_FINISHED_WITH_ERRORS' if any(c['status']=='ERROR' for c in summary['cases']) else 'PAIR_PILOT_FINISHED'
    save()


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path); p.add_argument('out', type=Path)
    p.add_argument('--shard', type=int, required=True); p.add_argument('--shards', type=int, default=4)
    p.add_argument('--nodes', type=int, default=100)
    p.add_argument('--subsets', type=Path)
    a = p.parse_args(); assert 0 <= a.shard < a.shards and a.nodes > 0
    campaign(a.source, a.out, a.shard, a.shards, a.nodes, a.subsets)
