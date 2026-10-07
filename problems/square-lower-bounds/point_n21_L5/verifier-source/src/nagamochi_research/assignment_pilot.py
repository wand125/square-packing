"""Exact finite incidence relaxation for n32 and conditional row-motion cuts.
No full packing proof: all-time unavoidability of the reconstructed moving
families and the cited chord lemmas are external premises of motion cuts.
"""
from itertools import combinations
from collections import Counter
from pathlib import Path
from time import perf_counter
import json

SCALE=5000
SIDE=30000
DIAMETER_SQ=51005000  # 2 * (1.01 * 5000)^2


def points(colour):
    return [(j*SCALE if (r+colour)%2==0 else (2*j+1)*SCALE//2,4570+4172*r)
            for r in range(6) for j in (range(1,6) if (r+colour)%2==0 else range(6))]


def cross(a,b,c):return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])


def hull(ps):
    ps=sorted(set(ps))
    def half(seq):
        out=[]
        for p in seq:
            while len(out)>1 and cross(out[-2],out[-1],p)<=0:out.pop()
            out.append(p)
        return out
    return half(ps)[:-1]+half(ps[::-1])[:-1] if len(ps)>1 else ps


def inside(h,p):
    if len(h)==1:return p==h[0]
    if len(h)==2:
        a,b=h
        return cross(a,b,p)==0 and min(a[0],b[0])<=p[0]<=max(a[0],b[0]) and min(a[1],b[1])<=p[1]<=max(a[1],b[1])
    return all(cross(a,b,p)>=0 for a,b in zip(h,h[1:]+h[:1]))


def groups(ps):
    return [(i,) for i in range(len(ps))]+[pair for pair in combinations(range(len(ps)),2)
             if sum((ps[pair[0]][j]-ps[pair[1]][j])**2 for j in (0,1))<DIAMETER_SQ]


def cases(gs,n):
    if n==33:return [dict(empty=[],pair=[],groups=list(range(33)))]
    assert n==32
    return [dict(empty=[i],pair=[],groups=[j for j in range(33) if j!=i]) for i in range(33)]+[
            dict(empty=[],pair=list(gs[g]),groups=[j for j in range(33) if j not in gs[g]]+[g]) for g in range(33,len(gs))]


def compatible(rg,bg,rp,bp):
    ps=[rp[i] for i in rg]+[bp[i] for i in bg]
    if any(sum((a[j]-b[j])**2 for j in (0,1))>=DIAMETER_SQ for a,b in combinations(ps,2)):return False
    h=hull(ps)
    # The convex hull of points strictly inside a box is also strictly inside.
    return not any(inside(h,p) for i,p in enumerate(rp) if i not in rg) and not any(inside(h,p) for i,p in enumerate(bp) if i not in bg)


def focus_range(frozen,focus):
    # Difference constraints y_b-y_a <= c; node 6 is fixed zero.
    inf=10**9;d=[[0 if i==j else inf for j in range(7)] for i in range(7)]
    def add(a,b,c):d[a][b]=min(d[a][b],c)
    for i in range(6):add(6,i,SIDE);add(i,6,0)
    add(6,0,4570);add(5,6,-(SIDE-4570))
    for i in range(5):add(i,i+1,4000 if i in (focus-1,focus) else 4330);add(i+1,i,0)
    for i in frozen:
        y=4570+4172*i;add(6,i,y);add(i,6,-y)
    for k in range(7):
        for i in range(7):
            for j in range(7):d[i][j]=min(d[i][j],d[i][k]+d[k][j])
    if any(d[i][i]<0 for i in range(7)):return None
    return (-d[focus][6],d[6][focus])


