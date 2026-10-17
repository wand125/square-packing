"""Independent, standard-library-only verification. Imports no producer code.
Run with python -u independent_verify.py [certificate.json].
Uses 128-bit certified root intervals, rather than producer's 48/100 bits.
"""
from fractions import Fraction as Q
from math import isqrt
from functools import lru_cache
from pathlib import Path
import json, hashlib, sys, time

SCALE = 1 << 128

@lru_cache(None)
def root(x):
    assert x >= 0
    k = isqrt(x.numerator * SCALE**2 // x.denominator)
    lo, hi = Q(k, SCALE), Q(k+1, SCALE)
    assert lo*lo <= x < hi*hi
    return lo, hi

def vertex(p, a):
    assert len(p) == 6 and sum(p) == 1
    assert all(0 <= x <= Q(13,20) for x in p)
    assert all(p[i] >= p[i+1] for i in range(5))
    assert len(a) == 6 and all(len(row) == 6 for row in a)
    assert all(a[i][j] == a[j][i] for i in range(6) for j in range(6))
    residual = Q(0)
    for i in range(6):
        error = Q(0)
        for j in range(6):
            covariance = (p[i] if i == j else 0) - p[i]*p[j]
            square = sum(a[i][k]*a[j][k] for k in range(6))
            error += abs(covariance-square)
        residual = max(residual,error)
    trace_lower = max(Q(0),sum(a[i][i] for i in range(6))-6*root(residual)[1])
    products = sorted(p[i]*p[j] for i in range(6) for j in range(i))
    assert len(products) == 15
    return root(Q(2))[0]*trace_lower - 2*sum(root(x)[1] for x in p) + 2 + sum(products[:10])/2

@lru_cache(None)
def chord(low, high):
    assert 0 <= low <= high
    if low == high:
        return Q(0)
    a,b = root(low)[0],root(high)[1]
    # g(a,b) decreases in a and increases in b for 0<=a<=b.
    return (b-a)**2/(2*(a+b))

def penalty(points):
    loss = Q(0)
    widths = []
    for coordinates in zip(*points):
        lo,hi = min(coordinates),max(coordinates)
        loss += chord(lo,hi)
        widths.append(hi-lo)
    # Equivalent pair sum, evaluated via polarization independently.
    loss += (sum(widths)**2-sum(w*w for w in widths))/16
    return loss

def main():
    start=time.monotonic()
    path=Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).with_name('certificate.json')
    raw=path.read_bytes()
    digest=hashlib.sha256(raw).hexdigest()
    cert=json.loads(raw)
    del raw
    points=[tuple(Q(x) for x in p) for p in cert['vertices']]
    assert len(points)==len(cert['witnesses']) and len(set(points))==len(points)
    expected=[]
    for support in range(2,7):
        expected += [(Q(1,support),)*support+(Q(0),)*(6-support),
                     (Q(13,20),)+(Q(7,20*(support-1)),)*(support-1)+(Q(0),)*(6-support)]
    assert points[:10]==expected
    # Pulling w2, then w3,... leaves these five maximal simplices.
    initial=[(0,2,4,6,8,1),(2,4,6,8,1,3),(4,6,8,1,3,5),
             (6,8,1,3,5,7),(8,1,3,5,7,9)]
    assert cert['initial']==[list(s) for s in initial]
    bounds=[]
    for i,(p,m) in enumerate(zip(points,cert['witnesses'])):
        bounds.append(vertex(p,[[Q(x) for x in row] for row in m]))
        if (i+1)%5000==0: print('Witnesses verified:',i+1,flush=True)
    del cert['witnesses']
    pending=[(s,0) for s in initial]
    leaves=0; minimum=None; maxdepth=0; used=set()
    for count,record in enumerate(cert['records'],1):
        assert pending,'Extraneous subdivision record'
        simplex,depth=pending.pop()
        assert len(set(simplex))==6
        used.update(simplex); maxdepth=max(maxdepth,depth)
        if record is None:
            margin=min(bounds[i] for i in simplex)-penalty([points[i] for i in simplex])
            assert margin>0,('Uncertified leaf',count,margin)
            minimum=margin if minimum is None else min(minimum,margin)
            leaves+=1
        else:
            assert len(record)==3 and all(type(x) is int for x in record)
            a,b,m=record
            assert 0<=a<6 and 0<=b<6 and a!=b and 0<=m<len(points)
            assert points[m]==tuple((x+y)/2 for x,y in zip(points[simplex[a]],points[simplex[b]]))
            first,second=list(simplex),list(simplex)
            first[a]=m;second[b]=m
            pending.extend([(tuple(first),depth+1),(tuple(second),depth+1)])
        if count%200000==0:print('Tree records verified:',count,'leaves:',leaves,flush=True)
    assert not pending,'Incomplete subdivision cover'
    assert used==set(range(len(points)))
    assert len(cert['records'])==2*leaves-5
    result={'status':'INDEPENDENT EXACT VERIFICATION PASSED','sha256':digest,
            'vertices':len(points),'records':len(cert['records']),'leaves':leaves,'max_depth':maxdepth,
            'minimum_margin_exact':str(minimum),'minimum_margin_float':float(minimum),
            'seconds':time.monotonic()-start}
    print(json.dumps(result,indent=2),flush=True)
    path.with_name('independent_result.json').write_text(json.dumps(result,indent=2)+'\n')

if __name__=='__main__':main()
