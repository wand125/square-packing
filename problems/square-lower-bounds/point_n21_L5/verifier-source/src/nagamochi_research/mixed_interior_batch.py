"""Stratified interior-patch separation with held-out probes and exact replay."""
import json,math
from fractions import Fraction as F
import numpy as np
from expanded_search_pilot import ROOT
from mixed_wall_batch import score
from mixed_density_check import expand,evaluate
from mixed_net_audit import centre_domains


def main():
    root=ROOT/'n21/shared-net-refit-3-batch';out=root/'interior-batch';out.mkdir(exist_ok=False)
    data={name:json.loads((root/file).read_text()) for name,file in [('fixed_mixed','fixed-candidate.json'),('added_density','mixed-candidate.json')]};models={k:expand(v) for k,v in data.items()}
    L,B=models['fixed_mixed'][:2];domains=centre_domains(L,B);old=json.loads((root/'next-pool.json').read_text());coords=[];labels=[];groups=[]
    for j in (1,2,3):
        E=float(F(domains[j]['centre_high'])-L/2)
        for part,count,shift in [('train',65,0),('held',64,.5)]:
            grid=.484375+(np.arange(count)+shift)/64*.03125
            for u in grid:
                for v in grid:coords.append((float(L/2)+u*E,float(L/2)+v*E,float(j*F(83,40000))));labels.append(part);groups.append(j)
    seeds=[]
    for w in sorted(old['witnesses'],key=lambda w:min(F(e['score']) for e in w['evaluations'].values())):
        xyz=np.array([float(F(w[k])) for k in ('cx','cy','t')])
        if any(np.linalg.norm(xyz-q)<.02 for q in seeds):continue
        seeds.append(xyz)
        if len(seeds)==10:break
    for i,(x,y,t) in enumerate(seeds):
        for dt in (-float(F(83,160000)),0,float(F(83,160000))):
            tt=max(0,min(math.sqrt(2)-1,t+dt));radius=float(B)*(1+2*tt-tt*tt)/(2*(1+tt*tt))
            for dx in (-.01,-.004,-.001,-.0001,0,.0001,.001,.004,.01):
                for dy in (-.01,-.004,-.001,-.0001,0,.0001,.001,.004,.01):
                    coords.append((max(radius,min(float(L)-radius,x+dx)),max(radius,min(float(L)-radius,y+dy)),tt));labels.append('train');groups.append(4+i)
    coords=np.array(coords);labels=np.array(labels);groups=np.array(groups);x,y,t=coords.T;reach=(float(L)-float(B)*(1+2*t-t*t)/(1+t*t))/2
    poses=np.c_[(x-float(L/2))/reach,(y-float(L/2))/reach,2*np.arctan(t)/(np.pi/4)]
    clipped=np.clip(poses,[-1,-1,0],[1,1,1]);assert np.max(abs(clipped-poses))<1e-12;poses=clipped
    values={k:score(v,poses) for k,v in data.items()};worst=np.minimum(*values.values())
    queues=[]
    for g in sorted(set(groups)):
        ids=np.flatnonzero((labels=='train')&(groups==g)&(worst<1.0001));queues.append(list(ids[np.argsort(worst[ids])]))
    selected=[];pool=list(old['witnesses'])
    for k in range(max(map(len,queues))):
        for queue in queues:
            if k>=len(queue) or len(selected)>=128:continue
            i=queue[k]
            if any(np.linalg.norm(coords[i]-coords[j])<.0001 for j in selected):continue
            x,y,t=[F(float(v)).limit_denominator(10**10) for v in coords[i]]
            try:checks={name:evaluate(m,x,y,t) for name,m in models.items()}
            except ValueError:continue
            if min(F(w['score']) for w in checks.values())>=F(10001,10000):continue
            reach=(L-B*(1+2*t-t*t)/(1+t*t))/2
            pool.append(dict(cx=str(x),cy=str(y),t=str(t),normalized_pose=[float((x-L/2)/reach),float((y-L/2)/reach),2*math.atan(float(t))/(math.pi/4)],evaluations=checks,sources=[dict(kind='interior_batch',group=int(groups[i]))]));selected.append(int(i))
        if len(selected)>=128:break
    np.savez_compressed(out/'probe.npz',coordinates=coords,poses=poses,labels=labels,groups=groups,selected=selected,**{'before_'+k:v for k,v in values.items()})
    result=dict(count=len(pool),previous_count=len(old['witnesses']),new_exact_count=len(selected),selected_groups={str(g):int(sum(groups[selected]==g)) for g in set(groups)},witnesses=pool,before={name:{part:dict(minimum=float(v[labels==part].min()),below_one=int(sum(v[labels==part]<1))) for part in ('train','held')} for name,v in values.items()})
    (out/'pool.json').write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items() if k!='witnesses'}),flush=True)
if __name__=='__main__':main()
