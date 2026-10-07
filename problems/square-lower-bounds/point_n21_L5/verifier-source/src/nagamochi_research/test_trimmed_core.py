import unittest
from fractions import Fraction as F
from trimmed_core import vertices,parameters,planes,coefficient
from score import area
from unified_measure import region,coefficient as square_coefficient

class TrimmedTest(unittest.TestCase):
    def test_area_inclusion_and_continuous_bound(self):
        D=F(1,2500);eps=F(1,10**8);h,g=parameters(D,eps);poly=vertices(D,eps)
        self.assertEqual(area(poly),(2*h)**2/(1+g))
        square=(2*h/(1+g))**2
        self.assertGreater(area(poly),square)
        # Analytic derivative numerator is positive throughout [0,D/2].
        u=D/2;self.assertGreaterEqual(1-2*u-u*u,0)
        for j in range(-20,21):
            t=u*j/20;c=(1-t*t)/(1+t*t);s=2*t/(1+t*t)
            for x,y in poly:
                self.assertLess(abs(c*x+s*y),F(1,2))
                self.assertLess(abs(-s*x+c*y),F(1,2))
    def test_coefficients_and_common_intersection(self):
        D=F(1,2500);B=F('.9995');t=F(1,5);box=tuple(map(F,['1','1.01','1','1.02']))
        common=planes(t,box,D)
        for kind,g in [('point',['1','1']),('segment',['0','1','2','1']),('rectangle',['0','0','2','2'])]:
            for x,y in [(box[0],box[2]),(box[1],box[3])]:
                p=planes(t,(x,x,y,y),D)
                self.assertLessEqual(coefficient(kind,g,common),coefficient(kind,g,p))
                self.assertGreaterEqual(coefficient(kind,g,p),square_coefficient(kind,tuple(map(F,g)),region(t,(x,x,y,y),B)))

if __name__=='__main__':unittest.main()
