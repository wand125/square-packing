// Research copy of frozen rectangle verifier; mixed contributions and bounded frontier.
// Outward-rounded interval verification. Compile without fast-math or FMA contraction.
#include <algorithm>
#include <array>
#include <cassert>
#include <cfenv>
#include <cmath>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <string>
#include <vector>
#include <chrono>
using namespace std;
double dn(double x){return nextafter(x,-INFINITY);} double up(double x){return nextafter(x,INFINITY);}
struct I {double l,h; I(double x=0):l(x),h(x){} I(double a,double b):l(a),h(b){} double mid()const{return l+(h-l)/2;}};
I operator+(I a,I b){return {dn(a.l+b.l),up(a.h+b.h)};}
I operator-(I a,I b){return {dn(a.l-b.h),up(a.h-b.l)};}
I operator-(I a){return {-a.h,-a.l};}
I operator*(I a,I b){double x[]={a.l*b.l,a.l*b.h,a.h*b.l,a.h*b.h};return {dn(*min_element(x,x+4)),up(*max_element(x,x+4))};}
I operator/(I a,I b){assert(b.l>0 || b.h<0);return a*I(dn(1/b.h),up(1/b.l));}
I mn(I a,I b){return {min(a.l,b.l),min(a.h,b.h)};} I mx(I a,I b){return {max(a.l,b.l),max(a.h,b.h)};}
I pos(I a){return {max(0.,a.l),max(0.,a.h)};} I ab(I a){return a.l>=0?a:(a.h<=0?-a:I(0,max(-a.l,a.h)));}
I readI(istream&in){string a,b;in>>a>>b;return {stod(a),stod(b)};}
struct R {I a,b,d,e,rho;}; struct P{double x,y;};
I cross(P a,P b,P c){return (I(b.x)-I(a.x))*(I(c.y)-I(a.y))-(I(b.y)-I(a.y))*(I(c.x)-I(a.x));}
double cr(P a,P b,P c){return (b.x-a.x)*(c.y-a.y)-(b.y-a.y)*(c.x-a.x);}

// Construct any polygon, then independently prove it is convex and inside the
// exact intersection. Its interval area is a rigorous lower bound regardless
// of errors in the approximate clipping stage.
double area_lower(const R&r,I cx,I cy,I c,I s,I B){
    I ex=B*(c+s)/I(2);
    if(r.d.h<= (cx-ex).l || r.a.l>= (cx+ex).h || r.e.h<= (cy-ex).l || r.b.l>= (cy+ex).h)return 0;
    I rx=(r.a+r.d)/I(2)-cx,ry=(r.b+r.e)/I(2)-cy;
    I hx=(r.d-r.a)/I(2),hy=(r.e-r.b)/I(2);
    if((ab(c*rx+s*ry)+c*hx+s*hy).h<=(B/I(2)).l && (ab(-s*rx+c*ry)+s*hx+c*hy).h<=(B/I(2)).l)
        return max(0.,((r.d-r.a)*(r.e-r.b)).l);
    double cc=c.mid(),ss=s.mid(),xx=cx.mid(),yy=cy.mid(),bb=B.mid();
    vector<P> p,q;
    for(auto uv: {P{-1,-1},P{1,-1},P{1,1},P{-1,1}})p.push_back({xx+bb/2*(cc*uv.x-ss*uv.y),yy+bb/2*(ss*uv.x+cc*uv.y)});
    double edges[]={r.a.mid(),r.b.mid(),r.d.mid(),r.e.mid()};
    for(int side=0;side<4;side++){
        q.clear();int axis=side%2;double sign=side<2?1:-1;
        for(size_t j=0;j<p.size();j++){
            P v=p[j],u=p[(j+p.size()-1)%p.size()];
            double dj=sign*((axis?v.y:v.x)-edges[side]),dk=sign*((axis?u.y:u.x)-edges[side]);
            if((dj>=0)!=(dk>=0)){double t=dk/(dk-dj);q.push_back({u.x+t*(v.x-u.x),u.y+t*(v.y-u.y)});}
            if(dj>=0)q.push_back(v);
        }
        p.swap(q);if(p.size()<3)return 0;
    }
    P center{0,0};for(auto v:p){center.x+=v.x/p.size();center.y+=v.y/p.size();}
    for(auto &v:p){v.x=center.x+(v.x-center.x)*(1-1e-9);v.y=center.y+(v.y-center.y)*(1-1e-9);}
    sort(p.begin(),p.end(),[](P a,P b){return a.x<b.x || (a.x==b.x && a.y<b.y);});
    vector<P> hull;
    for(auto v:p){while(hull.size()>1 && cr(hull[hull.size()-2],hull.back(),v)<=1e-14)hull.pop_back();hull.push_back(v);}
    size_t start=hull.size();
    for(int j=int(p.size())-2;j>=0;j--){P v=p[j];while(hull.size()>start && cr(hull[hull.size()-2],hull.back(),v)<=1e-14)hull.pop_back();hull.push_back(v);}
    if(hull.size()<4)return 0;hull.pop_back();p=hull;
    for(auto v:p){
        if(v.x<r.a.h || v.x>r.d.l || v.y<r.b.h || v.y>r.e.l)return 0;
        I dx=I(v.x)-cx,dy=I(v.y)-cy;
        if(ab(c*dx+s*dy).h>(B/I(2)).l || ab(-s*dx+c*dy).h>(B/I(2)).l)return 0;
    }
    for(size_t i=0;i<p.size();i++)for(size_t j=0;j<p.size();j++){
        if(j==i || j==(i+1)%p.size())continue;
        if(cross(p[i],p[(i+1)%p.size()],p[j]).l<=0)return 0;
    }
    I area(0);for(size_t j=1;j+1<p.size();j++)area=area+cross(p[0],p[j],p[j+1])/I(2);
    return max(0.,area.l);
}

