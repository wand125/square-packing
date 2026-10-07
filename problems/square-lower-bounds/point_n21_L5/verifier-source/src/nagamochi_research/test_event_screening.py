import unittest
import numpy as np
from event_screening import event_poses

class EventsTest(unittest.TestCase):
    def test_domain_and_thin_boundary_gap(self):
        L=2.;B=.9977
        ps=[dict(kind='point',geometry=['1','1'])]
        q=event_poses(ps,[1.],L,B,per_angle=8192)
        c=(1-q[:,2]**2)/(1+q[:,2]**2);s=2*q[:,2]/(1+q[:,2]**2);a=B*(c+s)/2
        self.assertTrue(np.all(q[:,:2]>=a[:,None]-1e-14))
        self.assertTrue(np.all(q[:,:2]<=L-a[:,None]+1e-14))
        axis=q[q[:,2]==0]
        # Edge gap has width 1-B=.0023; midpoint sampling must see it.
        self.assertTrue(np.any(np.max(np.abs(axis[:,:2]-1),axis=1)>B/2))
        np.testing.assert_array_equal(q,event_poses(ps,[1.],L,B))

if __name__=='__main__':unittest.main()
