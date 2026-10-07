from fractions import Fraction as F
from local_motion import snapshot,directed_hole
from elastic_motion import snapshot as elastic
from elastic_audit import triangle_edges
from verify_local_motion import empty
from motion_pilot import rows


def test_boundary_local_freezes_far_points_and_has_exact_hole():
    base=rows(6);ps=snapshot(0,0,F(2),F(1,2),'vertical')
    assert all(p==q for p,q in zip(base,ps) if p[0]>=2)
    hit=directed_hole(base,ps);assert hit is not None;empty(ps,hit['pose'])


def test_elastic_fixed_point_and_affine_path():
    c,i,fr=0,5,1;base=rows(6,colour=c)
    start=elastic(c,i,F(1,1000),F(0),'vertical',fr)
    end=elastic(c,i,F(1,1000),F(1),'vertical',fr)
    mid=elastic(c,i,F(1,1000),F(1,3),'vertical',fr)
    assert start==base
    assert mid==[tuple((2*a[j]+b[j])/3 for j in (0,1)) for a,b in zip(start,end)]
    fixed=base.index((F(11,2),F(457,500)+F(1043,1250)*fr));assert start[fixed]==end[fixed]
    for phase in ('vertical','row-left','leftmost-right'):
        for t in (F(0),F(1)):
            ps=elastic(c,i,F(1,1000),t,phase,fr)
            assert all(sum((ps[a][j]-ps[b][j])**2 for j in (0,1))<=1 for a,b in triangle_edges(c))
