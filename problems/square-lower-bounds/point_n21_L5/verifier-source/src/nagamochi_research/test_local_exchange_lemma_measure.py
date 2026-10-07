import numpy as np
import pytest
from local_exchange_lemma_measure import unrestricted_weights


@pytest.mark.parametrize('method',['highs','highs-ipm'])
def test_unrestricted_fit_preserves_budget_and_balances_coverage(method):
    A=np.array([[1.,0.],[0.,.5]])
    w,minimum=unrestricted_weights(A,np.array([1.,1.]),method=method)
    assert abs(sum(w)-2)<1e-12
    assert abs(minimum-2/3)<1e-12
    assert np.max(np.abs(A@w-minimum))<1e-12
