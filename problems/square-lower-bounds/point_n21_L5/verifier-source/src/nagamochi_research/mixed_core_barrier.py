"""Exact grid obstruction on the ORIGINAL unit-square centre domain.
Disjoint CLOSED cores avoid atomic boundary double-counting.
"""
from fractions import Fraction as F
from itertools import combinations
from pathlib import Path
import json


def grid(k,L,B):
    assert k>=2 and L>1 and 0<B<1
    pitch=(L-1)/(k-1)
    if pitch<=B:raise ValueError('Strictly disjoint closed core grid not established')
    centres=[(F(1,2)+i*pitch,F(1,2)+j*pitch) for i in range(k) for j in range(k)]
    assert all(F(1,2)<=x<=L-F(1,2) and F(1,2)<=y<=L-F(1,2) for x,y in centres)
    assert all(abs(x-u)>B or abs(y-v)>B for (x,y),(u,v) in combinations(centres,2))
    return dict(L=str(L),B=str(B),count=len(centres),pitch=str(pitch),strict_gap=str(pitch-B),centres=[list(map(str,p)) for p in centres],necessary_mass=str(k*k))


def minimum_nodes_under_current_sufficient_condition(k,L):
    # Necessary to avoid the grid: B >= (L-1)/(k-1).
    # Current sufficient containment B*(1+D)<1 then requires D<(k-L)/(L-1).
    cap=(k-L)/(L-1)
    if cap<=0:raise ValueError('This bound requires L<k')
    last=1
    while (1+last*cap)**2<=2:last+=1
    return dict(L=str(L),necessary_B_min=str((L-1)/(k-1)),step_strict_upper=str(cap),necessary_node_count=last+1,scope='Necessary count for the current uniform half-angle net and B*(1+D)<1 criterion, not an optimized arbitrary angle net.')


def main():
    out=Path('runs/mixed_core_grid_barrier_20260926');out.mkdir(exist_ok=True)
    result=dict(grid=grid(5,F('4.995'),F('0.9977')),fixed_B_threshold=str(1+4*F('0.9977')),current_step_threshold=str(1+F(4)/(1+F(83,40000))),next_targets=[minimum_nodes_under_current_sufficient_condition(5,F(L)) for L in ('4.985','4.99','4.995','4.999')],scope='Coverage obstruction, not a packing of 25 unit squares and not impossibility of a sharper method.')
    (out/'audit.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='grid'},indent=2))
if __name__=='__main__':main()
