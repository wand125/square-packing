"""D4 covariance of pose boxes for a D4-invariant measure (PL22).

Only scores are transported. Original pose domains stay in the packing
model; reflecting each physical box separately need not preserve packing.
"""
def images(box,L):
    x0,x1,y0,y1,t0,t1=box
    out=set()
    for swap in (False,True):
        u0,u1,v0,v1=(y0,y1,x0,x1) if swap else (x0,x1,y0,y1)
        for sx,sy in ((1,1),(1,-1),(-1,1),(-1,-1)):
            a,b=(u0,u1) if sx==1 else (L-u1,L-u0)
            c,d=(v0,v1) if sy==1 else (L-v1,L-v0)
            angle=(t0,t1) if sx*sy*(-1 if swap else 1)>0 else (-t1,-t0)
            out.add((a,b,c,d,*angle))
    return sorted(out)


def cached_bound(model,func,symmetry_name=None):
    if symmetry_name not in (None,'D4'):raise ValueError('Unknown symmetry')
    if symmetry_name=='D4':
        from mixed_net_audit import symmetry
        symmetry(model)
    cache={}
    def evaluate(*box):
        key=images(box,model[0])[0] if symmetry_name=='D4' else tuple(box)
        if key not in cache:cache[key]=func(model,*key)
        return cache[key]
    return evaluate,cache
