from fractions import Fraction as F
import pytest
from point_box_sieve import prepare,witness,replay


def test_exact_gate_rejects_float_near_boundary_false_positive():
    pts=[(F(1,2)+F(1,10**14),F(0))];ws=[F(1)]
    box=list(map(F,[0,0,0,0,0,0]))
    assert witness(pts,ws,box,prepare(pts,ws)) is None


def test_witness_and_serialized_mass_can_be_replayed():
    pts=[(F(1,2),F(1,2)),(F(4),F(4))];ws=[F(3,2),F(8)]
    box=['2/5','3/5','2/5','3/5','0','1/10']
    r=witness(pts,ws,box,prepare(pts,ws));assert replay(pts,ws,box,r)==F(3,2)
    r['indices']=[0,0]
    with pytest.raises(ValueError):replay(pts,ws,box,r)
