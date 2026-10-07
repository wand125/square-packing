import unittest
from fractions import Fraction as F
from polygon_core import vertices, inside_all_angles, outer_area_bound
from trimmed_core import vertices as octagon, parameters
from score import area, contains


class PolygonCoreTest(unittest.TestCase):
    def test_nested_exact_inner_cores(self):
        for D in (F(1,2), F(83,40000), F(1,2500)):
            old=octagon(D)
            for k in (1,2,4):
                new=vertices(D,k)
                self.assertEqual(len(new),8*k+8)
                self.assertTrue(all(inside_all_angles(p,D) for p in new))
                self.assertTrue(all(contains(new,p) for p in old))
                self.assertGreater(area(new),area(old))
                self.assertLess(area(new),outer_area_bound(D))
                old=new

    def test_endpoint_only_check_is_insufficient(self):
        D=F(1,2);h,_=parameters(D);u=D/2
        c,s=(1-u*u)/(1+u*u),2*u/(1+u*u)
        p=(h,h*(1-c)/s)
        self.assertEqual(c*p[0]+s*p[1],h)
        self.assertFalse(inside_all_angles(p,D))


if __name__=='__main__':unittest.main()
