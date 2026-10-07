import unittest
from fractions import Fraction as F
import numpy as np
from mixed_grid_pricing import candidate_pool, initial_state, propose_mixed_grid, screening_poses, quality_metrics, refinement_pool, refine_witnesses, KINDS
from unified_geometry import expand_primitives, matrix
from unified_measure import primitive_key


class MixedInitialTest(unittest.TestCase):
    def test_witness_descent_improves_and_stays_inside_domain(self):
        p=screening_poses(3.97,count=64,boundary_fraction=.5)
        def score(q):return ((q-np.array([1.9,1.9,.2]))**2).sum(axis=1)
        q,v=refine_witnesses(p,score(p),3.97,.9977,score,starts=8)
        self.assertTrue(np.all(v<=np.sort(score(p))[:8]+1e-12))
        t=q[:,2];e=(3.97-.9977*(1-t*t+2*t)/(1+t*t))/2
        self.assertTrue(np.all(np.abs(q[:,:2]-3.97/2)<=e[:,None]+1e-14))

    def test_refinement_is_bounded_unique_and_changes_geometry(self):
        ps=[dict(kind='point',geometry=['1','1']),dict(kind='rectangle',geometry=['.8','.8','1.2','1.2']),
            dict(kind='annulus',geometry=['1','1','.1','.9'])]
        pool=refinement_pool('3.97',ps,np.ones(3),per_kind=12)
        self.assertEqual(len(pool),36)
        keys={primitive_key(p['kind'],p['geometry'],F('3.97')) for p in pool}
        self.assertEqual(len(keys),len(pool))
        self.assertTrue(keys.isdisjoint({primitive_key(p['kind'],p['geometry'],F('3.97')) for p in ps}))
        for p in pool:
            g=list(map(F,p['geometry']))
            if p['kind']=='rectangle':self.assertTrue(g[0]<g[2] and g[1]<g[3])
            if p['kind']=='annulus':self.assertTrue(g[2]>0 and 0<=g[3]<1)

    def test_boundary_samples_fit_and_budget_quality_exposes_scaling(self):
        poses=screening_poses(3.97,count=192,boundary_fraction=.5)
        t=poses[:,2];c=(1-t*t)/(1+t*t);s=2*t/(1+t*t)
        e=(3.97-.9977*(c+s))/2
        self.assertTrue(np.all(np.abs(poses[:,:2]-3.97/2)<=e[:,None]+1e-14))
        self.assertTrue(np.any(t==0))
        q=quality_metrics([1.,1.1],mass=12.,target=10.)
        self.assertEqual(q['saved_mass']['below_one'],0)
        self.assertEqual(q['target_mass']['below_one'],2)
        self.assertAlmostEqual(q['target_mass']['max_deficit'],1/6)

    def test_bootstrap_covers_rotated_boundary_poses(self):
        ps, poses, weights, dual = initial_state('8.955')
        values = matrix(poses, .9977, expand_primitives(ps, F('8.955'))) @ weights
        np.testing.assert_allclose(values, 1.001, rtol=1e-11, atol=1e-11)
        self.assertEqual(len(poses), 1701)
        self.assertEqual(len(dual), len(poses))

    def test_pool_all_kinds_bounded_unique_and_non_grid(self):
        ps, _, ws, _ = initial_state('3.97')
        pool = candidate_pool('3.97', 4, ps, ws, per_kind=16, grid_fraction=0)
        self.assertEqual(set(p['kind'] for p in pool), set(KINDS))
        self.assertLessEqual(len(pool), 16*len(KINDS))
        self.assertNotIn('grid', [p['family'] for p in pool])
        self.assertEqual(len(pool), len({primitive_key(p['kind'], p['geometry'], F('3.97')) for p in pool}))
        self.assertEqual(pool, candidate_pool('3.97', 4, ps, ws, per_kind=16, grid_fraction=0))

    def test_prices_full_dual_and_no_input_mutation(self):
        ps, poses, ws, _ = initial_state('3.97')
        poses = poses[::89]; dual = np.full(len(poses), 20.)
        original = poses.copy()
        cols, report = propose_mixed_grid(poses, dual, F('3.97'), .9977, ps, ws, k=4, per_kind=8, max_columns=12)
        actual = matrix(poses, .9977, expand_primitives(cols, F('3.97'))).T @ dual
        np.testing.assert_allclose(actual, report['selected_scores'], rtol=1e-12)
        np.testing.assert_array_equal(poses, original)
        self.assertTrue(all(actual > 1))
        self.assertEqual(len(ps), 1)
        empty, _ = propose_mixed_grid(poses, np.zeros(len(poses)), F('3.97'), .9977, ps, ws, k=4, per_kind=8)
        self.assertEqual(empty, [])


if __name__ == '__main__':unittest.main()
