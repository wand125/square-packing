from fractions import Fraction as F
from itertools import product
import numpy as np
from axis_low_capture_capacity import compress,tile_cover


def test_compression_preserves_every_mask_cell():
    for bits in product((False,True),repeat=6):
        mask=np.array(bits).reshape(2,3);covered=set()
        for i,I,j,J in compress(mask):covered|={(x,y) for x in range(i,I) for y in range(j,J)}
        assert covered==set(zip(*np.where(mask)))


def test_grid_cover_includes_touching_endpoints_and_negative_indices():
    rectangles=[(F(-1),F(0),F(0),F(1))]
    assert tile_cover(rectangles,F(1),F(0),F(0))==[(-1,0),(-1,1),(0,0),(0,1)]
