from copy import deepcopy
from fractions import Fraction as F
import pytest
from full_pose_low_cover import split
from replay_local_pose_trees import check_tree


def test_rejects_holes_forged_bounds_and_hidden_descendants():
    root = tuple(map(F, [0, 1, 0, 1, 0, 1]))
    children = split(root)
    rows = {str(i): dict(box=list(map(str, b)), lower='1') for i, b in enumerate(children)}
    assert check_tree(root, rows, lambda *box: F(1)) == [F(1), F(1)]
    for change in ('hole', 'bound', 'box', 'descendant'):
        bad = deepcopy(rows)
        if change == 'hole': del bad['0']
        elif change == 'bound': bad['0']['lower'] = '2'
        elif change == 'box': bad['0']['box'][0] = '1/3'
        else: bad['00'] = deepcopy(bad['0'])
        with pytest.raises(ValueError): check_tree(root, bad, lambda *box: F(1))
