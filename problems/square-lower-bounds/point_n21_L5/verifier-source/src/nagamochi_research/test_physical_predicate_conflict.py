from fractions import Fraction as F
import copy,json
import pytest
from physical_predicate_conflict import wall_polynomials,strengthen,replay
from predicate_lp_capture import certify
from predicate_partition import replay_capture_record


def test_wall_polynomials_equal_exact_physical_inequalities():
    box=list(map(F,['2/5','3/5','4/5','6/5','0','1/2']))
    polys=wall_polynomials(3,box)
    for corner,(x,y) in enumerate([(box[0],box[2]),(box[0],box[3]),(box[1],box[2]),(box[1],box[3])]):
        for t in [F(0),F(1,7),F(2,5),F(1,2)]:
            r=1+t*t;h=(1+2*t-t*t)/(2*r)
            for k,value in enumerate([h-x,x+h-3,h-y,y+h-3]):
                a,b,c=polys[k][corner]
                assert a+b*t+c*t*t==2*r*value


def test_wall_cut_is_conditional_and_rejects_changed_assumptions():
    points=[(F(1),F(1,2),F(1)),(F(11,10),F(1,2),F(1,10))]
    box=list(map(F,['2/5','3/5','49/100','51/100','0','0']))
    base=certify(points,box);base['box']=list(map(str,box))
    assert F(base['lower'])==0
    proof=json.loads(json.dumps(strengthen(points,base,box,2)))
    assert replay(points,proof,2)['certified_unit_capture']
    assert proof['cuts']
    with pytest.raises(ValueError,match='container'):replay(points,proof,3)
    with pytest.raises(ValueError,match='context'):replay_capture_record(points,proof)
    bad=copy.deepcopy(proof);bad['cuts'][0]['pattern'][-4]=0
    with pytest.raises(ValueError,match='walls'):replay(points,bad,2)
    bad=copy.deepcopy(proof);bad['cuts'][0]['row']['rhs']+=1
    with pytest.raises(ValueError,match='cut mismatch'):replay(points,bad,2)
