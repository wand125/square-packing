"""Fixed-L strengthening of the all-epsilon direct normalized core model.

Reuses the SAME old direct regions, but retains larger inner cores available
at one positive epsilon. A proof here must never certify all epsilon>0.
"""
from fractions import Fraction as F
from packing_lemmas import fixed_core_sides
from normalized_axis_cells import geometry
from saturated_joint_search import assemble_model,search_model,replay_model

TAG='DIRECT_FIXED_EPSILON_STRICT_V1'


def sides(cfg,e):
    e=F(e);m=cfg['k']-1
    assert 0<e<=F(cfg['eps_max'])<m
    A,R=fixed_core_sides(cfg['k'],e,cfg['t'],cfg['rot_h'])
    assert A>1 and R>=F(cfg['rot_inner'])
    return A,R


def model(q):
    assert q['model']==TAG and q['coordinate_system']=='DIRECT_NORMALIZED_CELL_CENTRES'
    cfg=q['config'];missing=q['missing'];chosen=q['chosen']
    assert missing==sorted(set(missing)) and chosen and chosen==sorted(set(chosen))
    cells,pieces=geometry(cfg,missing)
    assert all(type(i) is int and 0<=i<len(pieces) for i in chosen)
    A,R=sides(cfg,q['fixed_epsilon']);m=cfg['k']-1
    polys=list(cells.values())+[pieces[i] for i in chosen];n=len(polys)
    indices={v:i for i,v in enumerate(cells)};forced=[]
    for cell,idx in indices.items():
        i,j=divmod(cell,m)
        for other,axis,valid in ((cell+m,0,i<m-1),(cell+1,1,j<m-1)):
            if valid and other in indices:
                row=[F(0)]*(2*n);row[2*idx+axis]=1;row[2*indices[other]+axis]=-1
                forced.append((row,-A))
    data=assemble_model(polys,[F(0)]*len(cells)+[F(cfg['t'])]*len(chosen),
                        [A]*len(cells)+[R]*len(chosen),forced,strict_separation=True)
    rows,b,pairs,polys,angles=data;domain_rows=sum(len(p) for p in polys)
    rows=[row+[F(int(i>=domain_rows))] for i,row in enumerate(rows)]
    pairs=[dict(i=p['i'],j=p['j'],options=[(row+[F(1)],rhs) for row,rhs in p['options']]) for p in pairs]
    rows.extend([[F(0)]*(2*n)+[F(-1)],[F(0)]*(2*n)+[F(1)]]);b.extend([F(0),F(1)])
    return rows,b,pairs,polys,angles


def verify(q):
    data=model(q)
    return replay_model(data,q['tree'],positive_index=len(data[0][0])-1)


def run(cfg,missing,chosen,e,nodes=300):
    q=dict(model=TAG,coordinate_system='DIRECT_NORMALIZED_CELL_CENTRES',config=cfg,
           missing=list(missing),chosen=list(chosen),fixed_epsilon=str(F(e)))
    data=model(q);q.update(search_model(data,nodes,branch_rule='fewest',positive_index=len(data[0][0])-1))
    q['verified']=verify(q)
    q['limitation']='Fixed epsilon only, specified axis occupancy and rotor band only.'
    return q
