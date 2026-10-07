from pathlib import Path
from fractions import Fraction as F
import sys,unittest,random
ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT/'src/nagamochi_research'))
from exact_fixed_angle_separator import projection,RangeMin
from certify_near_axis_sweep import Signs
from certify_n21_near_axis_path import sign_on_open_interval

class SweepAlgebra(unittest.TestCase):
 def test_projection_formula_against_polygon_edges(self):
  count=0
  for t in [F(1,10**8),F(1,100),F(1,5),F(5,12),F(1,2)]:
   a,b,r=1-t*t,2*t,1+t*t;L=F(5);D=F(3);h=(a+b)/(2*r)
   poly=[(2*D*(a*x+b*y),2*D*(-b*x+a*y)) for x,y in [(h,h),(L-h,h),(L-h,L-h),(h,L-h)]]
   umin,umax=min(x for x,y in poly),max(x for x,y in poly)
   low=D*r*(a+b);high=2*L*D*r*r-low
   for i in range(8):
    u0=umin+(umax-umin)*F(i,8);u1=umin+(umax-umin)*F(i+1,8)
    expected=projection(poly,u0,u1)
    actual=(max((a*u0-high)/b,(low-b*u1)/a,(a*low-b*high)/(r*r)),min((high-b*u0)/a,(a*u1-low)/b,(a*high-b*low)/(r*r)))
    self.assertEqual(actual,expected);self.assertLess(actual[0],actual[1]);count+=1
  self.assertEqual(count,40)
 def test_remainder_rejects_root_at_closed_upper_endpoint(self):
  with self.assertRaises(ValueError):sign_on_open_interval((0,1,-1000),F(1,1000))
  s=Signs(F(1,1000));self.assertEqual(s.sign((0,1,-1000)),1);self.assertEqual(s.T,F(1,2000));s.replay()
  self.assertEqual(sign_on_open_interval((0,1,-1000),s.T)[0],1)
 def test_range_min_against_direct_integer_array(self):
  rng=random.Random(20260928);tree=RangeMin(17);values=[0]*17
  for _ in range(100):
   lo=rng.randrange(17);hi=rng.randrange(lo,17);w=rng.randrange(-20,21)
   tree.add(lo,hi,w)
   for i in range(lo,hi+1):values[i]+=w
   for lo in range(17):
    hi=rng.randrange(lo,17);self.assertEqual(tree.query(lo,hi),min((values[i],i) for i in range(lo,hi+1)))

if __name__=='__main__':unittest.main()
