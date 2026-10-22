#!/usr/bin/env python3
"""Independent CLOSED intersection evaluator and scaled SPEC section 7 checks.
Runs one Rust worker and one numerical thread. No checker geometry is imported.
"""
import os
for key in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS'):
    os.environ[key]='1'
import argparse, fractions, hashlib, itertools, json, math, pathlib, struct, subprocess, time
import numpy as np
HERE=pathlib.Path(__file__).resolve().parent
BIN='./target/release/m4b-cert1'
TOL=1e-12

def pose(v):
    x,y,z=v[:3]; d=1+x*x+y*y+z*z
    r=np.array([[1+x*x-y*y-z*z,2*(x*y-z),2*(x*z+y)],
                [2*(x*y+z),1+y*y-x*x-z*z,2*(y*z-x)],
                [2*(x*z-y),2*(y*z+x),1+z*z-x*x-y*y]])/d
    h=np.abs(r).sum(axis=1)/2
    return r,h+v[3:]*(3-2*h)

def closed_piece(piece,r,c):
    """H^k of intersection, times exact-double density.
    Lines: six-slab segment clipping. Planes: Sutherland-Hodgman clipping
    of the rectangle against six cube halfplanes in its supporting plane.
    This is the intersection with the cube slice polygon, including its boundary.
    """
    b=np.array(piece['bounds']); free=np.flatnonzero(b[:,0]<b[:,1]); rho=piece['density']
    origin=b[:,0]; a=r.T; rhs=.5+a@c
    a=np.vstack((a,-a)); rhs=np.r_[rhs,.5-r.T@c]
    if len(free)==0:
        return rho if np.all(np.abs(r.T@(origin-c))<=.5+TOL) else 0.
    if len(free)==1:
        w=free[0]; lo,hi=b[w]
        base=origin.copy();base[w]=0
        for row,limit in zip(a,rhs):
            q=limit-row@base; t=row[w]
            if abs(t)<1e-15:
                if q< -TOL:return 0.
            elif t>0:hi=min(hi,q/t)
            else:lo=max(lo,q/t)
        return rho*max(0.,hi-lo)
    u,v=free
    polygon=[np.array([b[u,0],b[v,0]]),np.array([b[u,1],b[v,0]]),np.array([b[u,1],b[v,1]]),np.array([b[u,0],b[v,1]])]
    base=origin.copy();base[free]=0
    for row,limit in zip(a,rhs):
        coeff=row[free]; q=limit-row@base
        if np.linalg.norm(coeff)<1e-15:
            if q< -TOL:return 0.
            continue
        output=[]
        for start,end in zip(polygon,polygon[1:]+polygon[:1]):
            ds=q-coeff@start;de=q-coeff@end
            ins=ds>=0; ine=de>=0
            if ins!=ine:output.append(start+(end-start)*(ds/(ds-de)))
            if ine:output.append(end)
        polygon=output
        if not polygon:return 0.
    area=abs(sum(p[0]*q[1]-p[1]*q[0] for p,q in zip(polygon,polygon[1:]+polygon[:1])))/2
    return rho*area

def closed_mass(pieces,v):
    r,c=pose(v)
    return sum(closed_piece(p,r,c) for p in pieces)

def box(v,radius=0.):
    v=np.asarray(v);lo=v-radius;hi=v+radius
    lo[3:]=np.maximum(0,lo[3:]);hi[3:]=np.minimum(1,hi[3:])
    return [dict(lo=float(a),hi=float(b)) for a,b in zip(lo,hi)]

