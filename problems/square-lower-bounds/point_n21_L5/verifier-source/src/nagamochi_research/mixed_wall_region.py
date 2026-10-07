"""Strict continuous check of a small wall rectangle, never a whole angle."""
from fractions import Fraction as F
from pathlib import Path
import json,subprocess
from mixed_density_check import expand
from mixed_rotated_verify import compile_verifier,export
from expanded_search_pilot import ROOT


def verify(candidate,index,out,binary,nodes=100000,box=None):
    out.mkdir(parents=True,exist_ok=False);model=expand(json.loads(candidate.read_text()));manifest=export(model,index,out/'input.txt')
    # Dyadic roots avoid decimal root rounding and cover [0,1/64] x [63/64,1].
    wall=box is None
    box=tuple(map(F,box)) if box is not None else (F(1,128),F(127,128),F(1,128),F(1,128))
    assert all(F(float(v))==v for v in box), 'Root cell must be exactly representable'
    u,v,du,dv=box
    assert du>0 and dv>0 and 0<=u-du<u+du<=1 and 0<=v-dv<v+dv<=1
    (out/'region.txt').write_text(' '.join(float(v).hex() for v in box))
    manifest['scope']='WALL_REGION_ONLY_NOT_WHOLE_ANGLE' if wall else 'CENTRE_REGION_ONLY_NOT_WHOLE_ANGLE'
    manifest['normalized_rectangle']=list(map(str,(u-du,u+du,v-dv,v+dv)))
    E=F(manifest['E']);L=model[0]
    manifest['absolute_rectangle']=list(map(str,(L/2+(u-du)*E,L/2+(u+du)*E,L/2+(v-dv)*E,L/2+(v+dv)*E)))
    result=json.loads(subprocess.check_output([str(binary),str(out/'input.txt'),str(nodes),str(out/'region.txt')],text=True))
    result['manifest']=manifest;(out/'result.json').write_text(json.dumps(result,indent=2));return result


def main():
    root=ROOT/'n21/shared-net-refit-3-batch';binary=Path('/tmp/mixed-wall-region');compile_verifier(binary)
    for name,file in [('fixed_mixed','fixed-candidate.json'),('added_density','mixed-candidate.json')]:
        for index in (1,2,3):
            r=verify(root/file,index,root/'wall-regions'/name/str(index),binary)
            print(json.dumps(dict(candidate=name,index=index,**{k:r[k] for k in ('status','nodes','leaves','lower','seconds')})),flush=True)
if __name__=='__main__':main()
