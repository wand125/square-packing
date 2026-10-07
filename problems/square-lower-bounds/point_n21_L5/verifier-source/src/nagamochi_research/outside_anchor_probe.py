"""Conditional LOCAL epsilon certificates with one extra moving anchor box.

Never claims that the anchor samples cover all outside poses, or that a
packing cannot have two or more boxes outside the saved local family.
"""
import argparse,hashlib,importlib.util,json,time
from pathlib import Path
from fractions import Fraction as F
import numpy as np
from scipy.optimize import linprog
from scipy.sparse import coo_matrix
from robust_conflict_cover import overlap_gap


def coordinates(s):
    x,y,d,a,b,r=s[:6]
    return F(x,d),F(y,d),F(b,r+a)


def disjoint_cells(base_a,end_a,base_b,end_b,epsilon,alpha):
    """A fixed coordinate separates the two moving cells for ALL epsilon>0."""
    for a0,a1,b0,b1 in zip(coordinates(base_a),coordinates(end_a),coordinates(base_b),coordinates(end_b)):
        u,v=a0-b0,a1-b1
        if (u>=0 and v>2*alpha*epsilon) or (u<=0 and v < -2*alpha*epsilon):return True
    return False


def guaranteed_conflict(base_a,end_a,base_b,end_b,epsilon,alpha,safety_factor=56):
    assert safety_factor>28 and epsilon>0 and alpha>0
    g0,_=overlap_gap(base_a,base_b)
    if g0<0:return False
    num,den=overlap_gap(end_a,end_b)
    threshold=safety_factor*alpha*epsilon
    return num>0 and num*threshold.denominator>=threshold.numerator*den


def rational_cover(matrix,cuts,kept):
    if not kept:return dict(numerators=[0]*len(cuts),denominator=1,upper='0')
    fit=linprog(np.ones(len(cuts)),A_ub=-matrix[kept],b_ub=-np.ones(len(kept)),bounds=(0,None),method='highs',options={'time_limit':10})
    if not fit.success:raise RuntimeError(fit.message)
    nums=[max(0,int(np.ceil(x*10**9))) for x in fit.x];coverage={i:0 for i in kept}
    for c,w in zip(cuts,nums):
        if w:
            for i in c:
                if i in coverage:coverage[i]+=w
    den=min(coverage.values());assert den>0
    return dict(numerators=nums,denominator=den,upper=str(F(sum(nums),den)))