I slice(I z,I C,I O,I lo,I hi,I A1,I A2,I k1,I k2){
    I m1=O+k1*(z-C),m2=O+k2*(z-C);
    return pos(mn(hi,mn(m1+A1,m2+A2))-mx(lo,mx(m1-A1,m2-A2)));
}
struct Bound {double lower,fx,fy,center;};
struct Atom {I x,y,w;};
Bound bound(I cx,I cy,I dx,I dy,I B,I c,I s,const vector<R>&rs,const vector<Atom>&atoms){
    I ex=B*(c+s)/I(2);
    I X(cx.l-dx.h,cx.h+dx.h),Y(cy.l-dy.h,cy.h+dy.h);X={dn(X.l),up(X.h)};Y={dn(Y.l),up(Y.h)};
    I xb=X-ex,xt=X+ex,yb=Y-ex,yt=Y+ex;
    I fx(0),fy(0);double f=0;I A1=B/(I(2)*s),A2=B/(I(2)*c),k1=-c/s,k2=s/c;
    for(const auto&r:rs){
        if(r.d.h<=xb.l || r.a.l>=xt.h || r.e.h<=yb.l || r.b.l>=yt.h)continue;
        f=dn(f+dn(r.rho.l*area_lower(r,cx,cy,c,s,B)));
        I a(0),b(0),d(0),e(0);
        if(r.a.h>=xb.l && r.a.l<=xt.h)a=slice(r.a,X,Y,r.b,r.e,A1,A2,k1,k2);
        if(r.d.h>=xb.l && r.d.l<=xt.h)b=slice(r.d,X,Y,r.b,r.e,A1,A2,k1,k2);
        if(r.b.h>=yb.l && r.b.l<=yt.h)d=slice(r.b,Y,X,r.a,r.d,A2,A1,-k2,-k1);
        if(r.e.h>=yb.l && r.e.l<=yt.h)e=slice(r.e,Y,X,r.a,r.d,A2,A1,-k2,-k1);
        fx=fx+r.rho*(a-b);fy=fy+r.rho*(d-e);
    }
    double rx=up(dx.h*ab(fx).h),ry=up(dy.h*ab(fy).h);
    double atom=0;
    for(const auto &p:atoms){
        I px=p.x-X,py=p.y-Y;
        if(ab(c*px+s*py).h<=(B/I(2)).l && ab(-s*px+c*py).h<=(B/I(2)).l)
            atom=max(0.,dn(atom+p.w.l));
    }
    return {dn(dn(dn(f-rx)-ry)+atom),rx,ry,dn(f+atom)};
}

