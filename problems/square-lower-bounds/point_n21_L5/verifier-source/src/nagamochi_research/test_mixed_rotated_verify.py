import json
from fractions import Fraction as F
import pytest
from mixed_density_check import expand, evaluate
from mixed_rotated_verify import compile_verifier, export, query, run


@pytest.fixture(scope='module')
def binary(tmp_path_factory):
    path=tmp_path_factory.mktemp('cpp')/'verify';compile_verifier(path);return path


def model(mass=20,point=True):
    return dict(n=100,L='2',B='1/2',rectangles=[dict(rectangle=['0','0','2','2'],mass=str(mass))],
                points=[dict(point=['1','1'],mass='1')] if point else [],total_mass=str(mass+int(point)))


def test_nonzero_uniform_density_and_frontier(binary,tmp_path):
    candidate=tmp_path/'candidate.json';candidate.write_text(json.dumps(model()))
    for index in (1,100,200):
        r=run(candidate,index,tmp_path/str(index),binary,200)
        assert r['status']=='ANGLE_VERIFIED' and r['frontier']==[]
    candidate.write_text(json.dumps(model(4,False)))
    r=run(candidate,100,tmp_path/'fail',binary,1)
    assert r['status']=='ANGLE_BELOW_GAMMA'
    assert len(r['frontier'])==2 and r['exact_witnesses'][0]['score']=='1/4'


def test_atoms_certain_capture_and_closed_boundary(binary,tmp_path):
    m=expand(model(0));p=tmp_path/'in';export(m,100,p)
    t=F(83,400);c=(1-t*t)/(1+t*t);s=2*t/(1+t*t)
    # Centre exactly on capture edge; enlarging the centre cell loses the atom.
    cells=[(F(1),F(1),F(1,100),F(1,100)),
           (1+c/4,1+s/4,F(1,100),F(1,100)),
           (1+c/4,1+s/4,F(0),F(0))]
    lo=query(binary,p,cells)
    assert F(999,1000)<lo[0]<=1
    assert lo[1]<=0
    for cell,lower in zip(cells,lo):
        x,y,dx,dy=cell
        for a in (-1,0,1):
            for b in (-1,0,1):
                assert lower<=F(evaluate(m,x+a*dx,y+b*dy,t)['score'])


def test_partial_rectangles_lower_than_exact_samples(binary,tmp_path):
    d=model(4);d['rectangles']=[dict(rectangle=['1/3','1/5','7/5','8/5'],mass='4')]
    m=expand(d);p=tmp_path/'partial';export(m,100,p)
    cells=[(F(1)+F(i,20),F(1)+F(j,20),F(1,100),F(1,80)) for i in range(4) for j in range(4)]
    for cell,lower in zip(cells,query(binary,p,cells)):
        x,y,dx,dy=cell
        for a,b in ((-1,-1),(-1,1),(1,-1),(1,1),(0,0)):
            assert lower<=F(evaluate(m,x+a*dx,y+b*dy,F(83,400))['score'])


def test_wall_region_success_is_not_a_whole_angle(binary,tmp_path):
    from mixed_wall_region import verify
    p=tmp_path/'candidate.json';p.write_text(json.dumps(model()))
    r=verify(p,1,tmp_path/'region',binary,nodes=200)
    assert r['status']=='REGION_VERIFIED'
    assert r['manifest']['scope']=='WALL_REGION_ONLY_NOT_WHOLE_ANGLE'
    assert r['manifest']['normalized_rectangle']==['0','1/64','63/64','1']
    assert r['frontier']==[]


def test_arbitrary_region_requires_exact_root(binary,tmp_path):
    from mixed_wall_region import verify
    p=tmp_path/'candidate.json';p.write_text(json.dumps(model()))
    r=verify(p,1,tmp_path/'interior',binary,box=(F(1,2),F(1,2),F(1,64),F(1,64)))
    assert r['status']=='REGION_VERIFIED'
    assert r['manifest']['scope']=='CENTRE_REGION_ONLY_NOT_WHOLE_ANGLE'
    assert r['manifest']['normalized_rectangle']==['31/64','33/64','31/64','33/64']
    with pytest.raises(AssertionError,match='exactly representable'):
        verify(p,1,tmp_path/'bad',binary,box=(F(1,3),F(1,2),F(1,64),F(1,64)))


def test_verified_angle_replay_checks_manifest(binary,tmp_path):
    from verify_rotated_result import replay
    p=tmp_path/'candidate.json';p.write_text(json.dumps(model()));out=tmp_path/'full'
    run(p,1,out,binary,nodes=100)
    assert replay(out,binary)['status']=='ANGLE_RESULT_REPLAYED'
    r=json.loads((out/'result.json').read_text());r['manifest']['candidate_digest']='tampered';(out/'result.json').write_text(json.dumps(r))
    with pytest.raises(AssertionError,match='specification'):
        replay(out,binary)


def test_relocated_angle_uses_digest_not_original_path(binary,tmp_path):
    import shutil
    from verify_rotated_result import replay
    original=tmp_path/'original';original.mkdir()
    p=original/'candidate.json';p.write_text(json.dumps(model()))
    run(p,1,original/'angle',binary,nodes=100)
    moved=tmp_path/'moved';shutil.copytree(original,moved)
    original.rename(tmp_path/'unavailable')
    assert replay(moved/'angle',binary,moved/'candidate.json')['status']=='ANGLE_RESULT_REPLAYED'
    d=model(19);(moved/'candidate.json').write_text(json.dumps(d))
    with pytest.raises(AssertionError,match='specification'):
        replay(moved/'angle',binary,moved/'candidate.json')


def test_repair_pool_threshold_one_keeps_only_actual_deficit_sources(tmp_path):
    from mixed_shared_collect import collect
    for name,file,mass in [('fixed_mixed','fixed-candidate.json',F(20001,1250)),('added_density','mixed-candidate.json',15)]:
        d=model(mass,False);(tmp_path/file).write_text(json.dumps(d));m=expand(d)
        folder=tmp_path/'validation'/name;folder.mkdir(parents=True)
        w=evaluate(m,F(1),F(1),F(83,40000));(folder/'fresh.json').write_text(json.dumps(dict(witnesses=[w])))
    collect(tmp_path,F(1));r=json.loads((tmp_path/'next-pool.json').read_text())
    assert r['repair_threshold']=='1' and r['count']==1
    assert r['source_counts']['fixed_mixed']['below_gamma']==0
    assert r['source_counts']['added_density']['below_gamma']==1
    assert F(r['witnesses'][0]['evaluations']['fixed_mixed']['score'])>1
