"""Refine unresolved outside-anchor branches using newly priced clique cuts."""
import argparse,json,time
from fractions import Fraction as F
from pathlib import Path
from outside_anchor_probe import guaranteed_conflict
from refine_conflict_cover import run as refine


def run(family,branches,out,rounds):
    out.mkdir(parents=True,exist_ok=False);start=time.monotonic()
    f=json.loads((family/'family-poses.json').read_text());data=json.loads(branches.read_text())
    base,end=f['base'],f['endpoint'];E=F(data['epsilon_max']);alpha=F(data['alpha']);n=len(base)
    graph=[0]*n
    for i in range(n):
        for j in range(i):
            if guaranteed_conflict(base[i],end[i],base[j],end[j],E,alpha):
                graph[i]|=1<<j;graph[j]|=1<<i
    (out/'robust-graph.json').write_text(json.dumps([hex(x) for x in graph]))
    targets=[q for q in data['branches'] if q['outside_original_union'] and not q['excludes_one_anchor_plus_eleven_local']]
    records=[]
    for q in targets:
        blocked=set(q['blocked']);kept=[i for i in range(n) if i not in blocked];lookup={v:i for i,v in enumerate(kept)}
        assert all(guaranteed_conflict(q['base'],q['endpoint'],base[i],end[i],E,alpha) for i in blocked)
        source=out/f'anchor{q["index"]}';source.mkdir();local=[]
        for i in kept:
            mask=0
            for j in kept:
                if graph[i] & (1<<j):mask |= 1<<lookup[j]
            local.append(mask)
        cuts=set(tuple(lookup[i] for i in c if i in lookup) for c in data['cliques']);cuts.discard(())
        (source/'conflicts.json').write_text(json.dumps([hex(x) for x in local]));(source/'cliques.json').write_text(json.dumps(sorted(cuts)));(source/'kept-global.json').write_text(json.dumps(kept))
        refine(source,source/'refined',rounds)
        c=json.loads((source/'refined/cover.json').read_text());upper=F(c['finite_upper'])
        # Independent integer covering and graph-clique audit; the graph itself
        # was rebuilt from the two endpoint geometries, not copied from the LP.
        coverage=[0]*len(kept)
        for clique,w in zip(c['cliques'],c['numerators']):
            if not w:continue
            mask=sum(1<<i for i in clique)
            for i in clique:
                assert (mask ^ (1<<i)) & ~local[i] == 0;coverage[i]+=w
        assert min(coverage)>=c['denominator'] and F(sum(c['numerators']),c['denominator'])==upper
        records.append(dict(anchor=q['index'],upper=str(upper),excluded=upper<11,kept=len(kept)))
        (out/'progress.json').write_text(json.dumps(dict(records=[dict(operation='conditional_refinement',status='RUNNING',completed=len(records),total=len(targets),latest=records[-1])]),indent=2))
        print(json.dumps(records[-1]),flush=True)
    result=dict(status='EXACT_REFINED_LOCAL_ANCHOR_BRANCHES',branches=records,new_exclusions=sum(r['excluded'] for r in records),unresolved=sum(not r['excluded'] for r in records),seconds=time.monotonic()-start,
                epsilon_max=str(E),alpha=str(alpha),scope='One certified outside anchor plus eleven boxes in the original local union. Other outside poses and multiple outside boxes remain open.')
    (out/'result.json').write_text(json.dumps(result,indent=2));(out/'progress.json').write_text(json.dumps(dict(records=[dict(operation='conditional_refinement',status='STOPPED_LOCAL_PROOF_REVIEW',result=result)]),indent=2));print(json.dumps(result),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('family',type=Path);p.add_argument('branches',type=Path);p.add_argument('out',type=Path);p.add_argument('--rounds',type=int,default=4);a=p.parse_args();run(a.family,a.branches,a.out,a.rounds)
