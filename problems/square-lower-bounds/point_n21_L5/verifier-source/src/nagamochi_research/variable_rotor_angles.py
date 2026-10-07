"""Necessary LP relaxation with shared rotor angles and centre products.

Normalized axis cores and actual-angle rotor cores all have side one.
All are strictly inside the scaled physical boxes for epsilon > 0.
The angle arc and bilinear products are relaxed OUTWARDS; an LP witness
does not imply a packing. Only exact replay of exclusions is accepted.
"""
from fractions import Fraction as F
from itertools import combinations,product
from pathlib import Path
import json
from joint_angle_lp import rotation
from normalized_axis_cells import geometry
from epsilon_cell_envelope import geometry as envelope_geometry
from normalized_certificate_transfer import check_embedding
from saturated_joint_search import search_model,replay_model
from bounded_farkas import certificate


def model(config,missing,chosen,equilibrate=False,audit=False):
    check_embedding(dict(config=config,missing=missing))
    cells,_=geometry(config,missing);pieces=envelope_geometry(config,missing)[1]
    polys=list(cells.values())+[pieces[i] for i in chosen];na=len(cells);n=len(polys)
    t=F(config['t']);h=F(config['rot_h']);assert 0<t-h<t+h<F(1)
    c0,s0=rotation(t);cl,sl=rotation(t-h);ch,sh=rotation(t+h)
    # This module uses the first-quadrant monotonic branch of sin(theta).
    assert t+h<F(2,5)
    bounds=[];rows=[];rhs=[];products={};angles={};row_kinds=[];relative=[]
    def row(d,b,kind='geometry'):
        rows.append({i:F(v) for i,v in d.items() if v});rhs.append(F(b));row_kinds.append(kind)
    def var(lo,hi):
        i=len(bounds);bounds.append((F(lo),F(hi)));row({i:1},hi,'bounds');row({i:-1},-lo,'bounds');return i
    def mul(a,b):
        key=tuple(sorted((a,b)))
        if key in products:return products[key]
        la,ua=bounds[a];lb,ub=bounds[b];vals=[x*y for x in (la,ua) for y in (lb,ub)]
        z=var(min(vals),max(vals));products[key]=z
        row({z:-1,a:lb,b:la},la*lb,'product');row({z:-1,a:ub,b:ua},ua*ub,'product')
        row({z:1,a:-lb,b:-ua},-ua*lb,'product');row({z:1,a:-ub,b:-la},-la*ub,'product')
        return z
    for p in polys:
        for axis in (0,1):var(min(x[axis] for x in p),max(x[axis] for x in p))
    gap=var(0,1)
    for i,p in enumerate(polys):
        for (x,y),(X,Y) in zip(p,p[1:]+p[:1]):row({2*i:Y-y,2*i+1:x-X},(Y-y)*x+(x-X)*y)
    for i in range(na,n):
        c=var(ch,cl);s=var(sl,sh);angles[i]=(c,s)
        lower=min(c0*c1+s0*s1 for c1,s1 in ((cl,sl),(ch,sh)))
        row({c:c0,s:s0},1,'angle');row({c:-c0,s:-s0},-lower,'angle')
        # A normalized actual-angle centre has halfwidth <= (k-c-s)/2.
        for axis,sign in product((0,1),(-1,1)):row({2*i+axis:sign,c:F(1,2),s:F(1,2)},F(config['k'],2))
    index={v:i for i,v in enumerate(cells)};m=config['k']-1
    for cell,i in index.items():
        x,y=divmod(cell,m)
        for other,axis,valid in ((cell+m,0,x<m-1),(cell+1,1,y<m-1)):
            if valid and other in index:row({2*i+axis:1,2*index[other]+axis:-1,gap:1},-1)
    pairs=[]
    for i,j in combinations(range(n),2):
        extra={};threshold=F(1)
        if i<na<=j:
            c,s=angles[j];extra={c:F(1,2),s:F(1,2)};threshold=F(1,2)
        elif i>=na:
            ci,si=angles[i];cj,sj=angles[j];q=var(0,1)
            # |cross|-8h² <= |linearized cross| <= |cross|+8h²,
            # 1-dot <= 8h². Hence max(0,|linear|-16h²)
            # is <= cos(delta)+|sin(delta)|-1.
            lin={sj:c0,si:-c0,cj:-s0,ci:s0}
            relative.append((q,lin))
            for sign in (-1,1):row({**{v:sign*a for v,a in lin.items()},q:-1},16*h*h,'relative')
            extra={q:F(1,2)}
        options=[];guaranteed=False
        for owner in (i,j):
            for axis,sign in product((0,1),(-1,1)):
                if owner<na:
                    coefficients=[(2*j+axis,F(sign)),(2*i+axis,F(-sign))]
                    vectors=[(F(sign),F(0)) if axis==0 else (F(0),F(sign))]
                else:
                    c,s=angles[owner]
                    ab=[(c,F(sign)),(s,F(sign))] if axis==0 else [(s,F(-sign)),(c,F(sign))]
                    coefficients=[]
                    for v,(angle,factor) in enumerate(ab):
                        coefficients.extend([(mul(angle,2*j+v),factor),(mul(angle,2*i+v),-factor)])
                    vectors=[(a*ab[0][1],b*ab[1][1]) for a,b in product(bounds[ab[0][0]],bounds[ab[1][0]])]
                projections=[a*(x-X)+b*(y-Y) for a,b in vectors for x,y in polys[j] for X,Y in polys[i]]
                if max(projections)<=1:continue
                upper=F(1) if j<na else F(3,2)
                if min(projections)>upper:guaranteed=True
                d=dict(extra);d[gap]=1
                for v,a in coefficients:d[v]=d.get(v,F(0))-a
                options.append((d,-threshold))
        if not guaranteed:
            # Duplicate axes of two near-axis cores are the same branch.
            unique={tuple(sorted(d.items()))+(('rhs',b),):(d,b) for d,b in options}
            pairs.append(dict(i=i,j=j,options=list(unique.values())))
    nv=len(bounds)
    def dense(d):return [d.get(v,F(0)) for v in range(nv)]
    data=([dense(d) for d in rows],rhs,[dict(i=p['i'],j=p['j'],options=[(dense(d),b) for d,b in p['options']]) for p in pairs],polys,[F(0)]*na+[t]*(n-na))
    offsets=[F(0)]*nv;scales=[F(1)]*nv
    if equilibrate:
        # Exact affine variable changes avoid subtracting nearly equal floats
        # in the tiny angle arcs. Gap has zero offset: positivity is preserved.
        offsets=[(lo+hi)/2 for lo,hi in bounds];scales=[(hi-lo)/2 or F(1) for lo,hi in bounds]
        offsets[gap]=F(0);scales[gap]=h
        def change(row,rhs):return [a*s for a,s in zip(row,scales)],rhs-sum(a*x for a,x in zip(row,offsets))
        A,b,pairs,polys,angles=data
        changed=[change(row,rhs) for row,rhs in zip(A,b)]
        data=([row for row,rhs in changed],[rhs for row,rhs in changed],
              [dict(i=p['i'],j=p['j'],options=[change(row,rhs) for row,rhs in p['options']]) for p in pairs],polys,angles)
    if audit:return data,gap,dict(bounds=bounds,products=products,angles=angles,relative=relative,row_kinds=row_kinds,offsets=offsets,scales=scales)
    return data,gap


