"""PL25: remove dominated capture sets for nonnegative point weights."""

def minimal_indices(patterns):
    masks=[]
    for i,row in enumerate(patterns):
        if any(type(x) is not int or x<0 for x in row):raise ValueError('Nonnegative integer indices required')
        masks.append((sum(1<<x for x in set(row)),i))
    kept=[];seen=set()
    for mask,i in sorted(masks,key=lambda z:(z[0].bit_count(),z[1])):
        if mask in seen:continue
        seen.add(mask)
        if not any(small & mask==small for small,_ in kept):kept.append((mask,i))
    return [i for _,i in kept]
