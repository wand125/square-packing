from pathlib import Path
from fractions import Fraction as F
from itertools import product
import sys,unittest
ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT/'src/nagamochi_research'))
from compile_box_capture_rows import validate_partition
from stratified_box_cover import verify as cover
from verify_angle_clip import verify as clip

class Partition(unittest.TestCase):
 def test_all_octant_subsets_against_strata(self):
  root=[0,1,0,1,0,1];cells=[]
  for x,y,z in product((0,F(1,2)),repeat=3):cells.append([x,x+F(1,2),y,y+F(1,2),z,z+F(1,2)])
  def accepts(fn,*args):
   try:fn(*args);return True
   except ValueError:return False
  for mask in range(256):
   boxes=[b for i,b in enumerate(cells) if mask&(1<<i)]
   self.assertEqual(accepts(validate_partition,root,boxes),accepts(cover,root,boxes,[]))
   self.assertEqual(accepts(validate_partition,root,boxes),mask==255)
 def test_volume_match_does_not_hide_overlap_and_gap(self):
  root=[0,1,0,1,0,1];boxes=[[0,F(1,2),0,1,0,1]]*2
  with self.assertRaises(ValueError):validate_partition(root,boxes)
  with self.assertRaises(ValueError):cover(root,boxes,[])
 def test_clip_join_retains_exact_contact_face(self):
  root=[0,F(1,2),1,2,0,F(1,4)]
  r=clip(5,root,0);self.assertTrue(r['lower_open'])
  with self.assertRaises(ValueError):cover(root,[],[root])
  axis=root.copy();axis[5]=0
  self.assertTrue(cover(root,[axis],[root])['boundaries_checked'])
 def test_nonmonotone_angle_tail_is_rejected(self):
  with self.assertRaises(ValueError):clip(5,[0,F(1,2),1,2,0,F(1,2)],F(1,4))

if __name__=='__main__':unittest.main()
