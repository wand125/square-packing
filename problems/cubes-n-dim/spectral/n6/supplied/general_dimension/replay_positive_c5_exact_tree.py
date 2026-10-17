"""Standalone exact rational C5 verifier. Imports no producer or floating math."""
from fractions import Fraction as Q
from math import isqrt
from pathlib import Path
from collections import Counter
import gzip,json,hashlib,time
HERE=Path(__file__).resolve().parent

def main():
    start=time.time();path=HERE/'positive_c5_exact_tree.json.gz'
    records=json.loads(gzip.decompress(path.read_bytes()))
    pending=[(tuple(tuple(Q(k<j) for k in range(4)) for j in range(5)),0)]
    volume=Q(0);counts=Counter();depth=0;scale=2**48
    for record in records:
        assert pending,'Excess records'
        V,d=pending.pop()
        assert all(1>=p[0]>=p[1]>=p[2]>=p[3]>=0 for p in V)
        kind=record[0]
        if kind=='s':
            assert len(record)==3
            i,j=record[1:];assert isinstance(i,int) and isinstance(j,int) and 0<=j<i<5 and V[i]!=V[j]
            mid=tuple((x+y)/2 for x,y in zip(V[i],V[j]));A=list(V);B=list(V);A[i]=mid;B[j]=mid
            pending.extend([(tuple(A),d+1),(tuple(B),d+1)])
        elif kind=='a':
            assert len(record)==1
            assert 100*sum(max(p[k] for p in V)**2 for k in range(4))<=1
        elif kind=='f':
            assert len(record)==2 and len(record[1])==10
            C=[[Q(0) for _ in range(5)] for _ in range(5)];parameters=iter(record[1])
            for i in range(5):
                for j in range(i):
                    h=Q(next(parameters));assert 0<=h<=1
                    C[i][j]=(1-h*h)/(1+h*h);C[j][i]=2*h/(1+h*h)
                    assert C[i][j]>=0 and C[j][i]>=0 and C[i][j]**2+C[j][i]**2==1
            W=[(Q(1),)+p for p in V];m=[sum(w[k] for w in W)/5 for k in range(5)];n2=sum(x*x for x in m)
            M=Q(isqrt(n2.numerator*scale*scale//n2.denominator),scale)
            if M*M<n2:M+=Q(1,scale)
            assert M>0 and M*M>=n2 and (M-Q(1,scale))**2<n2
            for row in C:
                for w in W:
                    assert M*sum((row[k]-1)*w[k] for k in range(5))+sum(m[k]*w[k] for k in range(5))>=0
        else:raise AssertionError('Unknown record')
        counts[kind]+=1
        if kind!='s':volume+=Q(1,2**d);depth=max(depth,d)
    assert not pending,'Incomplete tree'
    assert volume==1 and counts['a']+counts['f']==counts['s']+1
    out=dict(verified=True,records=len(records),counts=dict(counts),maximum_depth=depth,exact_relative_volume=str(volume),compressed_tree_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),seconds=time.time()-start)
    print(json.dumps(out,indent=2));(HERE/'positive_c5_standalone_replay_result.json').write_text(json.dumps(out,indent=2)+'\n')
if __name__=='__main__':main()
