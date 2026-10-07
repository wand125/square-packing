"""Replay axis certificate using integer inequalities for every cached entry."""
import argparse,json,hashlib
from pathlib import Path
from fractions import Fraction as F
import numpy as np
from mixed_density_check import expand
from mixed_net_audit import symmetry,net_certificate,candidate_net
from mixed_axis_cells import axis_cell_lower


def replay(folder,candidate=None):
    result=json.loads((folder/'result.json').read_text());data=json.loads(Path(candidate or result['candidate']).read_text());model=expand(data)
    assert result['status']=='AXIS_VERIFIED' and result['net_index']==0 and result['digest']==model[-1]
    expected=dict(version='mixed-axis-integer-v1',candidate_digest=model[-1],gamma=result['gamma'],net_index=0,net_step=str(candidate_net(data)[0]),net_last=candidate_net(data)[1],centre_domain='D4 quarter of unit-bin centre domain')
    assert result['proof_spec']==expected
    assert result['proof_digest']==hashlib.sha256(json.dumps(expected,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    symmetry(model);net_certificate(model[1],*candidate_net(data));gamma=F(result['gamma']);assert gamma>0 and model[-2]<data['n']*gamma
    L,B,rs,ps,total,digest=model;axes=[[F(v) for v in a] for a in result['axes']];lo=L/2;hi=L-F(1,2)
    for dim,axis in enumerate(axes):
        expected={lo,hi}
        for r in rs:
            for endpoint in (r[dim],r[dim+2]):
                for shift in (-B/2,B/2):
                    if lo<endpoint+shift<hi:expected.add(endpoint+shift)
        for p,w in ps:
            for shift in (-B/2,B/2):
                if lo<p[dim]+shift<hi:expected.add(p[dim]+shift)
        assert axis==sorted(expected)
    z=np.load(folder/'integer-tables.npz');meta=result['table_metadata'];D=int(meta['coordinate_denominator']);W=1<<meta['weight_bits'];S=1<<meta['fraction_bits']
    assert D>0 and W>0 and S>0 and F(result['denominator'])==W*S*S
    def integer(v):
        q=v*D;assert q.denominator==1;return q.numerator
    ir=[[integer(v) for v in r[:4]] for r in rs];ip=[[integer(v) for v in p] for p,w in ps];h=integer(B/2)
    wi=z['density_weights'];pi=z['point_weights']
    for array in z.values():assert array.dtype==np.int64 and np.all(array>=0)
    assert len(wi)==len(rs) and len(pi)==len(ps)
    for v,r in zip(wi,rs):assert F(int(v),W)<=r[4]*(r[2]-r[0])*(r[3]-r[1])
    for v,(p,w) in zip(pi,ps):assert F(int(v),W)<=w
    assert (sum(map(int,wi))+sum(map(int,pi)))*S*S<2**63
    for dim,(axis,f,mask) in enumerate(zip(axes,(z['fx'],z['fy']),(z['hx'],z['hy']))):
        coords=[integer(v) for v in axis]
        assert f.shape==(len(axis),len(rs)) and mask.shape==(len(axis)-1,len(ps))
        assert np.all(f<=S) and np.all(mask<=1)
        for i,x in enumerate(coords):
            for j,r in enumerate(ir):
                length=max(0,min(r[dim+2],x+h)-max(r[dim],x-h))
                assert int(f[i,j])*(r[dim+2]-r[dim])<=S*length
        # Independent from midpoint capture: a charged atom must be in EVERY
        # square in the CLOSED cell. No boundary-only capture can slip in.
        for i,(a,b) in enumerate(zip(coords,coords[1:])):
            for j,p in enumerate(ip):
                if mask[i,j]:assert p[dim]-h<=a and b<=p[dim]+h
    den=W*S*S;density=(z['fx']*wi)@z['fy'].T
    lower=np.minimum(np.minimum(density[:-1,:-1],density[1:,:-1]),np.minimum(density[:-1,1:],density[1:,1:]))+((z['hx']*pi)@z['hy'].T)*S*S
    threshold=-((-gamma.numerator*den)//gamma.denominator);missing=set(map(tuple,np.argwhere(lower<threshold).tolist()));patches=set()
    for patch in result['exact_patches']:
        i,j=patch['i'],patch['j'];assert (i,j) in missing and (i,j) not in patches
        lower_exact=axis_cell_lower(model,axes[0][i],axes[0][i+1],axes[1][j],axes[1][j+1])
        assert lower_exact==F(patch['lower']) and lower_exact>=gamma;patches.add((i,j))
    assert missing==patches and lower.size==result['cells']
    assert F(int(lower.min()),den)==F(result['integer_minimum'])
    record=dict(status='AXIS_CERTIFICATE_REPLAYED',digest=digest,cells=int(lower.size),gamma=str(gamma),integer_minimum=float(F(int(lower.min()),den)),scope='Net angle zero only, no full packing certification.')
    (folder/'replayed.json').write_text(json.dumps(record,indent=2));print(json.dumps(record));return record
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('folder',type=Path);args=p.parse_args();replay(args.folder)
