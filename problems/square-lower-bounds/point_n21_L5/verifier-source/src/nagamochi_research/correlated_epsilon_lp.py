"""Keep one common epsilon in all centre and inner-side constraints.

This strengthens the uniform envelope. All constraints are necessary for the
same conditional angle classes; it does not classify arbitrary packings.
"""
from fractions import Fraction as F
from copy import deepcopy
from pathlib import Path
import json,time
from epsilon_cell_envelope import geometry,model as envelope_model
from joint_angle_lp import rotation
from saturated_joint_search import search_model,replay_model,assemble_model


def model(config,missing,chosen,restore_pairs=False):
    A,b,pairs,polys,angles=envelope_model(config,missing,chosen)
    cells,_=geometry(config,missing);indices={v:i for i,v in enumerate(cells)}
    k=config['k'];em=F(config['eps_max']);H=F(config['rot_half']);w=sum(rotation(F(config['t'])))
    n=len(polys);na=len(cells)
    if restore_pairs:
        R=F(config['rot_inner']);amin=F(config['axis_inner'])
        pairs=assemble_model(polys,angles,[amin]*na+[R]*len(chosen),[],
                             guaranteed_sides=[F(1)]*na+[R]*len(chosen))[2]
    A=[row+[F(0)] for row in A];b=list(b);pairs=deepcopy(pairs)
    for pair in pairs:
        i,j=pair['i'],pair['j'];options=[]
        for row,rhs in pair['options']:
            if j<na:derivative=-F(1,50)
            elif i>=na:derivative=F(0)
            else:
                # World axes see A(e)/2; rotated axes see w*A(e)/2.
                derivative=-F(1,100) if row[2*i]==0 or row[2*i+1]==0 else -w/100
            options.append((row+[derivative],rhs+derivative*em))
        pair['options']=options
    def add(coords,e,rhs):
        row=[F(0)]*(2*n+1)
        for index,value in coords:row[index]=value
        row[-1]=e;A.append(row);b.append(rhs)
    for cell,idx in indices.items():
        i,j=divmod(cell,k-1)
        for axis,v in ((0,i),(1,j)):
            lo=F(v,k-1)-F(1,2);hi=F(v+1,k-1)-F(1,2)
            add([(2*idx+axis,-1)],-lo,-lo*(k-1))
            add([(2*idx+axis,1)],hi,hi*(k-1))
        for other,axis,valid in ((cell+k-1,0,i<k-2),(cell+1,1,j<k-2)):
            if valid and other in indices:
                add([(2*idx+axis,1),(2*indices[other]+axis,-1)],-F(1,50),-1)
    for idx in range(na,n):
        for axis in (0,1):
            for sign in (-1,1):add([(2*idx+axis,sign)],F(1,2),H)
    add([],F(-1),F(0));add([],F(1),em)
    return A,b,pairs,polys,angles


def run(config,missing,chosen,node_limit=3000,branch_rule='gap',restore_pairs=False):
    start=time.monotonic();data=model(config,missing,chosen,restore_pairs);index=len(data[0][0])-1
    q=search_model(data,node_limit,positive_index=index,branch_rule=branch_rule)
    q.update(config=config,missing=list(missing),chosen=list(chosen),model='CORRELATED_EPSILON_V3' if restore_pairs else 'CORRELATED_EPSILON_V2')
    q['branch_rule']=branch_rule
    q['verified']=replay_model(data,q['tree'],positive_index=index);q['total_seconds']=time.monotonic()-start
    return q


def verify(q):
    assert q['model'] in ('CORRELATED_EPSILON_V1','CORRELATED_EPSILON_V2','CORRELATED_EPSILON_V3')
    data=model(q['config'],q['missing'],q['chosen'],restore_pairs=q['model']=='CORRELATED_EPSILON_V3')
    return replay_model(data,q['tree'],positive_index=None if q['model']=='CORRELATED_EPSILON_V1' else len(data[0][0])-1)
