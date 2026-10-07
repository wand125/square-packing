from fractions import Fraction as F
import numpy as np
import pytest
from scipy.optimize import linprog
from predicate_lp_capture import certify
from predicate_weight_rows import compile_model,evaluate,weight_rows


def setup_model():
    points=[(F(0),F(0),F(1)),(F(1),F(0),F(1)),(F(1,2),F(0),F(0))]
    box=list(map(F,['2/5','3/5','0','0','0','1/100']))
    return points,compile_model(points,box,certify(points,box))


def test_preservation_blocks_loss_and_allows_new_baseline_support():
    points,model=setup_model()
    assert evaluate(model,points)==1
    lost=[(x,y,F(0) if i==0 else w) for i,(x,y,w) in enumerate(points)]
    assert evaluate(model,lost)==0
    revived=[(x,y,F(1) if i==2 else w) for i,(x,y,w) in enumerate(lost)]
    assert evaluate(model,revived)==1
    with pytest.raises(ValueError):evaluate(model,list(reversed(points)))


def test_weight_lp_preserves_box_while_unconstrained_cost_does_not():
    points,model=setup_model();data=weight_rows(model,[0,1,2],[1,1,1])
    A=np.zeros((len(data['rows']),data['variables']));b=[]
    for k,(row,rhs) in enumerate(data['rows']):
        for j,v in row.items():A[k,j]=-float(v)
        b.append(-float(rhs))
    # Only the two endpoint supports are allowed. Without preservation optimum is zero.
    bounds=[(0,None),(0,None),(0,0)]+[(0,None)]*(data['variables']-3)
    c=[1,1,1]+[0]*(data['variables']-3)
    solution=linprog(c,A_ub=A,b_ub=b,bounds=bounds,method='highs')
    assert solution.success and solution.fun==pytest.approx(2)
    new=[(x,y,F(str(solution.x[i]))) for i,(x,y,w) in enumerate(points)]
    assert evaluate(model,new)>=1
    assert linprog(c,bounds=bounds,method='highs').fun==0


def test_orbit_total_mass_coefficients_and_invalid_map():
    points,model=setup_model();data=weight_rows(model,[0,0,1],[2,1])
    assert any(row.get(0)==F(1,2) for row,rhs in data['rows'])
    with pytest.raises(ValueError):weight_rows(model,[0,0,1],[1,2])


def test_strengthened_model_preserves_geometry_checked_cut():
    import json
    from predicate_conflict import strengthen
    points,model=setup_model()
    box=list(map(F,['2/5','3/5','0','0','0','1/100']))
    proof=json.loads(json.dumps(strengthen(points,certify(points,box),box)))
    compiled=compile_model(points,box,proof)
    assert evaluate(compiled,points)==F(proof['lower'])
    bad_box=box.copy();bad_box[1]=F(7,10)
    with pytest.raises(ValueError,match='proof box'):compile_model(points,bad_box,proof)
