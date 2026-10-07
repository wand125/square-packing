"""A continuous epsilon-family of LOCAL clique covers, not global unavoidability."""
import argparse,json,importlib.util,time
from pathlib import Path
from fractions import Fraction as F
from robust_conflict_cover import overlap_gap
from refine_conflict_cover import run as refine


def pair_slope(base_a,base_b,end_a,end_b,epsilon):
    assert epsilon>0
    for base,end in [(base_a,end_a),(base_b,end_b)]:
        assert F(base[3],base[5])==F(end[3],end[5])
        assert F(base[4],base[5])==F(end[4],end[5])
    g0,_=overlap_gap(base_a,base_b);g1,d1=overlap_gap(end_a,end_b)
    assert g0>=0 and g1>0
    return F(g1,d1)/epsilon


def run(source,checker,out,epsilon,alpha):
    out.mkdir(parents=True,exist_ok=False)
    spec=importlib.util.spec_from_file_location('external_dual',checker);ext=importlib.util.module_from_spec(spec);spec.loader.exec_module(ext)
    ext.set_t(4-epsilon)
    original=[v['square'] for v in json.loads((source/'poses.json').read_text())]
    moved=[]
    for s in original:
        x,y,d,a,b,r=s[:6];radius=F(abs(a)+abs(b),2*r)
        # Affine in epsilon; every unit box stays in its admissible centre interval.
        cx,cy=[radius+(F(v,d)-radius)*(4-epsilon-2*radius)/(4-2*radius) for v in (x,y)]
        t=F(b,r+a);moved.append(ext.make_square(cx,cy,t.numerator,t.denominator,0))
    n=len(original);graph=[0]*n;edges=0;target=56*alpha*epsilon
    for i in range(n):
        for j in range(i):
            zero,_=overlap_gap(original[i],original[j])
            if zero<0:continue
            num,den=overlap_gap(moved[i],moved[j])
            if num>0 and num*target.denominator>=target.numerator*den:
                graph[i]|=1<<j;graph[j]|=1<<i;edges+=1
    cuts=set()
    for seed in range(n):
        c=[seed];bits=graph[seed]
        while bits:
            bit=bits & -bits;v=bit.bit_length()-1;c.append(v);bits &= graph[v]
        cuts.add(tuple(sorted(c)))
    (out/'conflicts.json').write_text(json.dumps([hex(v) for v in graph]))
    (out/'cliques.json').write_text(json.dumps(sorted(cuts)))
    (out/'family-poses.json').write_text(json.dumps(dict(base=original,endpoint=moved,epsilon_max=str(epsilon))))
    print(json.dumps(dict(stage='family_graph',edges=edges,cliques=len(cuts),epsilon_max=str(epsilon),alpha=str(alpha))),flush=True)
    refine(out,out/'refined',5)
    cover=json.loads((out/'refined/cover.json').read_text());coverage=[0]*n;seen=[0]*n
    for c,w in zip(cover['cliques'],cover['numerators']):
        if not w:continue
        mask=sum(1<<v for v in c)
        for v in c:coverage[v]+=w;seen[v] |= mask & ((1<<v)-1)
    assert min(coverage)>=cover['denominator']
    bound=F(sum(cover['numerators']),cover['denominator']);minimum=None;count=0
    for i,bits in enumerate(seen):
        while bits:
            bit=bits & -bits;j=bit.bit_length()-1;bits^=bit
            slope=pair_slope(original[i],original[j],moved[i],moved[j],epsilon)
            if minimum is None or slope<minimum:minimum=slope
            count+=1
    assert minimum is not None
    coefficient=min(minimum/56,F(1,8)/epsilon)
    assert coefficient>=alpha
    # Fixed orientation and affine centres => every SAT overlap gap is
    # concave in epsilon (constant minus absolute affine function).
    # g(0)>=0, g(E)>0 imply g(e)>=e*g(E)/E for ALL real 0<e<=E.
    # The 28h perturbation bound then preserves every pair for h=coefficient*e.
    result=dict(status='EXACT_LOCAL_EPSILON_FAMILY',L='4-epsilon',epsilon_interval=['0',str(epsilon)],left_open=True,
                upper=str(bound),integer_upper=bound.numerator//bound.denominator,cells=n,used_cliques=sum(w>0 for w in cover['numerators']),
                pairs_rechecked=count,coordinate_radius_coefficient=str(coefficient),coefficient_float=float(coefficient),
                requested_coefficient=str(alpha),rule='For every real 0<epsilon<=epsilon_max, each pose follows the saved affine centre path and allows coordinate perturbations of coefficient*epsilon.',
                limitation='Only the union of these moving pose cells is covered. No global proof of s(12)=4.')
    (out/'result.json').write_text(json.dumps(result,indent=2));print(json.dumps(result),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('checker',type=Path);p.add_argument('out',type=Path);p.add_argument('--epsilon',type=F,default=F(1,1000));p.add_argument('--alpha',type=F,default=F(1,10000));a=p.parse_args();assert 0<a.epsilon<=1 and a.alpha>0;run(a.source,a.checker,a.out,a.epsilon,a.alpha)
