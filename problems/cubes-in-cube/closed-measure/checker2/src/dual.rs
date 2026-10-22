//! Forward interval duals, also carrying an independently rounded midpoint value.
use crate::interval::*;
use std::ops::{Add, Mul, Neg, Sub};
#[derive(Clone, Copy, Debug)]
pub struct D {
    pub v: I,
    pub g: [I; 6],
    pub m: I,
}
impl D {
    pub fn constant(v: I) -> Self {
        Self {
            v,
            g: [ZERO; 6],
            m: v,
        }
    }
    pub fn variable(v: I, k: usize) -> Self {
        let mut d = Self::constant(v);
        d.g[k] = ONE;
        d.m = I::pt(v.mid());
        d
    }
    pub fn abs(self) -> Self {
        let s = if self.v.lo > 0. {
            ONE
        } else if self.v.hi < 0. {
            -ONE
        } else {
            I::new(-1., 1.)
        };
        Self {
            v: self.v.abs(),
            g: self.g.map(|g| s * g),
            m: self.m.abs(),
        }
    }
    pub fn sincos(self) -> (Self, Self) {
        let (s, c) = sincos(self.v);
        let (sm, cm) = sincos(self.m);
        (
            Self {
                v: s,
                g: self.g.map(|g| c * g),
                m: sm,
            },
            Self {
                v: c,
                g: self.g.map(|g| -s * g),
                m: cm,
            },
        )
    }
    pub fn enclosure(self, delta: &[I; 6]) -> I {
        intersect(self.v, (0..6).fold(self.m, |s, k| s + self.g[k] * delta[k]))
    }
}
pub fn intersect(a: I, b: I) -> I {
    let v = I::new(a.lo.max(b.lo), a.hi.min(b.hi));
    assert!(v.lo <= v.hi, "disjoint enclosures: {:?} {:?}", a, b);
    v
}
impl Add for D {
    type Output = Self;
    fn add(self, b: Self) -> Self {
        Self {
            v: self.v + b.v,
            m: self.m + b.m,
            g: std::array::from_fn(|k| self.g[k] + b.g[k]),
        }
    }
}
impl Neg for D {
    type Output = Self;
    fn neg(self) -> Self {
        Self {
            v: -self.v,
            m: -self.m,
            g: self.g.map(|g| -g),
        }
    }
}
impl Sub for D {
    type Output = Self;
    fn sub(self, b: Self) -> Self {
        self + -b
    }
}
impl Mul for D {
    type Output = Self;
    fn mul(self, b: Self) -> Self {
        Self {
            v: self.v * b.v,
            m: self.m * b.m,
            g: std::array::from_fn(|k| self.g[k] * b.v + self.v * b.g[k]),
        }
    }
}
impl Mul<I> for D {
    type Output = Self;
    fn mul(self, b: I) -> Self {
        self * Self::constant(b)
    }
}
impl Add<I> for D {
    type Output = Self;
    fn add(self, b: I) -> Self {
        self + Self::constant(b)
    }
}
impl Sub<I> for D {
    type Output = Self;
    fn sub(self, b: I) -> Self {
        self - Self::constant(b)
    }
}
impl Mul<D> for I {
    type Output = D;
    fn mul(self, b: D) -> D {
        D::constant(self) * b
    }
}
impl Sub<D> for I {
    type Output = D;
    fn sub(self, b: D) -> D {
        D::constant(self) - b
    }
}
impl Add<D> for I {
    type Output = D;
    fn add(self, b: D) -> D {
        D::constant(self) + b
    }
}

impl From<I> for D {
    fn from(v: I) -> Self {
        Self::constant(v)
    }
}
