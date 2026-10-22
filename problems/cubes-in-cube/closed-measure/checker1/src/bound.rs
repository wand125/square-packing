use crate::interval::*;
use serde::{Deserialize, Serialize};
pub type Box6 = [I; 6];
pub fn side() -> I {
    I::p(3.)
}
pub fn root() -> Box6 {
    let a = (I::p(2.).sqrt() - ONE).hi;
    [
        I::new(0., a),
        I::new(0., a),
        I::new(-a, a),
        I::new(0., 0.5),
        I::new(0., 1.),
        I::new(0., 1.),
    ]
}
pub fn valid(b: &Box6) -> bool {
    b.iter()
        .all(|v| v.lo.is_finite() && v.hi.is_finite() && v.lo <= v.hi)
        && b[..3].iter().all(|v| v.lo >= -1. && v.hi <= 1.)
        && b[3..].iter().all(|v| v.lo >= 0. && v.hi <= 1.)
}
pub fn outside(b: &Box6) -> bool {
    let a = (I::p(2.).sqrt() - ONE).hi;
    b[..3].iter().any(|v| v.abs().lo > a)
        || sum(b[..3].iter().map(|v| I::p(v.abs().lo))).lo > 1.
        || b[0].hi < 0.
        || b[1].hi < 0.
        || b[0].hi < b[1].lo
        || b[1].hi < b[2].abs().lo
        || b[3].lo > 0.5
}
pub fn rotation(b: &Box6) -> [[I; 3]; 3] {
    let [x, y, z] = [b[0], b[1], b[2]];
    let [xx, yy, zz] = [x.sq(), y.sq(), z.sq()];
    let d = ONE + xx + yy + zz;
    let two = I::p(2.);
    [
        [ONE + xx - yy - zz, two * (x * y - z), two * (x * z + y)],
        [two * (x * y + z), ONE + yy - xx - zz, two * (y * z - x)],
        [two * (x * z - y), two * (y * z + x), ONE + zz - xx - yy],
    ]
    .map(|row| {
        row.map(|v| {
            let a = v / d;
            I::new(a.lo.max(-1.), a.hi.min(1.))
        })
    })
}
pub fn geometry(b: &Box6) -> ([[I; 3]; 3], [I; 3], [I; 3]) {
    let r = rotation(b);
    // Exact row l1 norms lie in [1,sqrt(3)]. This is an intersection, not a test.
    let h = r.map(|row| {
        let a = sum(row.map(I::abs)) * I::p(0.5);
        I::new(a.lo.max(0.5), a.hi.min((I::p(3.).sqrt() * I::p(0.5)).hi))
    });
    let c = std::array::from_fn(|w| h[w] + b[w + 3] * (side() - I::p(2.) * h[w]));
    (r, h, c)
}
#[derive(Clone, Copy, Debug, Serialize, Deserialize, PartialEq, Eq, Ord, PartialOrd)]
#[serde(rename_all = "snake_case")]
pub enum Reason {
    Outside,
    Bound,
    Unresolved,
    Split,
}
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Result {
    pub reason: Reason,
    pub lower: f64,
    pub contributions: [f64; 3],
    pub lemmas: [u64; 6],
}
// Cached affine form a.(y-c): only y-dependent operations remain per cell.
struct Form {
    a: [crate::dual::D; 3],
    mid: [I; 3],
    shift: [I; 6],
}
impl Form {
    fn new(a: [crate::dual::D; 3], mid: [I; 3], c: [crate::dual::D; 3]) -> Self {
        Self {
            a,
            mid,
            shift: std::array::from_fn(|k| -sum((0..3).map(|w| a[w].v * c[w].g[k]))),
        }
    }
    fn enclose(&self, pose: &Pose, y: [I; 3], naive: I) -> I {
        let ym = y.map(|v| I::p(v.mid()));
        let mut mv = sum((0..3).map(|w| self.mid[w] * (ym[w] - pose.cm[w])));
        for k in 0..6 {
            let g = self.shift[k] + sum((0..3).map(|w| self.a[w].g[k] * (y[w] - pose.c[w])));
            mv = mv + g * pose.delta[k];
        }
        for w in 0..3 {
            mv = mv + self.a[w].v * (y[w] - ym[w]);
        }
        naive.intersect(mv)
    }
}
struct Pose {
    rd: [[crate::dual::D; 3]; 3],
    rm: [[I; 3]; 3],
    delta: Box6,
    cm: [I; 3],
    tf: [Form; 3],
    cf: [[[Form; 3]; 3]; 3],
    fd: [[crate::dual::D; 2]; 3],
    fm: [[I; 2]; 3],
    direction: [[I; 3]; 3],
    absolute: [[I; 3]; 3],
    b: Box6,
    r: [[I; 3]; 3],
    h: [I; 3],
    c: [I; 3],
    witnesses: Vec<([[I; 3]; 3], [I; 3])>,
    chord: [[[[I; 3]; 3]; 3]; 3],
}
impl Pose {
    fn new(b: Box6) -> Self {
        let (rd, hd, cd) = crate::dual::geometry(&b);
        let r = rd.map(|row| row.map(|d| d.v));
        let h = hd.map(|d| d.v);
        let c = cd.map(|d| d.v);
        let m = b.map(|v| I::p(v.mid()));
        let (rm, hm, cm_dual) = crate::dual::geometry(&m);
        let cm = cm_dual.map(|d| d.v);
        let delta = std::array::from_fn(|k| b[k] - m[k]);
        let mv =
            |d: crate::dual::D, at: I| d.v.intersect(at + sum((0..6).map(|k| d.g[k] * delta[k])));
        let direction = std::array::from_fn(|w| std::array::from_fn(|j| mv(rd[w][j], rm[w][j].v)));
        let absolute =
            std::array::from_fn(|w| std::array::from_fn(|j| mv(rd[w][j].abs(), rm[w][j].v.abs())));
        let tf = std::array::from_fn(|j| {
            Form::new(
                std::array::from_fn(|w| rd[w][j]),
                std::array::from_fn(|w| rm[w][j].v),
                cd,
            )
        });
        let cf = std::array::from_fn(|w| {
            std::array::from_fn(|k| {
                std::array::from_fn(|j| {
                    Form::new(
                        std::array::from_fn(|v| rd[w][k] * rd[v][j] - rd[w][j] * rd[v][k]),
                        std::array::from_fn(|v| rm[w][k].v * rm[v][j].v - rm[w][j].v * rm[v][k].v),
                        cd,
                    )
                })
            })
        });
        let foffset = |hh: [crate::dual::D; 3], bb: Box6| {
            std::array::from_fn(|w| {
                let u = crate::dual::D::variable(bb[w + 3], w + 3);
                let span = crate::dual::constant(3.) - crate::dual::constant(2.) * hh[w];
                [
                    crate::dual::constant(1.) + u * span,
                    -crate::dual::constant(2.) + (crate::dual::constant(1.) - u) * span,
                ]
            })
        };
        let fd = foffset(hd, b);
        let fm = foffset(hm, m).map(|row| row.map(|d| d.v));
        let chord = std::array::from_fn(|w| {
            std::array::from_fn(|k| {
                std::array::from_fn(|j| {
                    std::array::from_fn(|v| r[w][k] * r[v][j] - r[w][j] * r[v][k])
                })
            })
        });
        let witnesses = (0..8)
            .map(|mask| {
                let q = std::array::from_fn(|j| {
                    I::p(if j < 3 {
                        b[j].mid()
                    } else if mask & (1 << (j - 3)) == 0 {
                        b[j].lo
                    } else {
                        b[j].hi
                    })
                });
                let (rr, _, cc) = geometry(&q);
                (rr, cc)
            })
            .collect();
        Self {
            rd,
            rm: rm.map(|row| row.map(|d| d.v)),
            delta,
            cm,
            tf,
            cf,
            fd,
            fm,
            direction,
            absolute,
            b,
            r,
            h,
            c,
            chord,
            witnesses,
        }
    }
    fn affine(&self, a: [I; 3], y: [I; 3]) -> I {
        sum((0..3).map(|w| a[w] * (y[w] - self.c[w])))
    }
    fn t(&self, y: [I; 3]) -> [I; 3] {
        std::array::from_fn(|i| {
            self.tf[i].enclose(
                self,
                y,
                self.affine(std::array::from_fn(|w| self.r[w][i]), y),
            )
        })
    }
    // SPEC W/P: collected affine full chord; each y coordinate appears once.
    fn chord(&self, y: [I; 3], w: usize, k: usize) -> bool {
        (0..3).filter(|&j| j != k).all(|j| {
            (self.cf[w][k][j]
                .enclose(self, y, self.affine(self.chord[w][k][j], y))
                .abs()
                + I::p(0.5) * self.absolute[w][j])
                .hi
                <= (I::p(0.5) * self.absolute[w][k]).lo
        })
    }
    // M's sum of absolute values also receives its own mean-value enclosure.
    fn m_quantity(&self, y: [I; 3], w: usize, j: usize, t: I) -> I {
        use crate::dual::D;
        let form = &self.tf[j];
        let ym = y.map(|v| I::p(v.mid()));
        let td = D {
            v: t,
            g: std::array::from_fn(|k| {
                form.shift[k] + sum((0..3).map(|a| form.a[a].g[k] * (y[a] - self.c[a])))
            }),
        };
        let d = self.rd[w][j].abs() + td.abs();
        let tm = sum((0..3).map(|a| form.mid[a] * (ym[a] - self.cm[a])));
        let mut mv = self.rm[w][j].abs() + tm.abs() + sum((0..6).map(|k| d.g[k] * self.delta[k]));
        let sign = if t.lo > 0. {
            ONE
        } else if t.hi < 0. {
            -ONE
        } else {
            I::new(-1., 1.)
        };
        for a in 0..3 {
            mv = mv + sign * form.a[a].v * (y[a] - ym[a]);
        }
        (self.absolute[w][j] + t.abs()).intersect(mv)
    }
    fn centre(&self, y: I, w: usize, side: usize, naive: I) -> I {
        let ym = I::p(y.mid());
        let sign = I::p(if side == 0 { -1. } else { 1. });
        let mv = self.fm[w][side]
            + sign * ym
            + sum((0..6).map(|k| self.fd[w][side].g[k] * self.delta[k]))
            + sign * (y - ym);
        naive.intersect(mv)
    }
    // SPEC S, F, W, M; return the first contributing lemma, in that order.
    fn single(&self, y: [I; 3], deg: [bool; 3], walls: [i32; 3], enabled: u8) -> Option<usize> {
        let t = self.t(y);
        if enabled & 1 != 0 && t.iter().all(|a| a.abs().hi <= 0.5) {
            return Some(0);
        } // S
          // F: 1-h +/- (y-c) >= 0. Collected using c=h+u(3-2h).
          // Exact nonnegative terms preserve contacts y=1,u=0 (and mirrors).
        let f = (0..3).all(|w| {
            let u = self.b[w + 3];
            let span = I::p(3.) - I::p(2.) * self.h[w];
            let left = if y[w].hi <= 1. {
                true
            } else {
                self.centre(y[w], w, 0, ONE - y[w] + u * span).lo >= 0.
            };
            let v = I::new((ONE - u).lo.max(0.), (ONE - u).hi.min(1.));
            let right = if y[w].lo >= 2. {
                true
            } else {
                self.centre(y[w], w, 1, y[w] - I::p(2.) + v * span).lo >= 0.
            };
            left && right
        });
        if enabled & 2 != 0 && f {
            return Some(1);
        }
        for w in 0..3 {
            if !deg[w] || walls[w] == 0 {
                continue;
            }
            for k in 0..3 {
                let d = self.direction[w][k];
                let sg = if d.lo > 0. {
                    1.
                } else if d.hi < 0. {
                    -1.
                } else {
                    continue;
                };
                let tk = t[k] * I::p(sg);
                if enabled & 4 != 0
                    && self.chord(y, w, k)
                    && (if walls[w] < 0 {
                        tk.lo >= -0.5
                    } else {
                        tk.hi <= 0.5
                    })
                {
                    return Some(2);
                } // W
            }
        }
        // M: certify every signed cube-face inequality either directly or by the wall lemma.
        if enabled & 8 != 0
            && (0..3).all(|k| {
                [1., -1.].iter().all(|&sg| {
                    (t[k] * I::p(sg)).hi <= 0.5
                        || (0..3).any(|w| {
                            deg[w]
                                && walls[w] != 0
                                && (self.direction[w][k] * I::p(sg * -(walls[w] as f64))).lo > 0.
                                && (0..3)
                                    .filter(|&j| j != k)
                                    .all(|j| self.m_quantity(y, w, j, t[j]).hi <= 0.5)
                        })
                })
            })
        {
            return Some(3);
        }
        None
    }
    // SPEC P and P': same cells translated exactly one world unit.
    fn pair(&self, y: [I; 3], z: [I; 3], w: usize, enabled: u8) -> Option<usize> {
        let t = self.t(y);
        let v = self.t(z);
        for k in 0..3 {
            let d = self.direction[w][k];
            let sg = if d.lo > 0. {
                1.
            } else if d.hi < 0. {
                -1.
            } else {
                continue;
            };
            if enabled & 16 != 0
                && (t[k] * I::p(sg)).hi <= 0.5
                && (v[k] * I::p(sg)).lo >= -0.5
                && self.chord(y, w, k)
            {
                return Some(4);
            }
        }
        for k in 0..3 {
            for sg in [1., -1.] {
                if enabled & 32 != 0
                    && (t[k] * I::p(sg)).hi <= 0.5
                    && (v[k] * I::p(sg)).lo >= -0.5
                    && (0..3)
                        .filter(|&j| j != k)
                        .all(|j| t[j].abs().hi <= 0.5 && v[j].abs().hi <= 0.5)
                {
                    return Some(5);
                }
            }
        }
        None
    }
}
#[derive(Clone)]
struct Value {
    mass: I,
    lemmas: [u64; 6],
}
// Exact cell endpoints are integer numerators over 10*2^level. No repeated floating bisection.
fn cell(
    p: &crate::measure::Piece,
    partner: Option<usize>,
    pose: &Pose,
    grid: [u64; 3],
    level: [u32; 3],
) -> Value {
    let data = crate::measure::DATA.get().unwrap();
    let y: [I; 3] = std::array::from_fn(|w| {
        let [lo, hi] = p.bounds[w];
        let den = 1u64 << level[w];
        let a = I::rational(
            (lo as u64 * den + (hi - lo) as u64 * grid[w]) as f64,
            (10 * den) as f64,
        );
        let b = if lo == hi {
            a
        } else {
            I::rational(
                (lo as u64 * den + (hi - lo) as u64 * (grid[w] + 1)) as f64,
                (10 * den) as f64,
            )
        };
        I::new(a.lo, b.hi)
    });
    let deg = p.bounds.map(|v| v[0] == v[1]);
    let walls = p.bounds.map(|v| {
        if v[0] <= 10 {
            -1
        } else if v[0] >= 20 {
            1
        } else {
            0
        }
    });
    let mut mass = I::p(p.density);
    for w in 0..3 {
        if !deg[w] {
            mass = mass
                * I::rational(
                    (p.bounds[w][1] - p.bounds[w][0]) as f64,
                    (10u64 << level[w]) as f64,
                );
        }
    }
    let a = pose.single(y, deg, walls, 63);
    let mut lemmas = [0; 6];
    if let Some(i) = a {
        lemmas[i] += 1;
    }
    let mut count = a.is_some() as u32;
    let mut z = y;
    if let Some(w) = partner {
        z[w] = I::rational((p.bounds[w][0] + 10) as f64, 10.);
        let mut zw = walls;
        zw[w] = if p.bounds[w][0] + 10 <= 10 {
            -1
        } else if p.bounds[w][0] + 10 >= 20 {
            1
        } else {
            0
        };
        let b = pose.single(z, deg, zw, 63);
        if let Some(i) = b {
            lemmas[i] += 1;
            count += 1;
        }
        if count == 0 {
            if let Some(i) = pose.pair(y, z, w, 63) {
                count = 1;
                lemmas[i] += 1;
            }
        }
    }
    let mut best = Value {
        mass: if count == 0 {
            ZERO
        } else {
            mass * I::p(count as f64)
        },
        lemmas,
    };
    if count == if partner.is_some() { 2 } else { 1 } {
        return best;
    }
    // If both cells are certainly disjoint, all descendants have zero value.
    let disjoint = |q| pose.t(q).iter().any(|t| t.lo > 0.5 || t.hi < -0.5);
    if disjoint(y) && (partner.is_none() || disjoint(z)) {
        return best;
    }
    // Exact pose witnesses can prove every descendant's rules impossible: if both
    // entire cells miss one admitted cube, no pointwise single/pair rule can hold.
    // This only prunes zero subtrees, never supplies a positive lower bound.
    if count == 0
        && pose.witnesses.iter().any(|(r, c)| {
            let miss = |q: [I; 3]| {
                (0..3).any(|i| {
                    let t = sum((0..3).map(|v| r[v][i] * (q[v] - c[v])));
                    t.lo > 0.5 || t.hi < -0.5
                })
            };
            miss(y) && (partner.is_none() || miss(z))
        })
    {
        return best;
    }
    let axis = (0..3)
        .filter(|&w| !deg[w] && level[w] < data.cell_depth)
        .max_by(|&a, &b| {
            let len =
                |w: usize| (p.bounds[w][1] - p.bounds[w][0]) as f64 / ((1u64 << level[w]) as f64);
            len(a).total_cmp(&len(b)).then_with(|| b.cmp(&a))
        });
    if let Some(w) = axis {
        let mut lv = level;
        lv[w] += 1;
        let mut g = grid;
        g[w] *= 2;
        let left = cell(p, partner, pose, g, lv);
        g[w] += 1;
        let right = cell(p, partner, pose, g, lv);
        let children = left.mass + right.mass;
        if children.lo > best.mass.lo {
            best = Value {
                mass: children,
                lemmas: std::array::from_fn(|i| left.lemmas[i] + right.lemmas[i]),
            };
        }
    }
    best
}
pub fn bound(b: &Box6, domain: bool) -> Result {
    evaluate(b, domain, true)
}
pub fn evaluate(b: &Box6, domain: bool, early: bool) -> Result {
    assert!(valid(b), "invalid parameter box");
    let mut out = Result {
        reason: Reason::Split,
        lower: 0.,
        contributions: [0.; 3],
        lemmas: [0; 6],
    };
    if domain && outside(b) {
        out.reason = Reason::Outside;
        return out;
    }
    let data = crate::measure::DATA.get().unwrap();
    let pose = Pose::new(*b);
    let mut total = ZERO;
    let mut types = [ZERO; 3];
    for &(i, pair) in &data.groups {
        let p = &data.pieces[i];
        let v = cell(p, pair.map(|(_, w)| w), &pose, [0; 3], [0; 3]);
        total = total + v.mass;
        types[p.dim] = types[p.dim] + v.mass;
        for k in 0..6 {
            out.lemmas[k] += v.lemmas[k];
        }
        out.lower = (data.sigma * total).lo.max(0.);
        if out.lower >= 1. {
            out.reason = Reason::Bound;
            if early {
                break;
            }
        }
    }
    out.contributions = types.map(|v| (data.sigma * v).lo.max(0.));
    out
}

