"""PL18 graph capacity for all low-score cells of a preverified pose cover."""
import argparse,json,hashlib
from fractions import Fraction as F
from functools import lru_cache
from pathlib import Path
from packing_lemmas import regions_force_core_intersection
from physical_pose_bound import restrict_centres
from mixed_density_check import expand


def nominal_core(L, box):
    tight = restrict_centres(L, box)
    if tight is None: return None
    x0,x1,y0,y1,a,b = tight
    # theta(t)=2 atan(t), so |theta(t)-theta(mid)| <= b-a.
    # |cos(delta)|+|sin(delta)| <= 1+|delta| <= 1+b-a.
    # A strict factor retains interior containment even at equality.
    side = F(999999,1000000)/(1+b-a)
    return ([(x0,y0),(x1,y0),(x1,y1),(x0,y1)], (a+b)/2, side)


def conflict(a,b):
    return regions_force_core_intersection(a[0],b[0],a[1],b[1],a[2],b[2])


def independent_set(adj):
    @lru_cache(None)
    def solve(mask):
        if not mask: return ()
        # Independent components are additive and avoid a product of searches.
        seed=mask & -mask;component=0;frontier=seed
        while frontier:
            component |= frontier
            neighbors=0
            for i in range(len(adj)):
                if frontier>>i&1:neighbors |= adj[i]
            frontier=neighbors & mask & ~component
        if component != mask:
            return solve(component)+solve(mask & ~component)
        vertices=[i for i in range(len(adj)) if mask>>i&1]
        v=max(vertices,key=lambda i:(adj[i]&mask).bit_count())
        rest=mask & ~(1<<v)
        without=solve(rest)
        with_v=(v,)+solve(rest & ~adj[v])
        return with_v if len(with_v)>=len(without) else without
    return solve((1<<len(adj))-1)


def independent_number(adj):
    return len(independent_set(adj))


def run(candidate,cover,threshold,out):
    model=expand(json.loads(candidate.read_text()));L=model[0];q=json.loads(cover.read_text())
    if q['digest']!=model[-1]:raise ValueError('Candidate and source cover mismatch')
    if threshold<=0:raise ValueError('Threshold must be positive')
    cores=[];paths=[]
    for path,rec in q['leaves'].items():
        if rec['kind']=='OUTSIDE' or F(rec['lower'])>=threshold:continue
        core=nominal_core(L,tuple(map(F,rec['box'])))
        if core is not None:
            if not conflict(core,core):raise ValueError('Cell can contain multiple boxes; refine before graph bound')
            cores.append(core);paths.append(path)
    adj=[0]*len(cores);edges=[]
    for i,a in enumerate(cores):
        for j,b in enumerate(cores[:i]):
            if conflict(a,b):
                adj[i]|=1<<j;adj[j]|=1<<i;edges.append([j,i])
    witness=independent_set(adj);capacity=len(witness)
    assert all(not(adj[i]>>j&1) for i in witness for j in witness)
    # Independently rebuild every edge and the self-capacity conditions.
    rebuilt=[nominal_core(L,tuple(map(F,q['leaves'][p]['box']))) for p in paths]
    assert all(conflict(c,c) for c in rebuilt)
    assert all(conflict(rebuilt[i],rebuilt[j]) for i,j in edges)
    result=dict(status='EXACT_CONFLICT_GRAPH_CAPACITY',threshold=str(threshold),paths=paths,edges=edges,
                capacity=capacity,independent_set_paths=[paths[i] for i in witness],cover_sha256=hashlib.sha256(cover.read_bytes()).hexdigest(),
                candidate_sha256=hashlib.sha256(candidate.read_bytes()).hexdigest(),
                source_cover_requires_independent_replay=True,general_packing_exclusion=False)
    out.write_text(json.dumps(result,indent=2));print(dict(cells=len(paths),edges=len(edges),capacity=capacity),flush=True)
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser()
    for key in ('candidate','cover','out'):p.add_argument(key,type=Path)
    p.add_argument('--threshold',type=F,default=F(3,10));a=p.parse_args()
    run(a.candidate,a.cover,a.threshold,a.out)
