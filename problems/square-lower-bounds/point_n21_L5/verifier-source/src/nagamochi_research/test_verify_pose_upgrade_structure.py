from copy import deepcopy
import pytest
from verify_pose_upgrade_structure import check


def test_inheritance_rejects_leaf_loss_and_unrecorded_mutation():
    old=dict(digest='d',symmetry='D4',threshold='1/2',leaves={'0':dict(box=['0']*6,lower='1/4',kind='POSSIBLE_LOW')})
    new=deepcopy(old);new['leaves']['0'].update(lower='3/4',kind='HIGH',bound_method='physical-adaptive1')
    local=dict(source_sha256='sha',method='physical-adaptive1',values={'0':'3/4'})
    assert check(old,new,local,'sha')['leaves']==1
    for kind in ('missing','box','lower','method'):
        bad=deepcopy(new)
        if kind=='missing':bad['leaves'].clear()
        elif kind=='box':bad['leaves']['0']['box'][0]='1'
        elif kind=='lower':bad['leaves']['0']['lower']='1'
        else:bad['leaves']['0']['bound_method']='square'
        with pytest.raises(ValueError):check(old,bad,local,'sha')
