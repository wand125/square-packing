from pathlib import Path
from fractions import Fraction as F
import json
from low_pose_point_capacity import patterns
from robust_pose_core import common_polygon
from score import contains
from score import square


def test_every_retained_row_has_certified_common_points(tmp_path):
    data=dict(n=20,L='4',B='9/10',rectangles=[],points=[],total_mass='0')
    p=tmp_path/'candidate.json';p.write_text(json.dumps(data))
    q=dict(leaves={'x':dict(kind='POSSIBLE_LOW',box=['1','11/10','1','11/10','-1/20','1/20']),
                  'y':dict(kind='HIGH',box=['0']*6)})
    pts,rows,paths,empty=patterns(p,q)
    assert not empty and paths==['x'] and rows[0]
    poly=common_polygon((F(4),F(999999,1000000)),*map(F,q['leaves']['x']['box']))
    assert all(contains(poly,pts[i]) for i in rows[0])


def test_correlated_core_inherits_points_and_stays_in_physical_cores(tmp_path):
    p=tmp_path/'candidate.json';p.write_text(json.dumps(dict(n=20,L='4',B='9/10',rectangles=[],points=[],total_mass='0')))
    b=list(map(F,['1','11/10','1','11/10','-1/20','1/20']))
    q=dict(leaves={'cell':dict(kind='POSSIBLE_LOW',box=list(map(str,b)))})
    old,_,_,_=patterns(p,q)
    pts,rows,paths,empty=patterns(p,q,extra_points=old,core_method='correlated')
    assert not empty and set(old)<=set(pts)
    for x in b[:2]:
        for y in b[2:4]:
            for i in range(9):
                core=square(x,y,F(999999,1000000),b[4]+(b[5]-b[4])*i/8)
                assert all(contains(core,pts[j]) for j in rows[0])
