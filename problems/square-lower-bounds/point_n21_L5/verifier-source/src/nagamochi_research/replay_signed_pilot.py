"""Rebuild full geometry; replay all reported integer witnesses and band bound."""
from pathlib import Path
from fractions import Fraction as F
import json,gzip,hashlib,argparse
from two_angle_cover import patterns
from packing_lemmas import axis_core_halfwidth,angle_envelope


def run(parent,folder):
    s=json.loads(parent.read_text());sha=hashlib.sha256(parent.read_bytes()).hexdigest()
    with gzip.open(folder/'geometry.json.gz','rt') as f:g=json.load(f)
    report=json.loads((folder/'results.json').read_text());assert sha==g['source_sha256']==report['source_sha256']
    pts={tuple(map(F,p)) for p in s['points']};pts=sorted(pts|{(x,-y) for x,y in pts})
    assert g['points']==[list(map(str,p)) for p in pts]
    L,t,B,h=map(F,(s['L'],s['t'],s['B'],s['h']));assert B*angle_envelope(t,h)[0]<1
    print('REBUILD_AXIS',flush=True);axis=patterns(pts,L,F(0),B)['patterns']
    print('REBUILD_POSITIVE',flush=True);positive=patterns(pts,L,t,B,h)['patterns']
    # Rebuild the negative geometry directly, rather than reusing permutation.
    print('REBUILD_NEGATIVE',flush=True);negative=patterns([(x,-y) for x,y in pts],L,t,B,h)['patterns']
    ds=[axis,positive,negative];assert ds==g['domains']
    bounds=[];count=0
    for r in report['records']:
        if 'numerators' not in r:continue
        w=r['numerators'];assert len(w)==len(pts) and all(type(x) is int and x>=0 for x in w)
        floors=[min(sum(w[i] for i in row) for row in rows) for rows in ds]
        total=sum(w);assert total==r['total'] and floors==r['floors']
        assert len(r['counts'])==3 and sum(r['counts'])==s['n'] and all(type(x) is int and x>=0 for x in r['counts'])
        gap=sum(a*b for a,b in zip(r['counts'],floors))-total
        assert gap==r['gap'] and r['exact_exclusion']==(gap>0);count+=1
        if min(floors)>0:bounds.append(F(total,min(floors)))
    result=dict(status='FULL_GEOMETRY_AND_INTEGER_WITNESSES_REPLAYED',L=str(L),axis_halfwidth=str(axis_core_halfwidth(B)),
                positive_band=[str(t-h),str(t+h)],negative_band=[str(-t-h),str(-t+h)],witnesses=count,
                uniform_band_mass=str(min(bounds)) if bounds else None,
                band_capacity=min(bounds).numerator//min(bounds).denominator if bounds else None,
                general_packing_exclusion=False)
    (folder/'replay.json').write_text(json.dumps(result,indent=2));print(json.dumps(result),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('parent',type=Path);p.add_argument('folder',type=Path);a=p.parse_args();run(a.parent,a.folder)
