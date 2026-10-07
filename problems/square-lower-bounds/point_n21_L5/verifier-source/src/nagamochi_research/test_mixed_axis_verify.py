import json
from pathlib import Path
import numpy as np
import pytest
from mixed_axis_verify import verify
from verify_axis_certificate import replay


def candidate(path,mass,n,point=False):
    d=dict(n=n,L='2',B='1/2',rectangles=[dict(rectangle=['0','0','2','2'],mass=str(mass))],points=[dict(point=['1','1'],mass='1')] if point else [],total_mass=str(mass+int(point)))
    path.write_text(json.dumps(d));return path


def test_full_axis_and_boundary_mask_tampering(tmp_path):
    p=candidate(tmp_path/'candidate.json',20,22,True);out=tmp_path/'proof'
    assert verify(p,out)['status']=='AXIS_VERIFIED'
    assert replay(out)['status']=='AXIS_CERTIFICATE_REPLAYED'
    with np.load(out/'integer-tables.npz') as z:tables={k:z[k].copy() for k in z.files}
    # Last x interval starts at the point's capture boundary. The point is
    # captured on that boundary but not throughout the interval.
    assert tables['hx'][-1,0]==0
    tables['hx'][-1,0]=1
    np.savez_compressed(out/'integer-tables.npz',**tables)
    with pytest.raises(AssertionError):replay(out)


def test_failed_lower_bound_returns_an_actual_rational_witness(tmp_path):
    p=candidate(tmp_path/'candidate.json',4,5);result=verify(p,tmp_path/'failed')
    assert result['status']=='AXIS_BELOW_GAMMA'
    assert result['witness']['score']=='1/4'


def test_relocated_axis_uses_digest_not_original_path(tmp_path):
    import shutil
    original=tmp_path/'original';original.mkdir()
    p=candidate(original/'candidate.json',20,22,True)
    verify(p,original/'axis')
    moved=tmp_path/'moved';shutil.copytree(original,moved)
    original.rename(tmp_path/'unavailable')
    assert replay(moved/'axis',moved/'candidate.json')['status']=='AXIS_CERTIFICATE_REPLAYED'
    candidate(moved/'candidate.json',19,22,True)
    with pytest.raises(AssertionError):replay(moved/'axis',moved/'candidate.json')
