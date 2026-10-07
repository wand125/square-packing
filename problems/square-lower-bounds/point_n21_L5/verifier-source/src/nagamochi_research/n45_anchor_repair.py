"""End-row anchor repair and exact cubic wall-lemma conditions.
Polynomial certificates are conditional on the cited geometric lemma;
full unavoidability/ownership/chord contradiction is not asserted.
"""
from fractions import Fraction as F
from time import perf_counter
import json
from n45_small_motion import ROOT,snapshot,heights
from motion_pilot import rows
from endpoint_cells import scan


def wall_poly(a,b,t):return -t**3+(1+a)*t*t+(1-2*b)*t+1-a

def wall_derivative(a,b,t):return -3*t*t+2*(1+a)*t+1-2*b

def certificate(a,b):
    assert 0<a<1 and 0<b<1 and a*a+(b-1)**2<=1
    # a > 2sqrt(2)-2, and 5/12 > sqrt(2)-1, checked without radicals.
    assert (a+2)**2>8 and (F(17,12))**2>2
    leaves=[]
    for j in range(64):
        lo,hi=F(5*j,768),F(5*(j+1),768);width=hi-lo
        bern=[wall_poly(a,b,lo),wall_poly(a,b,lo)+width*wall_derivative(a,b,lo)/3,
              wall_poly(a,b,hi)-width*wall_derivative(a,b,hi)/3,wall_poly(a,b,hi)]
        assert min(bern)>0
        leaves.append(dict(lo=str(lo),hi=str(hi),coefficients=list(map(str,bern))))
    return dict(gap=str(a),anchor=str(b),leaves=leaves)

def common_snapshot(colour,focus,time):
    end=F(39,40);target,_=heights(focus)
    if (colour+focus)%2:
        return snapshot(colour,focus,'leftmost-right',time,reflection=end)
    return [(x-(1-end)*time if y==target[focus] and x==1 else x,y) for x,y in rows(7,target,colour)]

def main():
    start=perf_counter();cert=certificate(F(847,1000),F(39,40));records=[]
    for focus in (0,6):
        for colour in (0,1):
            checks=[]
            for time in (F(0),F(1,2),F(1)):
                ps=common_snapshot(colour,focus,time)
                for t in (F(1,3),F(-1,3),F(2,5),F(-2,5)):
                    result=scan(ps,[F(1)]*len(ps),t,F(1,10**8),k=7);checks.append(dict(time=str(time),test=result))
            records.append(dict(colour=colour,focus=focus,checks=checks))
    # For internal gaps .854, the two existing sufficient conditions conflict.
    # f(9/25) is an exact upper bound on inf f; compare to triangle anchor minimum.
    a=F(427,500);t=F(9,25);f=(1-t*t)/2+(1-a)/(2*t)+(1+a)*t/2
    assert F(3,2)-f>0 and (F(3,2)-f)**2>1-a*a
    obstruction=dict(gap=str(a),sample_t=str(t),f_upper=str(f),scope='No common anchor satisfies both this triangle criterion and this wall-lemma criterion. Not a general geometric impossibility.')
    out=dict(certificate=cert,records=records,internal_obstruction=obstruction,seconds=perf_counter()-start)
    (ROOT/'anchor-repair.json').write_text(json.dumps(out,indent=2));print(json.dumps(dict(seconds=out['seconds'],states=len(records)*3,cell_checks=sum(len(r['checks']) for r in records),empty=sum('score' in c['test'] for r in records for c in r['checks']),cubic_leaves=len(cert['leaves']),internal_f_upper=str(f))))

if __name__=='__main__':main()
