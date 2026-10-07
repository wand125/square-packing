import copy
import unittest
from mixed_aux_policy import choose_branch

def result(maximum,holes,mean,mass=36.8):
    return dict(quality=dict(target=36.99,samples=65536,mass=mass,
        target_mass=dict(max_deficit=maximum,below_one=holes,mean_deficit=mean)))

class PolicyTests(unittest.TestCase):
    def test_n37_tradeoff_keeps_normal_despite_lower_mass(self):
        a=result(.026478,15,1.2714e-6,36.58645)
        b=result(.014674,21,2.1587e-6,36.58236)
        self.assertEqual(choose_branch(a,b)['recommended'],'normal')

    def test_all_quality_improves_without_mutation(self):
        a=result(.03,20,3e-6);b=result(.02,15,2e-6)
        before=copy.deepcopy((a,b));d=choose_branch(a,b)
        self.assertEqual(d['recommended'],'auxiliary');self.assertFalse(d['auto_promote'])
        self.assertEqual((a,b),before)

    def test_ties_budget_and_incomparable_audits(self):
        a=result(.03,20,3e-6)
        self.assertEqual(choose_branch(a,a)['recommended'],'normal')
        self.assertEqual(choose_branch(a,result(.01,1,1e-7,37))['recommended'],'normal')
        b=copy.deepcopy(a);b['quality']['target']=36.999
        with self.assertRaises(ValueError):choose_branch(a,b)

if __name__=='__main__':unittest.main()
