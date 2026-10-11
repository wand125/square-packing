"""Independent vertex SAT and rational rotation certificate checker; stdlib only."""
import argparse
from fractions import Fraction as Q
import itertools
import json
import math
from pathlib import Path


def vertices(x, y, c, s):
    return [(x+(p*c-q*s)/2, y+(p*s+q*c)/2) for p, q in [(-1,-1),(1,-1),(1,1),(-1,1)]]


def inspect(a, b, objects):
    """Input objects: (vertices, axes). Works with floats or exact Fractions."""
    wall = max([0] + [max(-x, x-b, -y, y-a) for vs,_ in objects for x,y in vs])
    pair_gaps=[]
    separators=[]
    for i,j in itertools.combinations(range(len(objects)),2):
        vi,ai=objects[i]; vj,aj=objects[j]
        gaps=[]
        for ax,ay in ai+aj:
            pi=[x*ax+y*ay for x,y in vi]; pj=[x*ax+y*ay for x,y in vj]
            gaps.append(max(min(pj)-max(pi),min(pi)-max(pj)))
        gap=max(gaps)
        pair_gaps.append(gap)
        separators.append({'i':i,'j':j,'axis':gaps.index(gap),'gap':str(gap)})
    return wall,max([0]+[-g for g in pair_gaps]),min(pair_gaps,default=None),separators


def numeric(data, tolerance=1e-10):
    a,b,n=data['a'],data['b'],data['n']; poses=data['poses']
    if not isinstance(n,int) or n<1 or len(poses)!=n or not all(len(p)==3 for p in poses):
        raise ValueError('invalid pose count')
    if not all(math.isfinite(v) for v in [a,b,*sum(poses,[])]) or min(a,b)<=0:
        raise ValueError('nonfinite or invalid dimensions')
    objects=[]
    for x,y,t in poses:
        c,s=math.cos(t),math.sin(t)
        objects.append((vertices(x,y,c,s),[(c,s),(-s,c)]))
    wall,overlap,gap,_=inspect(a,b,objects)
    xs=[x for vs,_ in objects for x,y in vs]; ys=[y for vs,_ in objects for x,y in vs]
    scale=max((max(xs)-min(xs))/b,(max(ys)-min(ys))/a)
    return {'numeric_feasible':wall<=tolerance and overlap<=tolerance and scale<=1+tolerance,
            'required_scale':scale,
            'tolerance':tolerance,'max_wall_violation':wall,'max_overlap':overlap,
            'min_pair_gap':gap,'checker':'independent_vertex_sat_float','exact_verified':False}


def exact(cert):
    if cert.get('schema')!='rational-unit-square-v1':
        raise ValueError('unknown certificate schema')
    a,b=Q(cert['a']),Q(cert['b']); n=cert['n']
    if min(a,b)<=0 or not isinstance(n,int) or n<1 or len(cert['squares'])!=n:
        raise ValueError('invalid exact metadata')
    objects=[]
    for p in cert['squares']:
        x,y,t=Q(p['x']),Q(p['y']),Q(p['tan_half_angle'])
        c,s=(1-t*t)/(1+t*t),2*t/(1+t*t)
        if c*c+s*s!=1:raise ValueError('non-unit rotation')
        objects.append((vertices(x,y,c,s),[(c,s),(-s,c)]))
    wall,overlap,gap,separators=inspect(a,b,objects)
    return {'exact_verified':wall==0 and overlap==0,'max_wall_violation':str(wall),
            'max_overlap':str(overlap),'min_pair_gap':str(gap),
            'checker':'independent_vertex_sat_fraction','separators':separators}


def certify(data):
    """Try rational reconstruction; exact() alone decides acceptance, never rounding."""
    for factor in [1.0,1.0+1e-10,1.0+1e-8,1.0+1e-6,1.0+1e-5]:
        cert={'schema':'rational-unit-square-v1','a':str(data['a']),'b':str(data['b']),
              'n':data['n'],'squares':[], 'reconstruction':{'center_expansion':factor,'decimal_digits':15}}
        for x,y,t in data['poses']:
            t=(t+math.pi/4)%(math.pi/2)-math.pi/4
            x=data['b']/2+(x-data['b']/2)*factor
            y=data['a']/2+(y-data['a']/2)*factor
            cert['squares'].append({'x':f'{x:.15f}','y':f'{y:.15f}',
                                   'tan_half_angle':f'{math.tan(t/2):.15f}'})
        result=exact(cert)
        if result['exact_verified']:
            cert['verification']=result
            return cert
    return None


def svg(data, dest):
    a,b=data['a'],data['b']; pad=.3; scale=140
    parts=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{(b+2*pad)*scale:.0f}" height="{(a+2*pad)*scale+65:.0f}" viewBox="{-pad} {-pad} {b+2*pad} {a+2*pad+65/scale}">',
           '<rect x="-0.3" y="-0.3" width="100%" height="100%" fill="#f7f8fc"/>',
           f'<rect width="{b}" height="{a}" fill="white" stroke="#172033" stroke-width=".015"/>']
    for i,(x,y,t) in enumerate(data['poses']):
        vs=vertices(x,y,math.cos(t),math.sin(t)); points=' '.join(f'{u:.12f},{a-v:.12f}' for u,v in vs)
        parts.append(f'<polygon points="{points}" fill="hsl({(i*43)%360},65%,72%)" fill-opacity=".8" stroke="#22334d" stroke-width=".008"/>')
        parts.append(f'<text x="{x}" y="{a-y+.04}" text-anchor="middle" font-family="sans-serif" font-size=".12">{i+1}</text>')
    label=f"a={a}, b={b}, n={data['n']} | {data.get('status','numerical_candidate')}"
    parts.append(f'<text x="0" y="{a+.24}" font-family="sans-serif" font-size=".12">{label}</text></svg>')
    Path(dest).write_text('\n'.join(parts))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('file');parser.add_argument('--exact',action='store_true')
    args=parser.parse_args();data=json.loads(Path(args.file).read_text())
    result=exact(data) if args.exact else numeric(data)
    print(json.dumps(result,indent=2));raise SystemExit(0 if result.get('exact_verified') or result.get('numeric_feasible') else 1)

# Certificate binding used by the local-improvement campaign and the viewer dataset.
def candidate_digest(data):
    import hashlib
    payload={k:data[k] for k in ('a','b','n','poses')}
    for k in ('a_exact','b_exact'):
        if k in data:payload[k]=str(Q(data[k]))
    return hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def bound_exact(cert,data):
    if Q(cert['a'])!=Q(data.get('a_exact',str(data['a']))) or Q(cert['b'])!=Q(data.get('b_exact',str(data['b']))) or cert['n']!=data['n']:
        raise ValueError('certificate target mismatch')
    if cert.get('source_candidate_sha256')!=candidate_digest(data):
        raise ValueError('certificate source mismatch')
    return exact(cert)


def bound_certify(data):
    cert=certify(data)
    if cert:
        cert['source_candidate_sha256']=candidate_digest(data)
        if not bound_exact(cert,data)['exact_verified']:raise ValueError('reconstructed certificate failed')
    return cert


def certificate_poses(cert):
    poses=[]
    for p in cert['squares']:
        t=Q(p['tan_half_angle']);c,s=(1-t*t)/(1+t*t),2*t/(1+t*t)
        poses.append([float(Q(p['x'])),float(Q(p['y'])),math.atan2(float(s),float(c))])
    return poses
