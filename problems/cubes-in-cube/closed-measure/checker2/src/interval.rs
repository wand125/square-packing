//! Binary64 intervals. No libm transcendental is used in certification.
use std::ops::{Add, Mul, Neg, Sub};
#[derive(Clone, Copy, Debug)]
pub struct I {
    pub lo: f64,
    pub hi: f64,
}
pub fn up(x: f64) -> f64 {
    if x == f64::INFINITY {
        x
    } else if x == 0. {
        f64::from_bits(1)
    } else {
        f64::from_bits(if x > 0. {
            x.to_bits() + 1
        } else {
            x.to_bits() - 1
        })
    }
}
pub fn down(x: f64) -> f64 {
    -up(-x)
}
impl I {
    pub const fn new(lo: f64, hi: f64) -> Self {
        Self { lo, hi }
    }
    pub const fn pt(x: f64) -> Self {
        Self::new(x, x)
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
        Self::new(
            if a.lo == 0. {
                0.
            } else {
                down(a.lo * a.lo).max(0.)
            },
            up(a.hi * a.hi),
        )
    }
    pub fn div_pos(self, x: f64) -> Self {
        assert!(x > 0.);
        Self::new(down(self.lo / x), up(self.hi / x))
    }
    pub fn mid(self) -> f64 {
        self.lo + (self.hi - self.lo) * 0.5
    }
    pub fn width(self) -> f64 {
        self.hi - self.lo
    }
}
impl Add for I {
    type Output = Self;
    fn add(self, b: Self) -> Self {
        if self.lo == 0. && self.hi == 0. {
            return b;
        }
        if b.lo == 0. && b.hi == 0. {
            return self;
        }
        if self.lo == self.hi && b.lo == b.hi && self.lo == -b.lo {
            return ZERO;
        }
        Self::new(down(self.lo + b.lo), up(self.hi + b.hi))
    }
}
impl Sub for I {
    type Output = Self;
    fn sub(self, b: Self) -> Self {
        self + (-b)
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
        if (self.lo == 0. && self.hi == 0.) || (b.lo == 0. && b.hi == 0.) {
            return ZERO;
        }
        if self.lo == 1. && self.hi == 1. {
            return b;
        }
        if b.lo == 1. && b.hi == 1. {
            return self;
        }
        if self.lo == -1. && self.hi == -1. {
            return -b;
        }
        if b.lo == -1. && b.hi == -1. {
            return -self;
        }
        let v = [
            self.lo * b.lo,
            self.lo * b.hi,
            self.hi * b.lo,
            self.hi * b.hi,
        ];
        Self::new(
            down(v.iter().copied().fold(f64::INFINITY, f64::min)),
            up(v.iter().copied().fold(f64::NEG_INFINITY, f64::max)),
        )
    }
}
pub const PI: I = I::new(3.141592653589793, 3.1415926535897936);
pub const ZERO: I = I::pt(0.);
pub const ONE: I = I::pt(1.);
pub const HALF: I = I::pt(0.5);
pub fn sincos(x: I) -> (I, I) {
    if x.lo == 0. && x.hi == 0. {
        return (ZERO, ONE);
    }
    if x.width() >= 6. {
        return (I::new(-1., 1.), I::new(-1., 1.));
    }
    let m = x.mid();
    let k = (m / (std::f64::consts::FRAC_PI_2)).round() as i32;
    assert!(k.abs() <= 8);
    let z = I::pt(m) - PI * I::pt(k as f64) * HALF;
    assert!(z.abs().hi < 1.);
    let z2 = z.sq();
    let mut st = z;
    let mut ct = ONE;
    let mut s = st;
    let mut c = ct;
    for n in 1..=16 {
        st = -(st * z2).div_pos((2 * n * (2 * n + 1)) as f64);
        ct = -(ct * z2).div_pos(((2 * n - 1) * 2 * n) as f64);
        s = s + st;
        c = c + ct;
    }
    // Degree 33/32 Taylor polynomials: on |z|<1, both errors <1/33! <2^-120.
    let remainder = f64::from_bits(903u64 << 52); // exactly 2^-120
    let err = I::new(-remainder, remainder);
    s = s + err;
    c = c + err;
    let (s, c) = match k.rem_euclid(4) {
        0 => (s, c),
        1 => (c, -s),
        2 => (-s, -c),
        _ => (-c, s),
    };
    let radius = up(up(m - x.lo).max(up(x.hi - m)));
    let widen = |v: I| {
        let v = v + I::new(-radius, radius);
        I::new(v.lo.max(-1.), v.hi.min(1.))
    };
    (widen(s), widen(c))
}
