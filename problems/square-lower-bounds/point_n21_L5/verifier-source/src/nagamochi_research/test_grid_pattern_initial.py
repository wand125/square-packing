import unittest
from fractions import Fraction as F
import numpy as np
from grid_pattern_initial import pattern_dictionary
from unified_geometry import expand_primitives,matrix
from unified_measure import primitive_key

class PatternTest(unittest.TestCase):
    def test_nonnegative_unit_mass_patterns_and_expansion(self):
        ps,P,names=pattern_dictionary('3.97',4)
        self.assertTrue(np.all(P.data>0))
        np.testing.assert_allclose(np.asarray(P.sum(axis=0)),1.)
        self.assertEqual(len(ps),len({primitive_key(p['kind'],p['geometry'],F('3.97')) for p in ps}))
        q=np.array([[1.,1.,0.],[1.8,1.6,.2],[2.,2.,.4]])
        A=matrix(q,.9977,expand_primitives(ps,F('3.97')))
        np.testing.assert_allclose(np.asarray(A@P)[:,0],(.9977/3.97)**2,rtol=1e-12)
        w=np.arange(1,len(names)+1,dtype=float);w/=w.sum()
        np.testing.assert_allclose((A@P)@w,A@(P@w),rtol=1e-12)
        self.assertAlmostEqual(float((P@w).sum()),1.)

if __name__=='__main__':unittest.main()
