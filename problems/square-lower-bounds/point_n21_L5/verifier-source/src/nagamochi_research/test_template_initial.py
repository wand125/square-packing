import unittest
import json,tempfile
from pathlib import Path
from fractions import Fraction as F
import numpy as np
from template_initial import transfer,load_template
from unified_measure import orbit

class TransferTest(unittest.TestCase):
    def test_point_orbit_uses_per_site_weight(self):
        d=dict(L='4',B='.9977',sites=[['1','1'],['1','3'],['3','1'],['3','3']],point_cols=[[0,1,2,3]],charge_cols=[],weights=['1/4'])
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'point.json';p.write_text(json.dumps(d));L,B,ps,w=load_template(p)
        self.assertEqual(len(ps),1)
        self.assertAlmostEqual(w.sum(),1.)
        with self.assertRaises(ValueError):transfer(ps,[-1.],4,5,1.,'wall')

    def test_wall_anchors_symmetry_and_mass(self):
        ps=[dict(kind='point',geometry=['1','2']),dict(kind='rectangle',geometry=['1','1','8','8'])]
        result,w=transfer(ps,np.array([1.,2.]),9,10,96.99,'wall')
        self.assertEqual(list(map(F,result[0]['geometry'])),[F(1),F(15,7)])
        self.assertEqual(list(map(F,result[1]['geometry'])),[F(1),F(1),F(9),F(9)])
        self.assertAlmostEqual(w.sum(),96.99)
        points=list(orbit('point',ps[0]['geometry'],F(9)))
        mapped,_=transfer([dict(kind='point',geometry=list(map(str,g))) for g in points],np.ones(8),9,10,8,'wall')
        self.assertEqual({tuple(map(F,p['geometry'])) for p in mapped},set(orbit('point',result[0]['geometry'],F(10))))

if __name__=='__main__':unittest.main()
