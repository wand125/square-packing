"""Replay a finite clique cover and certify a continuous neighbourhood bound.

No use of LP success or cached conflict edges as proof: recompute every pair
used by every positive-weight clique and all rational covering sums.
"""
from fractions import Fraction as F
import argparse,hashlib,json
from pathlib import Path


def overlap_gap(s,t):
    x,y,d,a,b,r=s[:6];X,Y,D,A,B,R=t[:6]
    dx,dy,den=X*d-x*D,Y*d-y*D,d*D
    rhs=den*(r*R+abs(a*A+b*B)+abs(a*B-b*A))
    gaps=[rhs-2*abs(a*dx+b*dy)*R,rhs-2*abs(-b*dx+a*dy)*R,
          rhs-2*abs(A*dx+B*dy)*r,rhs-2*abs(-B*dx+A*dy)*r]
    return min(gaps),2*den*r*R


def verify(poses_path,cover_path,out):
    poses=json.loads(poses_path.read_text());cover=json.loads(cover_path.read_text())
    squares=[q['square'] for q in poses];n=len(squares);coverage=[0]*n;edges=[0]*n
    den=cover['denominator'];nums=cover['numerators'];cuts=cover['cliques']
    assert type(den) is int and den>0 and len(nums)==len(cuts)
    for s in squares:
        x,y,d,a,b,r=s[:6]
        assert d>0 and r>0 and a*a+b*b==r*r and r+a!=0
        assert 0<=x<=4*d and 0<=y<=4*d
    for c,w in zip(cuts,nums):
        assert type(w) is int and w>=0 and len(c)==len(set(c))
        assert all(type(i) is int and 0<=i<n for i in c)
        if not w:continue
        mask=sum(1<<i for i in c)
        for i in c:
            coverage[i]+=w;edges[i] |= mask & ((1<<i)-1)
    assert min(coverage)>=den
    bound=F(sum(nums),den);assert bound==F(cover['finite_upper'])
    minimum=F(1,2);pair=None;count=0
    for i,bits in enumerate(edges):
        while bits:
            bit=bits & -bits;j=bit.bit_length()-1;bits^=bit
            num,d=overlap_gap(squares[i],squares[j]);assert num>0,(i,j)
            if num*minimum.denominator < minimum.numerator*d:
                minimum=F(num,d);pair=[i,j]
            count+=1
    h=min(F(1,8),minimum/56)
    assert 28*h < minimum and 2*h<F(1,2)
    # Both cos(t) and sin(t) are globally 2-Lipschitz. Under independent
    # |dcx|,|dcy|,|dt|<=h, any SAT overlap gap decreases by <=28h:
    # centre projection: <=16h (rotating axis) +4h (moving centres);
    # other-square half projection width: <=8h. Own half width stays 1/2.
    # All four original gaps stay positive, so each conflict survives.
    # Two squares in the SAME cell contain its original centre (2h<1/2).
    # Therefore every used clique is still an at-most-one rule for the
    # union of its cells. The unchanged rational cover bounds any packing
    # whose every square belongs to one of the saved pose cells.
    result=dict(status='EXACT_CONTINUOUS_LOCAL_COVER',cells=n,used_cliques=sum(w>0 for w in nums),
                pairs_rechecked=count,minimum_overlap_gap=str(minimum),minimum_pair=pair,
                radius=str(h),radius_float=float(h),upper=str(bound),integer_upper=bound.numerator//bound.denominator,
                theorem='Any packing of unit squares, all of whose (cx,cy,t) are within this coordinate radius of the saved poses, has at most integer_upper members.',
                limitation='The union of cells does not cover every container pose. This is not a proof of s(12)=4.',
                hashes={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (poses_path,cover_path)})
    out.write_text(json.dumps(result,indent=2));print(json.dumps(result))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('poses',type=Path);p.add_argument('cover',type=Path);p.add_argument('out',type=Path);a=p.parse_args();verify(a.poses,a.cover,a.out)
