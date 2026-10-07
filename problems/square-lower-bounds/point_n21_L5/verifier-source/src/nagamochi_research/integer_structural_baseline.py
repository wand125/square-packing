"""Exact prerequisites for the independent structural proof route at 6,7,8.

This establishes a necessary count and model embedding, not an endpoint proof.
"""
from fractions import Fraction as F
from pathlib import Path
import argparse,json,time
from epsilon_cell_envelope import parameters,check_parameters,geometry
from normalized_certificate_transfer import check_embedding


def baseline(n,k,eps_max=F(1,1000)):
    assert (n,k) in ((32,6),(45,7),(61,8))
    start=time.monotonic();q=parameters(k,eps_max=eps_max);check_parameters(q);m=k-1
    # For every e>0: 1-(1-e/m)*(1+e/m)=e^2/m^2>0.
    strict_coefficient=F(1,m*m);assert strict_coefficient>0
    # The original core side also exceeds the centre-cell width uniformly.
    original_width_coefficient=F(1,m)-F(1,50);assert original_width_coefficient>0
    base=dict(config=q,missing=[]);cells=check_embedding(base)
    old,pieces=geometry(q,[]);assert len(cells)==len(old)==m*m
    return dict(status='EXACT_NORMALIZATION_PREREQUISITES_ONLY',n=n,k=k,config=q,lower_endpoint=str(k-eps_max),
                axis_t_halfwidth=f'epsilon/{2*m}',axis_count_upper=m*m,
                necessary_outside_axis_band=n-m*m,strict_containment_gap_epsilon_squared=str(strict_coefficient),
                saturated_reference_regions=len(pieces),seconds=time.monotonic()-start,
                limitation='The count holds generally; reference regions assume saturated axis cells and one selected rotor band. No exclusion of the outside boxes or all-angle endpoint proof.')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('out',type=Path);p.add_argument('--fixed-targets',action='store_true');a=p.parse_args();a.out.mkdir(exist_ok=True,parents=True)
    for n,k in ((32,6),(45,7),(61,8)):
        em={32:F(1,25),45:F(7,200),61:F(3,100)}[n] if a.fixed_targets else F(1,1000)
        q=baseline(n,k,em);(a.out/f'n{n}.json').write_text(json.dumps(q,indent=2));print(n,k,q['necessary_outside_axis_band'],q['saturated_reference_regions'],q['seconds'],flush=True)
