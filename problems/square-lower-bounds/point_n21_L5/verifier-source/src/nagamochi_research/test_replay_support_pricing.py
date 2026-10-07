import json
import pytest
from replay_support_pricing import replay


def test_pricing_replay_rejects_wrong_flag_and_geometry(tmp_path):
    base=tmp_path/'base.json';dual=tmp_path/'dual.json';pricing=tmp_path/'pricing.json'
    base.write_text(json.dumps(dict(L='4')))
    dual.write_text(json.dumps(dict(records=[dict(B='999999/1000000',scale='1')],poses=[['2','2','0']],unscaled_weights=['2'])))
    c=dict(kind='point',geometry=['2','2'],dual_load='2',improves_dual=True)
    pricing.write_text(json.dumps(dict(columns=[c])))
    assert replay(base,dual,pricing)['improving']==1
    c['improves_dual']=False;pricing.write_text(json.dumps(dict(columns=[c])))
    with pytest.raises(ValueError):replay(base,dual,pricing)
    c['improves_dual']=True;c['geometry']=['5','2'];pricing.write_text(json.dumps(dict(columns=[c])))
    with pytest.raises(ValueError):replay(base,dual,pricing)
