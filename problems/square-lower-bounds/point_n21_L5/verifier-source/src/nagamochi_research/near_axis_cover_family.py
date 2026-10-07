"""Certify a rational moving-point cover for every 0<t<=1/1000.

No angular sampling is accepted as proof: point/break ordering and separation
of every under-covered cell from the centre domain use exact polynomial signs.
"""
from fractions import Fraction as F
from math import comb,floor,ceil
from pathlib import Path
import argparse,json,hashlib,time
from sympy import QQ
from sympy.polys.fields import field


def prove(source,out,max_t=F(1,1000)):
    start=time.monotonic();saved=json.loads(source.read_text());g=saved['geometry'];L=F(g['L'])
    assert F(g['t'])==F(1,1000) and g['midphases']
    K,t=field('t',QQ);seed=QQ(1,1000);T=F(max_t)
    assert 0<T<=F(1,10)
    def value(f):
        return f.numer.evaluate(0,seed)/f.denom.evaluate(0,seed)
    def constant(x):return K(QQ(x.numerator,x.denominator))
    def strf(f):return str(f.as_expr())
    def bernstein(poly):
        terms={p[0]:F(str(v)) for p,v in poly.to_dict().items()}
        if not terms:return 0,[F(0)]
        power=min(terms);degree=max(terms)-power
        coeff=[terms.get(i+power,F(0))*T**i for i in range(degree+1)]
        return power,[sum(coeff[i]*F(comb(k,i),comb(degree,i)) for i in range(k+1)) for k in range(degree+1)]
    cache={};sign_proofs=[]
    def nonnegative(f,record=True):
        if f in cache:return cache[f]
        np,nc=bernstein(f.numer);dp,dc=bernstein(f.denom)
        if dc[0]<0:nc=[-x for x in nc];dc=[-x for x in dc]
        ok=all(x>=0 for x in nc) and all(x>=0 for x in dc) and dc[0]>0 and dc[-1]>0
        if ok and record:
            sign_proofs.append(dict(expression=strf(f),numerator_t_power=np,denominator_t_power=dp,
                                    numerator_bernstein=list(map(str,nc)),denominator_bernstein=list(map(str,dc))))
        cache[f]=ok
        return ok
    h=t*t/1000;lo=t-h;hi=t+h
    c=(1-t*t)/(1+t*t);s=2*t/(1+t*t);w=c+s
    q=h/(1+t*lo);extent=(1-q*q+2*q)/(1+q*q);B=(1-t*t/100)/extent
    span=(1-lo*lo+2*lo)/(1+lo*lo);H=(constant(L)-span)/2;bound=H*w;limit=bound+B/2
    for expr in (lo,constant(F(1,4))-hi,constant(F(2,5))-q,B,H,1-B*extent):
        assert nonnegative(expr),strf(expr)
    assert F(str(value(B)))==F(g['B']) and F(str(value(h)))==F(g['h'])
    vertex_x=[H*(-c-s),H*(c-s),H*(c+s),H*(-c+s)]
    phases={K.zero,B/2}
    for x in vertex_x:
        raw=x+B/2;phases.add(raw-floor(value(raw/B))*B)
    order=sorted(phases,key=value)
    phases|={(a+b)/2 for a,b in zip(order,order[1:]+[order[0]+B])}
    coordinates=set()
    for phase in phases:
        for j in range(floor(value((-limit-phase)/B)),ceil(value((limit-phase)/B))+1):
            p=phase+j*B
            if -value(limit)<=value(p)<=value(limit):coordinates.add(p)
    coordinates=sorted(coordinates,key=value)
    assert [F(str(value(x))) for x in coordinates]==list(map(F,g['coordinates']))
    m=len(coordinates);points=[]
    for i,num in enumerate(saved['numerators']):
        if num:points.append((coordinates[i//m],coordinates[i%m],num))
    den=saved['denominator']
    assert type(den) is int and den>0 and all(type(v) is int and v>=0 for v in saved['numerators'])
    assert len(saved['numerators'])==m*m
    assert F(sum(p[2] for p in points),den)==F(saved['mass'])
    def breaks(axis):
        values={-bound,bound}|{p[axis]+shift for p in points for shift in (-B/2,B/2)}
        result=sorted(values,key=value)
        for a,b in zip(result,result[1:]):
            assert value(a)<value(b), 'accidental equality at seed'
            assert nonnegative(b-a),'point-order change: '+strf(b-a)
        return result
    xs,ys=breaks(0),breaks(1);bad=[];good=0
    for i,(a,b) in enumerate(zip(xs,xs[1:])):
        for j,(d,e) in enumerate(zip(ys,ys[1:])):
            x,y=value((a+b)/2),value((d+e)/2)
            weight=sum(num for px,py,num in points if abs(value(px)-x)<value(B)/2 and abs(value(py)-y)<value(B)/2)
            if weight>=den:good+=1;continue
            # SAT of the cell rectangle with the rotated centre-domain square.
            # Equality is enough: only its interior must be excluded.
            margins=[a-bound,-bound-b,d-bound,-bound-e,
                     c*a-s*e-H,-H-(c*b-s*d),s*a+c*d-H,-H-(s*b+c*e)]
            choices=[k for k,v in enumerate(margins) if value(v)>=0]
            selected=next((k for k in choices if nonnegative(margins[k])),None)
            assert selected is not None,('uncovered cell',i,j)
            bad.append(dict(i=i,j=j,separation_axis=selected))
    result=dict(status='EXACT_NEAR_AXIS_MOVING_COVER',L=str(L),max_t=str(T),parameter_interval=f'0<t<={T}',
                physical_angle_interval='t-t^2/1000 <= tan(theta_i/2) <= t+t^2/1000 independently for every counted box',
                mass=saved['mass'],upper=F(saved['mass']).numerator//F(saved['mass']).denominator,
                B=strf(B),H=strf(H),points=[dict(x=strf(x),y=strf(y),numerator=num) for x,y,num in points],
                denominator=den,x_breaks=list(map(strf,xs)),y_breaks=list(map(strf,ys)),
                covered_cells=good,excluded_cells=bad,polynomial_sign_proofs=sign_proofs,
                source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),seconds=time.monotonic()-start,
                limitation='Angle cluster only. t=0 is excluded; independently different angle clusters and arbitrary mixed orientations remain unresolved.')
    out.write_text(json.dumps(result,indent=2));print(L,len(points),result['mass'],good,len(bad),len(sign_proofs),result['seconds'],flush=True)
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('out',type=Path)
    p.add_argument('--max-t',type=F,default=F(1,1000))
    a=p.parse_args();prove(a.source,a.out,a.max_t)
