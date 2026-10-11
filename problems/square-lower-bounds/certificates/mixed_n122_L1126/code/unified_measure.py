"""Exact nonnegative D4 orbit measures: points, uniform segments, rectangles.

Each mass is the TOTAL mass of its eight-image orbit, including duplicates.
Segment coefficients are parameter fractions (length ratios); no sqrt or
rectangle-thickness approximation is involved. Closed cores strictly inside
unit squares prevent shared-boundary double counting in packing proofs.
"""
from fractions import Fraction as F
from hashlib import sha256
import json
from score import clip,area

SCHEMA='point_line_rectangle_v1'
RADIAL_SCHEMA='point_line_rectangle_radial_v1'
TRIMMED_SCHEMA='point_line_rectangle_radial_trimmed_v1'
RADIAL_KINDS=('disk','bump','annulus')

def orbit(kind,g,L):
    g=tuple(map(F,g))
    radial=kind in RADIAL_KINDS
    points=[g[:2]] if radial else [g] if kind=='point' else [(g[0],g[1]),(g[2],g[3])]
    for swap in (False,True):
        for sx,sy in ((1,1),(1,-1),(-1,1),(-1,-1)):
            p=[]
            for x,y in points:
                if swap:x,y=y,x
                p.append((x if sx==1 else L-x,y if sy==1 else L-y))
            if radial:yield p[0]+g[2:]
            elif kind=='point':yield p[0]
            elif kind=='rectangle':yield(min(p[0][0],p[1][0]),min(p[0][1],p[1][1]),max(p[0][0],p[1][0]),max(p[0][1],p[1][1]))
            else:yield p[0]+p[1]

def primitive_key(kind,g,L):
    images=[]
    for r in orbit(kind,g,L):
        if kind=='segment':r=min(r,r[2:]+r[:2])
        images.append(r)
    return(kind,min(images))

