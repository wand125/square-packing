"""Rebuild every coefficient at a new L; retain all supports and saved poses."""
import argparse,json
from pathlib import Path
from fractions import Fraction as F
import numpy as np
from expanded_search_pilot import ROOT,load,Geometry,columns,capture,solve
from mixed_density_refit import export
from mixed_density_check import expand,evaluate


def transfer_witness(q,oldL,newL,B,newB=None):
    t=F(q['t']);radius=B*(1+2*t-t*t)/(2*(1+t*t))
    newB=B if newB is None else newB
    newradius=newB*(1+2*t-t*t)/(2*(1+t*t))
    ratio=(newL/2-newradius)/(oldL/2-radius)
    x=newL/2+(F(q['cx'])-oldL/2)*ratio
    y=newL/2+(F(q['cy'])-oldL/2)*ratio
    return dict(cx=str(x),cy=str(y),t=str(t),normalized_pose=q['normalized_pose'],origin='L-transfer',parent_pose=q)


def prepare(source,out,target,variants=False,core=None,net=None):
    out.mkdir(parents=True,exist_ok=False)
    if (source/'model.json').exists():
        d=json.loads((source/'model.json').read_text());rects=np.array(d['rectangles']);saved=range(d['base_pose_count']);oldL=d['L'];B=d['B'];rhs=d['rhs']
    else:
        _,rects,saved,oldL,B,rhs,_=load(21)
        d=json.loads((ROOT/'n21/results.json').read_text())
    oldL=F(str(oldL));oldB=F(str(B));target=F(target);ratio=target/oldL
    B=float(core) if core is not None else B
    from mixed_net_audit import net_certificate
    proof_net=net if net is not None else d.get('proof_net',dict(step='83/40000',last=200))
    net_certificate(F(str(B)),F(proof_net['step']),proof_net['last'])
    ledger=json.loads((source/'cumulative-witnesses.json').read_text())
    with np.load(source/'replay.npz') as z:
        chosen=z['selected_rectangles'].copy()*float(ratio)
        poses=z['poses'].copy();ids=z['row_ids'].tolist()
    assert len(poses)==len(saved)+len(ledger)
    rects=rects*float(ratio);L=float(target)
    rules=d['rules']
    for rule in rules:rule['sites']=[[str(F(x)*ratio) for x in p] for p in rule['sites']]
    meta=dict(n=d.get('n',21),L=L,B=B,rhs=rhs,point_columns=d['point_columns'],rules=rules,rectangles=rects.tolist(),base_pose_count=len(saved),source=str(source.resolve()),oldL=str(oldL),targetL=str(target),oldB=str(oldB),proof_net=proof_net,budget=d.get('budget','20.999'),support_transform='Uniform L/oldL dilation; normalized poses retained; all coefficients rebuilt at target B')
    (out/'model.json').write_text(json.dumps(meta,indent=2))
    for rule in rules:rule['sites']=[tuple(map(F,p)) for p in rule['sites']]
    r=len(rects);p=d['point_columns'];geo=Geometry(L,B,rects);extra=Geometry(L,B,chosen)
    def block(q):
        pc,_,mapping=columns(q,rules,L,B)
        assert pc.shape[1]==p
        return np.hstack([geo.matrix(q),pc,extra.matrix(q)]),mapping
    aa,mapping=block(poses[ids])
    if variants:
        # Keep every dilated support. Price alternative transfers against the
        # new-L dual before allocating columns to the common comparison.
        from geometry import rectangle_key
        fit,_=solve(aa,rhs);dual=-fit.ineqlin.marginals
        original=np.vstack([rects,chosen])/float(ratio);delta=float(target-oldL)
        known={rectangle_key(row,L) for row in np.vstack([rects,chosen])};candidates=[]
        for row in original:
            for trial in (row,row+delta/2,np.where(row<float(oldL)/2,row,row+delta)):
                key=rectangle_key(trial,L)
                if key not in known:known.add(key);candidates.append(trial)
        candidates=np.array(candidates);loads=[]
        for lo in range(0,len(candidates),128):loads.extend(Geometry(L,B,candidates[lo:lo+128]).matrix(poses[ids]).T@dual)
        selected=[i for i in np.argsort(-np.array(loads)) if loads[i]>1+1e-5][:128]
        added=candidates[selected];chosen=np.vstack([chosen,added]);extra=Geometry(L,B,chosen)
        aa=np.hstack([aa,Geometry(L,B,added).matrix(poses[ids])])
        (out/'transfer-pricing.json').write_text(json.dumps(dict(candidates=len(candidates),selected=len(selected),loads=[float(loads[i]) for i in selected],rectangles=added.tolist()),indent=2))
        print(json.dumps(dict(stage='transfer-pricing',candidates=len(candidates),selected=len(selected),max_load=max(loads))),flush=True)
    mask=np.r_[np.arange(r),np.arange(r+p,r+p+len(chosen))]
    def audit(w):
        ri=np.flatnonzero(w[:r]>0);ni=np.flatnonzero(w[r+p:]>0);pi=np.flatnonzero(w[r:r+p]>0)
        density=np.vstack([rects[ri],chosen[ni]]);dw=np.r_[w[ri],w[r+p:][ni]]
        unique=sorted({i for j in pi for i in mapping['point_orbits'][j]});lookup={v:k for k,v in enumerate(unique)}
        vals=[]
        for lo in range(0,len(poses),1024):
            q=poses[lo:lo+1024];v=Geometry(L,B,density).matrix(q)@dw
            if unique:
                hits=capture(q,L,B,np.array([mapping['points'][i] for i in unique],float))
                for j in pi:v+=w[r+j]*hits[:,[lookup[i] for i in mapping['point_orbits'][j]]].mean(axis=1)
            vals.extend(v)
        return np.array(vals)
    records=[]
    while True:
        bad=set();weights={};coverages={}
        for name,cols in [('rectangles',mask),('mixed',np.arange(aa.shape[1]))]:
            fit,stat=solve(aa[:,cols],rhs);w=np.zeros(aa.shape[1]);w[cols]=fit.x
            vals=audit(w);failed=np.flatnonzero(vals<rhs-1e-8);bad.update(failed.tolist())
            stat.update(model=name,rows=len(aa),total_poses=len(poses),violations=len(failed),all_min=float(vals.min()),point_mass=float(sum(w[r:r+p])))
            print(json.dumps(stat),flush=True);records.append(stat);weights[name]=w;coverages[name]=vals
        if not bad:break
        missing=sorted(bad-set(ids))
        if not missing:raise RuntimeError('Inconsistent saved-row audit')
        more,_=block(poses[missing]);aa=np.vstack([aa,more]);ids+=missing
    newledger=[transfer_witness(q,oldL,target,oldB,F(str(B))) for q in ledger]
    (out/'cumulative-witnesses.json').write_text(json.dumps(newledger,indent=2))
    w=weights['mixed'];mass=sum((F(str(x)) for x in w),F(0))
    np.savez_compressed(out/'replay.npz',matrix=aa,row_ids=ids,selected_rectangles=chosen,poses=poses,weights_added_density=w,coverage_added_density=coverages['mixed'],weights_rectangles=weights['rectangles'])
    result=dict(status='BUDGET_EXHAUSTED' if mass>F(20999,1000) else 'FINITE_REPAIRED_NOT_CERTIFIED',L=str(target),mass=str(mass),total_poses=len(poses),support_columns=aa.shape[1],records=records)
    (out/'results.json').write_text(json.dumps(result,indent=2))
    if mass<=F(20999,1000):
        candidate=export(out/'mixed-candidate.json',meta,np.vstack([rects,chosen]),np.r_[w[:r],w[r+p:],w[r:r+p]],mapping)
        model=expand(candidate);checks=[evaluate(model,F(q['cx']),F(q['cy']),F(q['t'])) for q in newledger]
        assert all(F(q['score'])>=1 for q in checks),'Transferred exact pose failed'
        result['exact_rechecks']=len(checks);result['minimum_exact']=str(min(F(q['score']) for q in checks))
        (out/'exact-rechecks.json').write_text(json.dumps(checks,indent=2))
        (out/'results.json').write_text(json.dumps(result,indent=2))
    print(json.dumps({k:v for k,v in result.items() if k not in ('records','minimum_exact')}),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--L',type=F,required=True);p.add_argument('--variants',action='store_true');p.add_argument('--B',type=F);p.add_argument('--net-step',type=F);p.add_argument('--net-last',type=int);a=p.parse_args()
    if (a.net_step is None)!=(a.net_last is None):p.error('net step and last must be specified together')
    net=None if a.net_step is None else dict(step=str(a.net_step),last=a.net_last)
    prepare(a.source,a.out,a.L,a.variants,a.B,net)
