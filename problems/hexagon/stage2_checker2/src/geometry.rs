use crate::interval::I;
pub type Vec2=[I;2];
pub type Node=[I;9];
type Mat=[[I;2];2];
const ZERO:I=I::point(0.0);const ONE:I=I::point(1.0);const HALF:I=I::point(0.5);
fn add(a:Vec2,b:Vec2)->Vec2{[a[0]+b[0],a[1]+b[1]]}
fn sub(a:Vec2,b:Vec2)->Vec2{[a[0]-b[0],a[1]-b[1]]}
fn neg(a:Vec2)->Vec2{[-a[0],-a[1]]}
fn half(a:Vec2)->Vec2{[a[0]*HALF,a[1]*HALF]}
pub fn dot(a:Vec2,b:Vec2)->I{a[0]*b[0]+a[1]*b[1]}
fn apply(m:Mat,a:Vec2)->Vec2{[dot(m[0],a),dot(m[1],a)]}
fn compose(a:Mat,b:Mat)->Mat{let cols=[[b[0][0],b[1][0]],[b[0][1],b[1][1]]];[[dot(a[0],cols[0]),dot(a[0],cols[1])],[dot(a[1],cols[0]),dot(a[1],cols[1])]]}
fn perp(a:Vec2)->Vec2{[-a[1],a[0]]}
fn cs(u:f64)->(I,I){let u=I::point(u);let u2=u.sqr();let den=ONE+u2;((ONE-u2)/den,(I::point(2.0)*u)/den)}
pub fn axes(u:I)->[Vec2;2]{
    assert!(u.lo>=0.0 && u.hi<=1.0);
    let (cl,sl)=cs(u.lo);let (ch,sh)=cs(u.hi);
    let e=[I::new(ch.lo,cl.hi),I::new(sl.lo,sh.hi)];[e,perp(e)]
}
#[derive(Clone,Copy)]
pub struct Pose{pub c:Vec2,pub e:[Vec2;2]}
pub fn poses(n:&Node)->[Pose;3]{std::array::from_fn(|j|Pose{c:[n[3*j],n[3*j+1]],e:axes(n[3*j+2])})}
pub struct Geometry{pub v:I,pub h:I,normals:[Vec2;6],vertex:Vec2,maps:[[Mat;3];4],pub lemma:bool}
impl Geometry{
    pub fn new(scale:f64,lemma:bool)->Result<Self,String>{
        if !scale.is_finite() || scale<=0.0 || scale>1e100 {return Err("side-scale must be finite in (0, 1e100]".into())}
        if lemma && scale!=1.0{return Err("the local lemma requires --side-scale 1; use --no-lemma".into())}
        let r=I::enclosing(3.0_f64.sqrt());let t=r*HALF;
        let base=(ONE+r)*HALF;let v=if scale==1.0{base}else{base*I::enclosing(scale)};let h=v*t;
        let id=[[ONE,ZERO],[ZERO,ONE]];let m=[[-ONE,ZERO],[ZERO,ONE]];
        let rot_minus60=[[HALF,t],[-t,HALF]];
        // (M Rot60)^-1 = Rot(-60) M. Reflections reverse orientation;
        // the four signed choices of f restore a positively oriented square basis.
        let gi=[id,rot_minus60,m,compose(rot_minus60,m)];
        let ri=[id,[[-HALF,t],[-t,-HALF]],[[-HALF,-t],[t,-HALF]]];
        let maps=std::array::from_fn(|g|std::array::from_fn(|i|compose(ri[i],gi[g])));
        Ok(Self{v,h,normals:[[ZERO,-ONE],[t,-HALF],[t,HALF],[ZERO,ONE],[-t,HALF],[-t,-HALF]],vertex:[-v*HALF,-h],maps,lemma})
    }
    pub fn containment(&self,p:Pose)->bool{
        self.normals.iter().any(|&n|{let s=dot(n,p.c)+(dot(n,p.e[0]).abs()+dot(n,p.e[1]).abs())*HALF;s.lo>self.h.hi})
    }
    pub fn local_match(&self,p:Pose,g:usize,i:usize)->bool{
        let map=self.maps[g][i];let c=apply(map,p.c);let e=[apply(map,p.e[0]),apply(map,p.e[1])];
        // Use conservative sides of the decimal thresholds, not rounded-to-nearest comparisons.
        let cr=I::enclosing(0.9968018).hi;let radius2=I::enclosing(0.0025).lo;
        for f in [e[0],neg(e[0]),e[1],neg(e[1])]{
            if f[0].lo<cr{continue}let p=sub(sub(c,half(add(f,perp(f)))),self.vertex);
            if (p[0].sqr()+p[1].sqr()).hi<=radius2{return true}
        }false
    }
    pub fn local_lemma(&self,p:&[Pose;3])->bool{
        const PERMS:[[usize;3];6]=[[0,1,2],[0,2,1],[1,0,2],[1,2,0],[2,0,1],[2,1,0]];
        for g in 0..4{
            let fit:[[bool;3];3]=std::array::from_fn(|j|std::array::from_fn(|i|self.local_match(p[j],g,i)));
            if PERMS.iter().any(|pi|(0..3).all(|j|fit[j][pi[j]])){return true}
        }false
    }
    pub fn prune(&self,n:&Node)->Option<usize>{
        if n[3].lo>n[6].hi{return Some(2)}
        let p=poses(n);
        for q in p{if self.containment(q){return Some(0)}}
        for (a,b) in [(0,1),(0,2),(1,2)]{if overlap(p[a],p[b]){return Some(1)}}
        if self.lemma && self.local_lemma(&p){return Some(3)}None
    }
}
pub fn gap(a:Pose,b:Pose,owner:usize,axis:usize)->I{
    let (own,other)=if owner==0{(a,b)}else{(b,a)};let d=own.e[axis];
    let w=(dot(d,other.e[0]).abs()+dot(d,other.e[1]).abs())*HALF;
    dot(d,sub(b.c,a.c)).abs()-(HALF+w)
}
pub fn overlap(a:Pose,b:Pose)->bool{(0..2).all(|o|(0..2).all(|d|gap(a,b,o,d).hi<=0.0))}
