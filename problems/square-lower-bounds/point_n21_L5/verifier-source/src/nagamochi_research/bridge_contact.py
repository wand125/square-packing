"""Finite rational contact stress test for the saved D4 charge comparison."""
import bridge_lp as b
from fractions import Fraction as F
from time import perf_counter
import json,numpy as np
def contact_poses(pts):
    contacts=set()
    for t in (F(0),F(1,1000000),F(1,19),F(1,10),F(2,13),F(1,4),F(1,3),F(2,5),F(41,100)):
     c=(1-t*t)/(1+t*t);s=2*t/(1+t*t);r=(c+s)/2
     for u,v in pts:
      for a in (-1,1):
       for bb in (-1,1):
        for eps in (F(-1,1000000),F(1,1000000)):
         h=F(1,2)+eps;x=u+h*(a*c-bb*s);y=v+h*(a*s+bb*c)
         if r<=y<=x<=3:contacts.add((x,y,t))
    return sorted(contacts)


def main():
    start=perf_counter();root=b.ROOT;d=json.loads((root/'results.json').read_text())
    pts=[tuple(map(F,p)) for p in d['points']];rs=d['rules'];po=d['point_orbits'];ro=d['rule_orbits'];costs=d['costs']
    contacts=contact_poses(pts)
    ps=list(b.poses())+list(b.poses(True))+contacts
    print('poses',len(ps),flush=True)
    a=b.matrix(ps,pts,rs,po,ro);out={}
    for name,cols in d['models'].items():
     result,w=b.solve(a,costs,cols,ps,pts,rs,po,ro);out[name]=result
     print(name,result['mass'],flush=True)
    (root/'contact-results.json').write_text(json.dumps(dict(poses=len(ps),contact_poses=len(contacts),results=out,seconds=perf_counter()-start),indent=2))
    print('seconds',perf_counter()-start,flush=True)

if __name__=="__main__":main()
