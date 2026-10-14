use crate::interval::*;
use serde::{Deserialize, Serialize};
pub type Box6 = [I; 6];
pub fn side() -> I {
    I::p(2.) + ONE / I::p(2.).sqrt()
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
    Point,
    Centre,
    Pair,
    Wall,
    /// Inside a parameter box closed by an external local lemma (M5_EXCLUDE; diagnostic only, never a proof).
    Excluded,
    /// Local sign lemma at the wall-touching 45-degree cube (PROOF.md section 5).
    LocalAb,
    Split,
}
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Result {
    pub reason: Reason,
    pub p: usize,
    pub q: usize,
    pub axis: usize,
    pub sign: i32,
    /// Best sufficient residual for each rule; split heuristic only.
    pub scores: [f64; 3],
}
pub fn bound(b: &Box6, domain: bool) -> Result {
    assert!(valid(b), "invalid parameter box");
    let mut out = Result {
        reason: Reason::Split,
        p: 0,
        q: 0,
        axis: 0,
        sign: 1,
        scores: [-1e100; 3],
    };
    if domain && outside(b) {
        out.reason = Reason::Outside;
        return out;
    }
    if let Some(e) = excluded() {
        if (0..6).all(|j| b[j].lo >= e[j].0 && b[j].hi <= e[j].1) {
            out.reason = Reason::Excluded;
            return out;
        }
    }
    let (r, h, c) = geometry(b);
    let s = side();
    let points: [[I; 3]; 8] = std::array::from_fn(|p| {
        std::array::from_fn(|w| if p & (1 << w) == 0 { ONE } else { s - ONE })
    });
    let t0: [[I; 3]; 8] =
        points.map(|p| std::array::from_fn(|i| sum((0..3).map(|w| r[w][i] * (p[w] - c[w])))));
    // Wall tightening (PROOF.md section 3): tighten t_k(p) at walls. For the lower-wall coordinate
    // p_w = 1 we have p_w - c_w = 1 - h_w - u_w(s - 2h_w) <= 1 - h_w =: a_w, so with R = R_wk:
    //   R >= 0: R(p_w - c_w) <= R a_w = 1/2 - (1-R)^2/2 - R sigma/2,   sigma = sum_{j != k} |R_wj|
    //   R <= 0: R(p_w - c_w) >= -(1/2 - (1-|R|)^2/2 - |R| sigma/2)
    // (exact identity R(1 - h_w) = R - R^2/2 - R sigma/2 with h_w = (|R| + sigma)/2). The upper-wall coordinate
    // p_w = s - 1 has c_w - p_w <= a_w: the same with R replaced by -R. The other two terms are evaluated as
    // usual. Each bound is valid for every pose of the box; t is intersected with them.
    let half = I::p(0.5);
    let mut t = t0;
    for p in 0..8 {
        for k in 0..3 {
            for w in 0..3 {
                let rr = if p & (1 << w) == 0 { r[w][k] } else { -r[w][k] };
                let sigma = sum((0..3).filter(|&j| j != k).map(|j| r[w][j].abs()));
                let rest = sum((0..3).filter(|&v| v != w).map(|v| r[v][k] * (points[p][v] - c[v])));
                if rr.lo >= 0. {
                    let m = half - half * (ONE - rr).sq() - half * rr * sigma;
                    let hi = (m + rest).hi;
                    if hi < t[p][k].hi {
                        t[p][k] = I::new(t[p][k].lo, hi.max(t[p][k].lo));
                    }
                } else if rr.hi <= 0. {
                    let ra = -rr;
                    let m = half - half * (ONE - ra).sq() - half * ra * sigma;
                    let lo = (rest - m).lo;
                    if lo > t[p][k].lo {
                        t[p][k] = I::new(lo.min(t[p][k].hi), t[p][k].hi);
                    }
                }
            }
        }
    }
    for p in 0..8 {
        let score = t[p]
            .iter()
            .map(|v| 0.5 - v.abs().hi)
            .fold(f64::INFINITY, f64::min);
        out.scores[0] = out.scores[0].max(score);
        if score >= 0. && out.reason == Reason::Split {
            out.reason = Reason::Point;
            out.p = p;
        }
        let score = (0..3)
            .map(|w| {
                // u or 1-u is nonnegative EXACTLY on the admitted parameter domain.
                let v = if p & (1 << w) == 0 {
                    b[w + 3]
                } else {
                    ONE - b[w + 3]
                };
                let v = I::new(v.lo.max(0.), v.hi.min(1.));
                // 2-2h-v(s-2h); collect h to avoid interval dependency loss.
                (I::p(2.) - v * s - I::p(2.) * h[w] * (ONE - v)).lo
            })
            .fold(f64::INFINITY, f64::min);
        out.scores[1] = out.scores[1].max(score);
        if score >= 0. && out.reason == Reason::Split {
            out.reason = Reason::Centre;
            out.p = p;
        }
    }
    // Wall lemma (PROOF.md section 3; added after the
    // benchmark stalled at one-wall face contacts). For p_w = 1 (lower wall, c_w >= h_w):
    // (p-c)_w = sum_j R_wj t_j <= 1 - h_w. If sigma*R_wi > 0 and |R_wj| + |t_j| <= 1/2 for both j != i, then
    // R_wi t_i <= 1 - R_wi/2 - sum_{j!=i} |R_wj|(1/2 - |t_j|) <= 1 - R_wi/2 - (1 - R_wi^2) <= R_wi/2, i.e.
    // sigma*t_i <= 1/2. The upper wall p_w = s-1 (c_w <= s - h_w) is the mirror: replace R_wi by -R_wi.
    if out.reason == Reason::Split {
        let half = I::p(0.5);
        for p in 0..8 {
            let all = (0..3).all(|i| {
                [1., -1.].iter().all(|&sg| {
                    (half - t[p][i] * I::p(sg)).lo >= 0.
                        || (0..3).any(|w| {
                            let m = if p & (1 << w) == 0 { 1. } else { -1. }; // lower or upper wall
                            (r[w][i] * I::p(sg * m)).lo > 0.
                                && (0..3)
                                    .filter(|&j| j != i)
                                    .all(|j| (r[w][j].abs() + t[p][j].abs()).hi <= half.lo)
                        })
                })
            });
            if all {
                out.reason = Reason::Wall;
                out.p = p;
                break;
            }
        }
    }
    // Local sign lemma (PROOF.md section 5). Wall x = 0, the four
    // points q at x = 1. Axes a_k = column k of R; f = c + a_0/2; g = (1, s/2, s/2); e = g - f; p = a_1.e,
    // r = a_2.e; nu = (a_0y, a_0z); d = (s/2 - c_y, s/2 - c_z); a = s/2 - 1 = 1/(2 sqrt 2). Hypotheses, each
    // checked over the whole box: c_x >= h_x (built into the parametrisation), a_0x > 0, |d| < a_0x/2 - a,
    // a_1y + a_1z >= 0, a_2z - a_2y >= 0, |p|, |r| <= 1/2, |r| + a|a_2y + a_2z| <= 1/2,
    // |p| + a|a_1y - a_1z| <= 1/2, and t_0(q) >= -1/2 for all four q (the near side of axis 0).
    // Conclusion: q_A (signs (-sgn p, -sgn p)) or q_B (signs (sgn r, -sgn r)) lies in the closed cube.
    if out.reason == Reason::Split {
        let half = I::p(0.5);
        let a = s * half - ONE;
        let col = |k: usize| [r[0][k], r[1][k], r[2][k]];
        let (a0, a1, a2) = (col(0), col(1), col(2));
        let g = [ONE, s * half, s * half];
        let e: [I; 3] = std::array::from_fn(|w| g[w] - c[w] - half * a0[w]);
        let dot = |u: [I; 3], v: [I; 3]| u[0] * v[0] + u[1] * v[1] + u[2] * v[2];
        let (pp, rr) = (dot(a1, e), dot(a2, e));
        let d = [s * half - c[1], s * half - c[2]];
        let m = a0[0] * half - a;
        let ok = a0[0].lo > 0.
            && m.lo > 0.
            && (d[0].sq() + d[1].sq()).hi < m.sq().lo
            && (a1[1] + a1[2]).lo >= 0.
            && (a2[2] - a2[1]).lo >= 0.
            && pp.abs().hi <= half.lo
            && rr.abs().hi <= half.lo
            && (rr.abs() + a * (a2[1] + a2[2]).abs()).hi <= half.lo
            && (pp.abs() + a * (a1[1] - a1[2]).abs()).hi <= half.lo
            && (0..8).filter(|&q| q & 1 == 0).all(|q| t[q][0].lo >= -half.hi);
        if ok {
            out.reason = Reason::LocalAb;
        }
    }
    for p in 0usize..8 {
        for q in p + 1..8 {
            if (p ^ q).count_ones() != 2 {
                continue;
            } // exactly the 12 unit face diagonals
            for i in 0..3 {
                for sign in [1, -1] {
                    let mut score = (0..3)
                        .filter(|&j| j != i)
                        .map(|j| 0.5 - t[p][j].abs().hi.max(t[q][j].abs().hi))
                        .fold(f64::INFINITY, f64::min);
                    let a = if sign == 1 { t[p][i] } else { -t[p][i] };
                    let b = if sign == 1 { t[q][i] } else { -t[q][i] };
                    score = score.min(0.5 - a.hi).min(b.lo + 0.5);
                    out.scores[2] = out.scores[2].max(score);
                    if score >= 0. && out.reason == Reason::Split {
                        out.reason = Reason::Pair;
                        out.p = p;
                        out.q = q;
                        out.axis = i;
                        out.sign = sign;
                    }
                }
            }
        }
    }
    out
}

/// M5_EXCLUDE="lo0,hi0,...,lo5,hi5": a parameter box left to a local lemma (diagnostic only). Not a proof by itself;
/// the receipt counts its leaves under `excluded`.
pub fn excluded() -> Option<[(f64, f64); 6]> {
    static E: std::sync::OnceLock<Option<[(f64, f64); 6]>> = std::sync::OnceLock::new();
    *E.get_or_init(|| {
        let v: Vec<f64> = std::env::var("M5_EXCLUDE").ok()?.split(',').map(|x| x.trim().parse().unwrap()).collect();
        assert_eq!(v.len(), 12, "M5_EXCLUDE needs 12 numbers");
        Some(std::array::from_fn(|j| (v[2 * j], v[2 * j + 1])))
    })
}
