#!/usr/bin/env python3
"""Independent Python closed-intersection checks; standard library only.
Default: 200 boxes x 50 poses. The 20,000 x 50 suite is --validate in Rust.
"""
import json, math, random, subprocess, sys, pathlib
ROOT = pathlib.Path(__file__).resolve().parent
BIN = ROOT / 'target/release/m4b-cert2'
PIECES = [p for p in json.loads((ROOT.parent/'measure.json').read_text())['pieces'] if p['density'] > 0]
LIMITS = [2*math.pi, math.pi, math.pi/2, .5, .5, .5]
def pose(x):
    a,b,g=x[:3]; ca,sa,cb,sb,cg,sg=math.cos(a),math.sin(a),math.cos(b),math.sin(b),math.cos(g),math.sin(g)
    r=[[ca*cb*cg-sa*sg,-ca*cb*sg-sa*cg,ca*sb],[sa*cb*cg+ca*sg,-sa*cb*sg+ca*cg,sa*sb],[-sb*cg,sb*sg,cb]]
    h=[sum(map(abs,row))*.5 for row in r]
    return r,[h[w]+x[w+3]*(3-2*h[w]) for w in range(3)]
def mass(x):
    r,c=pose(x); total=0.
    for p in PIECES:
        bounds=p['bounds']; free=[w for w in range(3) if bounds[w][0]<bounds[w][1]]
        t=[sum(r[w][i]*(bounds[w][0]-c[w]) for w in range(3)) for i in range(3)]
        if not free: area=float(all(abs(v)<=.5+1e-14 for v in t))
        elif len(free)==1:
            w=free[0]; lo,hi=0.,bounds[w][1]-bounds[w][0]
            for i in range(3):
                a=r[w][i]
                if a==0:
                    if abs(t[i])>.5+1e-14: hi=-1.
                else:
                    aa,bb=sorted(((-.5-t[i])/a,(.5-t[i])/a));lo=max(lo,aa);hi=min(hi,bb)
            area=max(0.,hi-lo)
        else:
            u,v=free; l=bounds[u][1]-bounds[u][0];h=bounds[v][1]-bounds[v][0]; poly=[(0.,0.),(l,0.),(l,h),(0.,h)]
            for i in range(3):
                for sign in (-1,1):
                    new=[]
                    for a,b in zip(poly,poly[1:]+poly[:1]):
                        f=sign*(t[i]+r[u][i]*a[0]+r[v][i]*a[1])-.5;g=sign*(t[i]+r[u][i]*b[0]+r[v][i]*b[1])-.5
                        if f<=0: new.append(a)
                        if f*g<0:
                            z=f/(f-g);new.append(tuple(a[k]+z*(b[k]-a[k]) for k in (0,1)))
                    poly=new
            area=abs(sum(a[0]*b[1]-a[1]*b[0] for a,b in zip(poly,poly[1:]+poly[:1])))/2
        total+=p['density']*area
    return total*27/20

def run(n=200,aligned=False):
    rng=random.Random(883);boxes=[]
    for k in range(n):
        x=[rng.random()*v for v in LIMITS]
        if k%4==0: x[3+k%3]=0
        if aligned or k%4==1:
            x[:3]=[0,0,0];x[(k//4)%3]=rng.random()*1.5
            x[3:]=[rng.choice([0,.2,.25,.45,.5]) for _ in range(3)]
        rad=10**rng.uniform(-8,-2)
        boxes.append([[max(0,v-rad),min(limit,v+rad)] for v,limit in zip(x,LIMITS)])
    result=subprocess.run([str(BIN),'--threads','1','--batch'],input=''.join(json.dumps({'box':b})+'\n' for b in boxes),text=True,capture_output=True,check=True,timeout=120)
    outputs=[json.loads(s) for s in result.stdout.splitlines()];assert len(outputs)==n
    for b,out in zip(boxes,outputs):
        for _ in range(50):
            x=[rng.uniform(*v) for v in b];actual=mass(x)
            if actual<out['L']-1e-12: actual=precise_mass(x)*27/20
            assert actual>=out['L']-1e-12,(b,out,actual)
    print(f'{n} boxes / {n*50} poses; zero failures; aligned={aligned}')

def precise_mass(values):
    """80-digit independent fallback for ill-conditioned nearly parallel faces.
    Input pose numbers and densities retain their exact binary64 values.
    Geometry coordinates are exact tenths; trig uses an independent Decimal series.
    """
    from decimal import Decimal as D, localcontext
    with localcontext() as ctx:
        ctx.prec=80
        pi=D('3.1415926535897932384626433832795028841971693993751058209749445923078164062862089986')
        def sc(z):
            z=(z+pi)%(2*pi)-pi; zz=z*z; st=z;ct=D(1);s=st;c=ct
            for k in range(1,120):
                st*=-zz/D(2*k*(2*k+1));ct*=-zz/D((2*k-1)*2*k);s+=st;c+=ct
            return s,c
        x=[D.from_float(v) for v in values];sa,ca=sc(x[0]);sb,cb=sc(x[1]);sg,cg=sc(x[2])
        r=[[ca*cb*cg-sa*sg,-ca*cb*sg-sa*cg,ca*sb],[sa*cb*cg+ca*sg,-sa*cb*sg+ca*cg,sa*sb],[-sb*cg,sb*sg,cb]]
        half=D('.5');h=[sum(map(abs,row))*half for row in r];c=[h[w]+x[w+3]*(3-2*h[w]) for w in range(3)];total=D(0)
        for p in PIECES:
            bounds=[[D(round(v*10))/10 for v in pair] for pair in p['bounds']];free=[w for w in range(3) if bounds[w][0]<bounds[w][1]]
            t=[sum(r[w][i]*(bounds[w][0]-c[w]) for w in range(3)) for i in range(3)]
            if not free:area=D(all(abs(v)<=half for v in t))
            elif len(free)==1:
                w=free[0];lo=D(0);hi=bounds[w][1]-bounds[w][0]
                for i in range(3):
                    a=r[w][i]
                    if a==0:
                        if abs(t[i])>half: hi=D(-1)
                    else:
                        aa,bb=sorted(((-half-t[i])/a,(half-t[i])/a));lo=max(lo,aa);hi=min(hi,bb)
                area=max(D(0),hi-lo)
            else:
                u,v=free;l=bounds[u][1]-bounds[u][0];hh=bounds[v][1]-bounds[v][0];poly=[(D(0),D(0)),(l,D(0)),(l,hh),(D(0),hh)]
                for i in range(3):
                    for sign in (-1,1):
                        new=[]
                        for a,b in zip(poly,poly[1:]+poly[:1]):
                            f=sign*(t[i]+r[u][i]*a[0]+r[v][i]*a[1])-half;g=sign*(t[i]+r[u][i]*b[0]+r[v][i]*b[1])-half
                            if f<=0:new.append(a)
                            if f*g<0:
                                z=f/(f-g);new.append(tuple(a[k]+z*(b[k]-a[k]) for k in (0,1)))
                        poly=new
                area=abs(sum((a[0]*b[1]-a[1]*b[0] for a,b in zip(poly,poly[1:]+poly[:1])),D(0)))/2
            total+=D.from_float(p['density'])*area
        return float(total)

if __name__=='__main__': run(int(sys.argv[1]) if len(sys.argv)>1 else 200)
