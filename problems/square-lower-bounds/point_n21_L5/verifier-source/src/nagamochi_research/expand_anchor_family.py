"""Unconditional local-union cover after adding anchor cells; no global claim."""
import argparse,json,time
from fractions import Fraction as F
from pathlib import Path
from outside_anchor_probe import guaranteed_conflict
from refine_conflict_cover import run as refine


def run(family,branches,old_graph,out,rounds,alpha_override=None,preserve_original_radius=False,safety_factor=56):
    out.mkdir(parents=True,exist_ok=False);start=time.monotonic()
    f=json.loads((family/'family-poses.json').read_text());d=json.loads(branches.read_text())
    base=f['base'];end=f['endpoint'];old_n=len(base);E=F(d['epsilon_max']);alpha=F(d['alpha'])
    original_alpha=alpha
    if alpha_override is not None:
        assert 0<alpha_override<=alpha
        alpha=alpha_override
    for q in d['branches']:base.append(q['base']);end.append(q['endpoint'])
    n=len(base);graph=[int(v,16) for v in json.loads(old_graph.read_text())]+[0]*(n-old_n)
    radii=[original_alpha if preserve_original_radius else alpha]*old_n+[alpha]*(n-old_n)
    assert 28<safety_factor<=56 and max(radii)*E<F(1,8)
    assert len(graph)==n
    if (alpha_override is not None and not preserve_original_radius) or safety_factor<56:
        for i in range(old_n):
            for j in range(i):
                if not graph[i] & (1<<j) and guaranteed_conflict(base[i],end[i],base[j],end[j],E,max(radii[i],radii[j]),safety_factor):
                    graph[i]|=1<<j;graph[j]|=1<<i
    for i in range(old_n,n):
        for j in range(i):
            if guaranteed_conflict(base[i],end[i],base[j],end[j],E,max(radii[i],radii[j]),safety_factor):
                graph[i]|=1<<j;graph[j]|=1<<i
    cuts=set()
    for seed in range(n):
        c=[seed];bits=graph[seed]
        while bits:
            bit=bits & -bits;v=bit.bit_length()-1;c.append(v);bits &= graph[v]
        cuts.add(tuple(sorted(c)))
    (out/'conflicts.json').write_text(json.dumps([hex(v) for v in graph]));(out/'cliques.json').write_text(json.dumps(sorted(cuts)))
    (out/'family-poses.json').write_text(json.dumps(dict(base=base,endpoint=end,epsilon_max=str(E))))
    print(json.dumps(dict(stage='expanded_graph',cells=n,cliques=len(cuts))),flush=True)
    refine(out,out/'refined',rounds)
    c=json.loads((out/'refined/cover.json').read_text());cov=[0]*n;seen=[0]*n
    for clique,w in zip(c['cliques'],c['numerators']):
        assert type(w) is int and w>=0
        if not w:continue
        mask=sum(1<<i for i in clique)
        for i in clique:cov[i]+=w;seen[i] |= mask & ((1<<i)-1)
    assert min(cov)>=c['denominator']>0
    pairs=0
    for i,bits in enumerate(seen):
        while bits:
            bit=bits & -bits;j=bit.bit_length()-1;bits^=bit
            assert guaranteed_conflict(base[i],end[i],base[j],end[j],E,max(radii[i],radii[j]),safety_factor);pairs+=1
    upper=F(sum(c['numerators']),c['denominator']);assert upper==F(c['finite_upper'])
    result=dict(status='EXACT_EXPANDED_LOCAL_EPSILON_FAMILY',cells=n,original_cells=old_n,added_cells=n-old_n,
                epsilon_max=str(E),coordinate_radius_coefficient=str(alpha),upper=str(upper),integer_upper=upper.numerator//upper.denominator,
                original_radius_coefficient=str(radii[0]),added_radius_coefficient=str(alpha),preserves_original_radius=preserve_original_radius,
                safety_factor=safety_factor,proven_gap_loss_factor=28,
                excludes_twelve=upper<12,used_cliques=sum(w>0 for w in c['numerators']),pairs_rechecked=pairs,seconds=time.monotonic()-start,
                theorem='The bound applies to any number of boxes in the added anchor cells, provided ALL boxes belong to this expanded local union.',
                limitation='The expanded union still does not cover every container pose. Not a proof of s(12)=4.')
    (out/'result.json').write_text(json.dumps(result,indent=2));(out/'progress.json').write_text(json.dumps(dict(records=[dict(operation='expanded_local_cover',status='STOPPED_LOCAL_PROOF_REVIEW',result=result)]),indent=2));print(json.dumps(result),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('family',type=Path);p.add_argument('branches',type=Path);p.add_argument('old_graph',type=Path);p.add_argument('out',type=Path);p.add_argument('--rounds',type=int,default=8);p.add_argument('--alpha',type=F);p.add_argument('--preserve-original-radius',action='store_true');p.add_argument('--safety-factor',type=int,default=56);a=p.parse_args();run(a.family,a.branches,a.old_graph,a.out,a.rounds,a.alpha,a.preserve_original_radius,a.safety_factor)
