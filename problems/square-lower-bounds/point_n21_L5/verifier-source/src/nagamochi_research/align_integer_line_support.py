"""Experimental mass-preserving D4 alignment on integer lines, not a cover proof.

Only the coordinate tangent to an integer line is rounded to the common 1/q
mesh. Integer intersections stay fixed. Reflection-compatible ties are needed.
"""
from fractions import Fraction as F
from pathlib import Path
from collections import defaultdict
from math import lcm
import json,hashlib
from probe_external_integer_bridge import read


def project(x,y,L,q):
    x,y,L=map(F,(x,y,L))
    if L.denominator!=1 or not isinstance(q,int) or q<=0 or int(L)*q%2:
        raise ValueError('Require integer side and even L*q for reflected ties')
    # Decisions use the ORIGINAL coordinates; do not cascade onto new lines.
    return (F(round(x*q),q) if y.denominator==1 else x,
            F(round(y*q),q) if x.denominator==1 else y)


def run(source,out,q):
    if out.exists():raise FileExistsError(out)
    L,span,W,points=read(source);D=int(F(span)/L);newD=lcm(D,q)
    merged=defaultdict(int);moved=0;maxmove=F(0)
    for X,Y,w in points:
        x,y=F(X,D),F(Y,D);u,v=project(x,y,L,q)
        assert 0<=u<=L and 0<=v<=L
        moved+=(u,v)!=(x,y);maxmove=max(maxmove,abs(u-x),abs(v-y))
        U,V=u*newD,v*newD;assert U.denominator==V.denominator==1
        merged[int(U),int(V)]+=w
    assert sum(merged.values())==sum(w for x,y,w in points)
    assert maxmove<=F(1,2*q)
    out.write_text('\n'.join([f'{L.numerator} {L.denominator}',str(newD),str(W),str(len(merged))]+[f'{x} {y} {w}' for (x,y),w in sorted(merged.items())])+'\n')
    read(out) # exact D4 and nonnegativity replay
    result=dict(source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),sha256=hashlib.sha256(out.read_bytes()).hexdigest(),q=q,L=str(L),source_points=len(points),points=len(merged),moved_source_points=moved,max_coordinate_move=str(maxmove),total_mass=str(F(sum(merged.values()),W)),D4_verified=True,previous_proofs_inherited=False,general_coverage_verified=False)
    out.with_suffix('.alignment.json').write_text(json.dumps(result,indent=2));return result
