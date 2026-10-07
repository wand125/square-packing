"""Small exact transfer experiment for PL36 on a saved mixed measure."""
import json,hashlib
from pathlib import Path
from fractions import Fraction as F
from itertools import product
from closed_cover_bridge import chain_capture,predicate,quad_max,dilate_packing
from mixed_density_check import expand,pose_lower_bound


def run(candidate,out):
    if out.exists():raise FileExistsError(out)
    model=expand(json.loads(candidate.read_text()));L,B,rects,points,total,digest=model
    records=[]
    for cx,cy in [(F(3,2),F(3,2)),(F(3,2),F(1,2)),(L/2,L/2)]:
        for eps in (F(1,10000),F(1,1000),F(1,100)):
            box=(cx-eps,cx+eps,cy-eps,cy+eps,-eps,eps);corners=list(product(box[:2],box[2:4]));fixed=F(0);swing=[]
            for point,w in points:
                bounds=[]
                for kind in range(4):
                    ps=[predicate(point,kind,x,y,B) for x,y in corners]
                    upper=max(quad_max(*p,*box[4:]) for p in ps)
                    lower=-max(quad_max(*[-v for v in p],*box[4:]) for p in ps)
                    bounds.append((lower,upper))
                if all(hi<=0 for lo,hi in bounds):fixed+=w
                elif not any(lo>0 for lo,hi in bounds):swing.append((point,w,bounds))
            swing.sort(key=lambda r:-r[1]);chosen=swing[:12];chains=[]
            for kind in range(4):
                ids=[4*i+kind for i,row in enumerate(chosen) if row[2][kind][0]<=0<row[2][kind][1]]
                if ids:chains.append([ids[0]])
            density=pose_lower_bound((L,B,rects,[],total,digest),*box)
            if chains:
                proof=chain_capture([(p,w) for p,w,_ in chosen],box,chains,side=B);extra=F(proof['lower'])
            else:proof=None;extra=F(0)
            records.append(dict(box=list(map(str,box)),density_lower=str(density),fixed_point_mass=str(fixed),swing_points=len(swing),selected_points=len(chosen),unselected_mass=str(sum(w for _,w,_ in swing[12:])),baseline=str(density+fixed),chain_lower=str(density+fixed+extra),proof=proof))
    toy_points=[((F(1,2),1),F(1,2)),((F(3,2),1),F(1,2)),((1,F(1,2)),F(1,2)),((1,F(3,2)),F(1,2))]
    toy_box=(F(9,10),F(11,10),F(9,10),F(11,10),F(-1,100),F(1,100))
    toy=chain_capture(toy_points,toy_box,[[4],[14]])
    result=dict(status='EXACT_LOCAL_CHAIN_TRANSFER_PILOT',candidate_sha256=hashlib.sha256(candidate.read_bytes()).hexdigest(),records=records,toy=toy,
                dilation_example=dilate_packing([(F(1,2),F(1,2),0),(F(3,2),F(1,2),0)],2,F(201,100)),general_packing_exclusion=False)
    out.write_text(json.dumps(result,indent=2))
    for row in records:print('BOX',row['box'],'swing',row['swing_points'],'lower',float(F(row['baseline'])),float(F(row['chain_lower'])),flush=True)


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('candidate',type=Path);p.add_argument('out',type=Path);a=p.parse_args();run(a.candidate,a.out)
