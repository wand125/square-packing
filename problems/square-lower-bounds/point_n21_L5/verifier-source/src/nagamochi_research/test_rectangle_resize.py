import unittest
import numpy as np
from prepare_rectangle_resize import resize_rectangles


class RectangleResizeTest(unittest.TestCase):
    def test_uniform_and_wall(self):
        a=np.array([[1.,1.,9.,9.],[0.,0.,10.,10.]])
        v,failed=resize_rectangles(a,10,8,'uniform')
        np.testing.assert_allclose(v,a*.8);self.assertEqual(failed,[])
        v,failed=resize_rectangles(a,10,8,'central')
        np.testing.assert_allclose(v,[[1,1,7,7],[0,0,8,8]])

    def test_collapsed_columns_retained(self):
        a=np.array([[4.9,4.9,5.1,5.1],[0,0,10,10]])
        v,failed=resize_rectangles(a,10,8,'endpoint')
        self.assertEqual(len(v),len(a));self.assertEqual(failed,[0])
        np.testing.assert_allclose(v[0],a[0]*.8)
        np.testing.assert_allclose(v[1],[0,0,8,8])


if __name__=='__main__':unittest.main()
