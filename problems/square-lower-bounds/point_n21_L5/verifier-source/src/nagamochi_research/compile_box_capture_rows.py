"""PL42: independently replay rectangular pose boxes and export weight rows.

Full box containment is proved by exact quadratic maxima. This deliberately
avoids admissibility clipping, inherited masks, CHAIN, and numerical geometry.
"""
from pathlib import Path
from fractions import Fraction as F
from math import prod
import hashlib,json
from probe_external_integer_bridge import read


def quadmax(poly,a,b):
    c0,c1,c2=map(F,poly);a,b=F(a),F(b)
    if a>b:raise ValueError('Reversed interval')
    at=lambda t:c0+c1*t+c2*t*t
    values=[at(a),at(b)]
    if c2<0:
        t=-c1/(2*c2)
        if a<=t<=b:values.append(at(t))
    return max(values)


def contains_all(point,box):
    px,py=map(F,point);x0,x1,y0,y1,t0,t1=map(F,box)
    if not (x0<=x1 and y0<=y1 and 0<=t0<=t1<=F(1,2)):
        raise ValueError('Invalid pose box')
    # For t in [0,1/2], both rotation numerators are nonnegative.
    # Each signed projection attains its centre maximum at the stated corner.
    dx0,dx1,dy0,dy1=px-x0,px-x1,py-y0,py-y1
    polys=[(2*dx0-1,4*dy0,-2*dx0-1),
           (-2*dx1-1,-4*dy1,2*dx1-1),
           (2*dy0-1,-4*dx1,-2*dy0-1),
           (-2*dy1-1,4*dx0,2*dy1-1)]
    return all(quadmax(p,t0,t1)<=0 for p in polys)


def validate_partition(root,boxes):
    root=tuple(map(F,root));boxes=[tuple(map(F,b)) for b in boxes]
    def volume(b):return prod(b[i+1]-b[i] for i in (0,2,4))
    if len(root)!=6 or any(root[i]>=root[i+1] for i in (0,2,4)):
        raise ValueError('Need positive root volume')
    for b in boxes:
        if len(b)!=6 or any(not root[i]<=b[i]<b[i+1]<=root[i+1] for i in (0,2,4)):
            raise ValueError('Leaf outside root or nonpositive volume')
    for i,a in enumerate(boxes):
        for b in boxes[i+1:]:
            if all(max(a[k],b[k])<min(a[k+1],b[k+1]) for k in (0,2,4)):
                raise ValueError('Overlapping leaf interiors')
    if sum((volume(b) for b in boxes),F(0))!=volume(root):
        raise ValueError('Incomplete partition')
    return True


def geometry(candidate):
    L,span,W,pts=read(candidate);D=F(span)/L
    coords=[(F(x)/D,F(y)/D) for x,y,w in pts]
    weights=[F(w,W) for x,y,w in pts]
    payload=json.dumps([str(L),[[str(x),str(y)] for x,y in coords]],separators=(',',':'))
    return L,coords,weights,hashlib.sha256(payload.encode()).hexdigest()


def compile_rows(candidate,root_leaves,out):
    if out.exists():raise FileExistsError(out)
    L,coords,weights,digest=geometry(candidate);records=[]
    for entry in root_leaves:
        validate_partition(entry['root'],[r['box'] for r in entry['leaves']])
        for leaf in entry['leaves']:
            indices=leaf['indices']
            if len(indices)!=len(set(indices)) or not indices:raise ValueError('Invalid point indices')
            if any(not isinstance(i,int) or not 0<=i<len(coords) for i in indices):raise ValueError('Point index out of range')
            if not all(contains_all(coords[i],leaf['box']) for i in indices):raise ValueError('Unproved containment')
            mass=sum((weights[i] for i in indices),F(0))
            if mass<1:raise ValueError('Source does not certify leaf')
            records.append(dict(root_index=entry['root_index'],box=leaf['box'],indices=indices,source_capture=str(mass)))
    data=dict(status='EXACT_BOX_CAPTURE_ROWS',source_sha256=hashlib.sha256(candidate.read_bytes()).hexdigest(),geometry_sha256=digest,L=str(L),roots=[dict(root_index=r['root_index'],root=r['root'],leaf_count=len(r['leaves'])) for r in root_leaves],rows=records,geometry_replay='independent signed-projection quadratic maxima',partition_replay='containment, disjoint interiors and exact volume',general_coverage_verified=False)
    out.write_text(json.dumps(data,indent=2));return data


def replay_rows(certificate,candidate):
    d=json.loads(certificate.read_text());L,coords,weights,digest=geometry(candidate)
    if digest!=d['geometry_sha256'] or str(L)!=d['L']:raise ValueError('Changed geometry or point order')
    if len({r['root_index'] for r in d['roots']})!=len(d['roots']):raise ValueError('Duplicate roots')
    known={r['root_index'] for r in d['roots']}
    if any(r['root_index'] not in known for r in d['rows']):raise ValueError('Unknown root')
    for root in d['roots']:
        rows=[r for r in d['rows'] if r['root_index']==root['root_index']]
        if len(rows)!=root['leaf_count']:raise ValueError('Missing leaves')
        validate_partition(root['root'],[r['box'] for r in rows])
    captures=[]
    for row in d['rows']:
        indices=row['indices']
        if not indices or len(indices)!=len(set(indices)) or any(not isinstance(i,int) or not 0<=i<len(coords) for i in indices):raise ValueError('Invalid indices')
        if not all(contains_all(coords[i],row['box']) for i in indices):raise ValueError('Unproved containment')
        captures.append(sum((weights[i] for i in indices),F(0)))
    return dict(candidate_sha256=hashlib.sha256(candidate.read_bytes()).hexdigest(),geometry_verified=True,rows=len(captures),row_captures=list(map(str,captures)),passed_rows=sum(c>=1 for c in captures),retained_roots=[r['root_index'] for r in d['roots'] if all(c>=1 for row,c in zip(d['rows'],captures) if row['root_index']==r['root_index'])],general_coverage_verified=False)
