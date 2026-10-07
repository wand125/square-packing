import unittest
import numpy as np
from blend_initial import minimax_blend

class BlendTest(unittest.TestCase):
    def test_complementary_coverage_and_dominated_candidate(self):
        a,v=minimax_blend([[.8,1.2,.1],[1.2,.8,.1]])
        np.testing.assert_allclose(a,[.5,.5,0.],atol=1e-8)
        self.assertAlmostEqual(v,1.)
        with self.assertRaises(ValueError):minimax_blend([[np.nan]])

if __name__=='__main__':unittest.main()
