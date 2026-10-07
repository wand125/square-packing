import math, json, sys, random
import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'checker'))
from q3 import Q3
from fractions import Fraction as F
c=json.load(open(sys.argv[1])); r3=math.sqrt(3); L=float(Q3.parse(c["L"]))
P=[(float(Q3.parse(p["x"])),float(Q3.parse(p["y"])),float(F(p["w"]))) for p in c["points"]]
x0=(float(sys.argv[2]),float(sys.argv[3]))
def worst_at(th, x0):
    co,si=math.cos(th),math.sin(th)
    def f(cx,cy):
        adm=9
        for sx in(-.5,.5):
            for sy in(-.5,.5):
                x=cx+co*sx-si*sy; y=cy+si*sx+co*sy; adm=min(adm,y,(r3*x-y)/2,(r3*(L-x)-y)/2)
        ex=sorted((max(abs((px-cx)*co+(py-cy)*si),abs(-(px-cx)*si+(py-cy)*co))-.5,w) for px,py,w in P)
        acc=0
        for e,w in ex:
            acc+=w
            if acc>=1-1e-12: return adm,e
        return adm,9
    rng=random.Random(1); x=x0; best=(-9,x)
    for it in range(40000):
        sc=0.02*(0.9998**it)+1e-9
        cand=(x[0]+rng.gauss(0,sc),x[1]+rng.gauss(0,sc)); a,m=f(*cand)
        if a>=0 and m>best[0]: best=(m,cand); x=cand
    return best
for d in [0,0.5,1,2,3,3.3,3.5,3.6,3.7,3.8,4,4.5,5,6,8,10,12,15]:
    m,(cx,cy)=worst_at(math.radians(d),x0)
    print(f"theta {d:5.2f}  worst margin {m:+.6f}  at ({cx:.4f},{cy:.4f})")
