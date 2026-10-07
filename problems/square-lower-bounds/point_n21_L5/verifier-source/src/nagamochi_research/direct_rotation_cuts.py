"""Transport conditional core exclusions through quarter-turn containments.

For saturated axis cells the square centre container and occupied cell set are
quarter-turn invariant. Nominal axis and rotor squares are each invariant
under a quarter turn about their own centres. Rotating every centre therefore
preserves containment and strict nonoverlap. If rotated P_i is contained in
P_j, a packing in target regions i would give a packing in source regions j.
Reflections are deliberately absent: they change the specified rotor band.
"""
from itertools import combinations, product
from fractions import Fraction as F
from saturated_axis_cells import contained
from joint_angle_lp import rotation


def extend(cells, pieces, t, side, cuts):
    # Verify the geometric prerequisites instead of assuming region labels
    # transform as a permutation (the direct partition is asymmetric).
    canonical={tuple(sorted(p)) for p in cells.values()}
    assert all(tuple(sorted((-y,x) for x,y in p)) in canonical for p in cells.values())
    c,s=rotation(F(t));R=F(side)
    assert all(max(a*x+b*y for x,y in p)-min(a*x+b*y for x,y in p)<R
               for p in pieces for a,b in ((c,s),(-s,c)))
    maps=[]
    for turns in (1,2,3):
        mapping=[]
        for p in pieces:
            rotated=list(p)
            for _ in range(turns):rotated=[(-y,x) for x,y in rotated]
            mapping.append(next((j for j,z in enumerate(pieces) if contained(rotated,z)),None))
        maps.append(mapping)
    known={tuple(c) for c in cuts};derivations=[]
    # Equal mapped IDs imply both boxes lie in a capacity-one region.
    for turns,mapping in enumerate(maps,1):
        for i,j in combinations(range(len(pieces)),2):
            if mapping[i] is not None and mapping[i]==mapping[j] and (i,j) not in known:
                known.add((i,j));derivations.append(dict(target=[i,j],turns=turns,capacity_region=mapping[i]))
    changed=True
    while changed:
        changed=False
        for source in sorted(known.copy(), key=lambda c:(len(c),c)):
            for turns,mapping in enumerate(maps,1):
                choices=[[i for i,j in enumerate(mapping) if j==v] for v in source]
                for selected in product(*choices):
                    target=tuple(sorted(selected))
                    assert len(set(target))==len(source)
                    if target in known:continue
                    known.add(target);changed=True
                    derivations.append(dict(target=list(target),source=list(source),turns=turns))
    return sorted(known,key=lambda c:(len(c),c)),dict(maps=maps,derivations=derivations)
