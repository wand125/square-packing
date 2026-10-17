"""Replay the proof using Python standard-library exact rational arithmetic only."""
from fractions import Fraction as F
import json,time
from spectral_bound import sqrt_bounds,certify_witness

def main():
    start=time.time()
    with open('certificate.json') as f:c=json.load(f)
    V=[tuple(map(F,p)) for p in c['vertices']]
    initial=[tuple(list(range(2*k,10,2))+list(range(1,2*k+2,2))) for k in range(5)]
    assert [tuple(s) for s in c['initial']]==initial
    expected=[]
    for k in range(2,7):
        expected.append(tuple([F(1,k)]*k+[F(0)]*(6-k)))
        expected.append(tuple([F(13,20)]+[F(7,20*(k-1))]*(k-1)+[F(0)]*(6-k)))
    assert V[:10]==expected
    assert len(V)==len(c['witnesses'])
    for p in V:
        assert sum(p)==1 and all(F(0)<=p[i]<=F(13,20) for i in range(6))
        assert all(p[i]>=p[i+1] for i in range(5))
    q=[];roots=[]
    for p,a in zip(V,c['witnesses']):
        q.append(certify_witness(p,[[F(x) for x in row] for row in a])+sum(sorted(p[i]*p[j] for i in range(6) for j in range(i+1,6))[:10])/2)
        roots.append([sqrt_bounds(x,48) for x in p])
    stack=list(initial);leaves=0;slacks=[]
    for record in c['records']:
        assert stack,'Extra record'
        s=stack.pop()
        if record is None:
            loss=F(0)
            for k in range(6):
                i=min(s,key=lambda i:V[i][k]);j=max(s,key=lambda i:V[i][k])
                if V[i][k]==V[j][k]:continue
                al,au=roots[i][k];bl,bu=roots[j][k]
                loss+=(bu-al)**2/(2*(bl+al))
            widths=[max(V[i][k] for i in s)-min(V[i][k] for i in s) for k in range(6)]
            loss+=sum(widths[i]*widths[j] for i in range(6) for j in range(i+1,6))/8
            slack=min(q[i] for i in s)-loss
            assert slack>0,'Uncertified leaf'
            slacks.append(slack);leaves+=1
        else:
            a,b,m=record
            assert 0<=a<6 and 0<=b<6 and a!=b and 0<=m<len(V)
            assert V[m]==tuple((x+y)/2 for x,y in zip(V[s[a]],V[s[b]]))
            s1=list(s);s2=list(s);s1[a]=m;s2[b]=m
            stack.extend([tuple(s1),tuple(s2)])
    assert not stack,'Unprocessed simplices'
    print('VERIFIED using exact rational arithmetic only')
    print('vertices',len(V),'leaves',leaves,'records',len(c['records']))
    print('minimum leaf slack',float(min(slacks)))
    print('elapsed seconds',time.time()-start)
if __name__=='__main__':main()
