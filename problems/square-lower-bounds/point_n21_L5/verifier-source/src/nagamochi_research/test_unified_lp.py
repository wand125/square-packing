import unittest
import numpy as np
from scipy import sparse
from unified_grid_search import solve_matrix

class AdapterTest(unittest.TestCase):
    def test_separation_after_row_append(self):
        A=sparse.csr_matrix([[1.,0.],[0.,1.],[.25,.25]])
        poses=np.zeros((3,3));dual=np.array([1.,1.,0.])
        sol,report=solve_matrix(A,poses,1.,dual)
        self.assertAlmostEqual(sol.mass,4.)
        self.assertGreaterEqual(sol.min_coverage,1.-1e-9)
        self.assertGreater(report['rounds'],1)
        A=sparse.vstack([A, sparse.csr_matrix([[.1,.1]])],format='csr')
        sol,report=solve_matrix(A,np.zeros((4,3)),1.,np.r_[sol.dual,0.])
        self.assertAlmostEqual(sol.mass,10.)
        self.assertGreaterEqual(sol.min_coverage,1.-1e-9)
        with self.assertRaises(ValueError):solve_matrix(A,poses,1.,np.zeros(4))

if __name__=='__main__':unittest.main()
