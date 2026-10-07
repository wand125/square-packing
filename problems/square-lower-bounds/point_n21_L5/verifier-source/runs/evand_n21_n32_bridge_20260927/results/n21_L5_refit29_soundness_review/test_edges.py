"""Small adversarial checks; no optimization and no general packing claim."""
from pathlib import Path
from fractions import Fraction as F
from itertools import product
import sys,unittest
ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT/'src/nagamochi_research'))
from predicate_lp_capture import rational_bound
from predicate_conflict import verify_sum
from predicate_branch import replay_tree
from physical_pose_enclosure import enclose
from transfer_point_capture import bound,bound_alpha_one,classify

class Edges(unittest.TestCase):
 def test_dual_residual_exhaustive(self):
  # Include duplicate column entries, signed coefficients and infeasible corners.
  rows=[dict(terms=[(0,2),(0,-1),(1,1)],rhs=F(1)),dict(terms=[(1,-1),(2,2)],rhs=F(0))]
  cases=0
  for cost in product([F(0),F(1,3),F(2)],repeat=3):
   for multipliers in product([F(0),F(2,3),F(3)],repeat=2):
    lower,_=rational_bound(cost,rows,multipliers)
    for x in product([F(0),F(1,2),F(1)],repeat=3):
     if all(sum(v*x[j] for j,v in r['terms'])>=r['rhs'] for r in rows):
      self.assertLessEqual(lower,sum(c*z for c,z in zip(cost,x)));cases+=1
  self.assertGreater(cases,1000)
  with self.assertRaises(ValueError):rational_bound([1,1,1],rows,[-1,0])
 def test_strict_outside_equality(self):
  # g and -g may both be inside at g=0, but cannot both be strictly outside.
  g=[(F(-1,4),F(1),F(0))]*4
  neg=[tuple(-x for x in p) for p in g];box=[0,1,0,1,0,F(1,2)]
  row=verify_sum([g,neg],[0,0],box,[1,1]);self.assertEqual(row['maximum'],'0')
  self.assertTrue(row['strict_outside_used'])
  with self.assertRaises(ValueError):verify_sum([g,neg],[1,1],box,[1,1])
 def test_touching_physical_domain_not_empty(self):
  d=enclose(1,[F(1,2),F(1,2),F(1,2),F(1,2),0,0])
  self.assertIsNotNone(d['enclosing_box'])
  self.assertIsNone(enclose(F(999,1000),[F(1,2),F(1,2),F(1,2),F(1,2),0,0])['enclosing_box'])
 def test_open_and_fake_empty_rejected(self):
  self.assertFalse(replay_tree([1],[],0,1,{'kind':'OPEN'})['certified_unit_capture'])
  with self.assertRaises(ValueError):replay_tree([1],[],0,1,{'kind':'BRANCH','variable':0,'children':{'0':{'kind':'OPEN'}}})
  with self.assertRaises(ValueError):replay_tree([1],[],0,1,{'kind':'EMPTY','proof':{'multipliers':[],'lower':'0','penalty':'0'}})
 def test_transfer_zero_weights_and_boundary(self):
  coords=[(F(1),F(1)),(F(3,2),F(1)),(F(1,2),F(1)),(F(4),F(4))]
  box=[F(9,10),F(11,10),F(1),F(1),0,F(1,20)]
  kinds=[classify(p,box) for p in coords];count=0
  old=[F(1,2),F(0),F(3,4),F(1)]
  for new in product([F(0),F(1,3),F(1)],repeat=4):
   for q in [F(0),F(1,2),F(1),F(5,4)]:
    full=F(bound(coords,old,new,box,q)['lower']);fast=F(bound_alpha_one(coords,old,new,box,q)['lower']);self.assertGreaterEqual(full,fast)
    for bits in product([0,1],repeat=4):
     if any((k=='always' and not b) or (k=='outside' and b) for k,b in zip(kinds,bits)):continue
     if sum(w*b for w,b in zip(old,bits))>=q:
      self.assertLessEqual(full,sum(w*b for w,b in zip(new,bits)));count+=1
  self.assertGreater(count,100)

if __name__=='__main__':unittest.main()
