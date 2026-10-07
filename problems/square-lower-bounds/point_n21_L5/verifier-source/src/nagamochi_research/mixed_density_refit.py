"""Add exact new-pose witnesses to both models, repair saved-row violations."""
import json,argparse
from pathlib import Path
from fractions import Fraction as F
from time import perf_counter
import numpy as np
from expanded_search_pilot import ROOT,load,Geometry,columns,capture,solve
from mixed_density_check import expand,evaluate


def export(out,d,rects,weights,mapping):
    r=len(rects);pointweights={}
    for w,orbit in zip(weights[r:],mapping['point_orbits']):
        if w:
            for i in orbit:
                p=tuple(map(str,mapping['points'][i]));pointweights[p]=pointweights.get(p,F(0))+F(str(w))/8
    rr=[dict(rectangle=[str(F(str(v))) for v in row],mass=str(F(str(w)))) for row,w in zip(rects,weights[:r]) if w]
    total=sum(F(v['mass']) for v in rr)+sum(pointweights.values())
    candidate=dict(status='RESEARCH_CANDIDATE_NOT_CERTIFIED',n=d.get('n',21),L=str(F(str(d['L']))),B=str(F(str(d['B']))),rectangles=rr,points=[dict(point=p,mass=str(w)) for p,w in sorted(pointweights.items())],total_mass=str(total),rectangle_semantics='Each basis mass averages 8 D4 uniform densities.')
    if 'proof_net' in d:candidate['proof_net']=d['proof_net']
    expand(candidate);out.write_text(json.dumps(candidate,indent=2));return candidate


def run(previous=None,separation=None,output=None):
    start=perf_counter();root=ROOT/'n21';out=Path(output) if output else root/'exact-refit';out.mkdir(exist_ok=True);assert not list(out.iterdir())
    d=json.loads((root/'results.json').read_text());sep=json.loads(Path(separation or root/'new-separation.json').read_text());previous=Path(previous) if previous else None
    old=expand(json.loads(((previous if previous else root)/'mixed-candidate.json').read_text()))
    for w in sep['witnesses']:
        assert w['candidate_digest']==old[-1]
        checked=evaluate(old,F(w['cx']),F(w['cy']),F(w['t']))
        assert checked['score']==w['score'] and F(w['score'])<1
    _,rects,saved,L,B,rhs,_=load(21);r=len(rects);p=d['point_columns'];rules=d['rules']
    for rule in rules:rule['sites']=[tuple(map(F,q)) for q in rule['sites']]
    new=np.array([w['normalized_pose'] for w in sep['witnesses']]);projected=np.clip(new,[-1,-1,0],[1,1,1]);projection_error=float(np.max(np.abs(new-projected)));assert projection_error<1e-10;new=projected
    if previous:
        prior=np.load(previous/'replay.npz')
        if (previous/'cumulative-witnesses.json').exists():
            cumulative=json.loads((previous/'cumulative-witnesses.json').read_text())
        else:
            cumulative=json.loads((root/'new-separation.json').read_text())['witnesses']
        historical=np.clip(np.array([w['normalized_pose'] for w in cumulative]),[-1,-1,0],[1,1,1])
        saved=np.vstack([saved,historical])
    else:
        prior=np.load(root/'repair3-replay.npz');cumulative=[]
    allposes=np.vstack([saved,new]);ids=prior['row_ids'].tolist()+list(range(len(saved),len(allposes)))
    cumulative+=sep['witnesses']
    def block(ps):
        pc,_,mapping=columns(ps,rules,L,B)
        return np.hstack([Geometry(L,B,rects).matrix(ps),pc]),mapping
    extra,mapping=block(new);a=np.vstack([prior['matrix'][:,:r+p],extra]);records=[];weights={};coverages={}
    def audit(w):
        active=np.flatnonzero(w[:r]>0);v=[];activep=np.flatnonzero(w[r:]>0)
        unique=sorted({i for j in activep for i in mapping['point_orbits'][j]});lookup={i:j for j,i in enumerate(unique)}
        for lo in range(0,len(allposes),1024):
            ps=allposes[lo:lo+1024];value=Geometry(L,B,rects[active]).matrix(ps)@w[active]
            if len(unique):
                hits=capture(ps,L,B,np.array([mapping['points'][i] for i in unique],float))
                for j in activep:value+=w[r+j]*hits[:,[lookup[i] for i in mapping['point_orbits'][j]]].mean(axis=1)
            v.extend(value)
        return np.array(v)
    for iteration in range(5):
        bad=set();record=dict(iteration=iteration,rows=len(a),models={})
        for name,end in [('rectangles',r),('mixed',r+p)]:
            fit,stat=solve(a[:,:end],rhs);weights[name]=fit.x;v=audit(fit.x);coverages[name]=v
            violated=np.flatnonzero(v<rhs-1e-8);bad.update(violated.tolist())
            stat.update(full_saved_and_new_minimum=float(v.min()),violations_1e8=len(violated),point_mass=float(sum(fit.x[r:])))
            record['models'][name]=stat
        records.append(record);print(json.dumps(record),flush=True)
        if not bad:break
        extraids=sorted(bad-set(ids))
        if not extraids or iteration==4:break
        more,_=block(allposes[extraids]);a=np.vstack([a,more]);ids+=extraids
    candidate=export(out/'mixed-candidate.json',d,rects,weights['mixed'],mapping);model=expand(candidate)
    rechecks=[evaluate(model,F(w['cx']),F(w['cy']),F(w['t'])) for w in cumulative]
    (out/'cumulative-witnesses.json').write_text(json.dumps(cumulative,indent=2))
    np.savez_compressed(out/'replay.npz',matrix=a,row_ids=ids,rectangles=rects,**{'weights_'+k:v for k,v in weights.items()},**{'coverage_'+k:v for k,v in coverages.items()})
    result=dict(cumulative_exact_witnesses=len(cumulative),source_previous=str(previous),source_separation=str(separation),normalized_boundary_projection_error=projection_error,status='FINITE_REPAIRED_NOT_CERTIFIED' if all(v['violations_1e8']==0 for v in records[-1]['models'].values()) and all(F(v['score'])>=1 for v in rechecks) else 'REPAIR_INCOMPLETE',exact_input_witnesses=len(new),records=records,rechecked_exact_witnesses=rechecks,seconds=perf_counter()-start,budget=str(model[-2]),digest=model[-1],scope='Full saved rows and all cumulative exact witnesses; no global proof.')
    (out/'results.json').write_text(json.dumps(result,indent=2));print(json.dumps(dict(seconds=result['seconds'],minimum_exact_recheck=float(min(F(v['score']) for v in rechecks)))),flush=True)
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--previous');ap.add_argument('--separation');ap.add_argument('--output');args=ap.parse_args();run(args.previous,args.separation,args.output)
