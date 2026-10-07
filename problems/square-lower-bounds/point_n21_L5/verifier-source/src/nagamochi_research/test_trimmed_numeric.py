import unittest
import numpy as np
from fractions import Fraction as F
from trimmed_core import parameters,planes,coefficient
from trimmed_numeric import matrix
from unified_geometry import expand_primitives,matrix as square_matrix
from unified_measure import orbit,TRIMMED_SCHEMA,verify

class TrimmedNumericTest(unittest.TestCase):
    def test_exact_numeric_agreement_and_superset(self):
        L=F(4);D=F(1,2500);h,g=parameters(D)
        ps=[dict(kind='point',geometry=['1','1']),dict(kind='segment',geometry=['.2','.3','2','1.2']),dict(kind='rectangle',geometry=['.4','.5','1.7','2'])]
        q=np.random.default_rng(8).uniform([.5,.5,0],[3.5,3.5,.415],(35,3));ex=expand_primitives(ps,L)
        got=matrix(q,.9995,ex,float(h),float(g));ref=[]
        for x,y,t in q:
            iq=planes(F(str(t)),[F(str(x)),F(str(x)),F(str(y)),F(str(y))],D)
            ref.append([float(sum(coefficient(p['kind'],r,iq) for r in orbit(p['kind'],p['geometry'],L))/8) for p in ps])
        np.testing.assert_allclose(got,ref,atol=1e-11)
        self.assertTrue(np.all(got>=square_matrix(q,.9995,ex)-1e-11))
    def test_new_schema_exact_verification_and_binding(self):
        d=dict(schema=TRIMMED_SCHEMA,n=3,L='1.5',B='.9',net=dict(step='1/100',last=42),core=dict(kind='octagon_with_square_radial',margin='1/100000000'),total_mass='2.99',primitives=[dict(kind='point',geometry=['.75','.75'],mass='2.99')])
        w=verify(d,max_boxes=1)
        d['core']['margin']='1/10000000'
        with self.assertRaises(ValueError):verify(d,work=w,max_boxes=1)
        w=verify(d,max_boxes=10000)
        self.assertEqual(w['status'],'CERTIFIED')
        self.assertEqual(w['directions_completed'],43)

if __name__=='__main__':unittest.main()
