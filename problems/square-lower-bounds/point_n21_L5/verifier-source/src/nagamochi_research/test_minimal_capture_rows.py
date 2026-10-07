from itertools import product
from minimal_capture_rows import minimal_indices


def test_minimum_preserved_for_every_small_nonnegative_weight_assignment():
    patterns=[[0,1],[1,2],[0,1,2],[0,1,2,3],[1,3],[2],[2]]
    minimal=[patterns[i] for i in minimal_indices(patterns)]
    assert minimal==[[2],[0,1],[1,3]]
    for weights in product(range(3),repeat=4):
        assert min(sum(weights[i] for i in row) for row in patterns)==min(sum(weights[i] for i in row) for row in minimal)
    assert minimal_indices([[0],[],[1,2]])==[1]
