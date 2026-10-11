"""Independent exact vertex SAT with rational AABB rejection for larger packings.

No floating bounds enter the oracle. AABB separation is itself an exact separating
axis proof. Remaining pairs use each square's two exact edge-normal axes.
"""
from fractions import Fraction as F
import math
from verify import vertices, candidate_digest

def exact(cert):
    if cert.get('schema') != 'rational-unit-square-v1':raise ValueError('unknown certificate schema')
    a,b=F(cert['a']),F(cert['b']);n=cert['n']
    if min(a,b)<=0 or type(n) is not int or n<1 or len(cert['squares'])!=n:raise ValueError('invalid exact metadata')
    objects=[]
    for p in cert['squares']:
        t=F(p['tan_half_angle']);c,s=(1-t*t)/(1+t*t),2*t/(1+t*t)
        if c*c+s*s!=1:raise ValueError('non-unit rotation')
        vs=vertices(F(p['x']),F(p['y']),c,s)
        box=min(x for x,y in vs),max(x for x,y in vs),min(y for x,y in vs),max(y for x,y in vs)
        if box[0]<0 or box[1]>b or box[2]<0 or box[3]>a:
            return {'exact_verified':False,'reason':'wall_violation'}
        objects.append((vs,((c,s),(-s,c)),box))
    count=coarse=0
    for i,(vi,ai,bi) in enumerate(objects):
        for vj,aj,bj in objects[i+1:]:
            count+=1
            if bi[1]<=bj[0] or bj[1]<=bi[0] or bi[3]<=bj[2] or bj[3]<=bi[2]:coarse+=1;continue
            for ux,uy in ai+aj:
                pi=[x*ux+y*uy for x,y in vi];pj=[x*ux+y*uy for x,y in vj]
                if max(pi)<=min(pj) or max(pj)<=min(pi):break
            else:return {'exact_verified':False,'reason':'interior_overlap','pairs_checked':count}
    return dict(exact_verified=True,checker='independent_vertex_sat_fraction_aabb_v1',
                max_wall_violation='0',max_overlap='0',pairs_checked=count,
                aabb_separated=coarse,sat_separated=count-coarse,unit_edges=True,boundary_contact_allowed=True)

def bound_exact(cert,data):
    if (F(cert['a']),F(cert['b']),cert['n'])!=(F(data.get('a_exact',str(data['a']))),F(data.get('b_exact',str(data['b']))),data['n']):raise ValueError('certificate target mismatch')
    if cert.get('source_candidate_sha256')!=candidate_digest(data):raise ValueError('certificate source mismatch')
    return exact(cert)

def bound_certify(data):
    for factor in (1.,1.+1e-10,1.+1e-8,1.+1e-6,1.+1e-5):
        cert=dict(schema='rational-unit-square-v1',a=str(data.get('a_exact',data['a'])),
                  b=str(data.get('b_exact',data['b'])),n=data['n'],squares=[],
                  reconstruction=dict(center_expansion=factor,decimal_digits=15))
        for x,y,theta in data['poses']:
            theta=(theta+math.pi/4)%(math.pi/2)-math.pi/4
            cert['squares'].append(dict(x=f"{data['b']/2+(x-data['b']/2)*factor:.15f}",
                 y=f"{data['a']/2+(y-data['a']/2)*factor:.15f}",tan_half_angle=f'{math.tan(theta/2):.15f}'))
        check=exact(cert)
        if check['exact_verified']:
            cert['verification']=check;cert['source_candidate_sha256']=candidate_digest(data)
            return cert
    return None

def numeric(data,tolerance=1e-10):
    a,b,n=data['a'],data['b'],data['n'];poses=data['poses']
    if type(n) is not int or n<1 or len(poses)!=n or any(len(p)!=3 for p in poses):raise ValueError('invalid pose count')
    if min(a,b)<=0 or not all(math.isfinite(v) for v in (a,b,*[v for p in poses for v in p])):raise ValueError('invalid float geometry')
    objects=[];wall=overlap=0.
    for x,y,t in poses:
        c,s=math.cos(t),math.sin(t);vs=vertices(x,y,c,s)
        box=min(x for x,y in vs),max(x for x,y in vs),min(y for x,y in vs),max(y for x,y in vs)
        wall=max(wall,-box[0],box[1]-b,-box[2],box[3]-a)
        objects.append((vs,((c,s),(-s,c)),box))
    for i,(vi,ai,bi) in enumerate(objects):
        for vj,aj,bj in objects[i+1:]:
            if bi[1]<=bj[0] or bj[1]<=bi[0] or bi[3]<=bj[2] or bj[3]<=bi[2]:continue
            gaps=[]
            for ux,uy in ai+aj:
                pi=[x*ux+y*uy for x,y in vi];pj=[x*ux+y*uy for x,y in vj]
                gaps.append(max(min(pj)-max(pi),min(pi)-max(pj)))
            overlap=max(overlap,-max(gaps))
    boxes=[o[2] for o in objects]
    scale=max((max(q[1] for q in boxes)-min(q[0] for q in boxes))/b,(max(q[3] for q in boxes)-min(q[2] for q in boxes))/a)
    return dict(numeric_feasible=wall<=tolerance and overlap<=tolerance and scale<=1+tolerance,
        required_scale=scale,tolerance=tolerance,max_wall_violation=wall,max_overlap=overlap,
        checker='independent_vertex_sat_float_aabb_v1',exact_verified=False)
