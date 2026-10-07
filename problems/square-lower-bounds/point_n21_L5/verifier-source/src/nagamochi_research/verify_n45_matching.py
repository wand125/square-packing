"""Replay saved SAT assignments; transfer witnesses through layout symmetries."""
from itertools import combinations
from pathlib import Path
from collections import Counter
import json
from n45_matching import model, ROOT
from assignment_conflicts import replay


def verify():
    rp,bp,bg,cases,shapes,conflict=model()
    keys={tuple(c['groups']):i for i,c in enumerate(cases)}
    def casekey(gs):return tuple(sorted(gs))
    bygroups={casekey(c['groups']):i for i,c in enumerate(cases)}
    bybag={tuple(g):b for b,g in enumerate(bg)}
    accepted={};sources=[]
    for path in sorted(ROOT.glob('baseline*.json')):
        data=json.loads(path.read_text())
        if 'records' not in data:continue
        sources.append(path.name)
        for rec in data['records']:
            if rec['status']!='SAT':continue
            edges=[tuple(e) for e in rec['assignment']]
            allowed=set(cases[rec['case']]['groups'])
            assert len(edges)==45 and len({a for a,b in edges})==45 and {b for a,b in edges}==allowed
            assert all(e in shapes for e in edges)
            assert not any(conflict(a,b) for a,b in combinations(edges,2))
            for flipx,flipy in ((False,False),(True,False),(False,True),(True,True)):
                def transform(p):return (7000-p[0] if flipx else p[0],7000-p[1] if flipy else p[1])
                rm={a:rp.index(transform(p)) for a,p in enumerate(rp)}
                bm={b:bp.index(transform(p)) for b,p in enumerate(bp)}
                gm={b:bybag[tuple(sorted(bm[i] for i in g))] for b,g in enumerate(bg)}
                new=[(rm[a],gm[b]) for a,b in edges]
                ci=bygroups[casekey([b for a,b in new])]
                assert all(e in shapes for e in new)
                assert not any(conflict(a,b) for a,b in combinations(new,2))
                accepted[ci]=new
    result=dict(status='EXACT_ASSIGNMENT_REPLAY',cases=len(cases),
                retained_by_witness=len(accepted),unresolved=len(cases)-len(accepted),sources=sources,
                counts=dict(Counter('empty' if cases[i]['empty'] else 'pair' for i in accepted)),
                witnesses=[dict(case=i,assignment=accepted[i]) for i in sorted(accepted)],
                scope='Only incidence/hull feasibility, not simultaneous square placement or proof of unavoidability.')
    (ROOT/'verified.json').write_text(json.dumps(result,indent=2))
    print(json.dumps({k:v for k,v in result.items() if k!='witnesses'}))
    return result

if __name__=='__main__':verify()
