"""All-centre PL37 sweep on a certified one-sided half-angle interval.

Integer polynomial comparisons freeze the arrangement and PL43 projections.
The expansion can start at any rational half-angle in [0,1/2].
One band never certifies all angles or a packing bound alone.
"""
import argparse
import hashlib
import json
from fractions import Fraction as F
from pathlib import Path
from exact_fixed_angle_separator import RangeMin, separate
from probe_external_integer_bridge import read


def trim(p):
    p = tuple(p)
    while len(p)>1 and p[-1] == 0:
        p = p[:-1]
    return p or (0,)


def add(p,q):
    return trim(tuple((p[i] if i<len(p) else 0)+(q[i] if i<len(q) else 0)
                      for i in range(max(len(p),len(q)))))


def scale(p,c):
    return trim(tuple(c*x for x in p))


def sub(p,q):
    return add(p,scale(q,-1))


def mul(p,q):
    out = [0]*(len(p)+len(q)-1)
    for i,x in enumerate(p):
        for j,y in enumerate(q):
            out[i+j] += x*y
    return trim(out)


def capture_rectangle(x,y,D,*,basis=None):
    """Polynomial boundaries in transformed centre coordinates."""
    a,b,r=basis if basis is not None else ((1,0,-1),(0,2),(1,0,1))
    uc=add(scale(a,2*x),scale(b,2*y))
    vc=sub(scale(a,2*y),scale(b,2*x))
    up=tuple(add(uc,scale(r,s*D)) for s in (-1,1))
    vp=tuple(add(vc,scale(r,s*D)) for s in (-1,1))
    return up,vp


class Signs:
    def __init__(self,cap):
        self.T=F(cap)
        if not 0 < self.T <= F(1,1000):
            raise ValueError('Need 0 < cap <= 1/1000')
        self.conditions={}
        self.comparisons=0

    def sign(self,p):
        self.comparisons+=1
        p=trim(p)
        if p in self.conditions:
            return self.conditions[p]
        s=0
        for k,c in enumerate(p):
            if c:
                s=1 if c>0 else -1
                tail=sum(abs(x) for x in p[k+1:])
                if tail and abs(c)*self.T.denominator < 2*tail*self.T.numerator:
                    self.T=F(abs(c),2*tail)
                break
        self.conditions[p]=s
        return s

    def cmp(self,x,y):
        # Denominators are 1,a,b,r²; positive on the certified open interval.
        return self.sign(sub(mul(x[0],y[1]),mul(y[0],x[1])))

    def extremum(self,values,maximum):
        best=values[0]
        for item in values[1:]:
            c=self.cmp(item,best)
            if (maximum and c>0) or (not maximum and c<0):
                best=item
        return best

    def replay(self):
        # Exact remainder check, separately evaluated at the final common T.
        from certify_n21_near_axis_path import sign_on_open_interval
        for p,s in self.conditions.items():
            assert sign_on_open_interval(p,self.T)[0]==s
        encoded=json.dumps(sorted(self.conditions.items()),separators=(',',':')).encode()
        return hashlib.sha256(encoded).hexdigest()


