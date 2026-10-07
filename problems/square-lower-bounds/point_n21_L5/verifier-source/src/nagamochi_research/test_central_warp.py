import unittest
from fractions import Fraction as F
from central_warp import CentralWarp,warp_template
from unified_measure import orbit

class CentralWarpTest(unittest.TestCase):
    def test_boundary_symmetry_and_monotonicity(self):
        for power in (0,1,2,3):
            warp=CentralWarp('9.85','9.06',1,power)
            self.assertEqual(warp.map(1),1)
            self.assertEqual(warp.map(F('8.85')),F('8.06'))
            x=[F('9.85')*i/100 for i in range(101)];y=list(map(warp.map,x))
            self.assertTrue(all(a<b for a,b in zip(y,y[1:])))
            for a in x:self.assertEqual(warp.map(warp.L0-a),warp.L1-warp.map(a))
            if power:self.assertLess(warp.derivative(warp.L0/2),warp.derivative(1))
        with self.assertRaises(ValueError):CentralWarp(10,3,1,3)
    def test_nonnegative_mass_and_d4(self):
        ps=[dict(kind='point',geometry=['1','2']),dict(kind='rectangle',geometry=['1','1','8','8'])]
        out,w,meta=warp_template(ps,[10.,80.],'9.85','9.06',81.99999,1,2,1)
        self.assertAlmostEqual(w.sum(),81.99999)
        self.assertTrue((w>0).all())
        warp=CentralWarp('9.85','9.06',1,2)
        expected={(warp.map(x),warp.map(y)) for x,y in orbit('point',ps[0]['geometry'],F('9.85'))}
        self.assertEqual(expected,set(orbit('point',out[0]['geometry'],F('9.06'))))

    def test_expansion_and_identity(self):
        for L in ('9.055','9.06','9.065'):
            warp=CentralWarp('9.06',L,2,2)
            self.assertEqual(warp.map(1),1)
            self.assertEqual(warp.map(F('8.06')),F(L)-1)
            self.assertEqual(warp.map(F('4.53')),F(L)/2)
            if L=='9.065':self.assertGreater(warp.derivative(F('4.53')),1)
            if L=='9.06':self.assertEqual(warp.map(F('2.7')),F('2.7'))

if __name__=='__main__':unittest.main()
