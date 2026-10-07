import numpy as np
import pytest
from mixed_ladder_price import pricing_dual


def test_pricing_roundoff_does_not_change_original_lp_dual():
    original = np.array([-0.2, 6.854800493953997e-16, 0.0])
    snapshot = original.copy()
    assert np.array_equal(pricing_dual(original), [0.2, 0, 0])
    assert np.array_equal(original, snapshot)


@pytest.mark.parametrize('bad', [2e-9, np.nan, np.inf])
def test_pricing_rejects_materially_invalid_dual(bad):
    with pytest.raises(ValueError):
        pricing_dual([-1.0, bad])