def run(source,checker,out,grid):
    out.mkdir(parents=True,exist_ok=False);started=time.monotonic()
    f=json.loads((source/'family-poses.json').read_text());meta=json.loads((source/'result.json').read_text())
    base,end=f['base'],f['endpoint'];epsilon=F(f['epsilon_max']);alpha=F(meta['coordinate_radius_coefficient'])
    old=json.loads((source/'refined/cover.json').read_text())
    cuts=[c for c,w in zip(old['cliques'],old['numerators']) if w]
    rows=[];cols=[]
    for j,c in enumerate(cuts):
        for i in c:rows.append(i);cols.append(j)
    matrix=coo_matrix((np.ones(len(rows)),(rows,cols)),shape=(len(base),len(cuts))).tocsr()
    spec=importlib.util.spec_from_file_location('external_dual',checker);ext=importlib.util.module_from_spec(spec);spec.loader.exec_module(ext)
    angles=[F(0),F(1,20),F(1,10),F(1,5),F(3,10),F(2,5)]
    anchors=[]
    for t in angles:
        a,b,r=ext.cos_sin(t.numerator,t.denominator);radius=F(abs(a)+abs(b),2*r)
        for i in range(grid+1):
            for j in range(grid+1):
                def pose(L):
                    ext.set_t(L)
                    return ext.make_square(radius+F(i,grid)*(L-2*radius),radius+F(j,grid)*(L-2*radius),t.numerator,t.denominator,0)
                anchors.append((pose(F(4)),pose(4-epsilon)))
    results=[]
    def save(stage):
        record=dict(operation='conditional_cover',status='RUNNING',stage=stage,finished=len(results),anchors=len(anchors),updated_epoch=time.time())
        (out/'progress.json').write_text(json.dumps(dict(records=[record]),indent=2));print(json.dumps(record),flush=True)
    save('anchor_scan')
    for k,(a,z) in enumerate(anchors):
        blocked=[i for i in range(len(base)) if guaranteed_conflict(a,z,base[i],end[i],epsilon,alpha)]
        blocked_set=set(blocked);kept=[i for i in range(len(base)) if i not in blocked_set]
        cover=rational_cover(matrix,cuts,kept);upper=F(cover['upper'])
        outside=all(disjoint_cells(a,z,b,e,epsilon,alpha) for b,e in zip(base,end))
        results.append(dict(index=k,base=a,endpoint=z,blocked=blocked,outside_original_union=outside,cover=cover,
                            local_integer_upper=upper.numerator//upper.denominator,excludes_one_anchor_plus_eleven_local=upper<11))
        if k%25==24:save('anchor_scan')
    (out/'branches.json').write_text(json.dumps(dict(epsilon_max=str(epsilon),alpha=str(alpha),cliques=cuts,branches=results)))
    # Recompute ALL geometry used by the conditional certificates. The LP
    # is not trusted; use saved integers for the covering inequalities.
    save('exact_replay')
    needed=[0]*len(base)
    for c in cuts:
        mask=sum(1<<i for i in c)
        for i in c:needed[i] |= mask & ((1<<i)-1)
    pairs=0
    for i,bits in enumerate(needed):
        while bits:
            bit=bits & -bits;j=bit.bit_length()-1;bits^=bit
            assert guaranteed_conflict(base[i],end[i],base[j],end[j],epsilon,alpha);pairs+=1
    for q in results:
        a,z=q['base'],q['endpoint'];blocked=set(q['blocked'])
        assert all(guaranteed_conflict(a,z,base[i],end[i],epsilon,alpha) for i in blocked)
        if q['outside_original_union']:
            assert all(disjoint_cells(a,z,b,e,epsilon,alpha) for b,e in zip(base,end))
        cov=[0]*len(base);c=q['cover'];assert c['denominator']>0
        for clique,w in zip(cuts,c['numerators']):
            assert type(w) is int and w>=0
            for i in clique:cov[i]+=w
        assert all(i in blocked or cov[i]>=c['denominator'] for i in range(len(base)))
        assert F(sum(c['numerators']),c['denominator'])==F(c['upper'])
    outside=[q for q in results if q['outside_original_union']]
    result=dict(status='EXACT_CONDITIONAL_LOCAL_EPSILON_BRANCHES',anchors=len(results),outside_anchors=len(outside),
                excluded=sum(q['excludes_one_anchor_plus_eleven_local'] for q in results),
                outside_excluded=sum(q['excludes_one_anchor_plus_eleven_local'] for q in outside),
                epsilon_max=str(epsilon),alpha=str(alpha),local_pairs_rechecked=pairs,seconds=time.monotonic()-started,
                local_upper_min=str(min(F(q['cover']['upper']) for q in results)),local_upper_max=str(max(F(q['cover']['upper']) for q in results)),
                theorem='Each successful branch excludes one anchor in its moving cell PLUS eleven boxes in the original local union, for every real 0<epsilon<=epsilon_max.',
                limitation='Anchor cells do not cover all outside poses. Two or more outside boxes are not excluded. Not s(12)=4.',
                hashes={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [source/'family-poses.json',source/'refined/cover.json',source/'result.json',checker]})
    (out/'result.json').write_text(json.dumps(result,indent=2));(out/'progress.json').write_text(json.dumps(dict(records=[dict(operation='conditional_cover',status='STOPPED_LOCAL_PROOF_REVIEW',result=result)]),indent=2));print(json.dumps(result),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('checker',type=Path);p.add_argument('out',type=Path);p.add_argument('--grid',type=int,default=6);a=p.parse_args();assert a.grid>0;run(a.source,a.checker,a.out,a.grid)
