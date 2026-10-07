"""PL19: all-axis low-capture cover and an exact grid capacity upper bound.

Fresh one-sided integer capture tables cover the entire physical centre
square via D4 lifts. PL15 extends the same nominal-core score to a two-sided near-axis band.
"""
from fractions import Fraction as F
from pathlib import Path
import argparse,json,hashlib,time
import numpy as np
from mixed_density_check import expand
from mixed_axis_verify import lattice,tables
from mixed_net_audit import symmetry
from packing_lemmas import axis_core_halfwidth


def compress(mask):
    active={};out=[]
    for i,row in enumerate(mask):
        ids=np.flatnonzero(row);spans=[]
        if len(ids):
            lo=prev=int(ids[0])
            for v in ids[1:]:
                v=int(v)
                if v!=prev+1:spans.append((lo,prev+1));lo=v
                prev=v
            spans.append((lo,prev+1))
        current=set(spans)
        for key,start in list(active.items()):
            if key not in current:out.append((start,i,*key));del active[key]
        for key in current:active.setdefault(key,i)
    for key,start in active.items():out.append((start,len(mask),*key))
    return sorted(out)


def tile_cover(rects,side,ox,oy):
    occupied=set()
    for x0,x1,y0,y1 in rects:
        for i in range((x0-ox)//side,(x1-ox)//side+1):
            for j in range((y0-oy)//side,(y1-oy)//side+1):occupied.add((i,j))
    return sorted(occupied)


def run(candidate,out,thresholds):
    start=time.monotonic();q=json.loads(candidate.read_text());m=expand(q);symmetry(m)
    L,B=m[:2];axes=lattice(m);f,h,wi,pi,den,meta=tables(m,axes)
    density=(f[0]*wi)@f[1].T
    lower=np.minimum(np.minimum(density[:-1,:-1],density[1:,:-1]),np.minimum(density[:-1,1:],density[1:,1:]))
    lower+=(h[0]*pi)@h[1].T*(1<<meta['fraction_bits'])**2
    results=[]
    for tau in thresholds:
        cutoff=-((-tau.numerator*den)//tau.denominator)
        mask=lower<cutoff;rects=[];compressed=compress(mask)
        for i,I,j,J in compressed:
            x0,x1=axes[0][i],axes[0][I];y0,y1=axes[1][j],axes[1][J]
            for a,b in ((x0,x1),(L-x1,L-x0)):
                for c,d in ((y0,y1),(L-y1,L-y0)):rects.append((a,b,c,d))
        # Exact phases only; phase search is an upper-bound improvement, not
        # part of coverage completeness. Any returned grid covers all rects.
        best=None
        for ix in range(8):
            for iy in range(8):
                ox=F(1,2)+B*ix/8;oy=F(1,2)+B*iy/8
                tiles=tile_cover(rects,B,ox,oy)
                if best is None or len(tiles)<len(best[2]):best=(ox,oy,tiles)
        ox,oy,tiles=best
        assert tiles==tile_cover(rects,B,ox,oy)
        results.append(dict(threshold=str(tau),quarter_cells=int(mask.sum()),compressed_quarter_rectangles=len(compressed),
            full_rectangles=[list(map(str,r)) for r in rects],grid_origin=[str(ox),str(oy)],grid_side=str(B),tiles=tiles,
            axis_low_capture_capacity=len(tiles)))
    result=dict(status='EXACT_NEAR_AXIS_LOW_CAPTURE_GRID_COVER',near_axis_halfwidth=str(axis_core_halfwidth(B)),candidate_digest=m[-1],candidate_sha256=hashlib.sha256(candidate.read_bytes()).hexdigest(),
                L=str(L),B=str(B),near_axis_capture_floor=str(F(int(lower.min()),den)),cells=int(lower.size),results=results,seconds=time.monotonic()-start,
                limitation='Nominal axis-core score throughout the stated near-axis band. Other angles unproved; not a global exclusion.')
    out.write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items() if k!='results'}),flush=True)
    print([(r['threshold'],r['quarter_cells'],r['axis_low_capture_capacity']) for r in results],flush=True)
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('candidate',type=Path);p.add_argument('out',type=Path)
    p.add_argument('--thresholds',type=F,nargs='+',default=[F(4,5),F(9,10),F(19,20),F(1)])
    a=p.parse_args();run(a.candidate,a.out,a.thresholds)
