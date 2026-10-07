"""Exact induced graph capacities at every recorded capture threshold."""
import argparse,json,hashlib
from fractions import Fraction as F
from pathlib import Path
from pose_conflict_capacity import independent_number
from packing_lemmas import low_capture_bound


def run(cover,graph,n,mass,out):
    q=json.loads(cover.read_text());g=json.loads(graph.read_text())
    if g['cover_sha256']!=hashlib.sha256(cover.read_bytes()).hexdigest():raise ValueError('Cover hash mismatch')
    limit=F(g['threshold']);paths=g['paths']
    # Physically empty leaves may be absent from the graph; all other low
    # leaves must be represented. Recheck this condition from containment.
    from physical_pose_bound import restrict_centres
    # L is recovered from the root partition extrema, not a rounded value.
    L=max(F(r['box'][1]) for r in q['leaves'].values())+F(1,2)
    expected={p for p,r in q['leaves'].items() if r['kind']!='OUTSIDE' and F(r['lower'])<limit and restrict_centres(L,tuple(map(F,r['box']))) is not None}
    if set(paths)!=expected or len(paths)!=len(set(paths)):raise ValueError('Graph domain incomplete')
    values=[F(q['leaves'][p]['lower']) for p in paths]
    floor=min(F(r['lower']) for r in q['leaves'].values() if r['kind']!='OUTSIDE')
    rows=[]
    for t in sorted(set(values)|{limit}):
        if t<=floor:continue
        ids=[i for i,v in enumerate(values) if v<t];local={i:j for j,i in enumerate(ids)};adj=[0]*len(ids)
        for i,j in g['edges']:
            if i in local and j in local:
                a,b=local[i],local[j];adj[a]|=1<<b;adj[b]|=1<<a
        rows.append(dict(threshold=str(t),capacity=min(n,independent_number(adj)),cells=len(ids)))
    lower=low_capture_bound([n],[floor],[F(r['threshold'])-floor for r in rows],[r['capacity'] for r in rows])
    result=dict(status='EXACT_INDUCED_GRAPH_ARITHMETIC',records=rows,floor=str(floor),capture_sum_lower=str(lower),gap=str(lower-mass),
                source_graph_sha256=hashlib.sha256(graph.read_bytes()).hexdigest(),requires_verified_cover_and_graph=True,general_packing_exclusion=False)
    out.write_text(json.dumps(result,indent=2));print(dict(lower=float(lower),gap=float(lower-mass),thresholds=len(rows)),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for key in ('cover','graph','out'):p.add_argument(key,type=Path)
    p.add_argument('--n',type=int,required=True);p.add_argument('--mass',type=F,required=True);a=p.parse_args()
    run(a.cover,a.graph,a.n,a.mass,a.out)