/// Validation-only API: test every rule independently, including rules shadowed by S.
pub fn rule_flags(b: &Box6, y: [I; 3], w: usize) -> [bool; 6] {
    assert!(valid(b) && w < 3);
    let pose = Pose::new(*b);
    let deg = y.map(|v| v.lo == v.hi);
    let walls = y.map(|v| {
        if v.hi <= 1. {
            -1
        } else if v.lo >= 2. {
            1
        } else {
            0
        }
    });
    let mut z = y;
    z[w] = z[w] + ONE;
    std::array::from_fn(|k| {
        if k < 4 {
            pose.single(y, deg, walls, 1 << k).is_some()
        } else {
            pose.pair(y, z, w, 1 << k).is_some()
        }
    })
}

/// All scalar rule enclosures, exposed only for independent sampling validation.
pub fn enclosures(b: &Box6, y: [I; 3]) -> Vec<I> {
    let p = Pose::new(*b);
    let mut out = Vec::new();
    out.extend(p.t(y));
    for w in 0..3 {
        let mut z = y;
        z[w] = z[w] + ONE;
        out.extend(p.t(z));
        for k in 0..3 {
            out.push(p.direction[w][k]);
            out.push(p.absolute[w][k]);
            for j in 0..3 {
                if j != k {
                    out.push(p.cf[w][k][j].enclose(&p, y, p.affine(p.chord[w][k][j], y)));
                }
            }
        }
        let span = I::p(3.) - I::p(2.) * p.h[w];
        let u = b[w + 3];
        out.push(p.centre(y[w], w, 0, ONE - y[w] + u * span));
        let v = I::new((ONE - u).lo.max(0.), (ONE - u).hi.min(1.));
        out.push(p.centre(y[w], w, 1, y[w] - I::p(2.) + v * span));
        for j in 0..3 {
            out.push(p.m_quantity(y, w, j, p.t(y)[j]));
        }
    }
    out
}
