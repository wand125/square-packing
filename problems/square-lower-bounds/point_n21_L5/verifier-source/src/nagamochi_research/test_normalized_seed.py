from copy import deepcopy
from pathlib import Path
import json
import pytest
from normalized_seed import verify_case

ROOT=Path(__file__).resolve().parents[2]


def test_only_pure_envelope_proofs_transfer_to_fixed_normalized_scope():
    base=json.loads((ROOT/'runs/epsilon_cell_envelope_20260927/scaled-exact/k5-mNone.json').read_text())
    q=json.loads((ROOT/'runs/correlated_epsilon_20260927/normalized-n21/transferred-seed.json').read_text())
    case=q['cases'][0];assert verify_case(base,case)
    bad=deepcopy(case);bad['source_model']='CORRELATED_EPSILON_V2'
    with pytest.raises(AssertionError):verify_case(base,bad)
    for kind in ('CORRELATED_EPSILON_V2','NORMALIZED_MOVING_BANDS_V3','NORMALIZED_CAPPED_BANDS_V4'):
        bad=deepcopy(case);bad['model']=kind
        with pytest.raises(AssertionError):verify_case(base,bad)
