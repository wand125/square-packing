"""Endpoint counterexamples to grid-only rigidity and exact projection chains."""
from fractions import Fraction as F
from itertools import combinations
from math import lcm
from score import square
from endpoint_joint_probe import separation


def intervals(poly,axis):
    return min(p[axis] for p in poly),max(p[axis] for p in poly)


def longest_projection_chain(polys,axis):
    spans=[intervals(p,axis) for p in polys]
    order=sorted(range(len(polys)),key=lambda i:spans[i][1]);paths={}
    for i in order:
        prev=[paths[j] for j in paths if spans[j][1]<=spans[i][0]]
        paths[i]=(max(prev,key=len) if prev else [])+[i]
    result=max(paths.values(),key=len)
    widths=[spans[i][1]-spans[i][0] for i in result]
    assert all(w>=1 for w in widths)
    return dict(axis=axis,indices=result,length=len(result),sum_width=str(sum(widths)))


def example(k):
    # k²-5 axis-aligned boxes plus one rotated box, i.e. n12 or n21.
    poses=[(F(2*i+1,2),F(2*j+1,2),F(0)) for i in range(k) for j in range(k)
           if not (i>=k-2 and j>=k-2) and (i,j)!=(0,0)]
    poses.append((F(k-1),F(k-1),F(1,3)))
    polys=[square(x,y,1,t) for x,y,t in poses]
    assert len(polys)==k*k-4
    assert all(0<=x<=k and 0<=y<=k for p in polys for x,y in p)
    assert all(separation(a,b) is not None for a,b in combinations(polys,2))
    chains=[longest_projection_chain(polys,axis) for axis in (0,1)]
    assert max(c['length'] for c in chains)==k
    return dict(n=len(polys),L=k,poses=[list(map(str,p)) for p in poses],chains=chains,
                conclusion='Non-grid endpoint packings exist, including a rotated square. Projection chains can still force L>=k. Necessity of such chains for every packing is NOT proved.')


if __name__=='__main__':
    import argparse,json
    from pathlib import Path
    p=argparse.ArgumentParser();p.add_argument('out',type=Path);a=p.parse_args()
    a.out.write_text(json.dumps(dict(examples=[example(4),example(5)]),indent=2))
