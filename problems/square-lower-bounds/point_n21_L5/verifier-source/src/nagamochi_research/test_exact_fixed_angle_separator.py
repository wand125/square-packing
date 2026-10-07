from fractions import Fraction as F
import random
from exact_fixed_angle_separator import RangeMin,separate,projection
from score import square,contains

def test_tree_against_array():
 rng=random.Random(7);a=[0]*17;tree=RangeMin(17)
 for _ in range(150):
  l=rng.randrange(17);r=rng.randrange(l,17);w=rng.randrange(-7,8);tree.add(l,r,w)
  for i in range(l,r+1):a[i]+=w
  l=rng.randrange(17);r=rng.randrange(l,17);assert tree.query(l,r)==min((a[i],i) for i in range(l,r+1))

def test_axis_closed_boundaries_and_nonnegative_atoms():
 # Corner contacts capture more than adjacent open cells: optimum must be 0.
 pts=[(0,0,3),(0,2,3),(2,0,3),(2,2,3)];assert separate(F(2),1,pts,F(0))['minimum_numerator']==0
 # Four points spaced at half-unit coordinates guarantee at least one.
 pts=[(1,1,1),(1,3,1),(3,1,1),(3,3,1)];assert separate(F(2),2,pts,F(0))['minimum_numerator']==1

def test_rotation_sweep_against_every_small_arrangement_cell():
 # Independently clip the admissible-centre parallelogram against every grid cell.
 from score import clip,area
 pts=[(x,y,1+(3*x+7*y)%5) for x in range(1,6) for y in range(1,6)];L=F(3);D=2;t=F(1,3);p,q=1,3;a,b,r=8,6,10;h=F(7,10)
 poly=[(2*D*(a*x+b*y),2*D*(-b*x+a*y)) for x,y in [(h,h),(L-h,h),(L-h,L-h),(h,L-h)]]
 us=sorted({u for u,v in poly}|{F(2*(a*x+b*y)+s*D*r) for x,y,w in pts for s in (-1,1)})
 vs=sorted({v for u,v in poly}|{F(2*(-b*x+a*y)+s*D*r) for x,y,w in pts for s in (-1,1)})
 minima=[]
 for u0,u1 in zip(us,us[1:]):
  for v0,v1 in zip(vs,vs[1:]):
   poly2=poly
   for axis,bound,greater in [(0,u0,True),(0,u1,False),(1,v0,True),(1,v1,False)]:poly2=clip(poly2,axis,bound,greater)
   if not poly2 or not area(poly2):continue
   u=sum(x for x,y in poly2)/len(poly2);v=sum(y for x,y in poly2)/len(poly2);cx=(a*u-b*v)/(2*D*r*r);cy=(b*u+a*v)/(2*D*r*r)
   box=square(cx,cy,F(1),t);minima.append(sum(w for x,y,w in pts if contains(box,(F(x,D),F(y,D)))))
 assert min(minima)>0
 assert separate(L,D,pts,t)['minimum_numerator']==min(minima)

def test_rejects_negative_weights_and_degenerate_domain():
 import pytest
 with pytest.raises(ValueError):separate(F(2),1,[(1,1,-1)],F(0))
 with pytest.raises(ValueError):separate(F(1),1,[(0,0,1)],F(0))

def test_extra_witnesses_preserve_minimum_and_replay():
 pts=[(x,y,1+(x+3*y)%4) for x in range(1,6) for y in range(1,6)]
 baseline=separate(F(3),2,pts,F(1,3))
 result=separate(F(3),2,pts,F(1,3),extra_bins=8,violation_threshold=100)
 assert result['minimum_numerator']==baseline['minimum_numerator']
 assert result['witness']==baseline['witness']
 assert result['extra_witnesses']
 seen=set()
 for row in [result]+result['extra_witnesses']:
  pose=row['witness'];poly=square(F(pose['cx']),F(pose['cy']),F(1),F(pose['t']))
  hits=tuple(i for i,(x,y,w) in enumerate(pts) if contains(poly,(F(x,2),F(y,2))))
  assert hits not in seen;seen.add(hits)
  assert sum(pts[i][2] for i in hits)==row['minimum_numerator']


def test_multiple_mass_levels_keep_primary_result():
 pts=[(x,y,1+(x+3*y)%4) for x in range(1,6) for y in range(1,6)]
 one=separate(F(3),2,pts,F(1,3),extra_bins=4,violation_threshold=100)
 four=separate(F(3),2,pts,F(1,3),extra_bins=4,violation_threshold=100,levels_per_bin=4)
 assert one['minimum_numerator']==four['minimum_numerator']
 assert one['witness']==four['witness']
 assert len(four['extra_witnesses'])>=len(one['extra_witnesses'])
 for row in four['extra_witnesses']:
  p=row['witness'];poly=square(F(p['cx']),F(p['cy']),F(1),F(p['t']))
  assert sum(w for x,y,w in pts if contains(poly,(F(x,2),F(y,2))))==row['minimum_numerator']
