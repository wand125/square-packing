from pose_conflict_capacity import independent_number, nominal_core, conflict
from fractions import Fraction as F


def test_cycle_rank_beats_clique_size():
    adj=[(1<<((i-1)%5))|(1<<((i+1)%5)) for i in range(5)]
    assert independent_number(adj)==2
    assert independent_number([0]*4)==4
    assert independent_number([14,13,11,7])==1


def test_core_self_capacity_and_separated_centres():
    box=tuple(map(F,['1','11/10','1','11/10','-1/10','1/10']))
    a=nominal_core(F(4),box)
    assert conflict(a,a)
    b=nominal_core(F(4),tuple(x+2 if i<4 else x for i,x in enumerate(box)))
    assert not conflict(a,b)


def test_components_and_witness_against_exhaustive_graphs():
    from pose_conflict_capacity import independent_set
    from itertools import combinations
    pairs=list(combinations(range(4),2))
    for bits in range(1<<len(pairs)):
        adj=[0]*4
        for k,(i,j) in enumerate(pairs):
            if bits>>k&1:adj[i]|=1<<j;adj[j]|=1<<i
        valid=[mask for mask in range(16) if all(not(mask>>i&1 and mask>>j&1 and adj[i]>>j&1) for i,j in pairs)]
        witness=independent_set(adj)
        assert len(witness)==max(mask.bit_count() for mask in valid)
        assert all(not(adj[i]>>j&1) for i,j in combinations(witness,2))
