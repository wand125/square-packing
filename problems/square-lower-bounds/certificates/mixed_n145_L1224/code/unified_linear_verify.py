"""Experimental outward-rounded verifier for ONE net angle of a linear measure.

Points, arbitrary straight segments and axis-aligned rectangles are supported.
A single ANGLE_VERIFIED result is never a whole-packing certificate.
"""
import argparse,hashlib,json,subprocess
from pathlib import Path
from fractions import Fraction as F
from unified_measure import SCHEMA,validate,net_check,region,score_bounds
from mixed_rotated_verify import interval
SOURCE=Path(__file__).with_suffix('.cpp')


def compile_verifier(binary):
    subprocess.run(['c++','-O2','-std=c++17','-ffp-contract=off','-fno-fast-math',str(SOURCE),'-o',str(binary)],check=True)


def export(data,index,path):
    if data['schema']!=SCHEMA:raise ValueError('linear square-core measure required')
    L,B,n,expanded,mass,digest=validate(data);step,last=net_check(data)
    if not 0<mass<n or isinstance(index,bool) or not isinstance(index,int) or not 0<=index<=last:raise ValueError('budget/index')
    t=step*index;c=(1-t*t)/(1+t*t);s=2*t/(1+t*t);E=(L-B*(c+s))/2
    if E<=0:raise ValueError('empty centre domain')
    rects=[];points=[];segments=[]
    for kind,g,w in expanded:
        if kind=='rectangle':rects.append((*g,w/((g[2]-g[0])*(g[3]-g[1]))))
        elif kind=='point':points.append((*g,w))
        elif kind=='segment':segments.append((*g,w))
        else:raise ValueError('unsupported shape')
    lines=[interval(x) for x in (L,B,E,c,s,F(1))]
    for entries in (rects,points,segments):
        lines.append(str(len(entries)));lines.extend(' '.join(interval(x) for x in row) for row in entries)
    path.write_text('\n'.join(lines)+'\n')
    return dict(candidate_digest=digest,index=index,t=str(t),L=str(L),B=str(B),E=str(E),gamma='1',mass=str(mass),
                source_sha256=hashlib.sha256(SOURCE.read_bytes()).hexdigest(),input_sha256=hashlib.sha256(path.read_bytes()).hexdigest())


def run(candidate,index,out,binary,nodes=300000):
    out.mkdir(parents=True,exist_ok=False);data=json.loads(candidate.read_text());manifest=export(data,index,out/'input.txt')
    (out/'candidate.json').write_text(json.dumps(data,indent=2)+'\n');(out/'verify.cpp').write_bytes(SOURCE.read_bytes())
    r=subprocess.run([str(binary),str(out/'input.txt'),str(nodes)],text=True,capture_output=True,check=True)
    result=json.loads(r.stdout);result.update(manifest=manifest,scope='ONE_NET_ANGLE_ONLY',globally_verified=False)
    L,B,n,expanded,mass,digest=validate(data);E=F(manifest['E']);t=F(manifest['t']);witnesses=[]
    frontier=result['frontier'];ids=sorted(set(round(i*(len(frontier)-1)/7) for i in range(8))) if frontier else []
    for i in ids:
        x,y=(L/2+F(frontier[i][j])*E for j in (0,1));lo,hi=score_bounds(expanded,region(t,(x,x,y,y),B))
        if hi<1:witnesses.append(dict(cx=str(x),cy=str(y),t=str(t),mass=str(hi)))
    result['exact_witnesses']=witnesses
    if witnesses:result['status']='ANGLE_BELOW_GAMMA'
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');return result


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--candidate',type=Path,required=True);p.add_argument('--index',type=int,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--binary',type=Path,required=True);p.add_argument('--nodes',type=int,default=300000);a=p.parse_args();compile_verifier(a.binary)
    r=run(a.candidate,a.index,a.out,a.binary,a.nodes);print(json.dumps({k:v for k,v in r.items() if k not in ('frontier','exact_witnesses')},indent=2),flush=True)