int main(int argc,char**argv){
    static_assert(numeric_limits<double>::is_iec559 && sizeof(double)==8);
    assert(fegetround()==FE_TONEAREST); assert(argc>=3);
    ifstream in(argv[1]); assert(in);
    I L=readI(in),B=readI(in),E=readI(in),c=readI(in),s=readI(in),gamma=readI(in);
    int n;in>>n;vector<R>rs;
    for(int i=0;i<n;i++){R r;r.a=readI(in);r.b=readI(in);r.d=readI(in);r.e=readI(in);r.rho=readI(in);assert(r.rho.l>=0);rs.push_back(r);}
    in>>n;vector<Atom>atoms;
    for(int i=0;i<n;i++){Atom p;p.x=readI(in);p.y=readI(in);p.w=readI(in);assert(p.w.l>=0);atoms.push_back(p);}assert(in);
    cout<<setprecision(17);
    if(string(argv[2])=="query"){
        while(cin>>n){I cx=readI(cin),cy=readI(cin),dx=readI(cin),dy=readI(cin);assert(cin);
            auto b=bound(cx,cy,dx,dy,B,c,s,rs,atoms);cout<<b.lower<<endl;
        }return 0;
    }
    long long limit=stoll(argv[2]),nodes=0,leaves=0;assert(limit>0);
    auto start=chrono::steady_clock::now();double minbound=INFINITY;
    vector<array<double,4>> stack{{.5,.5,.5,.5}};
    bool region=argc==4;
    if(region){ifstream box(argv[3]);string v;for(int k=0;k<4;k++){box>>v;stack[0][k]=stod(v);}assert(box);
        auto z=stack[0];assert(z[2]>0 && z[3]>0 && z[0]-z[2]>=0 && z[0]+z[2]<=1 && z[1]-z[3]>=0 && z[1]+z[3]<=1);
    }
    while(!stack.empty() && nodes<limit){
        auto z=stack.back();stack.pop_back();nodes++;
        auto b=bound(L/I(2)+I(z[0])*E,L/I(2)+I(z[1])*E,I(z[2])*E,I(z[3])*E,B,c,s,rs,atoms);
        if(b.lower>=gamma.h){leaves++;minbound=min(minbound,b.lower);continue;}
        if(min(z[2],z[3])<=0x1p-40){stack.push_back(z);break;}
        // Density derivatives suggest a split; cap anisotropy for point jumps.
        int axis=b.fx>=b.fy?0:1;
        if(z[2]>4*z[3])axis=0;else if(z[3]>4*z[2])axis=1;
        else if(b.fx+b.fy<1e-14)axis=z[2]>=z[3]?0:1;
        z[axis+2]/=2;auto other=z;z[axis]-=z[axis+2];other[axis]+=other[axis+2];stack.push_back(z);stack.push_back(other);
    }
    cout<<"{\"status\":\""<<(stack.empty()?(region?"REGION_VERIFIED":"ANGLE_VERIFIED"):(region?"REGION_UNRESOLVED":"ANGLE_UNRESOLVED"))<<"\",\"nodes\":"<<nodes<<",\"leaves\":"<<leaves<<",\"lower\":";
    if(isfinite(minbound))cout<<minbound;else cout<<"null";
    cout<<",\"seconds\":"<<chrono::duration<double>(chrono::steady_clock::now()-start).count()<<",\"frontier\":[";
    for(size_t i=0;i<stack.size();i++){if(i)cout<<",";auto z=stack[i];cout<<"["<<z[0]<<","<<z[1]<<","<<z[2]<<","<<z[3]<<"]";}
    cout<<"]}"<<endl;
}