def run(config,missing,chosen,node_limit=3000,equilibrate=True):
    data,gap=model(config,missing,chosen,equilibrate)
    r=search_model(data,node_limit,positive_index=gap,branch_rule='fewest',certificate_solver=certificate)
    r.update(model='SHARED_ROTOR_ANGLE_MCCORMICK_V2' if equilibrate else 'SHARED_ROTOR_ANGLE_MCCORMICK_V1',config=config,missing=missing,chosen=chosen,variables=len(data[0][0]),rows=len(data[0]),gap_index=gap)
    r['verified']=replay_model(data,r['tree'],positive_index=gap)
    return r


def verify(q):
    assert q['model'] in ('SHARED_ROTOR_ANGLE_MCCORMICK_V1','SHARED_ROTOR_ANGLE_MCCORMICK_V2')
    data,gap=model(q['config'],q['missing'],q['chosen'],q['model'].endswith('V2'));assert q['gap_index']==gap
    return replay_model(data,q['tree'],positive_index=gap)


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('out',type=Path);p.add_argument('--nodes',type=int,default=3000);a=p.parse_args()
    q=json.loads(a.source.read_text());r=run(q['config'],q['missing'],q['chosen'],a.nodes)
    a.out.write_text(json.dumps(r,indent=2));print({k:r[k] for k in ('status','nodes','seconds','verified','variables','rows')},flush=True)
