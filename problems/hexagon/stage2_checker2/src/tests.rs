use super::*;
use crate::{geometry::{axes,poses,overlap,gap},interval::{next_up,next_down}};
#[test]
fn next_float_edges(){
    for x in [-1e300,-10.0,-1.0,-0.1,0.1,1.0,10.0,1e300]{assert!(x<next_up(x));assert!(next_down(x)<x);assert_eq!(next_down(next_up(x)),x);assert_eq!(next_up(next_down(x)),x);}
    for z in [0.0,-0.0]{assert_eq!(next_up(z).to_bits(),1);assert_eq!(next_down(z).to_bits(),(1u64<<63)|1);}
    assert_eq!(next_down(f64::from_bits(1)),0.0);assert_eq!(next_up(-f64::from_bits(1)),-0.0);
    assert_eq!(next_up(f64::MAX),f64::INFINITY);assert_eq!(next_down(-f64::MAX),f64::NEG_INFINITY);
    assert_eq!(next_up(f64::INFINITY),f64::INFINITY);assert_eq!(next_down(f64::INFINITY),f64::MAX);
    assert_eq!(next_down(f64::NEG_INFINITY),f64::NEG_INFINITY);assert_eq!(next_up(f64::NEG_INFINITY),-f64::MAX);
    assert!(next_up(f64::NAN).is_nan());assert!(next_down(f64::NAN).is_nan());
}
#[derive(Clone,Copy,Debug)]struct F{p:i128,q:i128}
impl F{
    fn new(p:i128,q:i128)->Self{assert_ne!(q,0);let (p,q)=if q<0{(-p,-q)}else{(p,q)};let(mut a,mut b)=(p.abs(),q);while b!=0{(a,b)=(b,a%b)}Self{p:p/a,q:q/a}}
    fn add(self,b:Self)->Self{Self::new(self.p*b.q+b.p*self.q,self.q*b.q)}
    fn neg(self)->Self{Self::new(-self.p,self.q)}
    fn mul(self,b:Self)->Self{Self::new(self.p*b.p,self.q*b.q)}
    fn div(self,b:Self)->Self{Self::new(self.p*b.q,self.q*b.p)}
    fn le(self,b:Self)->bool{self.p*b.q<=b.p*self.q}
    fn interval(self)->I{I::rational(self.p as i64,self.q as i64).unwrap()}
}
// Compare a binary endpoint with an exact small i128 fraction. No rounded reference
// division: decode the IEEE significand/exponent and cross multiply as integers.
fn float_cmp(x:f64,f:F)->std::cmp::Ordering{
    use std::cmp::Ordering::*;
    assert!(x.is_finite());assert!(f.q<1_000_000_000_000);
    if x==0.0{return 0i128.cmp(&f.p)}
    if x<0.0{return float_cmp(-x,f.neg()).reverse()}
    if f.p<=0{return Greater}
    let bits=x.to_bits();let eb=((bits>>52)&0x7ff)as i32;
    let m=if eb==0{bits&((1u64<<52)-1)}else{(bits&((1u64<<52)-1))|(1u64<<52)}as i128;
    let e=if eb==0{-1074}else{eb-1023-52};
    if e < -100 {return Less} // x < 2^-47 < 1/q for these small test fractions.
    if e>=0{(m*(1i128<<e)*f.q).cmp(&f.p)}else{(m*f.q).cmp(&(f.p*(1i128<<(-e))))}
}
fn contains(i:I,f:F){assert!(float_cmp(i.lo,f)!=std::cmp::Ordering::Greater,"{i:?} excludes {f:?}");assert!(float_cmp(i.hi,f)!=std::cmp::Ordering::Less,"{i:?} excludes {f:?}");}
#[test]
fn interval_random_exact_rationals(){
    let mut seed=0x458facdfe23178u64;
    let mut rand=||{seed=seed.wrapping_mul(6364136223846793005).wrapping_add(1442695040888963407);seed>>32};
    for _ in 0..5000{
        let mut sample=||F::new((rand()%2001)as i128-1000,(rand()%97+1)as i128);
        let(mut a,mut b,mut c,mut d)=(sample(),sample(),sample(),sample());
        if !a.le(b){std::mem::swap(&mut a,&mut b)}if !c.le(d){std::mem::swap(&mut c,&mut d)}
        for f in [a,b,c,d]{contains(f.interval(),f)}
        let x=I::new(a.interval().lo,b.interval().hi);let y=I::new(c.interval().lo,d.interval().hi);
        // Endpoints and an exact interior point; extrema of arithmetic are among endpoints.
        let xs=[a,b,a.add(b).div(F::new(2,1))];let ys=[c,d,c.add(d).div(F::new(2,1))];
        for p in xs{
            contains(-x,p.neg());contains(x.sqr(),p.mul(p));contains(x.abs(),F::new(p.p.abs(),p.q));
            for q in ys{contains(x+y,p.add(q));contains(x-y,p.add(q.neg()));contains(x*y,p.mul(q));if y.lo>0.0 || y.hi<0.0{contains(x/y,p.div(q));}}
        }
        if a.p<=0 && b.p>=0{contains(x.sqr(),F::new(0,1));contains(x.abs(),F::new(0,1));}
    }
}
#[test]
fn rational_validation_and_json(){
    for (p,q) in [(1,0),(1i64<<53,1),(1,-(1i64<<53)),(i64::MIN,1)]{assert!(I::rational(p,q).is_err())}
    assert!(json::parse(r#"{"excused":[["1/2",0]],"unicode":"\uD834\uDD1E"}"#).is_ok());
    for s in ["01","[1,]","{\"a\":0,\"a\":1}","1e", "1.","true false","\"\u{1}\"","\"\\uD800\""]{assert!(json::parse(s).is_err(),"{s}");}
    assert!(selection(Some("9-2"),742).is_err());assert!(selection(Some("742"),742).is_err());
    assert!(Geometry::new(1.01,true).is_err());assert!(Geometry::new(f64::NAN,false).is_err());
}
fn pinwheel(scale:f64,expand:f64)->Node{
    let r=3.0_f64.sqrt();let v=(1.0+r)/2.0;let h=v*r/2.0;let m=[-v/2.0+0.5,-h+0.5];
    let mut n=[I::point(0.0);9];let rotations=[(1.0,0.0),(-0.5,r/2.0),(-0.5,-r/2.0)];let us=[0.0,2.0-r,1.0/r];
    for j in 0..3{let (c,s)=rotations[j];let x=scale*(c*m[0]-s*m[1]);let y=scale*(s*m[0]+c*m[1]);
        n[3*j]=I::new(x-expand,x+expand);n[3*j+1]=I::new(y-expand,y+expand);n[3*j+2]=I::new((us[j]-expand).max(0.0),(us[j]+expand).min(1.0));}
    n
}
fn order23(mut n:Node)->Node{if n[3].lo>n[6].lo{for i in 0..3{n.swap(3+i,6+i)}}n}
#[test]
fn expanded_hexagon_genuine_packing_not_pruned(){
    let scale=1.01;let n=pinwheel(scale,0.0);let r=3.0_f64.sqrt();let h=scale*(1.0+r)*r/4.0;
    let normals=[[0.0,-1.0],[r/2.0,-0.5],[r/2.0,0.5],[0.0,1.0],[-r/2.0,0.5],[-r/2.0,-0.5]];
    let mut centres=[[0.0;2];3];let mut es=[[[0.0;2];2];3];let dot=|a:[f64;2],b:[f64;2]|a[0]*b[0]+a[1]*b[1];
    let mut slack=f64::INFINITY;
    for j in 0..3{centres[j]=[n[3*j].lo,n[3*j+1].lo];let u=n[3*j+2].lo;let c=(1.0-u*u)/(1.0+u*u);let s=2.0*u/(1.0+u*u);es[j]=[[c,s],[-s,c]];
        for normal in normals{slack=slack.min(h-dot(normal,centres[j])-(dot(normal,es[j][0]).abs()+dot(normal,es[j][1]).abs())/2.0);}}
    assert!(slack>0.001,"containment slack {slack}");
    let mut min_gap=f64::INFINITY;
    for (a,b) in [(0,1),(0,2),(1,2)]{let delta=[centres[b][0]-centres[a][0],centres[b][1]-centres[a][1]];let mut best=f64::NEG_INFINITY;
        for d in [es[a][0],es[a][1],es[b][0],es[b][1]]{let w=|j:usize|(dot(d,es[j][0]).abs()+dot(d,es[j][1]).abs())/2.0;best=best.max(dot(d,delta).abs()-w(a)-w(b));}
        assert!(best>0.001,"pair {a},{b}: {best}");min_gap=min_gap.min(best);
    }
    eprintln!("negative control: min containment slack {slack:.12}, min separating gap {min_gap:.12}");
    let g=Geometry::new(scale,false).unwrap();
    for expansion in [0.0,0.5e-6]{let n=order23(pinwheel(scale,expansion));let p=poses(&n);assert!(n[3].lo<=n[6].hi);for q in p{assert!(!g.containment(q));}for(a,b)in[(0,1),(0,2),(1,2)]{assert!(!overlap(p[a],p[b]));}assert_eq!(g.prune(&n),None);}
}
#[test]
fn pinwheel_local_lemma_identity_and_all_symmetries(){
    let g=Geometry::new(1.0,true).unwrap();let n=pinwheel(1.0,0.0);let p=poses(&n);
    for (j,q) in p.iter().enumerate(){assert!(g.local_match(*q,0,j));}assert!(g.local_lemma(&p));
    assert_eq!(g.prune(&order23(n)),Some(3));
    for turn in 0..6{for reflect in [false,true]{let angle=turn as f64*std::f64::consts::PI/3.0;let(c,s)=(angle.cos(),angle.sin());let mut transformed=n;
        for j in 0..3{let x=n[3*j].lo;let y=n[3*j+1].lo;let xx=c*x-s*y;let yy=s*x+c*y;transformed[3*j]=I::point(if reflect{-xx}else{xx});transformed[3*j+1]=I::point(yy);
            let theta=2.0*n[3*j+2].lo.atan()+angle;let theta=if reflect{std::f64::consts::PI-theta}else{theta};let theta=theta.rem_euclid(std::f64::consts::FRAC_PI_2);transformed[3*j+2]=I::point((theta/2.0).tan().min(1.0));}
        for perm in [[0,1,2],[0,2,1],[1,0,2],[1,2,0],[2,0,1],[2,1,0]]{let p=poses(&transformed);assert!(g.local_lemma(&[p[perm[0]],p[perm[1]],p[perm[2]]]),"turn={turn}, reflect={reflect}, perm={perm:?}");}
    }}
}
// An interval enclosure of the algebraic, exact pinwheel (not a nearby floating pose).
fn exact_pinwheel_enclosure()->Node{
    let r=I::enclosing(3.0_f64.sqrt());let hlf=I::point(0.5);let v=(I::point(1.0)+r)*hlf;let h=v*r*hlf;let x=-v*hlf+hlf;let y=-h+hlf;let t=r*hlf;
    let c=[[x,y],[-hlf*x-t*y,t*x-hlf*y],[-hlf*x+t*y,-t*x-hlf*y]];
    let u=[I::point(0.0),I::point(2.0)-r,I::point(1.0)/r];std::array::from_fn(|i|if i%3==2{u[i/3]}else{c[i/3][i%3]})
}
#[test]
fn tangency_is_not_replaced_with_an_epsilon(){
    for n in [pinwheel(1.0,0.0),exact_pinwheel_enclosure()]{let p=poses(&n);
        for (a,b)in[(0,1),(0,2),(1,2)]{let best=(0..2).flat_map(|o|(0..2).map(move|d|gap(p[a],p[b],o,d).hi)).fold(f64::NEG_INFINITY,f64::max);
            eprintln!("pinwheel pair {a},{b}: max G.hi = {best:e}");assert!(best>0.0 && best<1e-12);assert!(!overlap(p[a],p[b]));}
        assert!(Geometry::new(1.0,true).unwrap().local_lemma(&p));
    }
    // B does certify a strict overlap with interior margin.
    let a=poses(&pinwheel(1.0,0.0))[0];assert!(overlap(a,a));
}
#[test]
#[ignore = "Specification 3b is incompatible with mandated outward-rounded B at exact tangency; run explicitly to reproduce"]
fn requested_b_exact_pinwheel_tangency(){let p=poses(&exact_pinwheel_enclosure());assert!([(0,1),(0,2),(1,2)].iter().any(|&(a,b)|overlap(p[a],p[b])));}
#[test]
fn tight_axes_contain_algebraic_samples(){
    for i in 0..100{let u=I::new(i as f64/100.0,(i+1)as f64/100.0);let e=axes(u);for j in [i,i+1]{let f=F::new(j,100);let one=F::new(1,1);let den=one.add(f.mul(f));contains(e[0][0],one.add(f.mul(f).neg()).div(den));contains(e[0][1],F::new(2,1).mul(f).div(den));}}
}
#[test]
fn search_depth_and_accounting(){
    let g=Geometry::new(1.01,false).unwrap();let n=order23(pinwheel(1.01,0.5e-6));let r=solve(0,n,&g,4.0,3);
    assert_eq!(r.max_depth,4);assert_eq!(r.unproved,16);assert_eq!(r.nodes,31);assert_eq!(r.pruned,[0;4]);assert!(r.first.is_some());
    let r=solve(0,n.map(|v|I::point(v.lo)),&g,4.0,60);assert_eq!(r.nodes,1);assert_eq!(r.unproved,1);
}