def validate(data):
    if data.get('schema') not in (SCHEMA,RADIAL_SCHEMA,TRIMMED_SCHEMA):raise ValueError('unsupported measure schema')
    L,B=F(data['L']),F(data['B']);n=data['n']
    if isinstance(n,bool) or not isinstance(n,int) or n<1 or not 0<B<1<L:raise ValueError('invalid geometry')
    expanded=[];total=F(0)
    for a in data['primitives']:
        kind=a['kind'];g=tuple(map(F,a['geometry']));m=F(a['mass'])
        sizes={'point':2,'segment':4,'rectangle':4}
        if data['schema'] in (RADIAL_SCHEMA,TRIMMED_SCHEMA):sizes.update(disk=3,bump=3,annulus=4)
        if kind not in sizes or len(g)!=sizes[kind] or m<0:raise ValueError('invalid primitive')
        if not all(0<=x<=L for x in (g[:2] if kind in RADIAL_KINDS else g)):raise ValueError('outside support/center')
        if kind in RADIAL_KINDS and g[2]<=0:raise ValueError('positive radius required')
        if kind=='annulus' and not 0<=g[3]<1:raise ValueError('invalid inner radius ratio')
        if kind=='rectangle' and not(g[0]<g[2] and g[1]<g[3]):raise ValueError('zero/reversed rectangle')
        if kind=='segment' and g[:2]==g[2:]:raise ValueError('zero segment; use point')
        total+=m
        if m:expanded.extend((kind,r,m/8) for r in orbit(kind,g,L))
    if total!=F(data['total_mass']):raise ValueError('mass mismatch')
    semantic={k:data[k] for k in ('schema','n','L','B','primitives','total_mass','net')}
    if data['schema']==TRIMMED_SCHEMA:
        from trimmed_core import parameters
        if data['core'].get('kind')!='octagon_with_square_radial':raise ValueError('invalid trimmed core')
        parameters(data['net']['step'],data['core']['margin'])
        semantic['core']=data['core']
    digest=sha256(json.dumps(semantic,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    return L,B,n,expanded,total,digest

def net_check(data):
    B=F(data['B']);D=F(data['net']['step']);last=data['net']['last']
    if isinstance(last,bool) or not isinstance(last,int) or last<1 or D<=0:raise ValueError('invalid net')
    T=last*D
    if T>F(1,2) or (1+T)**2<2 or B*(1+D)>=1:raise ValueError('net does not strictly inscribe every angle')
    return D,last

def region(t,box,B):
    t=F(t);c=(1-t*t)/(1+t*t);s=2*t/(1+t*t)
    x0,x1,y0,y1=map(F,box)
    if x0>x1 or y0>y1:raise ValueError('reversed box')
    uv=[(c*x+s*y,-s*x+c*y) for x in (x0,x1) for y in (y0,y1)]
    return c,s,max(u for u,v in uv)-B/2,min(u for u,v in uv)+B/2,max(v for u,v in uv)-B/2,min(v for u,v in uv)+B/2

def coefficient(kind,g,reg):
    if kind in RADIAL_KINDS:raise ValueError('use coefficient_bounds for radial measures')
    c,s,u0,u1,v0,v1=reg
    if u0>u1 or v0>v1:return F(0)
    def uv(x,y):return(c*x+s*y,-s*x+c*y)
    if kind=='point':
        u,v=uv(*g);return F(u0<=u<=u1 and v0<=v<=v1)
    x0,y0,x1,y1=g
    if kind=='segment':
        a=uv(x0,y0);b=uv(x1,y1);lo=F(0);hi=F(1)
        for x,y,lower,upper in [(a[0],b[0],u0,u1),(a[1],b[1],v0,v1)]:
            slope=y-x
            if not slope:
                if not lower<=x<=upper:return F(0)
            else:
                p,q=(lower-x)/slope,(upper-x)/slope
                lo=max(lo,min(p,q));hi=min(hi,max(p,q))
        return max(F(0),hi-lo)
    poly=[uv(x,y) for x,y in [(x0,y0),(x1,y0),(x1,y1),(x0,y1)]]
    for axis,bound,greater in [(0,u0,True),(0,u1,False),(1,v0,True),(1,v1,False)]:poly=clip(poly,axis,bound,greater)
    return area(poly)/((x1-x0)*(y1-y0))

def coefficient_bounds(kind,g,reg,subdivisions=32):
    if kind not in RADIAL_KINDS:
        a=coefficient(kind,g,reg);return a,a
    from radial_measure import polygon_interval
    a,b=polygon_interval(kind,g[:2],g[2],reg,subdivisions,g[3] if kind=='annulus' else F(0))
    # Outward rational rounding bounds denominator growth when many primitives
    # and clipped polygons are summed; no float participates in acceptance.
    scale=10**15
    x=a*scale;y=b*scale
    return F(x.numerator//x.denominator,scale),F(-((-y.numerator)//y.denominator),scale)

def score_bounds(expanded,reg,subdivisions=32):
    lower=upper=F(0)
    for kind,g,m in expanded:
        a,b=coefficient_bounds(kind,g,reg,subdivisions);lower+=m*a;upper+=m*b
    return lower,upper

def score(expanded,reg):
    """Certain lower score; radial counterexamples require score_bounds upper."""
    return score_bounds(expanded,reg)[0]

def verify(data,work=None,max_boxes=1000,checkpoint=None,integral_subdivisions=32,max_integral_subdivisions=256):
    """Exact full-centre B&B at every net direction. Limits mean INCONCLUSIVE.

    A hash-bound checkpoint retains every unprocessed box. Completed leaves
    use only certain common-core mass. Full D4 symmetry is built into schema.
    """
    L,B,n,expanded,total,digest=validate(data);D,last=net_check(data)
    if total>=n:return dict(status='BUDGET_NOT_BELOW_N',mass_exact=str(total))
    if max_boxes<1:raise ValueError('positive work budget required')
    if not isinstance(integral_subdivisions,int) or not isinstance(max_integral_subdivisions,int) or not 1<=integral_subdivisions<=max_integral_subdivisions:raise ValueError('invalid integration budget')
    if work is None:work=dict(engine=data['schema'],status='RUNNING',input_sha256=digest,position=0,stack=None,boxes=0,directions_completed=0)
    else:
        work=json.loads(json.dumps(work))
        if work['engine']!=data['schema'] or work['input_sha256']!=digest:raise ValueError('checkpoint mismatch')
        if work['status'] in ('CERTIFIED','UNCOVERED'):return work
    start=work['boxes'];work['status']='RUNNING';work.pop('reason',None)
    def bounds(t,box,precision):
        reg=region(t,box,B)
        if data['schema']!=TRIMMED_SCHEMA:return score_bounds(expanded,reg,precision)
        from trimmed_core import planes,coefficient as trimmed_coefficient
        inequalities=planes(t,box,D,F(data['core']['margin']));lo=hi=F(0)
        for kind,g,m in expanded:
            if kind in RADIAL_KINDS:a,b=coefficient_bounds(kind,g,reg,precision)
            else:a=b=trimmed_coefficient(kind,g,inequalities)
            lo+=m*a;hi+=m*b
        return lo,hi
    def save():
        if checkpoint:checkpoint(work)
    while work['position']<=last:
        t=D*work['position'];c=(1-t*t)/(1+t*t);s=2*t/(1+t*t);a=B*(c+s)/2
        if 2*a>=L:raise ValueError('empty centre domain')
        if work['stack'] is None:work['stack']=[[str(z) for z in (a,L-a,a,L-a)]]
        while work['stack']:
            if work['boxes']-start>=max_boxes:work['status']='INCONCLUSIVE';save();return work
            box=list(map(F,work['stack'].pop()));work['boxes']+=1
            if bounds(t,box,integral_subdivisions)[0]<1:
                x0,x1,y0,y1=box;x=(x0+x1)/2;y=(y0+y1)/2
                precision=integral_subdivisions
                while True:
                    lower,upper=bounds(t,(x,x,y,y),precision)
                    if upper<1:
                        work.update(status='UNCOVERED',witness=dict(cx=str(x),cy=str(y),t=str(t),mass=str(upper),mass_lower=str(lower),mass_upper=str(upper)));save();return work
                    if lower>=1:break
                    if precision>=max_integral_subdivisions:
                        work['stack'].append(list(map(str,box)))
                        work.update(status='INCONCLUSIVE',reason='INTEGRAL_PRECISION',required_more_than=precision)
                        save();return work
                    precision=min(2*precision,max_integral_subdivisions)
                if x1-x0>=y1-y0:children=[(x0,x,y0,y1),(x,x1,y0,y1)]
                else:children=[(x0,x1,y0,y),(x0,x1,y,y1)]
                work['stack'].extend([[str(z) for z in child] for child in children])
            if work['boxes']%16==0:save()
        work['position']+=1;work['directions_completed']+=1;work['stack']=None;save()
    work['status']='CERTIFIED';save();return work
