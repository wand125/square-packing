"""Lift PL34 to a nonzero rational half-angle band by core inclusion."""
import argparse,json,hashlib
from pathlib import Path
from fractions import Fraction as F
from exact_axis_capture import calculate
from mixed_density_check import expand


def halfangle(outer,inner):
    outer,inner=F(outer),F(inner)
    if not 0<inner<outer<1:raise ValueError('Strictly nested cores required')
    return min(F(1,4),(outer/inner-1)/2)


def build(original,aligned,axis_certificate):
    d=json.loads(original.read_text());e=json.loads(aligned.read_text());cert=json.loads(axis_certificate.read_text())
    expand(d)
    for key in ('n','L','rectangles','points','total_mass'):
        if d[key]!=e[key]:raise ValueError('Measure changed: '+key)
    sha=hashlib.sha256(aligned.read_bytes()).hexdigest()
    if cert['candidate_sha256']!=sha:raise ValueError('Axis source changed')
    # Recompute all vertices with a different integer limb width.
    checked=calculate(e,cert['ratio_bits'],cert['mass_bits'],limb_bits=8)
    for key in ('L','B','knots','vertices','lower_bound','proves_capture_one','knots_sha256','lower_grid_sha256'):
        if cert[key]!=checked[key]:raise ValueError('Axis replay mismatch: '+key)
    B,b=F(d['B']),F(e['B']);T=halfangle(B,b)
    assert b*(1+2*T)<=B
    return dict(status='EXACT_NEAR_AXIS_CAPTURE',lemma='PL34 core-inclusion corollary',
                candidate_sha256=hashlib.sha256(original.read_bytes()).hexdigest(),axis_candidate_sha256=sha,
                axis_certificate_sha256=hashlib.sha256(axis_certificate.read_bytes()).hexdigest(),
                L=d['L'],B=str(B),aligned_core=str(b),t_interval=[str(-T),str(T)],
                lower_bound=checked['lower_bound'],proves_capture_one=checked['proves_capture_one'],
                replayed_axis_lower_grid_sha256=checked['lower_grid_sha256'],
                scope='All physical unit-square centres, only the stated half-angle band',
                general_packing_exclusion=False)


if __name__=='__main__':
    p=argparse.ArgumentParser()
    for name in ('original','aligned','axis_certificate','out'):p.add_argument(name,type=Path)
    a=p.parse_args()
    if a.out.exists():raise FileExistsError(a.out)
    result=build(a.original,a.aligned,a.axis_certificate)
    a.out.write_text(json.dumps(result,indent=2));print(result,flush=True)
