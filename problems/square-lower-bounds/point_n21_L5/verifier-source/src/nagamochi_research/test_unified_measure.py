import unittest,json
from fractions import Fraction as F
import numpy as np
from unified_measure import SCHEMA,orbit,region,coefficient,validate,verify
from unified_geometry import matrix,expand_primitives
from unified_grid_search import structured,shifted_controls

class UnifiedTests(unittest.TestCase):
    def test_segment_fraction_is_length_ratio_including_diagonal(self):
        reg=region(F(0),(F(1),F(1),F(1),F(1)),F(1))
        self.assertEqual(coefficient('segment',tuple(map(F,[0,0,2,2])),reg),F(1,2))
        self.assertEqual(coefficient('segment',tuple(map(F,[0,1,2,1])),reg),F(1,2))
        # Boundary line has positive mass; an endpoint by itself has zero line mass.
        self.assertEqual(coefficient('segment',(F(0),F(1,2),F(2),F(1,2)),reg),F(1,2))
        self.assertEqual(coefficient('segment',(F(0),F(0),F(1,2),F(1,2)),reg),0)

    def test_numeric_exact_all_types_random_rotations(self):
        L=F(4);B=F(9,10)
        ps=[dict(kind='point',geometry=['1','3/2']),dict(kind='segment',geometry=['1/4','1/3','7/4','9/5']),
            dict(kind='rectangle',geometry=['1/5','2/5','13/10','17/10'])]
        rng=np.random.default_rng(482)
        poses=[(F(int(x),100),F(int(y),100),F(int(t),1000)) for x,y,t in rng.integers([80,80,0],[320,320,415],size=(30,3))]
        got=matrix(np.asarray(poses,float),float(B),expand_primitives(ps,L))
        expected=[]
        for x,y,t in poses:
            reg=region(t,(x,x,y,y),B)
            expected.append([float(sum((coefficient(p['kind'],g,reg) for g in orbit(p['kind'],p['geometry'],L)),F(0))/8) for p in ps])
        np.testing.assert_allclose(got,expected,rtol=1e-10,atol=1e-11)

    def test_common_region_is_lower_bound_all_types(self):
        L=F(4);B=F(9,10);t=F(1,5);box=(F(1),F(11,10),F(6,5),F(7,5))
        common=region(t,box,B)
        for p in structured(L,4):
            for g in orbit(p['kind'],p['geometry'],L):
                lb=coefficient(p['kind'],g,common)
                for x,y in [(box[0],box[2]),(box[1],box[3]),(F(21,20),F(13,10))]:
                    self.assertLessEqual(lb,coefficient(p['kind'],g,region(t,(x,x,y,y),B)))

    def test_saved_rectangle_normalization_is_preserved(self):
        from geometry import Geometry
        import math
        L=3.97;B=.9977;r=np.asarray([[.2,.3,.7,.8],[.98,.8,1.,1.5]])
        poses=np.random.default_rng(203).uniform(0,1,(25,3));physical=[]
        for u,v,z in poses:
            theta=z*math.pi/4;e=(L-B*(math.cos(theta)+math.sin(theta)))/2
            physical.append([L/2+u*e,L/2+v*e,math.tan(theta/2)])
        ps=[dict(kind='rectangle',geometry=list(map(str,x))) for x in r]
        np.testing.assert_allclose(Geometry(L,B,r).matrix(poses),matrix(np.asarray(physical),B,expand_primitives(ps,F(str(L)))),rtol=1e-10,atol=1e-11)

    def test_control_count_shapes_and_validation(self):
        L=F(397,100);p=structured(L,4);q=shifted_controls(p,set(),L)
        self.assertEqual(len(p),len(q))
        for a,b in zip(p,q):
            self.assertEqual(a['kind'],b['kind']);x=list(map(F,a['geometry']));y=list(map(F,b['geometry']))
            if len(x)==4:self.assertEqual((x[2]-x[0],x[3]-x[1]),(y[2]-y[0],y[3]-y[1]))
            self.assertTrue(all(0<z<L for z in y))
        bad=dict(schema=SCHEMA,n=2,L='2',B='9/10',net=dict(step='1/100',last=42),total_mass='1',primitives=[dict(kind='segment',geometry=['1','1','1','1'],mass='1')])
        with self.assertRaises(ValueError):validate(bad)

    def test_full_net_completion_and_resume_binding(self):
        # Uniform density: analytically every full core has mass > 1.
        d=dict(schema=SCHEMA,n=6,L='3/2',B='9/10',net=dict(step='1/100',last=42),total_mass='5',
               primitives=[dict(kind='rectangle',geometry=['0','0','3/2','3/2'],mass='5')])
        w=verify(d,max_boxes=1)
        self.assertEqual(w['status'],'INCONCLUSIVE')
        bad=json.loads(json.dumps(d));bad['n']=7
        with self.assertRaises(ValueError):verify(bad,work=w,max_boxes=1)
        w=verify(d,work=w,max_boxes=20000)
        self.assertEqual(w['status'],'CERTIFIED');self.assertEqual(w['directions_completed'],43)
        d['primitives'][0]['mass']='1';d['total_mass']='1'
        self.assertEqual(verify(d,max_boxes=2)['status'],'UNCOVERED')

if __name__=='__main__':unittest.main()
