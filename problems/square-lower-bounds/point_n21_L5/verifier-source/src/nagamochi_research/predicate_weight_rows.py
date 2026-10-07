"""PL45 fixed-model weight constraints; all exported coefficients are rational.

Compile once against the source proof. Keep the resulting geometry/model fixed
when weights become zero or positive. A new weight vector needs no LP replay.
"""
from fractions import Fraction as F
from compile_box_capture_rows import contains_all
from predicate_lp_capture import replay_certificate


def compile_model(points,box,record):
    points=[tuple(map(F,p)) for p in points]
    if 'base' in record:
        from predicate_conflict import replay_strengthened
        if tuple(map(F,record['box']))!=tuple(map(F,box)):raise ValueError('Changed proof box')
        replay_strengthened(points,record)
        rows=record['base']['rows']+[cut['row'] for cut in record['cuts']]
        multipliers=record['multipliers'];record=record['base']
    else:
        replay_certificate(points,box,record)
        rows=record['rows'];multipliers=record['multipliers']
    if 'cost' not in record:
        raise ValueError('Need a nontrivial predicate model')
    costs=[{} for _ in record['cost']]
    next_y=record['predicates']
    for rec in record['point_records']:
        ids=rec['predicates']
        if len(ids)==1:index=ids[0]
        else:index=next_y;next_y+=1
        costs[index][rec['point']]=F(1)
    if next_y!=len(costs):raise ValueError('Invalid variable mapping')
    if any(sum((points[p][2]*v for p,v in terms.items()),F(0))!=F(c)
           for terms,c in zip(costs,record['cost'])):
        raise ValueError('Cost mapping mismatch')
    baseline=[i for i,(x,y,w) in enumerate(points) if contains_all((x,y),box)]
    at=[F(0)]*len(costs);constant=F(0)
    for row,lam in zip(rows,map(F,multipliers)):
        constant+=lam*row['rhs']
        for i,v in row['terms']:at[i]+=lam*v
    return dict(coordinates=[p[:2] for p in points],box=tuple(map(F,box)),
                baseline=baseline,costs=costs,at=at,constant=constant)


def evaluate(model,points):
    points=[tuple(map(F,p)) for p in points]
    if [p[:2] for p in points]!=model['coordinates']:raise ValueError('Changed geometry/order')
    if any(w<0 for x,y,w in points):raise ValueError('Negative weight')
    w=[p[2] for p in points]
    residual=[sum((w[p]*v for p,v in terms.items()),F(0))-a
              for terms,a in zip(model['costs'],model['at'])]
    return sum((w[p] for p in model['baseline']),F(0))+model['constant']+sum((min(F(0),r) for r in residual),F(0))


def weight_rows(model,orbit_ids,sizes,target=F(1)):
    """Return exact A*x>=b rows, x=(total orbit masses, nonnegative penalties).

    Penalty v=-u: c(w)+v >= A^T lambda; B(w)-sum(v)>=target-lambda*b.
    All variables have lower bound zero. Caller may add ordinary capture rows.
    """
    n=len(sizes)
    if len(orbit_ids)!=len(model['coordinates']) or any(s<=0 for s in sizes):
        raise ValueError('Invalid orbit map')
    if any(not 0<=i<n for i in orbit_ids) or [orbit_ids.count(i) for i in range(n)]!=list(sizes):
        raise ValueError('Orbit sizes mismatch')
    def orbit_terms(terms):
        out={}
        for p,v in terms.items():
            j=orbit_ids[p];out[j]=out.get(j,F(0))+v/F(sizes[j])
        return out
    rows=[]
    for i,(terms,a) in enumerate(zip(model['costs'],model['at'])):
        row=orbit_terms(terms);row[n+i]=F(1)
        rows.append((row,a))
    last=orbit_terms({p:F(1) for p in model['baseline']})
    last.update({n+i:F(-1) for i in range(len(model['costs']))})
    rows.append((last,F(target)-model['constant']))
    return dict(variables=n+len(model['costs']),orbit_variables=n,rows=rows)
