"""Bounded, outward-rounded mixed verification at nonzero proof-net angles.

C++ inherits the inscribed-polygon and density-derivative bounds from the
frozen rectangle verifier. Atomic contributions require capture throughout
an entire centre cell. UNRESOLVED frontiers are saved, never certified.
"""
from fractions import Fraction as F
from pathlib import Path
import argparse, hashlib, json, math, subprocess
from mixed_density_check import expand, evaluate
from mixed_net_audit import symmetry, net_certificate, centre_domains, candidate_net

SOURCE=Path(__file__).with_suffix('.cpp')


def interval(value):
    value=F(value);v=float(value)
    if not math.isfinite(v):raise ValueError('Non-finite interval')
    lo=math.nextafter(v,-math.inf) if F(v)>value else v
    hi=math.nextafter(v,math.inf) if F(v)<value else v
    assert F(lo)<=value<=F(hi)
    return f'{lo.hex()} {hi.hex()}'


def compile_verifier(binary):
    subprocess.run(['c++','-O2','-std=c++17','-ffp-contract=off','-fno-fast-math',str(SOURCE),str('-o'),str(binary)],check=True)


def export(model,index,path,gamma=F(10001,10000),net=None):
    step,last=net or (F(83,40000),200)
    if not 1<=index<=last:raise ValueError('Net index outside declared range')
    symmetry(model);net_certificate(model[1],step,last);L,B,rs,ps,total,digest=model
    if gamma<1:raise ValueError('This runner requires Gamma >= 1 with budget < n')
    domain=centre_domains(L,B,step,last)[index];E=F(domain['centre_high'])-L/2
    t=index*step;c=(1-t*t)/(1+t*t);s=2*t/(1+t*t)
    lines=[interval(v) for v in (L,B,E,c,s,gamma)]+[str(len(rs))]
    lines += [' '.join(interval(v) for v in r) for r in rs]
    lines += [str(len(ps))]+[' '.join(interval(v) for v in (*p,w)) for p,w in ps]
    path.write_text('\n'.join(lines)+'\n')
    return dict(candidate_digest=digest,net_index=index,t=str(t),gamma=str(gamma),domain=domain,
                E=str(E),source_sha256=hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
                input_sha256=hashlib.sha256(path.read_bytes()).hexdigest())


def query(binary,path,cells):
    data=''.join('0 '+' '.join(interval(v) for v in cell)+'\n' for cell in cells)
    p=subprocess.run([str(binary),str(path),'query'],input=data,text=True,capture_output=True,check=True)
    values=[F(float(x)) for x in p.stdout.splitlines()]
    assert len(values)==len(cells)
    return values


def run(candidate,index,out,binary,nodes=2000,gamma=F(10001,10000)):
    out.mkdir(parents=True,exist_ok=False)
    data=json.loads(candidate.read_text());model=expand(data);manifest=export(model,index,out/'input.txt',gamma,candidate_net(data))
    p=subprocess.run([str(binary),str(out/'input.txt'),str(nodes)],text=True,capture_output=True,check=True)
    result=json.loads(p.stdout);result['manifest']=manifest;result['candidate']=str(candidate)
    # Sample across the saved frontier using exact rational clipping.
    # A lower bound below Gamma alone is never evidence of an actual deficit.
    witnesses=[];L=model[0];E=F(manifest['E']);t=F(manifest['t'])
    frontier=result['frontier']
    indices=sorted(set(round(i*(len(frontier)-1)/min(63,len(frontier)-1)) for i in range(min(64,len(frontier))))) if len(frontier)>1 else range(len(frontier))
    for i in indices:
        z=frontier[i]
        x,y=(L/2+F(z[i])*E for i in (0,1))
        w=evaluate(model,x,y,t)
        if F(w['score'])<F(manifest['gamma']):witnesses.append(w)
    result['exact_witnesses']=witnesses
    result['frontier_area_fraction']=str(sum((4*F(z[2])*F(z[3]) for z in frontier),F(0)))
    if witnesses:result['status']='ANGLE_BELOW_GAMMA'
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--candidate',type=Path,required=True);p.add_argument('--index',type=int,required=True)
    p.add_argument('--out',type=Path,required=True);p.add_argument('--binary',type=Path,default=Path('/tmp/mixed_rotated_verify'))
    p.add_argument('--gamma',type=F,default=F(10001,10000));p.add_argument('--nodes',type=int,default=2000);a=p.parse_args();compile_verifier(a.binary)
    r=run(a.candidate,a.index,a.out,a.binary,a.nodes,a.gamma)
    print(json.dumps({k:v for k,v in r.items() if k not in ('frontier','manifest','exact_witnesses')},indent=2))
