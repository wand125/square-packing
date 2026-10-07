import math
r3=math.sqrt(3); L=1.5+r3; G=(L/2,L*r3/6)
def rot(p,a):
    x,y=p[0]-G[0],p[1]-G[1]; c,s=math.cos(a),math.sin(a); return (G[0]+c*x-s*y,G[1]+s*x+c*y)
base=[(1/r3,0),(1+1/r3,0),(1+1/r3,1),(1/r3,1)]   # flush on the base, top-left corner on the left side
sq=[[rot(p,2*math.pi*k/3) for p in base] for k in range(3)]
def inside(p):  # in T
    x,y=p; return y>=-1e-12 and r3*x-y>=-1e-12 and r3*(L-x)-y>=-1e-12
def sep(A,B):   # min over SAT axes of separation (positive = gap, 0 = touching, negative = overlap)
    best=-1e9
    for P in (A,B):
        for i in range(4):
            e=(P[(i+1)%4][0]-P[i][0],P[(i+1)%4][1]-P[i][1]); n=(-e[1],e[0]); l=math.hypot(*n); n=(n[0]/l,n[1]/l)
            pa=[n[0]*x+n[1]*y for x,y in A]; pb=[n[0]*x+n[1]*y for x,y in B]
            best=max(best,min(pb)-max(pa),min(pa)-max(pb))
    return best
print("L=",L,"all vertices inside:",all(inside(p) for s in sq for p in s))
print("pairwise separations:",[round(sep(sq[i],sq[j]),12) for i in range(3) for j in range(i+1,3)])
