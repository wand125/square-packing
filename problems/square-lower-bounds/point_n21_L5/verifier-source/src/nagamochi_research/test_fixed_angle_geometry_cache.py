from fractions import Fraction as F
import pytest
from fixed_angle_geometry_cache import compile_geometry,replay
from exact_fixed_angle_separator import separate


def test_cache_reweights_zero_mass_points_without_geometry_change():
    coordinates=[(x,y) for x in range(13) for y in range(13)]
    for t in (F(0),F(1,10**9),F(1,4),F(1,2)):
        cache=compile_geometry(F(3),4,coordinates,t)
        for mode in range(3):
            points=[(x,y,((7*x+3*y+mode)%13 if mode<2 else 0)) for x,y in coordinates]
            assert replay(cache,points)['minimum_numerator']==separate(F(3),4,points,t)['minimum_numerator']


def test_cache_rejects_changed_coordinates_order_and_negative_weights():
    points=[(1,1,1),(1,3,2),(3,1,3),(3,3,4)]
    cache=compile_geometry(F(2),2,[(x,y) for x,y,w in points],F(1,7))
    for bad in (list(reversed(points)),[(0,0,1)]+points[1:],[(1,1,-1)]+points[1:]):
        with pytest.raises(ValueError):replay(cache,bad)
