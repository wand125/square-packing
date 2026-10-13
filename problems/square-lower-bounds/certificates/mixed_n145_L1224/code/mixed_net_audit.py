"""Exact sufficient angle-net containment and mixed-budget/symmetry audit.
This does NOT check centre coverage at the net angles.
"""
from fractions import Fraction as F
from pathlib import Path
import json
from mixed_density_check import expand


def symmetry(model):
    L,B,rs,ps,total,digest=model;weights={}
    for p,w in ps:weights[p]=weights.get(p,F(0))+w
    weights={p:w for p,w in weights.items() if w}
    for transform in (lambda x,y:(L-x,y),lambda x,y:(y,x)):
        moved={}
        for (x,y),w in weights.items():
            p=transform(x,y);moved[p]=moved.get(p,F(0))+w
        if moved!=weights:raise ValueError('Point measure is not D4 invariant')
    return True  # Rectangle expansion itself takes the full D4 average.


def net_certificate(B,step=F(83,40000),last=200):
    B=F(B);step=F(step)
    if type(last) is not int or last<1:raise ValueError('Invalid last net index')
    end=step*last
    if not (0<B<1 and 0<step and F(0)<end<F(1)):raise ValueError('Invalid net')
    if (1+end)**2<2:raise ValueError('Net does not reach tan(pi/8)')
    if (1+(last-F(1,2))*step)**2>=2:raise ValueError('Last net node has no assigned orientation')
    # For t in [0,sqrt(2)-1], nearest arithmetic net point t_j has
    # |t-t_j|<=step/2. z=tan(|theta-theta_j|/2)<=step/2,
    # cos(delta)+sin(delta)=(1+2*z-z*z)/(1+z*z)<=1+2*z<=1+step.
    bound=B*(1+step)
    if bound>=1:raise ValueError('Core containment is not strict')
    return dict(step=str(step),count=last+1,endpoint=str(end),endpoint_check=str((1+end)**2-2),
                rotated_side_upper=str(bound),side_margin=str(1-bound),
                per_edge_margin=str((1-bound)/2),
                conclusion='Every unit-square orientation contains a concentric B-core at a net angle strictly in its interior.',
                remaining='Every admissible centre at every net angle must have mixed score >= Gamma, and M < n*Gamma. Not checked here.')


def candidate_net(data):
    """A declared net is part of the candidate digest; old files keep defaults."""
    spec=data.get('proof_net',dict(step='83/40000',last=200))
    if set(spec)!= {'step','last'}:raise ValueError('Invalid proof_net fields')
    step,last=F(spec['step']),spec['last']
    net_certificate(F(data['B']),step,last)
    return step,last



def centre_domains(L,B,step=F(83,40000),last=200):
    """Union of admissible unit-square centres assigned to each t-net node.

    On [0,tan(pi/8)], unit-square axis radius increases with t. The lower
    Voronoi endpoint therefore gives the largest centre domain in that bin.
    """
    records=[]
    for j in range(last+1):
        t=j*step;a=max(F(0),t-step/2)
        if a*a+2*a-1>0:continue  # No assigned original orientation.
        radius=(1+2*a-a*a)/(2*(1+a*a))
        core_radius=B*(1+2*t-t*t)/(2*(1+t*t))
        assert radius>=core_radius
        records.append(dict(index=j,t=str(t),original_t_lower=str(a),
                            centre_low=str(radius),centre_high=str(L-radius),
                            eliminated_boundary_width=str(radius-core_radius)))
    return records


def main():
    root=Path('runs/expanded_n12_n21_20260926/n21');records=[]
    for relative in ('exact-refit-5/mixed-candidate.json','exact-refit-5/targeted-pricing-polished/fixed-candidate.json','exact-refit-5/targeted-pricing-polished/mixed-candidate.json'):
        model=expand(json.loads((root/relative).read_text()));symmetry(model)
        records.append(dict(candidate=relative,digest=model[-1],mass=str(model[-2]),D4=True,net=net_certificate(model[1]),centre_domains=centre_domains(model[0],model[1])))
    output=Path('runs/mixed_strict_design_20260926');output.mkdir(exist_ok=True)
    (output/'net-audit.json').write_text(json.dumps(records,indent=2))
    print(json.dumps(dict(candidates=len(records),net=records[0]['net'],status='NET_AND_BUDGET_ONLY_NOT_COVERAGE')))
if __name__=='__main__':main()
