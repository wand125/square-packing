import copy,unittest
from unittest.mock import patch
from fractions import Fraction as F
import numpy as np
from unified_measure import RADIAL_SCHEMA,SCHEMA,validate,verify,orbit,region,score_bounds
from unified_geometry import matrix,expand_primitives

def fixture(kind='annulus'):
    return dict(schema=RADIAL_SCHEMA,n=2,L='3/2',B='9/10',net=dict(step='1/100',last=42),total_mass='1001/1000',
        primitives=[dict(kind=kind,geometry=['3/4','3/4','1/100']+(['9/10'] if kind=='annulus' else []),mass='1001/1000')])

class NativeTests(unittest.TestCase):
    def test_all_radial_types_complete_and_resume(self):
        for kind in ('disk','bump','annulus'):
            d=fixture(kind);w=verify(d,max_boxes=2)
            self.assertEqual(w['status'],'INCONCLUSIVE')
            self.assertEqual(verify(d,work=w,max_boxes=100)['status'],'CERTIFIED')
            bad=copy.deepcopy(d);bad['primitives'][0]['geometry'][2]='1/99'
            with self.assertRaises(ValueError):verify(bad,work=w)

    def test_negative_mass_and_invalid_schema(self):
        d=fixture();d['primitives'][0]['mass']='-1';d['total_mass']='-1'
        with self.assertRaises(ValueError):validate(d)
        d=fixture();d['schema']=SCHEMA
        with self.assertRaises(ValueError):validate(d)
        d=fixture();d['primitives'][0]['geometry'][-1]='1'
        with self.assertRaises(ValueError):validate(d)

    def test_ambiguous_integral_never_becomes_counterexample(self):
        d=fixture()
        with patch('unified_measure.score_bounds',return_value=(F(99,100),F(101,100))):
            w=verify(d,max_boxes=2,integral_subdivisions=1,max_integral_subdivisions=1)
        self.assertEqual(w['status'],'INCONCLUSIVE');self.assertEqual(w['reason'],'INTEGRAL_PRECISION')
        self.assertTrue(w['stack']);self.assertNotIn('witness',w)
        self.assertEqual(verify(d,work=w,max_boxes=100)['status'],'CERTIFIED')
        d['primitives'][0]['mass']='1/2';d['total_mass']='1/2'
        w=verify(d,max_boxes=3);self.assertEqual(w['status'],'UNCOVERED')
        self.assertLess(F(w['witness']['mass_upper']),1)

    def test_native_matrix_inside_exact_bounds(self):
        L=F(3);B=F(9,10)
        ps=[dict(kind=k,geometry=['3/5','7/10','1/4']+(['49/50'] if k=='annulus' else [])) for k in ('disk','bump','annulus')]
        poses=[(F(4,5),F(9,10),F(1,5)),(F(1),F(1),F(0))]
        values=matrix(np.array(poses,float),float(B),expand_primitives(ps,L))
        for i,(x,y,t) in enumerate(poses):
            for j,p in enumerate(ps):
                expanded=[(p['kind'],g,F(1,8)) for g in orbit(p['kind'],p['geometry'],L)]
                lo,hi=score_bounds(expanded,region(t,(x,x,y,y),B),64)
                self.assertLessEqual(float(lo),values[i,j]);self.assertGreaterEqual(float(hi),values[i,j])

if __name__=='__main__':unittest.main()
