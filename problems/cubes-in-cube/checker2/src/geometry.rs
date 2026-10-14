use crate::interval::*;
#[derive(Clone, Copy, Debug)]
pub struct Box6 {
    pub x: [I; 6],
    pub depth: u32,
}
#[derive(Clone, Debug)]
pub struct Outcome {
    pub rule: u8,
    pub points: Vec<usize>,
}
pub fn root() -> Box6 {
    Box6 {
        x: [
            I::new(0., (PI * I::pt(2.)).hi),
            I::new(0., PI.hi),
            I::new(0., (PI * HALF).hi),
            I::new(0., 0.5),
            I::new(0., 0.5),
            I::new(0., 0.5),
        ],
        depth: 0,
    }
}
pub fn split(b: Box6) -> [Box6; 2] {
    // r3 (10/15): compare angle widths in radians and centre widths in units of 1/4, instead of
    // relative to the root widths. Only the choice of coordinate changes; closing rules are untouched.
    let widths = [1., 1., 1., 4., 4., 4.];
    let mut j = 0;
    for i in 1..6 {
        if b.x[i].width() / widths[i] > b.x[j].width() / widths[j] {
            j = i;
        }
    }
    let m = b.x[j].mid();
    assert!(
        m > b.x[j].lo && m < b.x[j].hi,
        "floating subdivision exhausted"
    );
    let mut l = b;
    let mut r = b;
    l.depth += 1;
    r.depth += 1;
    l.x[j].hi = m;
    r.x[j].lo = m;
    [l, r]
}
pub fn rotation(b: &Box6) -> [[I; 3]; 3] {
    let (sa, ca) = sincos(b.x[0]);
    let (sb, cb) = sincos(b.x[1]);
    let (sg, cg) = sincos(b.x[2]);
    [
        [ca * cb * cg - sa * sg, -ca * cb * sg - sa * cg, ca * sb],
        [sa * cb * cg + ca * sg, -sa * cb * sg + ca * cg, sa * sb],
        [-sb * cg, sb * sg, cb],
    ]
}
pub fn close(b: &Box6) -> Option<Outcome> {
    close_filtered(b, u32::MAX)
}
pub fn close_filtered(b: &Box6, enabled: u32) -> Option<Outcome> {
    let r = rotation(b);
    let s = I::pt(2.) + INV_SQRT2;
    let a = INV_SQRT2 * HALF;
    let h: [I; 3] = std::array::from_fn(|w| (r[w][0].abs() + r[w][1].abs() + r[w][2].abs()) * HALF);
    let c: [I; 3] = std::array::from_fn(|w| h[w] + b.x[w + 3] * (s - I::pt(2.) * h[w]));
    let mut t = [[ZERO; 3]; 8];
    for p in 0..8 {
        for i in 0..3 {
            let mut bounds = [0.; 2];
            for (side, sign) in [-1., 1.].iter().enumerate() {
                let mut total = ZERO;
                for w in 0..3 {
                    let coord = if p & (1 << w) == 0 { ONE } else { s - ONE };
                    let coeff = r[w][i] * I::pt(*sign);
                    let raw = coeff * (coord - c[w]);
                    let wallcoeff = if p & (1 << w) == 0 { coeff } else { -coeff };
                    let term = if wallcoeff.lo >= 0. {
                        let sigma = (0..3)
                            .filter(|&j| j != i)
                            .fold(ZERO, |v, j| v + r[w][j].abs());
                        let tightened =
                            HALF - HALF * (ONE - wallcoeff).sq() - HALF * wallcoeff * sigma;
                        I::new(raw.lo, raw.hi.min(tightened.hi))
                    } else {
                        raw
                    };
                    total = total + term;
                }
                bounds[side] = total.hi;
            }
            t[p][i] = I::new(-bounds[0], bounds[1]);
        }
        if enabled & (1 << 1) != 0 && t[p].iter().all(|v| v.abs().hi <= 0.5) {
            return Some(Outcome {
                rule: 1,
                points: vec![p],
            });
        }
    }
    for p in 0..8 {
        if enabled & (1 << 2) != 0
            && (0..3).all(|w| {
                let u = if p & (1 << w) == 0 {
                    b.x[w + 3]
                } else {
                    ONE - b.x[w + 3]
                };
                (I::pt(2.) - u * s - I::pt(2.) * h[w] * (ONE - u)).lo >= 0.
            })
        {
            return Some(Outcome {
                rule: 2,
                points: vec![p],
            });
        }
    }
    for p in 0..8 {
        if enabled & (1 << 3) != 0
            && (0..3).all(|i| {
                [-1., 1.].iter().all(|&sign| {
                    if (t[p][i] * I::pt(sign)).hi <= 0.5 {
                        return true;
                    }
                    (0..3).any(|w| {
                        let coeff = r[w][i] * I::pt(if p & (1 << w) == 0 { sign } else { -sign });
                        coeff.lo > 0.
                            && (0..3)
                                .filter(|&j| j != i)
                                .all(|j| (r[w][j].abs() + t[p][j].abs()).hi <= 0.5)
                    })
                })
            })
        {
            return Some(Outcome {
                rule: 3,
                points: vec![p],
            });
        }
    }
    if enabled & (1 << 5) != 0 {
        for p in 0usize..8 {
            for q in p + 1..8 {
                if (p ^ q).count_ones() != 2 {
                    continue;
                }
                for i in 0..3 {
                    if (0..3)
                        .filter(|&j| j != i)
                        .all(|j| t[p][j].abs().hi <= 0.5 && t[q][j].abs().hi <= 0.5)
                    {
                        for sign in [-1., 1.] {
                            if (t[p][i] * I::pt(sign)).hi <= 0.5
                                && (t[q][i] * I::pt(sign)).lo >= -0.5
                            {
                                return Some(Outcome {
                                    rule: 5,
                                    points: vec![p, q],
                                });
                            }
                            if (t[q][i] * I::pt(sign)).hi <= 0.5
                                && (t[p][i] * I::pt(sign)).lo >= -0.5
                            {
                                return Some(Outcome {
                                    rule: 5,
                                    points: vec![q, p],
                                });
                            }
                        }
                    }
                }
            }
        }
    }
    if enabled & (1 << 6) == 0 {
        return None;
    }
    // Transport the whole wall statement, then independently relabel its frame.
    for w in 0..3 {
        let other: Vec<_> = (0..3).filter(|&v| v != w).collect();
        for order in 0..2 {
            let v1 = other[order];
            let v2 = other[1 - order];
            let d = [s * HALF - c[v1], s * HALF - c[v2]];
            for i0 in 0..3 {
                for sign0 in [-1., 1.] {
                    let a0w = r[w][i0] * I::pt(sign0);
                    if a0w.lo <= 0. {
                        continue;
                    }
                    let rhs = HALF * a0w - a;
                    if rhs.lo <= 0. || (d[0].sq() + d[1].sq()).hi >= rhs.sq().lo {
                        continue;
                    }
                    let pts: Vec<_> = (0..8).filter(|p| p & (1 << w) == 0).collect();
                    if !pts.iter().all(|&q| (t[q][i0] * I::pt(sign0)).lo >= -0.5) {
                        continue;
                    }
                    let e: [I; 3] = std::array::from_fn(|v| {
                        (if v == w { ONE } else { s * HALF })
                            - c[v]
                            - HALF * r[v][i0] * I::pt(sign0)
                    });
                    for i1 in 0..3 {
                        if i1 == i0 {
                            continue;
                        }
                        let i2 = 3 - i0 - i1;
                        for sign1 in [-1., 1.] {
                            for sign2 in [-1., 1.] {
                                let a1: [I; 3] = std::array::from_fn(|v| r[v][i1] * I::pt(sign1));
                                let a2: [I; 3] = std::array::from_fn(|v| r[v][i2] * I::pt(sign2));
                                if (a1[v1] + a1[v2]).lo < 0. || (a2[v2] - a2[v1]).lo < 0. {
                                    continue;
                                }
                                let p = (0..3).fold(ZERO, |sum, v| sum + a1[v] * e[v]);
                                let rr = (0..3).fold(ZERO, |sum, v| sum + a2[v] * e[v]);
                                if p.abs().hi <= 0.5
                                    && rr.abs().hi <= 0.5
                                    && (rr.abs() + a * (a2[v1] + a2[v2]).abs()).hi <= 0.5
                                    && (p.abs() + a * (a1[v1] - a1[v2]).abs()).hi <= 0.5
                                {
                                    return Some(Outcome {
                                        rule: 6,
                                        points: pts,
                                    });
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    None
}
