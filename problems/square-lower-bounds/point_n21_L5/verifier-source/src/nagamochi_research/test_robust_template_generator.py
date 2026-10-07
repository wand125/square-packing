import unittest
from unittest.mock import patch
from types import SimpleNamespace
import numpy as np
from robust_template_generator import maximin,remap_poses,minimum_change,solve_lp
from scipy.optimize import linprog

class RobustTest(unittest.TestCase):
    def test_indeterminate_retry_retains_constraints(self):
        A=np.array([[-1.,0.],[0.,-1.]])
        with patch('robust_template_generator.linprog',side_effect=[SimpleNamespace(status=4),linprog([1.,1.],A_ub=A,b_ub=[-1.,-2.])]) as mocked:
            r=solve_lp([1.,1.],A_ub=A,b_ub=[-1.,-2.],method='highs',options={})
            self.assertTrue(r.success)
            retry=mocked.call_args.kwargs
            self.assertIs(retry['A_ub'],A)
            self.assertEqual(retry['b_ub'],[-1.,-2.])
            self.assertEqual(retry['method'],'highs-ds')
            self.assertFalse(retry['options']['presolve'])

    def test_dual_prices_and_mass(self):
        A=np.array([[.2,.8,0],[.2,0,.8]])
        w,f,y=maximin(A,10,.5)
        self.assertAlmostEqual(w.sum(),10)
        self.assertAlmostEqual(f,3.)
        np.testing.assert_allclose(A[:,1:].T@y,[1.,1.],atol=1e-7)
        self.assertGreater(float(np.array([1.,1.])@y),1.)
    def test_pose_domain_conversion(self):
        q=np.array([[.9977/2,.9977/2,0],[4.53,4.53,.2]])
        p=remap_poses(q,9.06,.9977,.9995)
        np.testing.assert_allclose(p[0,:2],.9995/2)
        np.testing.assert_allclose(p[1],q[1])

    def test_minimum_change_preserves_good_weights(self):
        A=np.array([[1.,0.],[0.,1.]])
        ref=np.array([1.,1.]);w,f=minimum_change(A,2.,ref,0.,.9)
        np.testing.assert_array_equal(w,ref)
        w,f=minimum_change(A,2.,np.array([1.5,.5]),0.,.9)
        self.assertAlmostEqual(w.sum(),2.)
        self.assertGreaterEqual(f,.9-2e-7)
        with self.assertRaises(ValueError):minimum_change(A,2.,ref,0.,1.1)

if __name__=='__main__':unittest.main()
