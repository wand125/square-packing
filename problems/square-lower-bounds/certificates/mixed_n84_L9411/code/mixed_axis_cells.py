"""Exact axis-cell lower bounds: bilinear density plus interior-cell atom mask."""
from fractions import Fraction as F
from mixed_density_check import polygon_score
from score import square


def axis_cell_lower(model,x0,x1,y0,y1):
    """Cell must contain no rectangle or point capture breakpoints in its interior.

    Point membership is sampled at its interior, then kept at cell corners.
    Nonnegative closed point capture can only gain atoms on the boundaries.
    """
    L,B,rects,points,total,digest=model
    if not x0<x1 or not y0<y1:raise ValueError('Need positive area cell')
    for axis,lo,hi in ((0,x0,x1),(1,y0,y1)):
        events={v+s*B/2 for r in rects for v in (r[axis],r[axis+2]) for s in (-1,1)}
        events|={p[axis]+s*B/2 for p,w in points for s in (-1,1)}
        if any(lo<v<hi for v in events):raise ValueError('Unsplit capture event')
    _,atoms=polygon_score(square((x0+x1)/2,(y0+y1)/2,B,F(0)),[],points)
    density=[polygon_score(square(x,y,B,F(0)),rects,[])[0] for x in (x0,x1) for y in (y0,y1)]
    return min(density)+atoms


def boundary_trap():
    # Feasible axis centres in [1/2,1]^2, B=1/2. Every corner captures
    # one atom; every open-cell centre captures none. A corner-only test fails.
    from mixed_density_check import expand,evaluate
    d=dict(n=5,L='2',B='1/2',rectangles=[],points=[dict(point=[str(x),str(y)],mass='1') for x in (F(1,4),F(5,4)) for y in (F(1,4),F(5,4))],total_mass='4')
    m=expand(d);box=(F(1,2),F(1),F(1,2),F(1))
    scores=[F(evaluate(m,x,y,F(0))['score']) for x in (box[0],box[1]) for y in (box[2],box[3])]
    mid=F(evaluate(m,F(3,4),F(3,4),F(0))['score']);lower=axis_cell_lower(m,*box)
    assert scores==[1]*4 and mid==lower==0
    return dict(corner_scores=list(map(str,scores)),interior_score=str(mid),correct_cell_lower=str(lower),scope='Toy counterexample to point-aware verification by corner capture alone, not a production candidate.')

if __name__=='__main__':
    import json
    from pathlib import Path
    r=boundary_trap();p=Path('runs/mixed_strict_design_20260926');p.mkdir(exist_ok=True);(p/'axis-boundary-trap.json').write_text(json.dumps(r,indent=2));print(json.dumps(r))
