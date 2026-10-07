import numpy as np
from working_measure_lp import solve


def test_omitted_constraint_is_reintroduced_and_full_optimum_recovered():
    A=np.array([[1.,0.],[0.,.5],[.5,.5]])
    w,result=solve(A,np.array([0.,10.]),seed_count=1,batch=1)
    assert len(result['history'])>1
    assert result['history'][0]['violations']>0
    assert np.min(A@w)>=1-1e-7
    assert abs(sum(w)-3)<1e-8
    assert abs(result['gap'])<1e-8
    dual=np.zeros(len(A));dual[result['dual_rows']]=result['dual_weights']
    assert np.max(A.T@dual)<=1+1e-7
    assert abs(sum(dual)-3)<1e-8
