//! Each elementary operation is rounded outward, including underflow.
use serde::{Deserialize, Serialize};
use std::ops::{Add, Div, Mul, Neg, Sub};
#[derive(Clone, Copy, Debug, Serialize, Deserialize)]
pub struct I {
    pub lo: f64,
    pub hi: f64,
}
pub fn down(x: f64) -> f64 {
    x.next_down()
}
pub fn up(x: f64) -> f64 {
    x.next_up()
}
impl I {
    pub const fn new(lo: f64, hi: f64) -> Self {
        if lo.is_nan() || hi.is_nan() || lo > hi {
            Self {
                lo: f64::NEG_INFINITY,
                hi: f64::INFINITY,
            }
        } else {
            Self { lo, hi }
        }
    }
    pub const fn p(x: f64) -> Self {
        Self::new(x, x)
    }
    pub fn rational(n: f64, d: f64) -> Self {
        Self::p(n) / Self::p(d)
    }
    pub fn abs(self) -> Self {
        Self::new(
            if self.lo <= 0. && self.hi >= 0. {
                0.
            } else {
                self.lo.abs().min(self.hi.abs())
            },
            self.lo.abs().max(self.hi.abs()),
        )
    }
    pub fn sq(self) -> Self {
        let a = self.abs();
        Self::new(down(a.lo * a.lo).max(0.), up(a.hi * a.hi))
    }
    pub fn sqrt(self) -> Self {
        Self::new(down(self.lo.sqrt()).max(0.), up(self.hi.sqrt()))
    }
    pub fn max(self, b: Self) -> Self {
        Self::new(self.lo.max(b.lo), self.hi.max(b.hi))
    }
    pub fn min(self, b: Self) -> Self {
        Self::new(self.lo.min(b.lo), self.hi.min(b.hi))
    }
    pub fn mid(self) -> f64 {
        self.lo * 0.5 + self.hi * 0.5
    }
    pub fn width(self) -> f64 {
        self.hi - self.lo
    }
    pub fn pow(self, n: usize) -> Self {
        (0..n).fold(Self::p(1.), |a, _| a * self)
    }
}
impl Add for I {
    type Output = Self;
    fn add(self, b: Self) -> Self {
        Self::new(down(self.lo + b.lo), up(self.hi + b.hi))
    }
}
impl Sub for I {
    type Output = Self;
    fn sub(self, b: Self) -> Self {
        Self::new(down(self.lo - b.hi), up(self.hi - b.lo))
    }
}
impl Neg for I {
    type Output = Self;
    fn neg(self) -> Self {
        Self::new(-self.hi, -self.lo)
    }
}
impl Mul for I {
    type Output = Self;
    fn mul(self, b: Self) -> Self {
        let v = [
            self.lo * b.lo,
            self.lo * b.hi,
            self.hi * b.lo,
            self.hi * b.hi,
        ];
        if v.iter().any(|x| x.is_nan()) {
            return Self::new(f64::NEG_INFINITY, f64::INFINITY);
        }
        Self::new(
            down(v.into_iter().fold(f64::INFINITY, f64::min)),
            up(v.into_iter().fold(f64::NEG_INFINITY, f64::max)),
        )
    }
}
impl Div for I {
    type Output = Self;
    fn div(self, b: Self) -> Self {
        if b.lo <= 0. && b.hi >= 0. {
            return Self::new(f64::NEG_INFINITY, f64::INFINITY);
        }
        self * Self::new(down(1. / b.hi), up(1. / b.lo))
    }
}
pub const ZERO: I = I::p(0.);
pub const ONE: I = I::p(1.);
pub fn sum(v: impl IntoIterator<Item = I>) -> I {
    v.into_iter().fold(ZERO, |a, b| a + b)
}
