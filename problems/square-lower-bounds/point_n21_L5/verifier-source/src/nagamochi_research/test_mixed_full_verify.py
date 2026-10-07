from fractions import Fraction as F
import pytest
from mixed_full_verify import scale
from mixed_density_check import expand,evaluate
import json


def test_exact_scaling_preserves_geometry_and_scales_the_measure():
    data=dict(n=25,L='2',B='1/2',rectangles=[dict(rectangle=['0','0','2','2'],mass='20')],points=[dict(point=['1','1'],mass='1')],total_mass='21')
    out=scale(data,F(24));a,b=expand(data),expand(out)
    assert b[-2]==24 and b[-1]!=a[-1] and F(out['scaling_factor'])==F(8,7)
    assert out['rectangles'][0]['rectangle']==data['rectangles'][0]['rectangle']
    for t in (F(0),F(1,4)):
        before=evaluate(a,F(1),F(1),t);after=evaluate(b,F(1),F(1),t)
        for k in ('score','density','point_score'):assert F(after[k])==F(before[k])*F(8,7)
    with pytest.raises(ValueError):scale(data,F(25))
    with pytest.raises(ValueError):scale(data,F(20))


def test_fail_fast_preserves_incomplete_count(tmp_path):
    from mixed_full_verify import main
    data=dict(n=100,L='2',B='1/4',rectangles=[dict(rectangle=['0','0','2','2'],mass='20')],points=[],total_mass='20')
    source=tmp_path/'candidate.json';source.write_text(json.dumps(data))
    out=tmp_path/'round0';main(source,out,workers=1,nodes=20)
    r=json.loads((out/'summary.json').read_text())
    assert r['status']=='DEFICITS_REQUIRE_REPAIR' and r['complete_angles']<201
    assert r['verified_angles']==0 and not (out/'certificate.json').exists()


def test_full_proof_wrapper_and_portable_bundle(tmp_path):
    from mixed_full_verify import main
    from verify_mixed_full_proof import verify
    from package_mixed_proof import package
    from verify_rotated_result import replay
    from verify_axis_certificate import replay as axis_replay
    data=dict(n=100,L='2',B='1/2',rectangles=[dict(rectangle=['0','0','2','2'],mass='20')],points=[],total_mass='20')
    source=tmp_path/'candidate.json';source.write_text(json.dumps(data))
    out=tmp_path/'round0';main(source,out,workers=1,nodes=20)
    verify(out,workers=1)
    bundle=tmp_path/'portable';package(out,bundle)
    out.rename(tmp_path/'old-proof-unavailable')
    assert replay(bundle/'proof/net200',candidate=bundle/'proof/candidate.json')['status']=='ANGLE_RESULT_REPLAYED'
    assert axis_replay(bundle/'proof/axis',bundle/'proof/candidate.json')['status']=='AXIS_CERTIFICATE_REPLAYED'


def test_variable_net_complete_replay_and_net_tampering(tmp_path):
    from mixed_full_verify import main
    from verify_mixed_full_proof import verify
    from package_mixed_proof import package
    from mixed_net_audit import candidate_net
    data=dict(n=100,L='2',B='1/2',rectangles=[dict(rectangle=['0','0','2','2'],mass='20')],points=[],total_mass='20',proof_net=dict(step='1/7',last=3))
    source=tmp_path/'candidate.json';source.write_text(json.dumps(data));out=tmp_path/'round0'
    main(source,out,workers=1,nodes=20);verify(out,workers=1)
    cert=json.loads((out/'certificate.json').read_text());assert cert['angle_count']==4 and len(cert['results'])==4
    package(out,tmp_path/'bundle')
    before=expand(data)[-1];data['proof_net']['step']='3/20'
    assert expand(data)[-1]!=before
    data['proof_net']['last']=2
    with pytest.raises(ValueError):candidate_net(data)
    saved=json.loads((out/'candidate.json').read_text());saved['proof_net']['step']='3/20';(out/'candidate.json').write_text(json.dumps(saved))
    with pytest.raises(AssertionError):verify(out,workers=1)
