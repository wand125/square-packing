import unittest
import numpy as np
from template_repair import bounded_weights

class BoundedTest(unittest.TestCase):
    def test_mass_bounds_and_unseen_coverage_floor(self):
        A=np.array([[1.,0.],[0.,2.],[.2,.5]])
        base=np.array([1.,1.]);w,m=bounded_weights(A,base,.99,1.05)
        self.assertAlmostEqual(w.sum(),base.sum())
        self.assertTrue(np.all(w>=.99*base-1e-10))
        self.assertTrue(np.all(w<=1.05*base+1e-10))
        self.assertGreaterEqual(m,(A@base).min()-1e-10)
        unseen=np.array([[.1,.7],[0.,.4],[2.,1.]])
        self.assertTrue(np.all(unseen@w>=.99*(unseen@base)-1e-10))

if __name__=='__main__':unittest.main()
