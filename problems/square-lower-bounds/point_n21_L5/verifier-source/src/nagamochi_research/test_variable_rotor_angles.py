from fractions import Fraction as F
from pathlib import Path
from itertools import combinations
import json
import pytest
from bounded_farkas import repair
from variable_rotor_angles import model
from joint_angle_lp import rotation
from saturated_joint_search import replay_model

ROOT=Path(__file__).resolve().parents[2]/'runs/correlated_epsilon_20260927/normalized-missing'


def dot(row,x):return sum(a*x[i] for i,a in enumerate(row) if a)


def test_farkas_residual_is_paid_for_by_exact_bound_rows():
    e=F(1,10**12)
    # x+e*y <= -1, x>=0, and -1<=y<=1 is impossible.
    A=[[F(1),e],[F(-1),F(0)],[F(0),F(1)],[F(0),F(-1)]];b=[F(-1),F(0),F(1),F(1)]
    c=repair(A,b,{0:F(1),1:F(1)})
    assert F(c['negative_sum'])==-1+e
    assert replay_model((A,b,[],[],[]),dict(status='EXACT_INFEASIBLE',farkas=c))
    # A small negative raw sum is not enough if the bound correction costs more.
    with pytest.raises(AssertionError):repair(A,[-e/2,F(0),F(1),F(1)],{0:F(1),1:F(1)})


def test_actual_angles_satisfy_arc_products_and_separation_relaxations():
    q=json.loads((ROOT/'central-core-witness.json').read_text());config=q['config'];h=F(config['rot_h']);t=F(config['t'])
    data,gap,a=model(config,q['missing'],q['chosen'],audit=True)
    A,b,pairs,polys,_=data;centres=[tuple(map(F,p)) for p in q['centres']];na=8
    c0,s0=rotation(t)
    for pattern in ((-1,-1,1,1),(1,-1,1,-1),(0,0,0,0)):
        x=[F(0)]*len(a['bounds']);x[:24]=[v for p in centres for v in p];x[gap]=F(1,10**12)
        rots=[(F(1),F(0))]*na
        for (i,(ci,si)),sign in zip(a['angles'].items(),pattern):
            c,s=rotation(t+sign*h);x[ci]=c;x[si]=s;rots.append((c,s))
        for v,lin in a['relative']:x[v]=max(F(0),abs(sum(z*x[k] for k,z in lin.items()))-16*h*h)
        for (i,j),v in a['products'].items():x[v]=x[i]*x[j]
        for row,rhs,kind in zip(A,b,a['row_kinds']):
            if kind!='geometry':assert dot(row,x)<=rhs
        checked=0
        for p in pairs:
            i,j=p['i'],p['j'];c,s=rots[i];C,S=rots[j];dx=centres[j][0]-centres[i][0];dy=centres[j][1]-centres[i][1]
            width=(1+abs(c*C+s*S)+abs(c*S-s*C))/2
            sep=max(abs(dx*u+dy*v) for u,v in ((c,s),(-s,c),(C,S),(-S,C)))
            if sep>=width+x[gap]:
                assert any(dot(row,x)<=rhs for row,rhs in p['options']);checked+=1
        assert checked>20


def test_affine_equilibration_preserves_every_constraint_exactly():
    q=json.loads((ROOT/'central-core-witness.json').read_text())
    original,gap,a=model(q['config'],q['missing'],q['chosen'],audit=True)
    transformed,gap2,z=model(q['config'],q['missing'],q['chosen'],True,True)
    assert gap==gap2 and z['offsets'][gap]==0 and z['scales'][gap]>0
    y=[F((i%7)-3,7) for i in range(len(a['bounds']))];x=[o+s*v for o,s,v in zip(z['offsets'],z['scales'],y)]
    rows=list(zip(original[0],original[1]));new=list(zip(transformed[0],transformed[1]))
    for p,P in zip(original[2],transformed[2]):rows+=p['options'];new+=P['options']
    for (r,b),(R,B) in zip(rows,new):assert dot(r,x)-b==dot(R,y)-B
