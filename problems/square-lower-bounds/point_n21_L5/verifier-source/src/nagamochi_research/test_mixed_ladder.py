from fractions import Fraction as F
from mixed_ladder_prepare import transfer_witness


def test_transfer_preserves_normalized_centre_and_core_angle():
    q=dict(cx='3',cy='7/2',t='2/5',normalized_pose=[.2,.4,.9])
    a,b,B=F('4.98'),F('4.985'),F('.9977')
    moved=transfer_witness(q,a,b,B)
    t=F(q['t']);radius=B*(1+2*t-t*t)/(2*(1+t*t))
    for key in ('cx','cy'):
        assert (F(q[key])-a/2)/(a/2-radius)==(F(moved[key])-b/2)/(b/2-radius)
    assert moved['t']==q['t']
    assert transfer_witness(q,a,a,B)['cx']==q['cx']


def test_overbudget_repair_keeps_every_pose_and_support_without_export(tmp_path,monkeypatch):
    import json
    import numpy as np
    from types import SimpleNamespace
    import mixed_full_repair as module
    source=tmp_path/'source';source.mkdir();out=tmp_path/'repaired'
    meta=dict(L=2.,B=.9,rhs=1.001,rectangles=[[0.,0.,2.,2.]],point_columns=0,rules=[],base_pose_count=1)
    (source/'model.json').write_text(json.dumps(meta));(source/'cumulative-witnesses.json').write_text('[]')
    np.savez(source/'replay.npz',matrix=np.array([[.2025]]),row_ids=[0],selected_rectangles=np.empty((0,4)),poses=np.array([[0.,0.,0.]]))
    witness=dict(cx='1',cy='1',t='0',normalized_pose=[0.,0.,0.])
    monkeypatch.setattr(module,'collect',lambda scan,path:dict(witnesses=[witness]))
    monkeypatch.setattr(module,'columns',lambda poses,rules,L,B:(np.empty((len(poses),0)),None,dict(points=[],point_orbits=[])))
    monkeypatch.setattr(module,'solve',lambda matrix,rhs:(SimpleNamespace(x=np.array([22.])),dict(mass=22.)))
    monkeypatch.setattr(module,'export',lambda *args:(_ for _ in ()).throw(AssertionError('Overbudget candidate must not be exported')))
    module.repair(source,tmp_path/'scan',out)
    result=json.loads((out/'results.json').read_text())
    assert result['status']=='BUDGET_EXHAUSTED' and F(result['mass'])==22
    assert result['rational_replay']=='PENDING_AFTER_BUDGET_RECOVERY'
    with np.load(out/'replay.npz') as z:
        assert z['matrix'].shape==(2,1) and len(z['poses'])==2
        assert list(z['row_ids'])==[0,1] and z['weights_added_density'][0]==22
    assert json.loads((out/'cumulative-witnesses.json').read_text())==[witness]
    assert not (out/'mixed-candidate.json').exists()


def test_pricing_exports_only_final_candidate_and_replays_all_exact_poses(tmp_path,monkeypatch):
    import json
    import numpy as np
    from types import SimpleNamespace
    import mixed_ladder_price as module
    source=tmp_path/'source';source.mkdir();out=tmp_path/'priced'
    meta=dict(L=2.,B=.9,rhs=1.001,rectangles=[[0.,0.,2.,2.]],point_columns=0,rules=[],base_pose_count=0)
    (source/'model.json').write_text(json.dumps(meta))
    witness=dict(cx='1',cy='1',t='0',normalized_pose=[0.,0.,0.])
    (source/'cumulative-witnesses.json').write_text(json.dumps([witness]))
    np.savez(source/'replay.npz',matrix=np.array([[.2025]]),row_ids=[0],selected_rectangles=np.empty((0,4)),poses=np.array([[0.,0.,0.]]))
    monkeypatch.setattr(module,'columns',lambda poses,rules,L,B:(np.empty((len(poses),0)),None,dict(points=[],point_orbits=[])))
    def solve(a,rhs):
        w=np.zeros(a.shape[1]);w[0]=20.9 if a.shape[1]==1 else 20.7
        return SimpleNamespace(x=w,ineqlin=SimpleNamespace(marginals=-np.ones(len(a)))),dict(mass=float(sum(w)))
    monkeypatch.setattr(module,'solve',solve)
    monkeypatch.setattr(module,'propose_edges',lambda *args,**kwargs:([dict(rectangle=[.1,.1,1.,1.],score=1.1)],dict(columns=1)))
    module.run(source,out,1,F('20.8'))
    assert not (out/'step0/mixed-candidate.json').exists()
    assert json.loads((out/'step0/results.json').read_text())['status']=='FINITE_NUMERICAL_ONLY'
    r=json.loads((out/'step1/results.json').read_text())
    assert r['status']=='FINITE_REPAIRED_NOT_CERTIFIED' and r['exact_rechecks']==1
    check=json.loads((out/'step1/exact-rechecks.json').read_text())[0]
    assert F(check['score'])>=1
    with np.load(out/'step1/replay.npz') as z:assert z['matrix'].shape==(1,2)


def test_transfer_with_new_core_preserves_exact_normalized_centre():
    q=dict(cx='4',cy='3',t='1/5',normalized_pose=[.1,.2,.3]);oldL,newL=F('4.985'),F('4.9875');oldB,newB=F('.9977'),F('.998048')
    w=transfer_witness(q,oldL,newL,oldB,newB);t=F(q['t']);h=(1+2*t-t*t)/(2*(1+t*t))
    for k in ('cx','cy'):
        assert (F(w[k])-newL/2)/(newL/2-newB*h)==(F(q[k])-oldL/2)/(oldL/2-oldB*h)
    assert w['t']==q['t'] and w['normalized_pose']==q['normalized_pose']


def test_ladder_uses_completed_parent_metadata_and_rebuilds_coefficients(tmp_path,monkeypatch):
    import json
    import numpy as np
    import mixed_ladder_prepare as module
    source=tmp_path/'parent';source.mkdir();oldL=4.985;newL=F('4.9875');B=F('.998048')
    meta=dict(n=21,L=oldL,B=.9977,rhs=1.001,rectangles=[[0,0,oldL,oldL]],point_columns=0,rules=[],base_pose_count=1)
    (source/'model.json').write_text(json.dumps(meta))
    q=dict(cx='997/400',cy='997/400',t='0',normalized_pose=[0,0,0])
    (source/'cumulative-witnesses.json').write_text(json.dumps([q]))
    np.savez(source/'replay.npz',matrix=np.array([[123.]]),row_ids=[0],selected_rectangles=np.empty((0,4)),poses=np.array([[0.,0.,0.],[0.,0.,0.]]))
    monkeypatch.setattr(module,'load',lambda n:(_ for _ in ()).throw(AssertionError('Legacy parent must not be loaded')))
    monkeypatch.setattr(module,'columns',lambda poses,rules,L,B:(np.empty((len(poses),0)),None,dict(points=[],point_orbits=[])))
    out=tmp_path/'next';module.prepare(source,out,newL,core=B,net=dict(step='6039/3118900',last=214))
    d=json.loads((out/'model.json').read_text());assert d['oldL']=='997/200' and d['B']==float(B)
    with np.load(out/'replay.npz') as z:
        assert abs(z['matrix'][0,0]-float((B/newL)**2))<1e-14
        assert z['poses'].shape==(2,3)
    assert F(json.loads((out/'cumulative-witnesses.json').read_text())[0]['cx'])==newL/2
