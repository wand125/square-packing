from fractions import Fraction as F
from pathlib import Path
from copy import deepcopy
import json
import pytest
from saturated_joint_search import assemble_model
from normalized_pair_refinement import verify_completion
from replay_core_witness import verify as verify_witness
from normalized_axis_cells import verify as verify_case

ROOT=Path(__file__).resolve().parents[2]/'runs/correlated_epsilon_20260927/normalized-missing'


def test_strict_cores_remove_touch_only_separations():
    h=F(1,1000)
    polys=[[(0,0),(h,0),(h,h),(0,h)],[(1-h,0),(1,0),(1,h),(1-h,h)]]
    closed=assemble_model(polys,[F(0)]*2,[F(1)]*2,[])[2]
    strict=assemble_model(polys,[F(0)]*2,[F(1)]*2,[],strict_separation=True)[2]
    assert closed[0]['options'] and not strict[0]['options']


def test_central_witness_is_a_real_obstruction_to_the_relaxation():
    q=json.loads((ROOT/'central-core-witness.json').read_text())
    r=verify_witness(q)
    assert F(r['minimum_pair_gap'])>0 and F(r['minimum_container_margin'])>0
    assert F(r['rotated_side'])<1


def test_moving_band_proof_cannot_be_reported_for_fixed_band():
    q=json.loads((ROOT/'n12-m4-moving-full4.json').read_text())
    repo=Path(__file__).resolve().parents[2]
    base=json.loads((repo/q['source']).read_text());pairs=json.loads((repo/q['pair_path']).read_text())
    assert verify_completion(base,pairs,q)['target_excluded']
    bad=deepcopy(q);bad.pop('rotated_t_halfwidth_rule')
    with pytest.raises(AssertionError):verify_completion(base,pairs,bad)
    bad=deepcopy(q);bad['cases']=[c for c in bad['cases'] if c['model']!='NORMALIZED_MOVING_BANDS_V3']
    assert not verify_completion(base,pairs,bad)['target_excluded']


def test_capped_band_certificate_requires_its_own_scope():
    q=json.loads((ROOT/'n12-central-capped-band.json').read_text())
    assert verify_case(q)
    bad=deepcopy(q);bad['rotated_t_halfwidth_rule']='fixed'
    with pytest.raises(AssertionError):verify_case(bad)
    full=json.loads((ROOT/'n12-m4-capped-full4.json').read_text())
    repo=Path(__file__).resolve().parents[2]
    base=json.loads((repo/full['source']).read_text());pairs=json.loads((repo/full['pair_path']).read_text())
    bad=deepcopy(full);bad.pop('rotated_t_halfwidth_rule')
    with pytest.raises(AssertionError):verify_completion(base,pairs,bad)


def test_capped_band_strict_inclusion_and_full_width_threshold():
    m=3;cap=F(1,100000)
    for e in (F(1,10**12),F(3,50000),F(1,1000)):
        h=min(cap,e/(2*m));sigma=1-e/m
        assert sigma*(1+2*h)<=1-e*e/(m*m)<1
    assert min(cap,F(3,50000)/(2*m))==cap
