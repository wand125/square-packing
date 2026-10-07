from fractions import Fraction as F
from copy import deepcopy
import pytest
from saturated_joint_search import search_model,replay_model
from resume_disjunctive import resume_model
from exact_lp_rows import weighted_columns


def test_resume_replays_old_proofs_and_only_solves_pending_child():
    A=[[F(1)],[F(-1)]];b=[F(1,2),F(-1,2)]
    pairs=[dict(i=0,j=1,options=[([F(1)],F(0)),([F(-1)],F(-1))])]
    data=(A,b,pairs,[],[])
    child=search_model((A+[[F(1)]],b+[F(0)],pairs,[],[]))['tree']
    old=dict(status='UNRESOLVED_BRANCH',pair=0,children=[child,dict(status='PENDING_NODE_LIMIT')])
    r=resume_model(data,old,1)
    assert r['verified'] and r['nodes']==1 and r['reused_subtrees']==1
    assert replay_model(data,r['tree'])
    bad=deepcopy(old);bad['children'][0]['farkas']['negative_sum']='-999'
    with pytest.raises(AssertionError):resume_model(data,bad,1)


def test_zero_skipping_keeps_exact_column_sums():
    A=[[F(0),F(1,3),F(0)],[F(2,7),F(0),F(-5,11)],[F(0)]*3];ids=[0,1,2];y=[F(7,9),F(23,27),F(5)]
    assert weighted_columns(A,ids,y)==[sum(A[i][j]*w for i,w in zip(ids,y)) for j in range(3)]


def test_ordered_branching_skips_satisfied_pairs_and_replays():
    A=[[F(1)],[F(-1)]];b=[F(1,2),F(-1,2)]
    pairs=[dict(i=0,j=1,options=[([F(1)],F(1))]),
           dict(i=0,j=2,options=[([F(1)],F(0)),([F(-1)],F(-1))])]
    data=(A,b,pairs,[],[]);r=search_model(data,branch_rule='ordered')
    assert r['tree']['pair']==1 and replay_model(data,r['tree'])
