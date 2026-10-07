"""Replay collected direct pair exclusions and count surviving target subsets."""
from collections import Counter
from functools import lru_cache
from itertools import combinations
from pathlib import Path
import argparse,json,time
from direct_normalized_search import verify
from normalized_axis_cells import geometry
from joint_angle_lp import rotation
from fractions import Fraction as F


def count_sets(n, edges, target):
    adj = [0]*n
    for i,j in edges:
        adj[i] |= 1 << j; adj[j] |= 1 << i
    @lru_cache(None)
    def count(mask, k):
        if k == 0: return 1
        if mask.bit_count() < k: return 0
        bit = mask & -mask; v = bit.bit_length()-1; rest = mask ^ bit
        return count(rest, k) + count(rest & ~adj[v], k-1)
    return count((1 << n)-1, target)


def review(root):
    start=time.monotonic();base=json.loads((root/'n32.json').read_text());cfg=base['config']
    _,pieces=geometry(cfg,[]);R=F(cfg['rot_inner']);c,s=rotation(F(cfg['t']))
    assert all(max(a*x+b*y for x,y in p)-min(a*x+b*y for x,y in p)<R
               for p in pieces for a,b in ((c,s),(-s,c)))
    edges=[];leaves=Counter();seen=set();statuses=Counter()
    def walk(t):
        if not t.get('children'):leaves[t['status']]+=1
        for child in t.get('children',[]):walk(child)
    for path in sorted(root.glob('shard*/pair-*.json')):
        q=json.loads(path.read_text());assert q['config']==cfg and q['missing']==[]
        key=tuple(q['chosen']);assert len(key)==2 and key not in seen;seen.add(key)
        ok=verify(q);assert ok==q['verified'];statuses[q['status']]+=1
        if ok:edges.append(key)
        else:walk(q['tree'])
    n=len(pieces);target=base['necessary_outside_axis_band']
    result=dict(status='EXACT_CONDITIONAL_PAIR_GRAPH',regions=n,target=target,
                reviewed_pairs=len(seen),total_pairs=n*(n-1)//2,edges=edges,
                surviving_target_sets=count_sets(n,edges,target),statuses=dict(statuses),
                unresolved_leaf_counts=dict(leaves),seconds=time.monotonic()-start,
                limitation='Partial graph if not all pairs reviewed. Missing cells and other rotor bands not covered.')
    (root/'pair-review.json').write_text(json.dumps(result,indent=2))
    print({k:v for k,v in result.items() if k!='edges'},'excluded_pairs',len(edges),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('root',type=Path);a=p.parse_args();review(a.root)
