from fractions import Fraction as F
from translated_core_bound import translated_lower_bound
from robust_pose_core import polygon_lower_bound


def test_full_density_does_not_lose_mass_from_centre_motion():
    model=(F(4),F(9,10),[(F(0),F(0),F(4),F(4),F(1))],[])
    box=tuple(map(F,['1','2','1','2','0','0']))
    assert polygon_lower_bound(model,*box)==0
    assert translated_lower_bound(model,*box)==F(81,100)


def test_separate_rectangle_minima_and_closed_atoms():
    model=(F(4),F(1),[(F(0),F(0),F(2),F(4),F(1)),
                     (F(2),F(0),F(4),F(4),F(1))],
           [((F(2),F(2)),F(3))])
    box=tuple(map(F,['1.5','2.5','2','2','0','0']))
    # Each rectangle has a zero-overlap endpoint; the atom is on both closed
    # endpoint cores, hence on every intermediate translated core.
    assert translated_lower_bound(model,*box)==3


def test_correlated_translation_dominates_old_and_bounds_exact_samples():
    from translated_core_bound import translated_correlated_lower_bound
    from mixed_density_check import polygon_score
    from score import square
    from itertools import product
    model=(F(4),F(9,10),[(F(1),F(1),F(3),F(3),F(2)),
        (F(3,2),F(1),F(5,2),F(3),F(1))],[((F(2),F(2)),F(1))])
    for a,b in [(F(-1,10),F(1,10)),(F(1,10),F(1,5)),(F(0),F(0))]:
        box=(F(19,10),F(21,10),F(19,10),F(21,10),a,b)
        lower=translated_correlated_lower_bound(model,*box)
        assert lower>=translated_lower_bound(model,*box)
        for x,y,t in product([box[0],F(2),box[1]],[box[2],F(2),box[3]],[a,(a+b)/2,b]):
            assert lower<=sum(polygon_score(square(x,y,model[1],t),model[2],model[3]))
