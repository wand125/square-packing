import unittest
from fractions import Fraction as F
import numpy as np
from radial_measure import interval,polygon_interval,pi_bounds,disk_integral,variable_matrix,numerical_matrix
from unified_measure import region,orbit

class RadialTests(unittest.TestCase):
    def test_variable_annuli_and_orbits(self):
        nodes,weights=np.polynomial.legendre.leggauss(256)
        L=F(3);B=F(1);p=(F(3,5),F(1,10));R=F(1,4)
        t=F(1,5);cx=F(2,5);cy=F(1,3)
        poses=np.array([[float(cx),float(cy),float(t)]])
        for q in (F(0),F(1,2),F(9,10),F(49,50)):
            k=np.array([[2,float(p[0]),float(p[1]),float(R),float(q)]])
            val=variable_matrix(poses,float(B),k,float(L),nodes,weights)[0,0]
            lo=hi=F(0)
            for pp in orbit('point',p,L):
                a,b=polygon_interval('annulus',pp,R,region(t,(cx,cx,cy,cy),B),32,q)
                lo+=a/8;hi+=b/8
            self.assertLessEqual(float(lo),val);self.assertGreaterEqual(float(hi),val)
            if q==F(1,2):self.assertAlmostEqual(val,numerical_matrix(poses,float(B),k[:,:4],float(L),nodes,weights)[0,0])
        for q in (F(-1,10),F(1)):
            with self.assertRaises(ValueError):polygon_interval('annulus',p,R,region(t,(cx,cx,cy,cy),B),8,q)

    def test_pi(self):
        lo,hi=pi_bounds()
        self.assertLess(lo,F('3.14159265358979323846264338327950288419716939937510'))
        self.assertGreater(hi,F('3.14159265358979323846264338327950288419716939937511'))
        self.assertLess(hi-lo,F(1,10**44))

    def test_interval_and_quadrature(self):
        nodes,weights=np.polynomial.legendre.leggauss(128)
        for kind in ('disk','bump','annulus'):
            for t in (F(0),F(1,5)):
                reg=region(t,(F(0),)*4,F(1));p=(F(3,5),F(1,10));R=F(1,4)
                lo,hi=interval(kind,p,R,reg,4)
                c,s=reg[:2];u=float(c*p[0]+s*p[1]);v=float(-s*p[0]+c*p[1])
                val=disk_integral(u,v,float(R),1.,kind=='bump',nodes,weights)
                norm=np.pi*float(R)**2
                if kind=='bump':norm/=2
                if kind=='annulus':val-=disk_integral(u,v,float(R)/2,1.,False,nodes,weights);norm*=.75
                self.assertLessEqual(float(lo),val/norm)
                self.assertGreaterEqual(float(hi),val/norm)
                tighter=interval(kind,p,R,reg,5)
                self.assertGreaterEqual(tighter[0],lo)
                self.assertLessEqual(tighter[1],hi)
                p0,p1=polygon_interval(kind,p,R,reg,16)
                self.assertLessEqual(float(p0),val/norm)
                self.assertGreaterEqual(float(p1),val/norm)
                self.assertLess(p1-p0,hi-lo)

    def test_known_geometry(self):
        for kind in ('disk','bump','annulus'):
            reg=region(F(0),(F(0),)*4,F(1))
            lo,hi=interval(kind,(0,0),F(1,4),reg,3)
            self.assertLessEqual(lo,1);self.assertEqual(hi,1)
            self.assertEqual(interval(kind,(2,2),F(1,4),reg,2),(0,0))
            # Symmetry bisects each radial kernel exactly.
            lo,hi=interval(kind,(F(1,2),0),F(1,4),reg,3)
            self.assertLessEqual(lo,F(1,2));self.assertGreaterEqual(hi,F(1,2))

if __name__=='__main__':unittest.main()
