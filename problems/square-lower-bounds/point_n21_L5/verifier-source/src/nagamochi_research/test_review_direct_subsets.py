from itertools import combinations
from review_direct_subsets import survivors


def test_higher_order_cuts_match_exhaustive_enumeration():
    cases=[[],[(0,)],[(0,1)],[(0,2,4)],[(0,1),(1,3,4),(0,2,4)],
           list(combinations(range(6),3))]
    for cuts in cases:
        for size in range(7):
            expected=[list(c) for c in combinations(range(6),size)
                      if not any(set(cut)<=set(c) for cut in cuts)]
            assert list(survivors(6,cuts,size))==expected
