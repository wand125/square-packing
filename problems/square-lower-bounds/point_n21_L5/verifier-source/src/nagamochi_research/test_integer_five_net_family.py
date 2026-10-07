from fractions import Fraction as F
import pytest
from integer_five_net_family import family,identity_certificate


def test_endpoint_family_has_valid_last_bin_and_strict_containment():
    identity_certificate()
    for e in (F(1),F(1,80),F(1,1000),F(7,12345)):
        r=family(e);B,D,L=map(F,(r['B'],r['step'],r['L']));last=r['last']
        assert (1+last*D)**2>=2 and (1+(last-F(1,2))*D)**2<2
        assert B*(1+D)<1 and 1+4*B>L
    with pytest.raises(ValueError):family(0)


def test_integer_four_uses_its_own_grid_threshold():
    identity_certificate(4)
    for e in (F(1,25),F(1,10000)):
        r=family(e,4);B=F(r['B']);assert F(r['L'])==4-e
        assert 1+3*B-F(r['L'])==e/2
        assert F(r['containment_margin_lower'])==e*e/36
