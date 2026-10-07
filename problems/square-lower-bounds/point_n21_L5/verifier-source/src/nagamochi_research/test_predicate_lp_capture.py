from fractions import Fraction as F
import pytest
from predicate_lp_capture import certify,rational_bound


def test_opposed_edges_cover_a_positive_volume_box():
    # At every pose at least one endpoint is captured, though neither is always in.
    pts=[(F(0),F(0),F(1)),(F(1),F(0),F(1))]
    box=[F(2,5),F(3,5),F(-1,100),F(1,100),F(0),F(1,100)]
    result=certify(pts,box)
    assert F(result['baseline'])==0 and F(result['lower'])==1
    assert result['certified_unit_capture']
    lower,penalty=rational_bound(list(map(F,result['cost'])),result['rows'],list(map(F,result['multipliers'])))
    assert lower==1 and penalty==0


def test_fractional_relaxation_failure_is_not_a_counterexample():
    # Four corners cover every axis-aligned centre in the box, but an LP can use halves.
    pts=[(F(x),F(y),F(1)) for x in (0,1) for y in (0,1)]
    result=certify(pts,[F(2,5),F(3,5),F(2,5),F(3,5),F(0),F(0)])
    assert F(result['lower'])<1 and not result['certified_unit_capture']


def test_exact_residual_accounts_for_infeasible_dual_proposal():
    rows=[dict(terms=[(0,1)],rhs=1)]
    bound,penalty=rational_bound([F(1)],rows,[F(2)])
    assert bound==1 and penalty==-1
    with pytest.raises(ValueError):rational_bound([F(1)],rows,[F(-1)])
    assert F(certify([(F(1,2),F(0),F(2))],[F(2,5),F(3,5),F(0),F(0),F(0),F(0)])['lower'])==2


def test_replay_reconstructs_rows_and_rejects_claimed_bound():
    from predicate_lp_capture import replay_certificate
    pts=[(F(0),F(0),F(1)),(F(1),F(0),F(1))]
    box=[F(2,5),F(3,5),F(0),F(0),F(0),F(1,100)]
    import json
    record=json.loads(json.dumps(certify(pts,box)))
    assert replay_certificate(pts,box,record)['certified_unit_capture']
    record['lower']='2'
    with pytest.raises(ValueError):replay_certificate(pts,box,record)


@pytest.mark.parametrize('angle',[(F(0),F(1,100)),(F(1,8),F(1,3)),(F(2,5),F(1,2))])
def test_exact_endpoint_screen_preserves_reference_model(angle):
    # Includes closed-boundary coincidences and wide angle intervals, where
    # endpoint tests alone cannot certify the quadratic's interior maximum.
    pts=[(F(x,2),F(y,2),F(1,3)) for x in range(3) for y in range(3)]
    box=[F(2,5),F(3,5),F(2,5),F(3,5),*angle]
    reference=certify(pts,box,endpoint_screen=False)
    screened=certify(pts,box,multipliers=reference['multipliers'])
    reference['numerical_lp_objective']=None
    assert screened==reference
