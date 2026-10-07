"""Replay every finite score with arbitrary-size integers and audit geometry samples.
This does not certify the continuous pose domain.
"""
from pathlib import Path
from fractions import Fraction as F
import json,hashlib,argparse,random
import numpy as np
from probe_external_integer_bridge import read
from score import square,contains

def run(directory,out):
 assert not out.exists();report=json.loads((directory/'result.json').read_text());candidate=directory/'candidate.txt';assert hashlib.sha256(candidate.read_bytes()).hexdigest()==report['sha256'];L,span,W,pts=read(candidate);state=np.load(directory/'incidence.npz');counts=state['counts'];ids=state['orbit_ids'];sizes=state['sizes'];poses=json.loads((directory/'poses.json').read_text());assert len(poses)==len(counts)==report['training_rows'];assert len(ids)==len(pts);orbit_weights=[]
 for j,k in enumerate(sizes):
  group=[pts[i][2] for i in range(len(pts)) if ids[i]==j];assert len(group)==k and len(set(group))==1;orbit_weights.append(group[0])
 assert np.all(counts>=0) and np.all(counts<=sizes)
 exact=[sum(int(n)*w for n,w in zip(row,orbit_weights)) for row in counts];minimum=F(min(exact),W);assert minimum==F(report['training_minimum']) and minimum>=1;mass=F(sum(w for x,y,w in pts),W);assert mass==F(report['total_mass']) and mass<F(20999,1000)
 rng=random.Random(9280600);chosen=sorted(set([exact.index(min(exact))]+rng.sample(range(len(poses)),32)));checked=[]
 for i in chosen:
  x,y,t=map(F,poses[i]);poly=square(x,y,F(1),t);assert all(0<=x<=L and 0<=y<=L for x,y in poly);score=sum((F(w,W) for x,y,w in pts if contains(poly,(F(x)*L/span,F(y)*L/span))),F(0));assert score==F(exact[i],W);checked.append(i)
 data=dict(status='ALL_FINITE_SCORES_REPLAYED',candidate_sha256=report['sha256'],rows=len(exact),minimum=str(minimum),total_mass=str(mass),polygon_geometry_rows=checked,geometry_all_rows_independently_replayed=False,general_coverage_verified=False)
 out.write_text(json.dumps(data,indent=2));print(data)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('directory',type=Path);p.add_argument('out',type=Path);a=p.parse_args();run(a.directory,a.out)
