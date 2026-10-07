from fractions import Fraction as F
from mix_point_candidates import rational_simplex, mixture_upper_bound, run


def test_simplex_is_exact_and_nonnegative():
    values = rational_simplex([0.3333333334,0.6666666667,-1e-15])
    assert sum(values) == 1 and min(values) == 0


def test_dual_bound_for_complementary_candidates():
    dual,upper=mixture_upper_bound([[F(0),F(2)],[F(2),F(0)]],[0.5,0.5])
    assert dual == [F(1,2),F(1,2)] and upper == 1


def test_complementary_captures_and_exact_export(tmp_path):
    # Nine grid points in [0,3]^2, split into corners versus other points.
    # Each source has mass 4 and a zero-capture axis square; their mixture
    # can give all nine points mass 4/9.
    from exact_fixed_angle_separator import run as separate
    from probe_external_integer_bridge import read
    geometry = [(x,y) for x in (1,3,5) for y in (1,3,5)]
    corner = [int(x != 3 and y != 3) for x,y in geometry]
    candidates=[]; reports=[]
    for j,weights in enumerate(([5*c for c in corner],[4*(1-c) for c in corner])):
        candidate=tmp_path/f'source{j}.txt'
        candidate.write_text('\n'.join(['3 1','2','5','9']+
                             [f'{x} {y} {w}' for (x,y),w in zip(geometry,weights)])+'\n')
        report=tmp_path/f'sep{j}.json'
        separate(candidate,[F(0)],report)
        candidates.append(candidate);reports.append(report)
    result=run(candidates,reports,[F(0)],tmp_path/'out',rounds=2)
    last=result['rounds'][-1]
    assert F(last['total_mass']) == 4
    assert F(last['fixed_angle_minimum']) >= F(4,9)-F(1,10**8)
    assert all(F(c)>0 for c in last['coefficients'])
    L,span,W,pts=read(tmp_path/'out'/f"round{last['round']}"/'candidate.txt')
    assert sum(w for x,y,w in pts) == 4*W
