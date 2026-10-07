from fractions import Fraction as F
import pytest
from joint_angle_lp import model,solve,replay,four_same_angle
from endpoint_joint_probe import separation
from score import square
from itertools import combinations


def test_four_parallel_squares_overlap_xy():
    for t in (F(1,1000),F(1,3)):
        q=four_same_angle(t);assert F(q['xy_overlap_margin'])>0
        polys=[square(F(x),F(y),1,t) for x,y in q['centres']]
        assert all(separation(a,b) is not None for a,b in combinations(polys,2))
        for axis in (0,1):
            assert max(min(p[axis] for p in poly) for poly in polys)<min(max(p[axis] for p in poly) for poly in polys)


def test_exact_bound_and_tamper_rejection():
    grid=[(x,y) for x in range(4) for y in range(3)];angles=[F(0)]*12
    q=solve(grid,angles);assert q['status']=='EXACT_BRANCH_OPTIMUM' and F(q['lower'])==4
    A,b=model(grid,angles);dual=list(map(F,q['dual']));primal=list(map(F,q['primal']))
    assert replay(A,b,dual,primal)==4
    dual[0]+=1
    with pytest.raises(AssertionError):replay(A,b,dual,primal)


def test_symbolic_family_and_active_system_recovery():
    from joint_angle_family import verify_case
    grid=[(x,y) for x in range(4) for y in range(3)]
    q=solve(grid,[F(1,1000)]*12)
    assert q['status']=='EXACT_BRANCH_OPTIMUM' and q['reconstruction']=='exact_active_system'
    q=solve(grid,[F(1,10)]*12)
    case=dict(n=12,grid=grid,pattern='same',t='1/10',**q)
    proof=verify_case(case)
    assert proof['status']=='EXACT_SYMBOLIC_CONDITIONAL_LOWER_BOUND'
    cone=next(c for c in proof['unequal_angle_cones'] if c['nominal_t']=='1/10')
    h=F(cone['each_t_radius'])
    perturbed=[F(1,10)+(h/2 if (x+y)%2 else -h/2) for x,y in grid]
    exact=solve(grid,perturbed)
    assert exact['status']=='EXACT_BRANCH_OPTIMUM' and F(exact['lower'])>4
    case['dual'][0]='-1/2'
    with pytest.raises((KeyError,AssertionError)):verify_case(case)
