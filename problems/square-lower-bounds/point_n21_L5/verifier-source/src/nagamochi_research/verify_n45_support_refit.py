"""Replay finite duals, rationalize candidates, find full-centre counterexamples."""
import json
from fractions import Fraction as F
from n45_support_refit import ROOT, hit
from endpoint_cells import scan

def main():
    d=json.loads((ROOT/'results.json').read_text());ps=[tuple(map(F,p)) for p in d['poses']]
    orbits=[[tuple(map(F,p)) for p in o] for o in d['point_orbits']]
    records={}
    for name,m in d['models'].items():
        dual=[(v['index'],F(v['weight'])) for v in m['dual']]
        assert all(y>=0 for i,y in dual)
        for col in m['columns']:
            load=sum(y*(1 if col==0 else sum(hit(p,ps[i]) for p in orbits[col-1])) for i,y in dual)
            assert load<=d['costs'][col]
        assert sum(y for i,y in dual)==F(m['exact_finite_lower_bound'])
        weights=[F(w).limit_denominator(10**6) for w in m['weights']]
        assert all(w>=0 for w in weights)
        assert all(sum(w*(1 if j==0 else sum(hit(p,pose) for p in orbits[j-1])) for j,w in zip(m['columns'],weights))>=1 for pose in ps)
        mass=sum(d['costs'][j]*w for j,w in zip(m['columns'],weights))
        pts=[];ws=[]
        for j,w in zip(m['columns'],weights):
            if j==0:assert w==0
            elif w:
                assert (4*w).denominator==1
                pts.extend(orbits[j-1]);ws.extend([w]*len(orbits[j-1]))
        checks=[]
        for t in (F(0),F(1,19),F(1,3),F(2,5)):
            r=scan(pts,ws,t,F(1,10**8),k=7);checks.append(r)
            if 'score' in r:break
        records[name]=dict(exact_mass=str(mass),finite_primal_dual_verified=True,centre_checks=checks)
    (ROOT/'verified.json').write_text(json.dumps(records,indent=2));print(json.dumps(records))
if __name__=='__main__':main()