def case_data(case,gs,ps):
    owner={i:g for g in case['groups'] for i in gs[g]}
    bad=case['empty']+case['pair'];frozen={int((ps[i][1]-4570)//4172) for i in bad}
    return dict(owner=owner,frozen=frozen,ranges=[focus_range(frozen,i) for i in range(6)])


def match(adj,left):
    right={}
    def visit(a,seen):
        for b in adj[a]:
            if b in seen:continue
            seen.add(b)
            if b not in right or visit(right[b],seen):right[b]=a;return True
        return False
    for a in left:
        if not visit(a,set()):
            # Alternating reachability gives an explicit deficient Hall set.
            ls={a};rs=set();stack=[a]
            while stack:
                x=stack.pop()
                for y in adj[x]:
                    if y in rs:continue
                    rs.add(y)
                    if y in right and right[y] not in ls:ls.add(right[y]);stack.append(right[y])
            assert len(rs)<len(ls)
            return None,dict(left=sorted(ls),neighbors=sorted(rs))
    return {a:b for b,a in right.items()},None


def motion_links(rd,bd,rg,bg,rp,bp):
    links=[];segments=[[],[]];missing=[];blocked=[]
    for i in range(6):
        rr,br=rd['ranges'][i],bd['ranges'][i]
        if rr is None or br is None or max(rr[0],br[0])>min(rr[1],br[1]):
            blocked.append(i);continue
        longcolour=0 if i%2 else 1
        ld,sd=(rd,bd) if longcolour==0 else (bd,rd)
        lp,sp=(rp,bp) if longcolour==0 else (bp,rp)
        lg=rg if longcolour==0 else bg
        for side in (0,1):
            lx=2500 if side==0 else 27500;sx=5000 if side==0 else 25000;y=4570+4172*i
            li=lp.index((lx,y));si=sp.index((sx,y));lo=ld['owner'].get(li);so=sd['owner'].get(si)
            if lo is None or len(lg[lo])!=1:continue  # Theorem 8 freezes this point.
            if so is None:
                missing.append(dict(row=i,side=side,longcolour=longcolour));continue
            pair=(lo,so) if longcolour==0 else (so,lo)
            links.append(pair)
            if i not in ld['frozen']:segments[side].append(pair[0])
    return links,segments,missing,blocked


def analyse(n,rp,bp,rg,bg,compat):
    rc=cases(rg,n);bc=cases(bg,n);rd=[case_data(c,rg,rp) for c in rc];bd=[case_data(c,bg,bp) for c in bc]
    stats=Counter();records=[]
    for ri,r in enumerate(rc):
        for bi,b in enumerate(bc):
            adj={a:sorted(compat[a]&set(b['groups'])) for a in r['groups']}
            matching,witness=match(adj,r['groups'])
            entry=dict(red_case=ri,blue_case=bi)
            if matching is None:
                entry.update(status='EXACT_INCIDENCE_HALL_REJECTION',hall=witness)
            else:
                links,segs,missing,blocked=motion_links(rd[ri],bd[bi],rg,bg,rp,bp)
                if missing:entry.update(status='CONDITIONAL_MOTION_EMPTY_ANCHOR',missing=missing)
                else:
                    forced=set(links);restricted={a:[bb for bb in adj[a] if all((a!=x and bb!=y) or (a==x and bb==y) for x,y in forced)] for a in adj}
                    matching,witness=match(restricted,r['groups'])
                    if matching is None:entry.update(status='CONDITIONAL_MOTION_HALL_REJECTION',hall=witness,links=sorted(forced))
                    elif max(map(lambda x:len(set(x)),segs),default=0)>=6:
                        entry.update(status='CONDITIONAL_SIX_BOX_CHORD_REJECTION',segments=[sorted(set(x)) for x in segs])
                    else:entry.update(status='UNRESOLVED',matching=sorted(matching.items()),
                                      segments=[sorted(set(x)) for x in segs],blocked_rows=blocked,links=sorted(forced))
            stats[entry['status']]+=1;records.append(entry)
    return dict(n=n,cases=len(records),counts=dict(stats),records=records)


def main():
    started=perf_counter();rp,bp=points(0),points(1);rg,bg=groups(rp),groups(bp)
    compat={a:{b for b in range(len(bg)) if compatible(rg[a],bg[b],rp,bp)} for a in range(len(rg))}
    out=Path('runs/bentz_assignment_20260926');out.mkdir(parents=True,exist_ok=False)
    data={'scale':SCALE,'red_points':rp,'blue_points':bp,'red_groups':rg,'blue_groups':bg,
          'compatible_pairs':[(a,b) for a,neighbors in compat.items() for b in sorted(neighbors)],
          'results':[analyse(n,rp,bp,rg,bg,compat) for n in (33,32)],
          'scope':'Incidence cuts are necessary under base unavoidability. Motion cuts additionally assume all-time unavoidability of the row paths and the chord lemmas; not a new packing proof.'}
    data['seconds']=perf_counter()-started
    (out/'results.json').write_text(json.dumps(data,indent=2))
    print(json.dumps(dict(seconds=data['seconds'],compatible_pairs=len(data['compatible_pairs']),
                         results=[{k:v for k,v in r.items() if k!='records'} for r in data['results']])),flush=True)


if __name__=='__main__':main()
