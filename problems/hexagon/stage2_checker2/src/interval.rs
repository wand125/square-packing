//! Outward rounding. No fast-math, epsilon comparisons, or fused arithmetic.
use std::ops::{Add, Sub, Mul, Div, Neg};
#[derive(Clone, Copy, Debug, PartialEq)]
pub struct I { pub lo: f64, pub hi: f64 }
pub fn next_up(x: f64) -> f64 {
    if x.is_nan() || x == f64::INFINITY { return x; }
    if x == 0.0 { return f64::from_bits(1); }
    f64::from_bits(if x > 0.0 { x.to_bits()+1 } else { x.to_bits()-1 })
}
pub fn next_down(x: f64) -> f64 { -next_up(-x) }
impl I {
    pub const fn point(x: f64) -> Self { Self { lo: x, hi: x } }
    pub fn new(lo: f64, hi: f64) -> Self { assert!(!lo.is_nan() && !hi.is_nan() && lo<=hi); Self {lo,hi} }
    pub fn rounded(lo: f64, hi: f64) -> Self { Self::new(next_down(lo), next_up(hi)) }
    pub fn enclosing(x: f64) -> Self { Self::rounded(x,x) }
    pub fn rational(p: i64, q: i64) -> Result<Self,String> {
        if p.unsigned_abs() >= 1u64<<53 || q.unsigned_abs() >= 1u64<<53 || q == 0 { return Err("rational requires |p|, |q| < 2^53 and q != 0".into()); }
        Ok(Self::enclosing(p as f64/q as f64))
    }
    pub fn sqr(self) -> Self {
        if self.lo >= 0.0 { Self::rounded(self.lo*self.lo,self.hi*self.hi) }
        else if self.hi <= 0.0 { Self::rounded(self.hi*self.hi,self.lo*self.lo) }
        else { Self::new(0.0,next_up((self.lo*self.lo).max(self.hi*self.hi))) }
    }
    pub fn abs(self) -> Self {
        if self.lo >= 0.0 {self} else if self.hi <= 0.0 {-self}
        else {Self::new(0.0,(-self.lo).max(self.hi))}
    }
    pub fn width(self) -> f64 { self.hi-self.lo }
}
impl Add for I {type Output=Self; fn add(self,b:Self)->Self {Self::rounded(self.lo+b.lo,self.hi+b.hi)}}
impl Sub for I {type Output=Self; fn sub(self,b:Self)->Self {Self::rounded(self.lo-b.hi,self.hi-b.lo)}}
impl Mul for I {type Output=Self; fn mul(self,b:Self)->Self {
    let p=[self.lo*b.lo,self.lo*b.hi,self.hi*b.lo,self.hi*b.hi];
    // Conservative total extension for 0 * infinity (not used by the verifier).
    if p.iter().any(|v|v.is_nan()) {return Self::new(f64::NEG_INFINITY,f64::INFINITY)}
    Self::rounded(p.iter().copied().fold(f64::INFINITY,f64::min),p.iter().copied().fold(f64::NEG_INFINITY,f64::max))
}}
impl Div for I {type Output=Self; fn div(self,b:Self)->Self {
    assert!(b.lo>0.0 || b.hi<0.0,"division by interval containing zero");
    let p=[self.lo/b.lo,self.lo/b.hi,self.hi/b.lo,self.hi/b.hi];
    if p.iter().any(|v|v.is_nan()) {return Self::new(f64::NEG_INFINITY,f64::INFINITY)}
    Self::rounded(p.iter().copied().fold(f64::INFINITY,f64::min),p.iter().copied().fold(f64::NEG_INFINITY,f64::max))
}}
impl Neg for I {type Output=Self; fn neg(self)->Self {Self::new(-self.hi,-self.lo)}}
