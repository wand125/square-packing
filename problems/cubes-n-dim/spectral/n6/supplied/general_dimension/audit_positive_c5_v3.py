"""Independent exact acceptance and coverage replay; producer used only as witness oracle.
The proposal() oracle has no authority to accept any cell or split.
"""
from fractions import Fraction as Q
from math import isqrt
from collections import Counter
import importlib.util, hashlib, json, time
from pathlib import Path
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('witness_oracle',HERE/'certify_positive_c5_v3.py')
oracle=importlib.util.module_from_spec(spec);spec.loader.exec_module(oracle)
SCALE=2**48

def leaf(V):
    assert all(len(p)==4 and 1>=p[0]>=p[1]>=p[2]>=p[3]>=0 for p in V)
    upper=[max(p[k] for p in V) for k in range(4)]
    if 100*sum(x*x for x in upper)<=1:
        return 'near_axis',None
    W=[(Q(1),)+p for p in V]
    center=[sum(w[k] for w in W)/len(W) for k in range(5)]
    n2=sum(x*x for x in center)
    integer=isqrt(n2.numerator*SCALE*SCALE//n2.denominator)
    M=Q(integer,SCALE)
    if M*M<n2: M+=Q(1,SCALE)
    assert M>0 and M*M>=n2 and (M-Q(1,SCALE))**2<n2
    allocation=oracle.proposal(list(map(float,center)))
    assert len(allocation)==5
    for i in range(5):
        assert len(allocation[i])==5 and allocation[i][i]==0
        for j in range(i):
            p,q=allocation[i][j],allocation[j][i]
            assert isinstance(p,Q) and isinstance(q,Q) and p>=0 and q>=0 and p*p+q*q==1
    # Independently clear the positive M denominator in each demand check.
    # M*sum_j((allocation_ij-1)*w_j) + center dot w >= 0.
    for row in allocation:
        for w in W:
            demand=sum((row[k]-1)*w[k] for k in range(5))
            support=sum(center[k]*w[k] for k in range(5))
            if M*demand+support<0: return None,None
    return 'fixed_rational_flow',allocation

def main():
    begin=time.time(); initial=tuple(tuple(Q(k<j) for k in range(4)) for j in range(5))
    pending=[(initial,0)];counts=Counter();splits=0;depth=0;volume=Q(0);digest=hashlib.sha256()
    while pending:
        vertices,d=pending.pop()
        kind,witness=leaf(vertices)
        if kind:
            counts[kind]+=1;depth=max(depth,d);volume+=Q(1,2**d)
            digest.update(repr((vertices,kind,witness)).encode());continue
        edges=[(sum((vertices[a][k]-vertices[b][k])**2 for k in range(4)),a,b) for a in range(5) for b in range(a)]
        length,a,b=sorted(edges)[-1];assert length>0
        mid=tuple((x+y)/2 for x,y in zip(vertices[a],vertices[b]))
        first=list(vertices);second=list(vertices);first[a]=mid;second[b]=mid
        pending.extend([(tuple(first),d+1),(tuple(second),d+1)]);splits+=1
    assert volume==1 and sum(counts.values())==splits+1
    result=dict(verified=True,splits=splits,leaves=dict(counts),maximum_depth=depth,exact_relative_volume=str(volume),leaf_digest=digest.hexdigest(),seconds=time.time()-begin,witness_source='producer proposal only; independent acceptance, norm bracket, capacities, geometry, and traversal')
    print(json.dumps(result,indent=2));(HERE/'positive_c5_independent_audit_result.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
