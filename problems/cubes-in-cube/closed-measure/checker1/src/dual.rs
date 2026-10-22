//! Forward interval automatic differentiation, including Clarke absolute values.
use crate::interval::*;
use std::ops::{Add, Div, Mul, Neg, Sub};
#[derive(Clone, Copy, Debug)]
pub struct D {
    pub v: I,
    pub g: [I; 6],
}
impl D {
    pub fn constant(v: I) -> Self {
        Self { v, g: [ZERO; 6] }
    }
    pub fn variable(v: I, k: usize) -> Self {
        let mut d = Self::constant(v);
        d.g[k] = ONE;
        d
    }
    pub fn abs(self) -> Self {
        let sign = if self.v.lo > 0. {
            ONE
        } else if self.v.hi < 0. {
            -ONE
        } else {
            I::new(-1., 1.)
        };
        Self {
            v: self.v.abs(),
            g: self.g.map(|g| sign * g),
        }
    }
    pub fn sq(self) -> Self {
        Self {
            v: self.v.sq(),
            g: self.g.map(|g| I::p(2.) * self.v * g),
        }
    }
}
impl Add for D {
    type Output = Self;
    fn add(self, b: Self) -> Self {
        Self {
            v: self.v + b.v,
            g: std::array::from_fn(|k| self.g[k] + b.g[k]),
        }
    }
}
impl Sub for D {
    type Output = Self;
    fn sub(self, b: Self) -> Self {
        Self {
            v: self.v - b.v,
            g: std::array::from_fn(|k| self.g[k] - b.g[k]),
        }
    }
}
impl Neg for D {
    type Output = Self;
    fn neg(self) -> Self {
        Self {
            v: -self.v,
            g: self.g.map(|g| -g),
        }
    }
}
impl Mul for D {
    type Output = Self;
    fn mul(self, b: Self) -> Self {
        Self {
            v: self.v * b.v,
            g: std::array::from_fn(|k| self.g[k] * b.v + self.v * b.g[k]),
        }
    }
}
impl Div for D {
    type Output = Self;
    fn div(self, b: Self) -> Self {
        Self {
            v: self.v / b.v,
            g: std::array::from_fn(|k| (self.g[k] * b.v - self.v * b.g[k]) / b.v.sq()),
        }
    }
}
pub fn constant(x: f64) -> D {
    D::constant(I::p(x))
}
pub fn geometry(b: &[I; 6]) -> ([[D; 3]; 3], [D; 3], [D; 3]) {
    let p: [D; 6] = std::array::from_fn(|k| D::variable(b[k], k));
    let [x, y, z] = [p[0], p[1], p[2]];
    let [xx, yy, zz] = [x.sq(), y.sq(), z.sq()];
    let one = constant(1.);
    let two = constant(2.);
    let den = one + xx + yy + zz;
    let r = [
        [one + xx - yy - zz, two * (x * y - z), two * (x * z + y)],
        [two * (x * y + z), one + yy - xx - zz, two * (y * z - x)],
        [two * (x * z - y), two * (y * z + x), one + zz - xx - yy],
    ]
    .map(|row| {
        row.map(|n| {
            let mut d = n / den;
            d.v = d.v.intersect(I::new(-1., 1.));
            d
        })
    });
    let h = r.map(|row| {
        let mut d = (constant(0.) + row[0].abs() + row[1].abs() + row[2].abs()) * constant(0.5);
        d.v = d.v.intersect(I::new(0.5, (I::p(3.).sqrt() * I::p(0.5)).hi));
        d
    });
    let c = std::array::from_fn(|w| h[w] + p[w + 3] * (constant(3.) - two * h[w]));
    (r, h, c)
}
