"""Finite near-wall batch separation; rational replay before LP insertion."""
import json,math
from pathlib import Path
from fractions import Fraction as F
import numpy as np
from expanded_search_pilot import ROOT,Geometry,capture
from mixed_density_check import expand,evaluate
from mixed_net_audit import centre_domains


def score(data,poses):
    L,B=float(F(data['L'])),float(F(data['B']))
    rs=np.array([[float(F(x)) for x in r['rectangle']] for r in data['rectangles']]);rw=np.array([float(F(r['mass'])) for r in data['rectangles']])
    ps=np.array([[float(F(x)) for x in p['point']] for p in data['points']]);pw=np.array([float(F(p['mass'])) for p in data['points']])
    g=Geometry(L,B,rs);return np.concatenate([g.matrix(p)@rw+capture(p,L,B,ps,shrink=0)@pw for p in np.array_split(poses,max(1,math.ceil(len(poses)/512)))])


def build():
    root=ROOT/'n21/shared-net-refit-2';out=root/'wall-batch-balanced';out.mkdir(exist_ok=False)
    data={name:json.loads((root/file).read_text()) for name,file in [('fixed_mixed','fixed-candidate.json'),('added_density','mixed-candidate.json')]};models={k:expand(v) for k,v in data.items()}
    L,B=models['fixed_mixed'][:2];domains=centre_domains(L,B);coordinates=[];labels=[]
    # Independent train and validation grids in the required unit-bin domain.
    # A logarithmic inward wall spacing resolves the tiny recurrent hole.
    for split in ('train','held'):
        shift=0 if split=='train' else .5
        for j in (1,2,3):
            e=float(F(domains[j]['centre_high'])-L/2)
            us=(np.arange(161)+shift)/160*.012
            gaps=np.r_[0,np.geomspace(1e-8,.02,25)] if split=='train' else np.geomspace(1.3e-8,.018,26)
            for u in us:
                for gap in gaps:coordinates.append((float(L/2)+u*e,float(L/2)+(1-gap)*e,float(j*F(83,40000))));labels.append(split)
    # Broader patches around all previously found holes, including internal ones.
    old=json.loads((root/'next-pool.json').read_text());seeds=[]
    for w in sorted(old['witnesses'],key=lambda w:min(F(v['score']) for v in w['evaluations'].values())):
        x,y,t=map(lambda k:float(F(w[k])),('cx','cy','t'))
        if any(np.linalg.norm(np.array((x,y,t))-q)<.005 for q in seeds):continue
        seeds.append(np.array((x,y,t)))
        if len(seeds)==12:break
    for x,y,t in seeds:
        radius=float(B)*(1+2*t-t*t)/(2*(1+t*t))
        for dx in (-.005,-.001,-.0001,0,.0001,.001,.005):
            for dy in (-.005,-.001,-.0001,0,.0001,.001,.005):
                coordinates.append((min(float(L)-radius,max(radius,x+dx)),min(float(L)-radius,max(radius,y+dy)),t));labels.append('train')
    coordinates=np.array(coordinates);labels=np.array(labels)
    def normalized(xyz):
        x,y,t=xyz.T;c=(1-t*t)/(1+t*t);s=2*t/(1+t*t);reach=(float(L)-float(B)*(c+s))/2
        return np.c_[(x-float(L)/2)/reach,(y-float(L)/2)/reach,2*np.arctan(t)/(np.pi/4)]
    poses=normalized(coordinates);values={name:score(d,poses) for name,d in data.items()}
    pool=list(old['witnesses']);selected=[];exact=[]
    worst=np.minimum(*values.values());train=np.flatnonzero(labels=='train')
    wall=train[coordinates[train,2]<.01];interior=train[coordinates[train,2]>=.01]
    queues=[list(a[np.argsort(worst[a])]) for a in (wall,interior)]
    ordered=[a[k] for k in range(max(map(len,queues))) for a in queues if k<len(a)]
    for i in ordered:
        if len(selected)>=64:break
        if worst[i]>=1.0001:continue
        if any(np.linalg.norm(coordinates[i]-coordinates[j])<2e-5 for j in selected):continue
        x,y,t=(F(float(v)).limit_denominator(10**10) for v in coordinates[i]);reach=(L-B*(1+2*t-t*t)/(1+t*t))/2
        # Rounded exploratory poses can be infinitesimally outside; skip them.
        try:checks={name:evaluate(m,x,y,t) for name,m in models.items()}
        except ValueError:continue
        if min(F(w['score']) for w in checks.values())>=F(10001,10000):continue
        w=dict(cx=str(x),cy=str(y),t=str(t),normalized_pose=[float((x-L/2)/reach),float((y-L/2)/reach),2*math.atan(float(t))/(math.pi/4)],evaluations=checks,sources=[dict(kind='wall_batch',candidate_digest=m[-1],candidate=name) for name,m in models.items()])
        selected.append(int(i));exact.append(w);pool.append(w)
    np.savez_compressed(out/'probe.npz',coordinates=coordinates,poses=poses,labels=labels,selected=selected,**{'before_'+k:v for k,v in values.items()})
    result=dict(count=len(pool),previous_count=len(old['witnesses']),new_exact_count=len(exact),witnesses=pool,probe_counts={k:int(sum(labels==k)) for k in ('train','held')},before={name:{part:dict(minimum=float(v[labels==part].min()),below_one=int(sum(v[labels==part]<1))) for part in ('train','held')} for name,v in values.items()})
    (out/'pool.json').write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items() if k!='witnesses'}),flush=True)
if __name__=='__main__':build()
