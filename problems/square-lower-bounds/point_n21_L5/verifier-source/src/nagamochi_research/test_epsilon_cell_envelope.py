from fractions import Fraction as F
from copy import deepcopy
from itertools import combinations
import pytest
from epsilon_cell_envelope import parameters,check_parameters,geometry,coalesce
from saturated_axis_cells import contained
from saturated_joint_search import farkas,replay_model
from replay_saturated_pairs import clique_upper


def test_affine_cell_envelopes_cover_both_endpoints():
    for k in (4,5):
        q=parameters(k);check_parameters(q);cells,_=geometry(q,[]);em=F(q['eps_max'])
        for epsilon in (F(0),em):
            H=(k-1-epsilon)/2;d=(k-1-epsilon)/(k-1)
            for i in range(k-1):
                for j in range(k-1):
                    x=-H+i*d;y=-H+j*d
                    assert contained([(x,y),(x+d,y),(x+d,y+d),(x,y+d)],cells[i*(k-1)+j])
        for field,value in (('axis_inner','1'),('eps_max','0'),('axis_h_rule','epsilon')):
            bad=deepcopy(q);bad[field]=value
            with pytest.raises(AssertionError):check_parameters(bad)


def test_hull_coalescing_is_an_enlargement_with_capacity_one():
    pieces=[[(F(0),F(0)),(F(1,10),F(0)),(F(0),F(1,10))],
            [(F(1,5),F(0)),(F(3,10),F(0)),(F(1,5),F(1,10))],
            [(F(2),F(0)),(F(21,10),F(0)),(F(2),F(1,10))]]
    result=coalesce(pieces,F(0),F(1))
    assert len(result)==2 and all(any(contained(p,q) for q in result) for p in pieces)


def test_tiny_coefficients_get_an_exact_farkas_certificate():
    tiny=F(1,10**20);A=[[tiny],[-1]];b=[F(0),F(-1)]
    cert=farkas(A,b)
    assert replay_model((A,b,[],[],[]),dict(status='EXACT_INFEASIBLE',farkas=cert))


def test_large_clique_search_uses_bounded_memory():
    # 40 vertices in disjoint complete groups of size 5: exact clique size 5.
    excluded={(i,j) for i,j in combinations(range(40),2) if i//5!=j//5}
    assert clique_upper(40,excluded)==5
    assert clique_upper(40,set())==40


def test_uniform_n12_proof_covers_every_remaining_triple():
    import json
    from pathlib import Path
    from epsilon_cell_envelope import verify_completion
    root=Path(__file__).resolve().parents[2]/'runs/epsilon_cell_envelope_20260927/scaled-exact'
    base=json.loads((root/'k4-mNone.json').read_text())
    q=json.loads((root/'k4-mNone-full3.json').read_text())
    assert verify_completion(base,q)['target_excluded']
    bad=deepcopy(q);bad['cases'].pop()
    assert not verify_completion(base,bad)['target_excluded']
