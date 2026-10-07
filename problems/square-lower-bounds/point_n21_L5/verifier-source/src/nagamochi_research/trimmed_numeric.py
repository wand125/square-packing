"""Numerical octagon coefficients; radial columns keep conservative square cores."""
import numpy as np
from numba import njit
from unified_geometry import matrix as square_matrix

@njit(cache=True)
def polygon_coefficient(kind,g,planes):
    if kind==1:
        for a,b,c in planes:
            if a*g[0]+b*g[1]>c:return 0.
        return 1.
    if kind==2:
        lo=0.;hi=1.
        for a,b,c in planes:
            v=c-a*g[0]-b*g[1];s=a*(g[2]-g[0])+b*(g[3]-g[1])
            if s==0:
                if v<0:return 0.
            elif s>0:hi=min(hi,v/s)
            else:lo=max(lo,v/s)
        return max(0.,hi-lo)
    inside=True
    for a,b,c in planes:
        lo=a*(g[0] if a>=0 else g[2])+b*(g[1] if b>=0 else g[3])
        hi=a*(g[2] if a>=0 else g[0])+b*(g[3] if b>=0 else g[1])
        if lo>c:return 0.
        if hi>c:inside=False
    if inside:return 1.
    poly=np.zeros((16,2));poly[0]=[g[0],g[1]];poly[1]=[g[2],g[1]];poly[2]=[g[2],g[3]];poly[3]=[g[0],g[3]];count=4
    for a,b,c in planes:
        new=np.zeros((16,2));size=0
        for i in range(count):
            P=poly[i];Q=poly[(i+1)%count];v=c-a*P[0]-b*P[1];w=c-a*Q[0]-b*Q[1]
            if v>=0:new[size]=P;size+=1
            if v*w<0:
                f=v/(v-w);new[size]=P+f*(Q-P);size+=1
        poly=new;count=size
    total=0.
    for i in range(count):total+=poly[i,0]*poly[(i+1)%count,1]-poly[i,1]*poly[(i+1)%count,0]
    return abs(total)/2/((g[2]-g[0])*(g[3]-g[1]))

@njit(cache=True)
def matrix(poses,B,expanded,h,gamma):
    result=np.zeros((len(poses),len(expanded)//8))
    radial=[j for j in range(len(expanded)//8) if expanded[8*j,0]>2]
    if len(radial):
        rex=np.empty((8*len(radial),5))
        for j in range(len(radial)):rex[8*j:8*j+8]=expanded[8*radial[j]:8*radial[j]+8]
        values=square_matrix(poses,B,rex)
        for j in range(len(radial)):result[:,radial[j]]=values[:,j]
    for i in range(len(poses)):
        x,y,t=poses[i];c=(1-t*t)/(1+t*t);s=2*t/(1+t*t);planes=np.zeros((8,3));k=0
        for swap in (0,1):
            for sx in (-1.,1.):
                for sy in (-1.,1.):
                    a=sx*(1. if swap==0 else gamma);b=sy*(gamma if swap==0 else 1.)
                    A=a*c-b*s;BB=a*s+b*c;planes[k]=[A,BB,h+A*x+BB*y];k+=1
        for col in range(len(expanded)//8):
            if expanded[8*col,0]>2:continue
            value=0.
            for j in range(8*col,8*col+8):value+=polygon_coefficient(int(expanded[j,0]),expanded[j,1:],planes)
            result[i,col]=value/8
    return result
