import unittest
import numpy as np
from square_plus_one_initial import seam_pool,fixed_budget
from unified_measure import primitive_key
from fractions import Fraction as F

class SeamTest(unittest.TestCase):
    def test_distinct_valid_dictionary(self):
        ps=seam_pool('9.06',9);keys=[primitive_key(p['kind'],p['geometry'],F('9.06')) for p in ps]
        self.assertEqual(len(keys),len(set(keys)))
        self.assertEqual({p['kind'] for p in ps},{'point','segment','rectangle','disk','annulus'})
    def test_uniform_floor_budget(self):
        A=np.array([[.2,.8,0],[.2,0,.8]])
        w,f=fixed_budget(A,10,.5)
        self.assertAlmostEqual(w.sum(),10)
        self.assertGreaterEqual(w[0],5-1e-8)
        self.assertGreaterEqual((A@w).min(),2)
        self.assertTrue(np.all(A@w>=A[:,0]*5-1e-8))

if __name__=='__main__':unittest.main()
