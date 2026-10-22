use crate::dual::{intersect, D};
use crate::interval::*;
#[derive(Clone, Copy, Debug)]
pub struct Box6 {
    pub x: [I; 6],
    pub depth: u32,
}
#[derive(Clone, Debug)]
pub struct Outcome {
    pub counts: [u64; 6],
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
// Amendment 2: strict separation only; shared simplex faces are retained.
pub fn outside(b: &Box6) -> bool {
    b.x[3].lo > b.x[4].hi || b.x[4].lo > b.x[5].hi
}
pub fn split(b: Box6) -> [Box6; 2] {
    // Amendment 2: the 300-probe comparison favours equal width divisors
    // (uw=1: 1.87e8 nodes; uw=4: 5.12e8). Ties retain the lowest index.
    let widths = [1.; 6];
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
use crate::measure::{data, tenth, Piece};
// Affine expression in world coordinates: a.y + b <= 0.
#[derive(Clone, Copy)]
pub struct Aff {
    pub a: [D; 3],
    pub b: D,
}
impl Aff {
    pub fn scale(self, s: impl Into<D>) -> Self {
        let s = s.into();
        Self {
            a: self.a.map(|a| a * s),
            b: self.b * s,
        }
    }
    pub fn sub(self, v: Self) -> Self {
        Self {
            a: std::array::from_fn(|w| self.a[w] - v.a[w]),
            b: self.b - v.b,
        }
    }
    pub fn shift(mut self, v: impl Into<D>) -> Self {
        self.b = self.b + v.into();
        self
    }
}
impl Aff {
    // Retain y-y0 until coefficient-corner enumeration, avoiding a second
    // interval occurrence of the same spatial coefficient during translation.
    pub fn centred(&self, piece: &Piece, delta: &[I; 6]) -> ([I; 3], I, [I; 3]) {
        let cell: [I; 3] =
            std::array::from_fn(|w| I::new(tenth(piece.b[w][0]).lo, tenth(piece.b[w][1]).hi));
        let y0 = cell.map(|y| I::pt(y.mid()));
        let centre = (0..3).fold(self.b.m, |s, w| s + self.a[w].m * y0[w]);
        let mv = (0..6).fold(centre, |s, k| {
            let g = (0..3).fold(self.b.g[k], |v, w| v + self.a[w].g[k] * cell[w]);
            s + g * delta[k]
        });
        let naive = (0..3).fold(self.b.v, |s, w| s + self.a[w].v * y0[w]);
        (self.a.map(|a| a.enclosure(delta)), intersect(naive, mv), y0)
    }
    pub fn local(&self, piece: &Piece, delta: &[I; 6]) -> ([I; 3], I) {
        let base: [I; 3] = std::array::from_fn(|w| tenth(piece.b[w][0]));
        let cell: [I; 3] = std::array::from_fn(|w| I::new(base[w].lo, tenth(piece.b[w][1]).hi));
        let y0 = cell.map(|y| I::pt(y.mid()));
        let at_mid = (0..3).fold(self.b.m, |s, w| s + self.a[w].m * y0[w]);
        let g: [I; 6] =
            std::array::from_fn(|k| (0..3).fold(self.b.g[k], |s, w| s + self.a[w].g[k] * cell[w]));
        let a = self.a.map(|a| a.enclosure(delta));
        let mv = (0..6).fold(at_mid, |s, k| s + g[k] * delta[k]);
        let mv_base = (0..3).fold(mv, |s, w| s + a[w] * (base[w] - y0[w]));
        // Preserve the original collected naive expression, including F wall zeros.
        let naive = (0..3).fold(self.b.v, |s, w| s + self.a[w].v * base[w]);
        (a, intersect(naive, mv_base))
    }
    pub fn enclosure(&self, piece: &Piece, y: [I; 3], delta: &[I; 6]) -> I {
        let cell: [I; 3] =
            std::array::from_fn(|w| I::new(tenth(piece.b[w][0]).lo, tenth(piece.b[w][1]).hi));
        let y0 = cell.map(|v| I::pt(v.mid()));
        let centre = (0..3).fold(self.b.m, |s, w| s + self.a[w].m * y0[w]);
        let mv = (0..6).fold(centre, |s, k| {
            let g = (0..3).fold(self.b.g[k], |v, w| v + self.a[w].g[k] * cell[w]);
            s + g * delta[k]
        });
        let mv = (0..3).fold(mv, |s, w| s + self.a[w].enclosure(delta) * (y[w] - y0[w]));
        let naive = (0..3).fold(self.b.v, |s, w| s + self.a[w].v * y[w]);
        intersect(naive, mv)
    }
}
fn absolute(v: Aff, rhs: impl Into<D>, out: &mut Vec<Aff>) {
    let rhs = rhs.into();
    out.push(v.shift(-rhs));
    out.push(v.scale(-ONE).shift(-rhs));
}
pub struct Pose {
    pub r: [[D; 3]; 3],
    pub h: [D; 3],
    pub c: [D; 3],
    pub u: [D; 3],
    pub t: [Aff; 3],
    pub delta: [I; 6],
}
pub fn pose(b: &Box6) -> Pose {
    let x: [D; 6] = std::array::from_fn(|k| D::variable(b.x[k], k));
    let delta = std::array::from_fn(|k| b.x[k] - I::pt(b.x[k].mid()));
    // Analytic derivatives of Rz(alpha) Ry(beta) Rz(gamma), propagated
    // using d sin = cos and d cos = -sin with our interval trig.
    let (sa, ca) = x[0].sincos();
    let (sb, cb) = x[1].sincos();
    let (sg, cg) = x[2].sincos();
    let r = [
        [ca * cb * cg - sa * sg, -ca * cb * sg - sa * cg, ca * sb],
        [sa * cb * cg + ca * sg, -sa * cb * sg + ca * cg, sa * sb],
        [-sb * cg, sb * sg, cb],
    ];
    let h = std::array::from_fn(|w| (r[w][0].abs() + r[w][1].abs() + r[w][2].abs()) * HALF);
    let u = std::array::from_fn(|w| x[w + 3]);
    let c = std::array::from_fn(|w| h[w] + u[w] * (I::pt(3.) - I::pt(2.) * h[w]));
    let t = std::array::from_fn(|i| Aff {
        a: std::array::from_fn(|w| r[w][i]),
        b: -(0..3).fold(D::constant(ZERO), |v, w| v + r[w][i] * c[w]),
    });
    Pose {
        r,
        h,
        c,
        u,
        t,
        delta,
    }
}
// SPEC W/P full chord, collected before evaluation to avoid repeating y.
fn chord(p: &Pose, w: usize, k: usize) -> Vec<Aff> {
    let mut v = vec![];
    for j in 0..3 {
        if j != k {
            absolute(
                p.t[j].scale(p.r[w][k]).sub(p.t[k].scale(p.r[w][j])),
                HALF * (p.r[w][k].abs() - p.r[w][j].abs()),
                &mut v,
            )
        }
    }
    v
}
// Each alternative is a convex certified region. Taking their maximum is safe;
// their areas must never be summed because the alternatives can overlap.
pub fn rules(p: &Pose, piece: &Piece, pair: Option<usize>) -> Vec<(usize, Vec<Aff>)> {
    let mut all = vec![];
    if let Some(w) = pair {
        for k in 0..3 {
            // SPEC P: fixed nonzero sign is mandatory.
            let d = p.r[w][k];
            let di = d.enclosure(&p.delta);
            if di.lo > 0. || di.hi < 0. {
                let sign = I::pt(if di.lo > 0. { 1. } else { -1. });
                let mut v = chord(p, w, k);
                v.push(p.t[k].scale(sign).shift(-HALF));
                v.push(p.t[k].shift(d).scale(-sign).shift(-HALF));
                all.push((4, v));
            }
            // SPEC P': slab pair, both signs, no division.
            for s in [-1., 1.] {
                let sign = I::pt(s);
                let mut v = vec![];
                for j in 0..3 {
                    if j != k {
                        absolute(p.t[j], HALF, &mut v);
                        absolute(p.t[j].shift(p.r[w][j]), HALF, &mut v);
                    }
                }
                v.push(p.t[k].scale(sign).shift(-HALF));
                v.push(p.t[k].shift(d).scale(-sign).shift(-HALF));
                all.push((5, v));
            }
        }
    } else {
        // SPEC S.
        let mut v = vec![];
        for t in p.t {
            absolute(t, HALF, &mut v)
        }
        all.push((0, v));
        // SPEC F, collected: y-1-u(3-2h)<=0 and -y-1+3u+2h(1-u)<=0.
        let mut v = vec![];
        for w in 0..3 {
            let mut a = [D::constant(ZERO); 3];
            a[w] = D::constant(ONE);
            v.push(Aff {
                a,
                b: -ONE - p.u[w] * (I::pt(3.) - I::pt(2.) * p.h[w]),
            });
            a[w] = D::constant(-ONE);
            v.push(Aff {
                a,
                b: -ONE + I::pt(3.) * p.u[w] + I::pt(2.) * p.h[w] * (ONE - p.u[w]),
            });
        }
        all.push((1, v));
        for w in 0..3 {
            if piece.b[w][0] != piece.b[w][1] {
                continue;
            }
            let q = piece.b[w][0];
            if q > 10 && q < 20 {
                continue;
            }
            let lower = q <= 10;
            for k in 0..3 {
                let d = p.r[w][k];
                let di = d.enclosure(&p.delta);
                if di.lo <= 0. && di.hi >= 0. {
                    continue;
                }
                let sign = I::pt(if di.lo > 0. { 1. } else { -1. });
                // SPEC W.
                let mut v = chord(p, w, k);
                v.push(p.t[k].scale(if lower { -sign } else { sign }).shift(-HALF));
                all.push((2, v));
                // SPEC M: wall lemma supplies one face; explicitly certify the opposite
                // face and the stronger transverse hypotheses of M5 PROOF §3.
                let mut v = vec![];
                for j in 0..3 {
                    if j != k {
                        absolute(p.t[j], HALF - p.r[w][j].abs(), &mut v)
                    }
                }
                v.push(p.t[k].scale(if lower { -sign } else { sign }).shift(-HALF));
                all.push((3, v));
            }
        }
    }
    all
}
// SPEC §8. Local coordinates z are nonnegative distances from the exact
// rational lower corner. Enumerate ALL interval coefficient corners anyway.
// Floating clipping only proposes vertices. Each final dyadic vertex is
// certified by outward interval arithmetic against EVERY half-plane, then
// convexity proves its hull is inside. Failed certification yields zero.
// This avoids assuming that a rounded line intersection is on the inner side.
pub fn region(piece: &Piece, conditions: &[Aff], delta: &[I; 6]) -> f64 {
    // Both certify the same unchanged rule. Maximum, never sum: the regions
    // overlap. The collected lower-corner version preserves exact wall slack.
    let centred = region_form(piece, conditions, delta, true);
    if piece.dim == 0 && centred == 1. {
        return 1.;
    }
    centred.max(region_form(piece, conditions, delta, false))
}
fn region_form(piece: &Piece, conditions: &[Aff], delta: &[I; 6], centred: bool) -> f64 {
    let free: Vec<_> = (0..3).filter(|&w| piece.b[w][0] < piece.b[w][1]).collect();
    let n = free.len();
    let len: Vec<_> = free
        .iter()
        .map(|&w| tenth(piece.b[w][1] - piece.b[w][0]).lo)
        .collect();
    let mut hs: Vec<([f64; 2], f64)> = vec![];
    for f in conditions {
        let base: [I; 3] = std::array::from_fn(|w| tenth(piece.b[w][0]));
        let (coeff, mut b, shift) = if centred {
            let (a, b, y0) = f.centred(piece, delta);
            (a, b, std::array::from_fn(|w| base[w] - y0[w]))
        } else {
            let (a, b) = f.local(piece, delta);
            (a, b, [ZERO; 3])
        };
        // Degenerate axes do not enter corner enumeration.
        for w in 0..3 {
            if !free.contains(&w) {
                b = b + coeff[w] * shift[w];
            }
        }
        if n == 0 {
            if b.hi > 0. {
                return 0.;
            }
            continue;
        }
        for mask in 0..(1 << n) {
            let mut a = [0.; 2];
            for i in 0..n {
                let v = coeff[free[i]];
                a[i] = if mask & (1 << i) == 0 { v.lo } else { v.hi };
            }
            let rhs = (0..n).fold(b, |v, i| v + I::pt(a[i]) * shift[free[i]]);
            hs.push((a, -rhs.hi));
        }
    }
    if n == 0 {
        return 1.;
    }
    let eval =
        |a: [f64; 2], v: [f64; 2]| -> I { I::pt(a[0]) * I::pt(v[0]) + I::pt(a[1]) * I::pt(v[1]) };
    if n == 1 {
        let mut lo: f64 = 0.;
        let mut hi = len[0];
        for &(a, b) in &hs {
            if a[0] > 0. {
                hi = hi.min(down(b / a[0]));
            } else if a[0] < 0. {
                lo = lo.max(up(b / a[0]));
            } else if b < 0. {
                return 0.;
            }
        }
        if hi <= lo {
            return 0.;
        }
        for _ in 0..16 {
            if hs
                .iter()
                .all(|&(a, b)| eval(a, [lo, 0.]).hi <= b && eval(a, [hi, 0.]).hi <= b)
            {
                return down(hi - lo).max(0.);
            }
            lo = up(lo);
            hi = down(hi);
        }
        return 0.;
    }
    let mut poly = vec![[0., 0.], [len[0], 0.], [len[0], len[1]], [0., len[1]]];
    for &(a, b) in &hs {
        let mut next = vec![];
        if poly.len() < 3 {
            return 0.;
        }
        for i in 0..poly.len() {
            let v = poly[i];
            let w = poly[(i + 1) % poly.len()];
            let fv = a[0] * v[0] + a[1] * v[1] - b;
            let fw = a[0] * w[0] + a[1] * w[1] - b;
            if fv <= 0. {
                next.push(v);
            }
            if (fv < 0. && fw > 0.) || (fv > 0. && fw < 0.) {
                let t = fv / (fv - fw);
                next.push([v[0] + t * (w[0] - v[0]), v[1] + t * (w[1] - v[1])]);
            }
        }
        poly = next;
    }
    if poly.len() < 3 {
        return 0.;
    }
    let centre: [f64; 2] =
        std::array::from_fn(|i| poly.iter().map(|v| v[i]).sum::<f64>() / poly.len() as f64);
    for attempt in 0..10 {
        let factor = if attempt == 0 {
            1.
        } else {
            1. - 2f64.powi(-48 + attempt * 4)
        };
        let mut vertices: Vec<[f64; 2]> = poly
            .iter()
            .map(|v| std::array::from_fn(|i| centre[i] + factor * (v[i] - centre[i])))
            .collect();
        if !vertices.iter().all(|&v| {
            v[0] >= 0.
                && v[0] <= len[0]
                && v[1] >= 0.
                && v[1] <= len[1]
                && hs.iter().all(|&(a, b)| eval(a, v).hi <= b)
        }) {
            continue;
        }
        // Verify convex cyclic order as well: rounded clipping proposals alone
        // cannot justify adding triangle areas. Every non-edge vertex must be
        // rigorously on the left of every edge (or discard the proposal).
        let cross = |o: [f64; 2], a: [f64; 2], b: [f64; 2]| {
            (I::pt(a[0]) - I::pt(o[0])) * (I::pt(b[1]) - I::pt(o[1]))
                - (I::pt(a[1]) - I::pt(o[1])) * (I::pt(b[0]) - I::pt(o[0]))
        };
        // Drop ambiguous or collinear vertices; every retained point was already
        // certified. The resulting hull is an inner subset, never an expansion
        // outside the certified half-planes.
        vertices.sort_by(|a, b| a[0].total_cmp(&b[0]).then(a[1].total_cmp(&b[1])));
        vertices.dedup();
        let mut lower = Vec::new();
        for &v in &vertices {
            while lower.len() >= 2
                && cross(lower[lower.len() - 2], lower[lower.len() - 1], v).lo <= 0.
            {
                lower.pop();
            }
            lower.push(v);
        }
        let mut upper = Vec::new();
        for &v in vertices.iter().rev() {
            while upper.len() >= 2
                && cross(upper[upper.len() - 2], upper[upper.len() - 1], v).lo <= 0.
            {
                upper.pop();
            }
            upper.push(v);
        }
        lower.pop();
        upper.pop();
        lower.extend(upper);
        vertices = lower;
        if vertices.len() < 3 {
            continue;
        }
        if !(0..vertices.len()).all(|i| {
            (0..vertices.len())
                .filter(|&j| j != i && j != (i + 1) % vertices.len())
                .all(|j| {
                    cross(vertices[i], vertices[(i + 1) % vertices.len()], vertices[j]).lo >= 0.
                })
        }) {
            continue;
        }
        // Signed triangle fan: interval determinant encloses exact dyadic area.
        let origin = vertices[0];
        let mut area = ZERO;
        for i in 1..vertices.len() - 1 {
            let a = vertices[i];
            let b = vertices[i + 1];
            area = area + (I::pt(a[0]) - I::pt(origin[0])) * (I::pt(b[1]) - I::pt(origin[1]))
                - (I::pt(a[1]) - I::pt(origin[1])) * (I::pt(b[0]) - I::pt(origin[0]));
        }
        return (area * HALF).lo.max(0.);
    }
    0.
}
#[derive(Clone, Debug)]
pub struct Bound {
    pub lower: f64,
    pub types: [f64; 3],
    pub counts: [u64; 6],
}
impl Bound {
    pub fn json(&self) -> String {
        format!(
            "{{\"L\":{},\"contributions\":{:?},\"lemma_counts\":{:?}}}",
            self.lower, self.types, self.counts
        )
    }
}
// Box-only affine dual coefficients are shared by all support cells.
struct RuleCache {
    common: Vec<(usize, Vec<Aff>)>,
    walls: [Vec<(usize, Vec<Aff>)>; 6],
    pairs: [Vec<(usize, Vec<Aff>)>; 3],
}
impl RuleCache {
    fn new(p: &Pose) -> Self {
        let full = Piece {
            b: [[0, 30]; 3],
            rho: 1.,
            dim: 3,
        };
        let common = rules(p, &full, None);
        let walls = std::array::from_fn(|n| {
            let mut piece = full.clone();
            piece.b[n / 2] = [if n % 2 == 0 { 0 } else { 30 }; 2];
            rules(p, &piece, None).into_iter().skip(2).collect()
        });
        let pairs = std::array::from_fn(|w| rules(p, &full, Some(w)));
        Self {
            common,
            walls,
            pairs,
        }
    }
}
fn best(cache: &RuleCache, delta: &[I; 6], c: &Piece, pair: Option<usize>) -> (f64, usize) {
    let mut best = (0., 0);
    let mut visit = |list: &Vec<(usize, Vec<Aff>)>| {
        for (rule, conditions) in list {
            let a = region(c, conditions, delta);
            if a > best.0 {
                best = (a, *rule);
            }
        }
    };
    if let Some(w) = pair {
        visit(&cache.pairs[w]);
    } else {
        visit(&cache.common);
        for w in 0..3 {
            if c.b[w][0] == c.b[w][1] {
                if c.b[w][0] <= 10 {
                    visit(&cache.walls[2 * w]);
                } else if c.b[w][0] >= 20 {
                    visit(&cache.walls[2 * w + 1]);
                }
            }
        }
    }
    best
}
pub fn bound(b: &Box6) -> Bound {
    bound_pose(&pose(b))
}
pub fn bound_pose(p: &Pose) -> Bound {
    let d = data();
    let cache = RuleCache::new(p);
    let mut total = ZERO;
    let mut types = [ZERO; 3];
    let mut counts = [0; 6];
    for &i in &d.singles {
        let piece = &d.pieces[i];
        let (a, r) = best(&cache, &p.delta, piece, None);
        if a > 0. {
            counts[r] += 1;
        }
        let v = I::pt(a) * I::pt(piece.rho);
        total = total + v;
        types[piece.dim] = types[piece.dim] + v;
    }
    for &(i, j, w) in &d.pairs {
        let a = &d.pieces[i];
        let (v, r) = best(&cache, &p.delta, a, None);
        let (vv, rr) = best(&cache, &p.delta, &d.pieces[j], None);
        let (pair, rp) = best(&cache, &p.delta, a, Some(w));
        let single = (I::pt(v) + I::pt(vv)).lo.max(0.);
        let amount = if pair > single {
            if pair > 0. {
                counts[rp] += 1;
            }
            pair
        } else {
            if v > 0. {
                counts[r] += 1;
            }
            if vv > 0. {
                counts[rr] += 1;
            }
            single
        };
        let value = I::pt(amount) * I::pt(a.rho);
        total = total + value;
        types[a.dim] = types[a.dim] + value;
    }
    Bound {
        lower: (total * d.sigma).lo.max(0.),
        types: types.map(|v| (v * d.sigma).lo.max(0.)),
        counts,
    }
}
pub fn close(b: &Box6) -> Option<Outcome> {
    let v = bound(b);
    if v.lower >= 1. {
        Some(Outcome { counts: v.counts })
    } else {
        None
    }
}
