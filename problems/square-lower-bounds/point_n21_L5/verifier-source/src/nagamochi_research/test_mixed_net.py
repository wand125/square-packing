from fractions import Fraction as F
import pytest
from mixed_net_audit import net_certificate,symmetry
from mixed_axis_cells import boundary_trap,axis_cell_lower
from mixed_net_witnesses import map_witness
from mixed_density_check import expand,evaluate
from test_mixed_density_check import example


def test_net_has_strict_margin_and_rejects_invalid_spacing():
    cert=net_certificate(F(9977,10000))
    assert cert['side_margin']=='91909/400000000'
    step=F(83,40000)
    for t in (F(0),F(1,3),F(2,5),F(414,1000)):
        j=int(t/step+F(1,2));a=j*step;z=abs(t-a)/(1+t*a)
        assert abs(t-a)<=step/2
        assert (1+2*z-z*z)/(1+z*z)<=1+step
    with pytest.raises(ValueError):net_certificate(F(9999,10000))
    with pytest.raises(ValueError):net_certificate(F(9977,10000),F(1,1000))


def test_axis_boundary_trap_and_unsplit_events():
    assert boundary_trap()['interior_score']=='0'
    model=expand(example())
    assert axis_cell_lower(model,F(19,10),F(21,10),F(19,10),F(21,10))==F(5,4)
    with pytest.raises(ValueError,match='Unsplit'):axis_cell_lower(model,F(3,2),F(2),F(19,10),F(21,10))


def test_symmetry_and_last_net_angle_mapping():
    data=example();model=expand(data);assert symmetry(model)
    w=evaluate(model,F(2),F(2),F(83,200));mapped=map_witness(model,w)
    t=F(mapped['canonical_witness']['t'])
    assert mapped['net_index']==200 and t*t+2*t-1<0
    assert mapped['net_score']==w['score']
    data['points'][0]['point']=['2','1']
    with pytest.raises(ValueError):symmetry(expand(data))


def test_unit_centre_domains_are_smaller_than_core_domains():
    from mixed_net_audit import centre_domains
    domains=centre_domains(F('4.98'),F('0.9977'))
    assert len(domains)==201 and domains[0]['centre_low']=='1/2'
    assert all(F(d['eliminated_boundary_width'])>0 for d in domains)
    for d in domains:
        a=F(d['original_t_lower'])
        assert a*a+2*a<=1
        assert F(d['centre_low'])==(1+2*a-a*a)/(2*(1+a*a))