def sweep(L,D,points,cap=F(1,1000),*,center=F(0),direction=1):
    L=F(L)
    if not isinstance(D,int) or D<=0 or L<=1 or (L*D).denominator!=1:
        raise ValueError('Need L > 1 and positive integer D with integer L*D')
    if any(not isinstance(v,int) for p in points for v in p) or any(w<0 for x,y,w in points):
        raise ValueError('Need integer coordinates and nonnegative integer masses')
    center=F(center)
    if direction not in (-1,1) or not 0<=center<=F(1,2):
        raise ValueError('Need center in [0,1/2] and direction +/-1')
    reach=(F(1,2)-center) if direction==1 else center/2
    if reach<=0:raise ValueError('No positive step in requested direction')
    span=int(L*D)
    signs=Signs(cap)
    signs.T=min(signs.T,reach)
    p,q=center.numerator,center.denominator
    one=(1,)
    a=trim((q*q-p*p,-2*p*q*direction,-q*q))
    b=trim((2*p*q,2*q*q*direction))
    r=trim((q*q+p*p,2*p*q*direction,q*q))
    rr=mul(r,r)
    assert all(signs.sign(poly)==1 for poly in (a,b,r))
    # Full-dimensional physical centre domain for the whole interval.
    assert signs.sign(sub(scale(r,span),scale(add(a,b),D)))==1
    low=scale(mul(r,add(a,b)),D)
    high=sub(scale(rr,2*span),low)
    us={(0,),scale(add(a,b),2*span)}
    vs={scale(b,-2*span),scale(a,2*span)}
    rectangles=[]
    for x,y,w in points:  # Include zero-mass geometry for later weight reuse.
        up,vp=capture_rectangle(x,y,D,basis=(a,b,r))
        us.update(up);vs.update(vp);rectangles.append((up,vp,w))
    def ordered(values):
        out=sorted(values,key=lambda p:p+(0,)*(3-len(p)))
        for x,y in zip(out,out[1:]):
            assert signs.sign(sub(y,x))==1
        return out
    us,vs=ordered(us),ordered(vs)
    vid={p:i for i,p in enumerate(vs)}
    events={}
    for (u0,u1),(v0,v1),w in rectangles:
        lo,hi=vid[v0],vid[v1]-1
        assert lo<=hi
        events.setdefault(u0,[]).append((lo,hi,w))
        events.setdefault(u1,[]).append((lo,hi,-w))
    tree=RangeMin(len(vs)-1)
    best=None;strips=0
    def search(value,right):
        lo,hi=0,len(vs)
        while lo<hi:
            mid=(lo+hi)//2
            c=signs.cmp((vs[mid],one),value)
            if c<0 or (right and c==0):lo=mid+1
            else:hi=mid
        return lo
    constant_lower=(sub(mul(a,low),mul(b,high)),rr)
    constant_upper=(sub(mul(a,high),mul(b,low)),rr)
    for u0,u1 in zip(us,us[1:]):
        for lo,hi,w in events.get(u0,[]):tree.add(lo,hi,w)
        v0=signs.extremum(((sub(mul(a,u0),high),b),
                          (sub(low,mul(b,u1)),a),constant_lower),True)
        v1=signs.extremum(((sub(high,mul(b,u0)),a),
                          (sub(mul(a,u1),low),b),constant_upper),False)
        if signs.cmp(v0,v1)>=0:continue
        lo=search(v0,True)-1
        hi=search(v1,False)-1
        assert 0<=lo<=hi<len(vs)-1
        mass,index=tree.query(lo,hi)
        if best is None or mass<best:
            best=mass
            best_cell=dict(u0=u0,u1=u1,v0=vs[index],v1=vs[index+1])
        strips+=1
    assert best is not None
    digest=signs.replay()
    return dict(status='EXACT_OPEN_ANGLE_ALL_CENTRE_MINIMUM',
                interval=dict(lower=str(center if direction==1 else center-signs.T),
                              lower_open=direction==1,
                              upper=str(center+signs.T if direction==1 else center),
                              upper_open=direction==-1),
                parameter_interval=dict(lower='0',lower_open=True,upper=str(signs.T)),
                expansion_center=str(center),direction=direction,
                minimum_numerator=best,minimum_cell=best_cell,u_strips=strips,u_boundaries=len(us),
                v_boundaries=len(vs),comparisons=signs.comparisons,
                polynomial_conditions=len(signs.conditions),conditions_sha256=digest,
                all_polynomial_signs_replayed=True,all_angles_verified=False)


def run(candidate,out,cap=F(1,1000),*,center=F(0),direction=1):
    if out.exists():raise FileExistsError(out)
    L,span,W,points=read(candidate);D=int(F(span)/L)
    result=sweep(L,D,points,cap,center=center,direction=direction)
    center=F(center)
    T=F(result['parameter_interval']['upper'])
    checks=[]
    for t in (center+direction*T,center+direction*T/10**7):
        numeric=separate(L,D,points,t)
        if numeric['minimum_numerator']!=result['minimum_numerator']:
            diagnostic=dict(symbolic=result,numeric=numeric)
            out.with_suffix('.mismatch.json').write_text(json.dumps(diagnostic,indent=2))
            raise AssertionError(json.dumps(diagnostic))
        checks.append(numeric)
    anchor=separate(L,D,points,center)
    result.update(candidate_sha256=hashlib.sha256(candidate.read_bytes()).hexdigest(),
                  L=str(L),minimum=str(F(result['minimum_numerator'],W)),
                  anchor_minimum=str(F(anchor['minimum_numerator'],W)),
                  closed_band_verified=min(anchor['minimum_numerator'],result['minimum_numerator'])>=W,
                  fixed_angle_crosschecks=checks,anchor_crosscheck=anchor,
                  general_coverage_verified=False)
    if center==0:
        result.update(axis_minimum=result['anchor_minimum'],axis_crosscheck=anchor)
    out.write_text(json.dumps(result,indent=2))
    print(json.dumps({k:v for k,v in result.items() if 'crosscheck' not in k}),flush=True)
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('candidate',type=Path);p.add_argument('out',type=Path)
    p.add_argument('--cap',type=F,default=F(1,1000))
    p.add_argument('--center',type=F,default=F(0));p.add_argument('--direction',type=int,choices=(-1,1),default=1)
    args=p.parse_args();run(args.candidate,args.out,args.cap,center=args.center,direction=args.direction)
