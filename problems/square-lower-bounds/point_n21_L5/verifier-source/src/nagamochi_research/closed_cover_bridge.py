"""PL35: exact centre dilation; PL36: finite closed-predicate chain partitions.

No finite pose experiment in this module proves a full packing bound.
"""
from fractions import Fraction as F
from itertools import product
from score import square


def dilate_packing(poses, source, target):
    source, target = F(source), F(target)
    if not 0 < source < target:
        raise ValueError('Require 0 < source < target')
    poses = [tuple(map(F, p)) for p in poses]
    old = [square(x, y, F(1), t) for x, y, t in poses]
    if any(not (0 <= x <= source and 0 <= y <= source) for q in old for x, y in q):
        raise ValueError('Original square outside container')
    lam = target / source
    newposes = [(lam*x, lam*y, t) for x, y, t in poses]
    new = [square(x, y, F(1), t) for x, y, t in newposes]
    if any(not (0 < x < target and 0 < y < target) for q in new for x, y in q):
        raise AssertionError('Dilated containment failed')
    witnesses = []
    for i in range(len(old)):
        for j in range(i):
            found = None
            for q in (old[i], old[j]):
                for k in range(4):
                    dx = q[(k+1)%4][0]-q[k][0]; dy = q[(k+1)%4][1]-q[k][1]
                    axis = (-dy, dx)
                    def bounds(poly):
                        vals = [axis[0]*x+axis[1]*y for x,y in poly]
                        return min(vals),max(vals)
                    ai,bi=bounds(old[i]);aj,bj=bounds(old[j])
                    if ai >= bj or aj >= bi:
                        ni,xi=bounds(new[i]);nj,xj=bounds(new[j])
                        gap=max(ni-xj,nj-xi)
                        if gap <= 0:raise AssertionError('Strict separation failed')
                        found=dict(pair=[j,i],axis=list(map(str,axis)),gap=str(gap));break
                if found:break
            if found is None:raise ValueError('Original interiors overlap')
            witnesses.append(found)
    return dict(poses=[list(map(str,p)) for p in newposes],pairs=witnesses,scale=str(lam))


def quad_max(a,b,c,lo,hi):
    values=[a+b*t+c*t*t for t in (lo,hi)]
    if c<0:
        vertex=-b/(2*c)
        if lo<vertex<hi:values.append(a+b*vertex+c*vertex*vertex)
    return max(values)


def predicate(point, kind, cx, cy, side):
    x,y=point[0]-cx,point[1]-cy; h=side/2
    # (1+t^2) times each signed local-coordinate excess over side/2.
    if kind==0:return x-h,2*y,-x-h
    if kind==1:return -x-h,-2*y,x-h
    if kind==2:return y-h,-2*x,-y-h
    if kind==3:return -y-h,2*x,y-h
    raise ValueError('Unknown half-plane')


def chain_capture(points, box, chains, side=F(1)):
    """Recompute all implications and all chain cells with exact Fractions.

    points: ((x,y),mass). Predicate id is 4*point_index+halfplane.
    The result is a lower bound only on this pose box, with closed point capture.
    """
    side=F(side); box=tuple(map(F,box))
    points=[(tuple(map(F,p)),F(w)) for p,w in points]
    if side<=0 or len(box)!=6 or any(box[i]>box[i+1] for i in (0,2,4)) or any(w<0 for _,w in points):
        raise ValueError('Invalid domain or nonnegative measure')
    count=4*len(points)
    if not chains or any(not chain or len(set(chain))!=len(chain) or any(not isinstance(i,int) or i<0 or i>=count for i in chain) for chain in chains):
        raise ValueError('Invalid chains')
    corners=list(product(box[:2],box[2:4]))
    polynomials=[[predicate(p,k,x,y,side) for x,y in corners] for p,_ in points for k in range(4)]
    def maximum(i,j=None):
        terms=polynomials[i] if j is None else [tuple(a-b for a,b in zip(p,q)) for p,q in zip(polynomials[i],polynomials[j])]
        return max(quad_max(*poly,*box[4:]) for poly in terms)
    edges=[(i,j) for i in range(count) for j in range(count) if i!=j and maximum(j,i)<=0]
    opposed=[]
    for i in range(count):
        for j in range(i):
            total=[tuple(a+b for a,b in zip(p,q)) for p,q in zip(polynomials[i],polynomials[j])]
            if max(quad_max(*poly,*box[4:]) for poly in total)<=0:opposed.append((i,j))
    edge_set=set(edges)
    # Ascending G along a chain: G_next <= 0 implies G_prev <= 0.
    for chain in chains:
        if any((b,a) not in edge_set for a,b in zip(chain,chain[1:])):
            raise ValueError('Unproved chain ordering')
    always={i for i in range(count) if maximum(i)<=0}
    always_out={i for i in range(count) if max(quad_max(*[-v for v in poly],*box[4:]) for poly in polynomials[i])<0}
    def close(inside,outside):
        changed=True
        while changed:
            prev=(len(inside),len(outside))
            for a,b in edges:
                if a in inside:inside.add(b)
                if b in outside:outside.add(a)
            # G_a + G_b <= 0: strict positivity of either forces the other inside.
            for a,b in opposed:
                if a in outside:inside.add(b)
                if b in outside:inside.add(a)
            if inside & outside:return None
            changed=prev!=(len(inside),len(outside))
        return sum(w for p,(_,w) in enumerate(points) if all(4*p+k in inside for k in range(4)))
    baseline=sum(w for p,(_,w) in enumerate(points) if all(4*p+k in always for k in range(4)))
    leaves=[]
    for cuts in product(*(range(len(chain)+1) for chain in chains)):
        ins=set(always);outs=set(always_out)
        for chain,cut in zip(chains,cuts):ins.update(chain[:cut]);outs.update(chain[cut:])
        lower=close(ins,outs)
        leaves.append(dict(cuts=list(cuts),status='IMPOSSIBLE' if lower is None else 'BOUNDED',lower=None if lower is None else str(lower)))
    live=[F(r['lower']) for r in leaves if r['lower'] is not None]
    if not live:raise ValueError('No live cell in nonempty box')
    return dict(status='EXACT_CHAIN_BOX_LOWER_BOUND',lemma='PL36',box=list(map(str,box)),side=str(side),baseline=str(baseline),lower=str(min(live)),predicates=count,implications=len(edges),opposed_pairs=len(opposed),chains=chains,leaves=leaves,general_packing_exclusion=False)
