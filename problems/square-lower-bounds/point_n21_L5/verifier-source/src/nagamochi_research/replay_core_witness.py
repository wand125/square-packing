"""Exact check of the relaxed-core counterexample; never a unit-square witness."""
from fractions import Fraction as F
from itertools import combinations
from normalized_axis_cells import model,geometry
from joint_angle_lp import rotation


def verify(q):
    config=q['config'];centres=[tuple(map(F,p)) for p in q['centres']]
    values=[v for p in centres for v in p]+[F(q['common_gap'])]
    A,b,pairs,polys,angles=model(config,q['missing'],q['chosen'],True,True)
    assert len(values)==len(A[0]) and values[-1]>0
    assert all(sum(a*x for a,x in zip(row,values))<=rhs for row,rhs in zip(A,b))
    assert all(any(sum(a*x for a,x in zip(row,values))<=rhs for row,rhs in p['options']) for p in pairs)
    na=len(geometry(config,q['missing'])[0]);sides=[F(1)]*na+[F(config['rot_inner'])]*len(q['chosen'])
    rotations=list(map(rotation,angles));gaps=[];margins=[]
    for i,j in combinations(range(len(centres)),2):
        c,s=rotations[i];C,S=rotations[j];dx=centres[j][0]-centres[i][0];dy=centres[j][1]-centres[i][1]
        options=[]
        for a,bb in ((c,s),(-s,c),(C,S),(-S,C)):
            width=sum(sides[z]*(abs(a*rotations[z][0]+bb*rotations[z][1])+abs(-a*rotations[z][1]+bb*rotations[z][0]))/2 for z in (i,j))
            options.append(abs(a*dx+bb*dy)-width)
        gaps.append(max(options))
    for (x,y),side,(c,s) in zip(centres,sides,rotations):
        margins.extend([F(config['k'],2)-abs(x)-side*(abs(c)+abs(s))/2,F(config['k'],2)-abs(y)-side*(abs(c)+abs(s))/2])
    assert min(gaps)>0 and min(margins)>0
    return dict(minimum_pair_gap=str(min(gaps)),minimum_container_margin=str(min(margins)),
                axis_side='1',rotated_side=str(F(config['rot_inner'])),
                limitation='The rotated squares have side strictly less than one.')
