"""Normalize centre cells to width one before relaxing epsilon.

For L=k-e, scale all coordinates by 1/(1-e/(k-1)). The near-axis
unit nominal cores are strictly inside the scaled physical squares, so
each CLOSED unit centre cell contains at most one near-axis box.
"""
from fractions import Fraction as F
from itertools import combinations
from functools import lru_cache
import json
from epsilon_cell_envelope import check_parameters,coalesce,geometry as envelope_geometry
from saturated_axis_cells import subtract_open,remove_contained
from saturated_joint_search import assemble_model,search_model,replay_model
from joint_angle_lp import rotation
from fixed_orientation_cover import angle_envelope


@lru_cache(maxsize=32)
def domains(encoded,missing):
    q=json.loads(encoded);check_parameters(q);k=q['k'];m=k-1;R=F(q['rot_inner']);t=F(q['t'])
    _,span=angle_envelope(t,F(q['rot_h']));H=F(q['rot_half'])
    assert span>=1 and F(1,m)>F(1,5000)
    assert len(set(missing))==len(missing) and all(type(i) is int and 0<=i<m*m for i in missing)
    cells={}
    for i in range(m):
        for j in range(m):
            if i*m+j in missing:continue
            x=-F(m,2)+i;y=-F(m,2)+j
            cells[i*m+j]=[(x,y),(x+1,y),(x+1,y+1),(x,y+1)]
    c,s=rotation(t);w=c+s;pieces=[[(-H,-H),(H,-H),(H,H),(-H,H)]]
    for cell in cells.values():
        inequalities=[]
        for a,b,threshold in ((F(1),F(0),(1+R*w)/2),(F(0),F(1),(1+R*w)/2),
                              (c,s,(R+w)/2),(-s,c,(R+w)/2)):
            for sign in (-1,1):
                aa,bb=sign*a,sign*b
                inequalities.append((aa,bb,threshold+min(aa*x+bb*y for x,y in cell)))
        new={}
        for p in pieces:
            for z in subtract_open(p,inequalities):new[tuple(sorted(set(z)))]=z
        pieces=list(new.values())
    return cells,coalesce(remove_contained(pieces),t,R)


def geometry(q,missing=()):return domains(json.dumps(q,sort_keys=True),tuple(missing))


def model(q,missing,chosen,reference_pieces=False,strict=False,unit_rotor=False,tight_rotor_centres=True):
    cells,pieces=geometry(q,missing);m=q['k']-1;R=F(q['rot_inner']);t=F(q['t'])
    if reference_pieces:
        # The normalized unit cells lie in the old cell envelopes and their
        # cores have side 1 >= old A_min. Hence the old residual domains still
        # cover every possible normalized rotated centre (a weaker cover).
        pieces=envelope_geometry(q,missing)[1]
    if unit_rotor:
        assert strict and reference_pieces
        em=F(q['eps_max']);w=sum(rotation(t))
        if tight_rotor_centres:
            assert 0<=t-em/10000 and t+em/10000<=1
            assert F(2,10000)<=(w-1)/m and F(2,10000)<F(1,m)
        else:
            # h=min(rot_h,e/(2m)): sigma*(1+2h)<=1-e^2/m^2<1.
            # Keep the old H envelope; do not require the stronger H0 bound.
            assert 0<em<m and 0<=t-F(q['rot_h']) and t+F(q['rot_h'])<=1
        R=F(1)
    indices={v:i for i,v in enumerate(cells)};polys=list(cells.values())+[pieces[i] for i in chosen]
    n=len(polys);forced=[]
    for cell,idx in indices.items():
        i,j=divmod(cell,m)
        for other,axis,valid in ((cell+m,0,i<m-1),(cell+1,1,j<m-1)):
            if valid and other in indices:
                row=[F(0)]*(2*n);row[2*idx+axis]=1;row[2*indices[other]+axis]=-1;forced.append((row,F(-1)))
    data=assemble_model(polys,[F(0)]*len(cells)+[t]*len(chosen),[F(1)]*len(cells)+[R]*len(chosen),forced,strict_separation=strict)
    if not strict:return data
    A,b,pairs,polys,angles=data;domain_rows=sum(len(p) for p in polys)
    A=[row+[F(int(i>=domain_rows))] for i,row in enumerate(A)]
    pairs=[dict(i=p['i'],j=p['j'],options=[(row+[F(1)],rhs) for row,rhs in p['options']]) for p in pairs]
    A.extend([[F(0)]*(2*n)+[F(-1)],[F(0)]*(2*n)+[F(1)]]);b.extend([F(0),F(1)])
    if unit_rotor and tight_rotor_centres:
        H=(q['k']-sum(rotation(t)))/2
        for idx in range(len(cells),n):
            for axis in (0,1):
                for sign in (-1,1):
                    row=[F(0)]*(2*n+1);row[2*idx+axis]=sign;A.append(row);b.append(H)
    return A,b,pairs,polys,angles


def run(config,missing,chosen,node_limit=1000,strict=False,unit_rotor=False,tight_rotor_centres=True):
    data=model(config,missing,chosen,reference_pieces=True,strict=strict,unit_rotor=unit_rotor,tight_rotor_centres=tight_rotor_centres)
    index=len(data[0][0])-1 if strict else None
    result=search_model(data,node_limit,branch_rule='fewest',positive_index=index)
    variant='NORMALIZED_MOVING_BANDS_V3' if unit_rotor else ('NORMALIZED_STRICT_CORES_V2' if strict else 'NORMALIZED_CELLS_V1')
    if unit_rotor and not tight_rotor_centres:variant='NORMALIZED_CAPPED_BANDS_V4'
    result.update(model=variant,config=config,missing=list(missing),chosen=list(chosen))
    if unit_rotor:result['rotated_t_halfwidth_rule']='epsilon/10000'
    if variant=='NORMALIZED_CAPPED_BANDS_V4':result['rotated_t_halfwidth_rule']='min(rot_h,epsilon/(2*(k-1)))'
    result['verified']=replay_model(data,result['tree'],positive_index=index);return result


def verify(q):
    assert q['model'] in ('NORMALIZED_CELLS_V1','NORMALIZED_STRICT_CORES_V2','NORMALIZED_MOVING_BANDS_V3','NORMALIZED_CAPPED_BANDS_V4')
    strict=q['model']!='NORMALIZED_CELLS_V1';unit_rotor=q['model'] in ('NORMALIZED_MOVING_BANDS_V3','NORMALIZED_CAPPED_BANDS_V4')
    capped=q['model']=='NORMALIZED_CAPPED_BANDS_V4'
    if unit_rotor:assert q['rotated_t_halfwidth_rule']==('min(rot_h,epsilon/(2*(k-1)))' if capped else 'epsilon/10000')
    data=model(q['config'],q['missing'],q['chosen'],reference_pieces=True,strict=strict,unit_rotor=unit_rotor,tight_rotor_centres=not capped)
    return replay_model(data,q['tree'],positive_index=len(data[0][0])-1 if strict else None)
