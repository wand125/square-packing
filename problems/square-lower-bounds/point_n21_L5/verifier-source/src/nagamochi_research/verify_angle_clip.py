"""Independent rational check of one-sided physical angle clipping."""
from fractions import Fraction as F


def verify(L, original, cut):
    L=F(L); b=list(map(F,original)); cut=F(cut)
    if L<=0 or len(b)!=6 or any(b[i]>b[i+1] for i in (0,2,4)) or not 0<=b[4]<=cut<=b[5]<=F(1,2):
        raise ValueError('Invalid clip domain')
    if cut==b[5]:return dict(clipped=False)
    # w(t)=(1+2t-t²)/(1+t²) increases up to sqrt(2)-1.
    if b[5]*b[5]+2*b[5]>1:
        raise ValueError('Clipped interval is not increasing')
    K=2*min(b[1],L-b[0],b[3],L-b[2])
    w=(1+2*cut-cut*cut)/(1+cut*cut)
    if w<K:
        raise ValueError('Clip may discard admissible poses')
    return dict(clipped=True,excluded_interval=[str(cut),str(b[5])],
                lower_open=True,upper_open=False,capacity=str(K),width_at_cut=str(w),
                reason='For t>cut, strict increase gives w(t)>K; no centre in original box is physical')
