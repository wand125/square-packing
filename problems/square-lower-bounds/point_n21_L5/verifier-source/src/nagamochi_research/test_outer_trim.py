import unittest
from fractions import Fraction as F
from outer_trim import trim_template,resize_template,endpoint_resize_template


class TrimTest(unittest.TestCase):
    def test_density_and_wall_anchors(self):
        ps=[dict(kind='rectangle',geometry=['0','0','10','10'])]
        out,w,m=trim_template(ps,[100],10,8,64)
        self.assertEqual(len(out),4)
        self.assertEqual(m['raw_mass'],64)
        self.assertTrue(all(x==16 for x in w))
        self.assertEqual(out[-1]['geometry'],['4','4','8','8'])
        out,w,m=trim_template([dict(kind='segment',geometry=['1','1','9','9'])],[8],10,8,6)
        self.assertEqual([p['geometry'] for p in out],[['1','1','4','4'],['4','4','7','7']])
        self.assertEqual(m['raw_mass'],6)

    def test_point_removal_identity_and_radial_restriction(self):
        ps=[dict(kind='point',geometry=['1','9']),dict(kind='point',geometry=['5','5'])]
        out,w,m=trim_template(ps,[2,3],10,8,2)
        self.assertEqual(out[0]['geometry'],['1','7']);self.assertEqual(len(out),1)
        self.assertEqual(m['removed_mass'],3)
        out,w,m=trim_template(ps,[2,3],10,10,5)
        self.assertEqual(len(out),2);self.assertEqual(m['removed_mass'],0)
        ps=[dict(kind='disk',geometry=['2','2','1']),dict(kind='bump',geometry=['4','4','1'])]
        out,w,m=trim_template(ps,[2,3],10,8,2)
        self.assertEqual(len(out),1);self.assertEqual(m['dropped_radial_columns'],1)

    def test_invalid_weights(self):
        for weights in ([-1],[float('nan')],[]):
            with self.assertRaises(ValueError):trim_template([dict(kind='point',geometry=['1','1'])],weights,10,8,2)

    def test_extension_density(self):
        ps=[dict(kind='rectangle',geometry=['0','0','8','8']),dict(kind='segment',geometry=['1','1','7','1'])]
        out,w,m=resize_template(ps,[64,6],8,10,108)
        self.assertEqual(out[0]['geometry'],['0','0','10','10'])
        self.assertEqual(out[1]['geometry'],['1','1','9','1'])
        self.assertEqual(m['raw_mass'],108)

    def test_endpoint_retains_central_mass(self):
        ps=[dict(kind='rectangle',geometry=['0','0','10','10']),dict(kind='point',geometry=['5','5']),dict(kind='disk',geometry=['5','5','1'])]
        out,w,m=endpoint_resize_template(ps,[100,2,3],10,8,69)
        self.assertEqual(out[0]['geometry'],['0','0','8','8'])
        self.assertEqual(out[1]['geometry'],['4','4'])
        self.assertEqual(out[2]['geometry'],['4','4','1'])
        self.assertEqual(m['raw_mass'],69)


if __name__=='__main__':unittest.main()
