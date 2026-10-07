from fractions import Fraction as F
import numpy as np
from repair_lemma_measure import coefficients,expand_primitives
from mixed_density_check import expand,evaluate


def test_signed_pose_adapter_matches_rational_score():
    d=dict(n=12,L='4',B='9/10',rectangles=[dict(rectangle=['1/2','1','3/2','2'],mass='2')],points=[],total_mass='2')
    primitives=[dict(kind='rectangle',geometry=d['rectangles'][0]['rectangle'])]
    model=expand(d);p=[tuple(map(F,['7/10','13/10','-1/3'])),tuple(map(F,['7/10','27/10','1/3']))]
    actual=coefficients(p,F(9,10),expand_primitives(primitives,F(4)),F(4))@np.array([2.])
    expected=[float(F(evaluate(model,*q)['score'])) for q in p]
    assert np.max(np.abs(actual-expected))<1e-12
    assert actual[0]==actual[1]
