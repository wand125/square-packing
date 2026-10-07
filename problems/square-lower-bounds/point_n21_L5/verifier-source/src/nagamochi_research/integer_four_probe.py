"""Exact diagnostics for n12 -> 4; none is a certificate for s(12)=4."""
from fractions import Fraction as F
from itertools import combinations
from endpoint_joint_probe import separation
from score import square, cross, sub


def grid_avoiders():
    centres = [(F(3,4), F(3,2)), (F(5,2), F(3,4)),
               (F(13,4), F(5,2)), (F(3,2), F(13,4))]
    side, t = F(21,20), F(2,5)
    polys = [square(x,y,side,t) for x,y in centres]
    grid = [(F(i),F(j)) for i in range(1,4) for j in range(1,4)]
    for poly in polys:
        assert all(0 <= x <= 4 and 0 <= y <= 4 for x,y in poly)
        assert all(not all(cross(sub(q,p),sub(z,p)) > 0
                           for p,q in zip(poly,poly[1:]+poly[:1])) for z in grid)
    pairs = []
    for i,j in combinations(range(4),2):
        witness = separation(polys[i],polys[j])
        assert witness is not None
        pairs.append(dict(i=i,j=j,**witness))
    return dict(status='EXACT_FOUR_GRID_AVOIDERS', L='4', side=str(side), t=str(t),
                centres=[list(map(str,p)) for p in centres], pairs=pairs,
                grid_points=9, necessary_avoiders_for_12=3,
                limitation='Not a packing of twelve squares. Grid-avoider count alone cannot give a contradiction.')


if __name__ == '__main__':
    import argparse
    import json
    from pathlib import Path
    from integer_five_net_family import family, identity_certificate
    from mixed_endpoint_probe import probe
    parser = argparse.ArgumentParser()
    parser.add_argument('candidate', type=Path)
    parser.add_argument('out', type=Path)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    data = json.loads(args.candidate.read_text())
    assert data['n'] == 12
    results = {'endpoint-probe': probe(data,k=4,targets=['3.96','3.98','3.99','4']),
               'grid-avoiders': grid_avoiders(),
               'net-family': dict(identity=identity_certificate(4),
                                  examples=[family(e,4) for e in ['1/25','1/100','1/1000','1/10000']])}
    for name, result in results.items():
        with (args.out / (name+'.json')).open('x') as f:
            json.dump(result,f,indent=2)
