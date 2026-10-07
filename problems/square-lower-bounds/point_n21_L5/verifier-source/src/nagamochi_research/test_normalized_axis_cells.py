from fractions import Fraction as F
from epsilon_cell_envelope import parameters,geometry as envelope_geometry
from normalized_axis_cells import geometry
from fixed_orientation_cover import angle_envelope
from saturated_axis_cells import contained
from score import square,cross,sub


def test_nominal_cores_are_strictly_inside_scaled_physical_squares():
    for k in (4,5,6,7,8):
        em=F(1,1000) if k<6 else F(1,10)
        q=parameters(k,eps_max=em);m=k-1;t=F(q['t']);h=F(q['rot_h']);R=F(q['rot_inner'])
        for e in (F(1,10**12),F(1,10**6),em):
            sigma=1-e/m
            for tau,nominal,side in ((-e/(2*m),F(0),F(1)),(e/(2*m),F(0),F(1)),(t-h,t,R),(t+h,t,R)):
                outer=square(0,0,1/sigma,tau);inner=square(0,0,side,nominal)
                assert all(cross(sub(b,a),sub(p,a))>0 for a,b in zip(outer,outer[1:]+outer[:1]) for p in inner)
            _,span=angle_envelope(t,h)
            assert (k-e-span)/(2*sigma)<=F(q['rot_half'])


def test_normalized_unit_cells_are_in_the_envelope_cells():
    for k in (4,5):
        q=parameters(k);cells,_=geometry(q,[]);old,_=envelope_geometry(q,[])
        assert all(contained(p,old[i]) for i,p in cells.items())


def test_transfer_rejects_correlated_coordinate_labels():
    import json
    import pytest
    from pathlib import Path
    from copy import deepcopy
    from normalized_certificate_transfer import transfer
    root=Path(__file__).resolve().parents[2]/'runs/epsilon_cell_envelope_20260927/scaled-exact'
    base=json.loads((root/'k4-mNone.json').read_text());q=json.loads((root/'k4-mNone-full3.json').read_text())
    result=transfer(base,q)
    assert result['near_axis_t_halfwidth']=='epsilon/6' and result['axis_boxes']==9
    bad=deepcopy(q);bad['cases'][0]['model']='CORRELATED_EPSILON_V2'
    with pytest.raises(AssertionError):transfer(base,bad)