class Checker:
    def __init__(self,depth):
        self.p=subprocess.Popen([BIN,'--threads','1','--cell-depth',str(depth),'--batch'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,text=True)
    def query(self,b,**kw):
        self.p.stdin.write(json.dumps(dict(box=b,**kw))+'\n');self.p.stdin.flush()
        line=self.p.stdout.readline()
        assert line,'checker terminated'
        return json.loads(line)
    def close(self):
        self.p.stdin.close();assert self.p.wait(timeout=30)==0

def run():
    parser=argparse.ArgumentParser();parser.add_argument('--boxes',type=int,default=400);parser.add_argument('--poses',type=int,default=12);parser.add_argument('--cell-depth',type=int,default=6);args=parser.parse_args()
    os.chdir(HERE);start=time.monotonic();rng=np.random.default_rng(73191)
    data=json.loads(pathlib.Path('../measure.json').read_text());pieces=[p for p in data['pieces'] if p['density']>0]
    info=json.loads(subprocess.check_output([BIN,'--threads','1','--measure-info']))
    assert info['density_bits']==[struct.pack('>d',p['density']).hex() for p in pieces]
    total=fractions.Fraction()
    for p in pieces:
        mass=fractions.Fraction(p['density'])
        for lo,hi in p['bounds']:
            if lo!=hi:mass*=fractions.Fraction(round(10*hi)-round(10*lo),10)
        total+=mass
    assert fractions.Fraction(info['T']['lo'])<=total<=fractions.Fraction(info['T']['hi'])
    assert total*fractions.Fraction(27,20)<info['n_claim']==25
    assert hashlib.sha256(pathlib.Path('../measure.json').read_bytes()).hexdigest()==info['measure_sha256']
    check=Checker(args.cell_depth);failures=[];minimum=math.inf;nonzero=0
    for i in range(args.boxes):
        v=np.r_[rng.uniform(-.4,.4,3),rng.uniform(0,1,3)]
        if i%4==0:v[3+rng.integers(3)]=rng.choice([0.,1.])
        if i%4==1:
            v[:3]=0;v[i%3]=rng.choice([0.,.002,.05,.2,.4]);v[3:]=rng.choice([0.,.2,.25,.45,.5],3)
        b=box(v,10**rng.uniform(-5,-.4)); result=check.query(b);lower=result['lower'];nonzero+=lower>0
        lo=np.array([x['lo'] for x in b]);hi=np.array([x['hi'] for x in b])
        for j in range(args.poses):
            sample=lo+(hi-lo)*rng.random(6)
            actual=1.35*closed_mass(pieces,sample);minimum=min(minimum,actual-lower)
            if actual<lower-TOL:failures.append(dict(test=1,box=b,actual=actual,result=result))
        if time.monotonic()-start>450:raise RuntimeError('validation budget exceeded')
    print('soundness',args.boxes,args.poses,'nonzero',nonzero,'failures',len(failures),flush=True)
    # Each rule tested separately, even if an earlier single rule also holds.
    hits=[0]*6;queries=0
    for i in range(1000):
        v=np.r_[rng.uniform(-.4,.4,3),rng.uniform(0,1,3)]
        p=pieces[i%len(pieces)];bounds=np.array(p['bounds']);y=rng.uniform(bounds[:,0],bounds[:,1]);w=int(np.flatnonzero(bounds[:,0]==bounds[:,1])[0])
        if i%3==0:
            v[:3]=rng.uniform(-.015,.015,3);v[3:]=np.clip((y-.5)/2,0,1)
        if i%3==1:
            v[:3]=0;v[3:]=np.clip((y-.5)/2,0,1);v[3+w]=.5 if y[w]>=1 else 0
        b=box(v,0. if i%3==1 else 1e-5)
        width=np.where(bounds[:,0]<bounds[:,1],.00001,0.)
        cy=[dict(lo=float(a),hi=float(b)) for a,b in zip(y-width,y+width)]
        flags=check.query(b,cell=cy,axis=w)['rules'];queries+=1
        for k,ok in enumerate(flags):
            if not ok:continue
            hits[k]+=1
            for _ in range(4):
                sample=np.array([rng.uniform(q['lo'],q['hi']) for q in b]);pt=y+rng.uniform(-1,1,3)*width;r,c=pose(sample)
                inside=np.max(np.abs(r.T@(pt-c)))<=.5+TOL
                pt[w]+=1
                partner=np.max(np.abs(r.T@(pt-c)))<=.5+TOL
                if not (inside or (k>=4 and partner)):failures.append(dict(test=2,rule=k,box=b,cell=cy))
    print('rules',hits,flush=True)
    assert all(hits),'a rule received no positive tests'
    # Conjugation H R H^T for proper signed permutations maps vector q -> H q.
    # For improper H use -H on quaternion vector; cube axes may be reflected.
    symmetry_errors=[]
    for _ in range(3):
        v=np.r_[rng.uniform(-.3,.3,3),rng.uniform(.05,.95,3)]
        baseline=check.query(box(v),full=True)['lower']
        for perm in itertools.permutations(range(3)):
            for signs in itertools.product([-1,1],repeat=3):
                h=np.eye(3)[list(perm)]*np.array(signs)[:,None]
                q=round(np.linalg.det(h))*h@v[:3];u=np.array([v[3+perm[w]] if signs[w]>0 else 1-v[3+perm[w]] for w in range(3)])
                value=check.query(box(np.r_[q,u]),full=True)['lower'];symmetry_errors.append(abs(value-baseline))
                if abs(value-baseline)>1e-9:failures.append(dict(test=3,error=value-baseline))
    check.close()
    # Symmetry-breaking input mutations must be refused specifically by check 1.
    out=pathlib.Path('validation');out.mkdir(exist_ok=True)
    rejects=[]
    for kind in ('density','bound','removed'):
        changed=json.loads(json.dumps(data));idx=next(i for i,p in enumerate(changed['pieces']) if p['density']>0)
        if kind=='density':changed['pieces'][idx]['density']*=1.01
        if kind=='bound':
            changed['pieces'][idx]['bounds'][0]=[x+.1 for x in changed['pieces'][idx]['bounds'][0]]
        if kind=='removed':changed['pieces'].pop(idx)
        file=out/(kind+'.json');file.write_text(json.dumps(changed))
        result=subprocess.run([BIN,'--threads','1','--measure',str(file),'--measure-info'],capture_output=True,text=True,timeout=30)
        rejects.append(result.returncode!=0 and 'check 1' in result.stderr);file.unlink()
    assert all(rejects)
    # Fixed-round equivalence and stop/resume; strict task limit forbids a 2-thread run.
    import shutil
    for name in ('direct','resumed','repeat'):
        d=out/name
        if d.exists():shutil.rmtree(d)
    def trial(name,rounds,resume=False):
        cmd=[BIN,'--threads','1','--seconds','60','--cell-depth','0','--max-depth','12','--rounds',str(rounds),'--output',str(out/name),'--keep-leaves']
        if resume:cmd+=['--resume']
        subprocess.run(cmd,stdout=subprocess.DEVNULL,check=True,timeout=65)
        return json.loads((out/name/'receipt.json').read_text())
    direct=trial('direct',8);trial('resumed',3);resumed=trial('resumed',5,True);repeat=trial('repeat',8)
    for key in ('boxes','pending','unresolved','leaf_chain','leaf_sha256','closed_volume_fraction','leaves_by_reason'):
        assert direct[key]==resumed[key]==repeat[key],key
    # Clipping regressions: closed point, boundary line and boundary plane all count.
    v=np.array([0.,0.,0.,0.,0.,0.]);r,c=pose(v)
    for p,expected in [(dict(bounds=[[1,1],[1,1],[1,1]],density=2),2),
                       (dict(bounds=[[1,1],[0,1],[1,1]],density=2),2),
                       (dict(bounds=[[1,1],[0,1],[0,1]],density=2),2)]:
        assert abs(closed_piece(p,r,c)-expected)<TOL
    report=dict(status='passed' if not failures else 'failed',boxes=args.boxes,poses_per_box=args.poses,cell_depth=args.cell_depth,nonzero_bounds=nonzero,minimum_margin=minimum,rule_queries=queries,rule_hits=hits,symmetry_images=len(symmetry_errors),max_symmetry_error=max(symmetry_errors),data_mutations_rejected=rejects,exact_total=str(total),thread_count=1,two_thread_test='not run: explicit one-thread resource limit',resume_determinism=True,seconds=time.monotonic()-start,failures=failures)
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2));assert not failures
if __name__=='__main__':run()
