"""Exact conditional centre-region lemmas for Bentz n22's exceptional row.

These certify only the stated geometric implications; motion unavoidability,
box distinctness and allocation of forbidden points remain external premises.
"""
from fractions import Fraction as F
from pathlib import Path
import json
from motion_pilot import sqrt_interval


def distance_bounds(box,point):
    """Point coordinates may themselves be enclosing rational intervals."""
    low=high=F(0)
    for (a,b),(c,d) in zip(box,point):
        low+=max(F(0),a-d,c-b)**2
        high+=max(abs(a-d),abs(b-c))**2
    return low,high


def setup(kind):
    s2=sqrt_interval(2);line=(s2[0]-F(1,2),s2[1]-F(1,2))
    xmin=F(3,2)*s2[0]-1
    if kind=='middle':
        y=F(5,2);domain=((xmin,F(243,200)),(F(357,200),F(643,200)))
        forbidden=[(line,(F(2),F(2))),(line,(F(3),F(3)))]
        target=((F(3,2),F(3,2)),(y,y))
    elif kind=='edge':
        y=F(9,10);domain=((xmin,F(243,200)),(F(1,2),F(323,200)))
        forbidden=[];target=(line,(F(1),F(1)))
    else:raise ValueError(kind)
    covered=((F(1,2),F(1,2)),(y,y))
    return domain,covered,forbidden,target


def close(box,covered,forbidden,target):
    radius_sq=2*F(101,200)**2
    if distance_bounds(box,covered)[0]>=radius_sq:return 'outside_cover_disk'
    if any(distance_bounds(box,p)[1]<F(1,4) for p in forbidden):return 'inside_forbidden_disk'
    if distance_bounds(box,target)[1]<F(1,4):return 'inside_target_disk'
    return None


def split(box):
    axis=max(range(2),key=lambda i:box[i][1]-box[i][0]);a,b=box[axis];m=(a+b)/2
    left=list(box);right=list(box);left[axis]=(a,m);right[axis]=(m,b)
    return tuple(left),tuple(right)


def build(box,covered,forbidden,target,depth=0):
    reason=close(box,covered,forbidden,target)
    if reason:return reason
    if depth>=50:raise RuntimeError('Unresolved region; no certificate')
    a,b=split(box)
    return [build(a,covered,forbidden,target,depth+1),build(b,covered,forbidden,target,depth+1)]


def replay(tree,box,covered,forbidden,target):
    if isinstance(tree,str):
        # Check the claimed leaf reason, not an approximate margin or saved bound.
        predicates={'outside_cover_disk':distance_bounds(box,covered)[0]>=2*F(101,200)**2,
                    'inside_forbidden_disk':any(distance_bounds(box,p)[1]<F(1,4) for p in forbidden),
                    'inside_target_disk':distance_bounds(box,target)[1]<F(1,4)}
        assert predicates.get(tree,False)
        return 1
    assert isinstance(tree,list) and len(tree)==2
    a,b=split(box)
    return replay(tree[0],a,covered,forbidden,target)+replay(tree[1],b,covered,forbidden,target)


if __name__=='__main__':
    import sys
    out=Path('runs/bentz_motion_20260926')
    for kind in ('middle','edge'):
        args=setup(kind);path=out/f'centre-{kind}.json'
        if '--verify' not in sys.argv:path.write_text(json.dumps(build(*args)))
        leaves=replay(json.loads(path.read_text()),*args)
        print(json.dumps(dict(kind=kind,leaves=leaves,status='VERIFIED_CONDITIONAL_CENTRE_LEMMA')))
