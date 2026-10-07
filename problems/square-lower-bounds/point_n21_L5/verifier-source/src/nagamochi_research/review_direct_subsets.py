"""Replay small-set cuts and enumerate surviving target region subsets.

Unfinished or numerically feasible cases supply no exclusions. Even a partial
collection of replayed cuts gives a rigorous conditional candidate reduction.
"""
import argparse, hashlib, json, time
from collections import Counter
from fractions import Fraction as F
from pathlib import Path
from direct_normalized_search import verify
from normalized_axis_cells import geometry
from joint_angle_lp import rotation


def survivors(n, cuts, target):
    assert 0 <= target <= n
    adjacent = [0]*n; ending = [[] for _ in range(n)]
    for cut in cuts:
        assert cut and list(cut)==sorted(set(cut)) and all(type(i) is int and 0<=i<n for i in cut)
        if len(cut)==2:
            i,j=cut; adjacent[i] |= 1 << j; adjacent[j] |= 1 << i
        else:
            ending[cut[-1]].append(sum(1 << i for i in cut))
    def walk(available, chosen, bits):
        if len(chosen)==target:
            yield list(chosen); return
        while available.bit_count() >= target-len(chosen):
            bit=available & -available; available ^= bit; v=bit.bit_length()-1
            newbits=bits | bit
            if any(newbits & mask == mask for mask in ending[v]):continue
            yield from walk(available & ~adjacent[v], chosen+(v,), newbits)
    yield from walk((1 << n)-1, (), 0)


def review(root, out, symmetry=False):
    start=time.monotonic();base=json.loads((root/'n32.json').read_text());cfg=base['config']
    cells,pieces=geometry(cfg,[]);R=F(cfg['rot_inner']);c,s=rotation(F(cfg['t']))
    assert all(max(a*x+b*y for x,y in p)-min(a*x+b*y for x,y in p)<R
               for p in pieces for a,b in ((c,s),(-s,c)))
    cuts=[];proofs=[];counts=Counter();leaves=Counter();seen=set()
    def walk(t):
        if not t.get('children'):leaves[t['status']]+=1
        for child in t.get('children',[]):walk(child)
    paths=sorted(root.glob('shard*/pair-*.json'))+sorted(root.glob('triples*/pair-*.json'))
    for path in paths:
        raw=path.read_bytes();q=json.loads(raw)
        assert q['config']==cfg and q['missing']==[]
        key=tuple(q['chosen']);assert key not in seen;seen.add(key)
        if q.get('verified'):
            assert verify(q)
            cuts.append(key);proofs.append(dict(path=str(path.relative_to(root)),sha256=hashlib.sha256(raw).hexdigest()))
            counts[f'excluded_{len(key)}']+=1
        else:
            counts[f'unresolved_{len(key)}']+=1;walk(q['tree'])
    rotation_proof=None
    if symmetry:
        from direct_rotation_cuts import extend
        cuts,rotation_proof=extend(cells,pieces,cfg['t'],cfg['rot_inner'],cuts)
    target=base['necessary_outside_axis_band'];remaining=list(survivors(len(pieces),cuts,target))
    out.mkdir(parents=True,exist_ok=True)
    (out/'remaining.json').write_text(json.dumps(remaining))
    q=dict(status='EXACT_CONDITIONAL_SUBSET_REDUCTION',config=cfg,missing=[],
           regions=len(pieces),target=target,cuts=[list(c) for c in cuts],proofs=proofs,
           reviewed_cases=len(paths),counts=dict(counts),remaining_sets=len(remaining),rotation_proof=rotation_proof,
           unresolved_leaf_counts=dict(leaves),seconds=time.monotonic()-start,
           limitation='Saturated axis cells and specified rotor band only. No unrestricted lower bound.')
    (out/'review.json').write_text(json.dumps(q,indent=2))
    print({k:q[k] for k in ('status','reviewed_cases','counts','remaining_sets','unresolved_leaf_counts','seconds')},flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('root',type=Path);p.add_argument('out',type=Path)
    p.add_argument('--symmetry',action='store_true')
    a=p.parse_args();review(a.root,a.out,a.symmetry)
