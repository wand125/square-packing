//!
//! Claim checked: for every R in O(4) whose first column u satisfies max_e u_e^2 <= 2/3,
//!   F_1(R) = sum_e |R_e1| (2 - w_e) < 1,  w_e = sum_j |R_ej|.
//! (The near region max_e u_e^2 >= 2/3 is the hand proof of PROOF.md §3.)
//!
//! Reduction (PROOF.md §4): left signed permutations give u_1 >= u_2 >= u_3 >= u_4 >= 0, written
//! u = (1, t) / |(1, t)| with 1 >= t_0 >= t_1 >= t_2 >= 0. The other three columns are N_u S, N_u the
//! columns 2..4 of the Householder reflection taking e_1 to u, S in O(3). Right signed permutations of
//! columns 2..4 and S -> -S reduce S to the rotations S(q), q = (1, x, y, z) in the Voronoi cell of 1 for the
//! binary octahedral group: |x|, |y|, |z| <= sqrt(2) - 1 and |x| + |y| + |z| <= 1 (we use the superset 0.4143).
//!
//! A box is closed when (in order): the ordering / l1 constraint is infeasible; |t|^2 <= 1/2 on the whole box
//! (near region); or an upper bound of F_1 is < 1. Each entry of R is enclosed by the mean-value form
//! R(c) + sum_k dR/dz_k(box) (z_k - c_k), with the gradient over the box from forward-mode automatic
//! differentiation in interval arithmetic, intersected with the naive enclosure and with [-1, 1].
//! All interval operations round outward (next_down / next_up after each correctly rounded f64 operation).

use std::collections::HashSet;
use std::fs::OpenOptions;
use std::io::{BufRead, BufReader, Write};
use std::sync::atomic::{AtomicUsize, Ordering};
use std::sync::{Arc, Mutex};
use std::time::Instant;

// ---------------------------------------------------------------- intervals with outward rounding
#[derive(Clone, Copy, Debug)]
struct I {
    lo: f64,
    hi: f64,
}
const ENTIRE: I = I { lo: f64::NEG_INFINITY, hi: f64::INFINITY };
#[inline]
fn dn(x: f64) -> f64 {
    x.next_down()
}
#[inline]
fn up(x: f64) -> f64 {
    x.next_up()
}
impl I {
    fn pt(x: f64) -> I {
        I { lo: x, hi: x }
    }
    fn finite(self) -> bool {
        self.lo.is_finite() && self.hi.is_finite() && self.lo <= self.hi
    }
    fn mag(self) -> f64 {
        self.lo.abs().max(self.hi.abs())
    }
    fn abs(self) -> I {
        if !self.finite() {
            return I { lo: 0.0, hi: f64::INFINITY };
        }
        if self.lo >= 0.0 {
            self
        } else if self.hi <= 0.0 {
            I { lo: -self.hi, hi: -self.lo }
        } else {
            I { lo: 0.0, hi: self.mag() }
        }
    }
    fn meet(self, o: I) -> I {
        I { lo: self.lo.max(o.lo), hi: self.hi.min(o.hi) }
    }
    /// sqrt of a quantity known to be >= 0 (a negative lower end is clamped to 0).
    fn sqrt_nonneg(self) -> I {
        if !self.finite() {
            return I { lo: 0.0, hi: f64::INFINITY };
        }
        let lo = if self.lo <= 0.0 { 0.0 } else { dn(self.lo.sqrt()).max(0.0) };
        I { lo, hi: up(self.hi.max(0.0).sqrt()) }
    }
}

trait Num: Copy {
    fn cst(x: f64) -> Self;
    fn add(self, o: Self) -> Self;
    fn sub(self, o: Self) -> Self;
    fn mul(self, o: Self) -> Self;
    fn sq(self) -> Self;
    fn recip(self) -> Self; // argument > 0
    fn sqrt(self) -> Self; // argument > 0
}

impl Num for I {
    fn cst(x: f64) -> I {
        I::pt(x)
    }
    fn add(self, o: I) -> I {
        I { lo: dn(self.lo + o.lo), hi: up(self.hi + o.hi) }
    }
    fn sub(self, o: I) -> I {
        I { lo: dn(self.lo - o.hi), hi: up(self.hi - o.lo) }
    }
    fn mul(self, o: I) -> I {
        if !self.finite() || !o.finite() {
            return ENTIRE;
        }
        let p = [self.lo * o.lo, self.lo * o.hi, self.hi * o.lo, self.hi * o.hi];
        let (mut a, mut b) = (p[0], p[0]);
        for &x in &p[1..] {
            a = a.min(x);
            b = b.max(x);
        }
        I { lo: dn(a), hi: up(b) }
    }
    fn sq(self) -> I {
        if !self.finite() {
            return I { lo: 0.0, hi: f64::INFINITY };
        }
        if self.lo >= 0.0 {
            I { lo: dn(self.lo * self.lo).max(0.0), hi: up(self.hi * self.hi) }
        } else if self.hi <= 0.0 {
            I { lo: dn(self.hi * self.hi).max(0.0), hi: up(self.lo * self.lo) }
        } else {
            let m = self.mag();
            I { lo: 0.0, hi: up(m * m) }
        }
    }
    fn recip(self) -> I {
        if !self.finite() || self.lo <= 0.0 {
            return ENTIRE;
        }
        I { lo: dn(1.0 / self.hi), hi: up(1.0 / self.lo) }
    }
    fn sqrt(self) -> I {
        if !self.finite() || self.lo < 0.0 {
            return ENTIRE;
        }
        I { lo: dn(self.lo.sqrt()).max(0.0), hi: up(self.hi.sqrt()) }
    }
}

// ---------------------------------------------------------------- forward-mode AD over intervals
const NV: usize = 6;
#[derive(Clone, Copy)]
struct D {
    v: I,
    g: [I; NV],
}
const ZERO: I = I { lo: 0.0, hi: 0.0 };
impl Num for D {
    fn cst(x: f64) -> D {
        D { v: I::pt(x), g: [ZERO; NV] }
    }
    fn add(self, o: D) -> D {
        let mut g = [ZERO; NV];
        for k in 0..NV {
            g[k] = self.g[k].add(o.g[k]);
        }
        D { v: self.v.add(o.v), g }
    }
    fn sub(self, o: D) -> D {
        let mut g = [ZERO; NV];
        for k in 0..NV {
            g[k] = self.g[k].sub(o.g[k]);
        }
        D { v: self.v.sub(o.v), g }
    }
    fn mul(self, o: D) -> D {
        let mut g = [ZERO; NV];
        for k in 0..NV {
            g[k] = self.g[k].mul(o.v).add(self.v.mul(o.g[k]));
        }
        D { v: self.v.mul(o.v), g }
    }
    fn sq(self) -> D {
        let two_v = self.v.mul(I::pt(2.0));
        let mut g = [ZERO; NV];
        for k in 0..NV {
            g[k] = two_v.mul(self.g[k]);
        }
        D { v: self.v.sq(), g }
    }
    fn recip(self) -> D {
        // d(1/a) = -a'/a^2
        let r = self.v.recip();
        let r2 = r.sq();
        let mut g = [ZERO; NV];
        for k in 0..NV {
            g[k] = ZERO.sub(self.g[k].mul(r2));
        }
        D { v: r, g }
    }
    fn sqrt(self) -> D {
        // d sqrt(a) = a' / (2 sqrt(a))
        let s = self.v.sqrt();
        let h = s.mul(I::pt(2.0)).recip();
        let mut g = [ZERO; NV];
        for k in 0..NV {
            g[k] = self.g[k].mul(h);
        }
        D { v: s, g }
    }
}

// ---------------------------------------------------------------- the rotation R(z)
/// z = (t0, t1, t2, x, y, z). Returns R as rows e = 0..3, columns j = 0..3 (column 0 = u).
fn eval<T: Num>(z: &[T; NV]) -> [[T; 4]; 4] {
    let one = T::cst(1.0);
    let two = T::cst(2.0);
    let t = [z[0], z[1], z[2]];
    let tt = t[0].sq().add(t[1].sq()).add(t[2].sq());
    let u1 = tt.add(one).sqrt().recip();
    let u = [u1, t[0].mul(u1), t[1].mul(u1), t[2].mul(u1)];
    let coef = u1.add(one).mul(tt.recip()); // u1^2 / (1 - u1)
    // N = columns 2..4 of the Householder reflection taking e_1 to u
    let mut n = [[T::cst(0.0); 3]; 4];
    for j in 0..3 {
        n[0][j] = u[j + 1];
    }
    for e in 0..3 {
        for j in 0..3 {
            let p = if e == j { t[e].sq() } else { t[e].mul(t[j]) };
            let d = if e == j { one } else { T::cst(0.0) };
            n[e + 1][j] = d.sub(p.mul(coef));
        }
    }
    // S = rotation of the quaternion (1, x, y, z)
    let (x, y, w) = (z[3], z[4], z[5]);
    let (xx, yy, ww) = (x.sq(), y.sq(), w.sq());
    let inv = one.add(xx).add(yy).add(ww).recip();
    let (xy, xw, yw) = (x.mul(y), x.mul(w), y.mul(w));
    let s = [
        [one.sub(two.mul(yy.add(ww)).mul(inv)), two.mul(xy.sub(w)).mul(inv), two.mul(xw.add(y)).mul(inv)],
        [two.mul(xy.add(w)).mul(inv), one.sub(two.mul(xx.add(ww)).mul(inv)), two.mul(yw.sub(x)).mul(inv)],
        [two.mul(xw.sub(y)).mul(inv), two.mul(yw.add(x)).mul(inv), one.sub(two.mul(xx.add(yy)).mul(inv))],
    ];
    let mut r = [[T::cst(0.0); 4]; 4];
    for e in 0..4 {
        r[e][0] = u[e];
        for j in 0..3 {
            r[e][j + 1] = n[e][0].mul(s[0][j]).add(n[e][1].mul(s[1][j])).add(n[e][2].mul(s[2][j]));
        }
    }
    r
}

// ---------------------------------------------------------------- one box
type Bx = [I; NV];
const SMAX: f64 = 0.4143; // > sqrt(2) - 1

enum Verdict {
    Infeasible,
    Near,
    ClosedG,
    ClosedF,
    Open([f64; NV]), // split scores per coordinate
}

fn check(b: &Bx) -> (Verdict, f64) {
    // ordering 1 >= t0 >= t1 >= t2 >= 0 and |x|+|y|+|z| <= 1
    if b[0].hi < b[1].lo || b[1].hi < b[2].lo {
        return (Verdict::Infeasible, f64::NAN);
    }
    let s_l1 = b[3].abs().add(b[4].abs()).add(b[5].abs()); // lower end rounded down
    if s_l1.lo > 1.0 {
        return (Verdict::Infeasible, f64::NAN);
    }
    // near region: |t|^2 <= 1/2 on the whole box (u_1^2 >= 2/3)
    let tt = b[0].sq().add(b[1].sq()).add(b[2].sq());
    if tt.hi <= 0.5 {
        return (Verdict::Near, f64::NAN);
    }
    // mean-value enclosure of R
    let mut zb = [D::cst(0.0); NV];
    let mut zc = [I::pt(0.0); NV];
    let mut dz = [ZERO; NV];
    for k in 0..NV {
        let mut g = [ZERO; NV];
        g[k] = I::pt(1.0);
        zb[k] = D { v: b[k], g };
        let c = 0.5 * (b[k].lo + b[k].hi);
        zc[k] = I::pt(c);
        dz[k] = I { lo: dn(b[k].lo - c), hi: up(b[k].hi - c) };
    }
    let rb = eval(&zb);
    let rc = eval(&zc);
    let mut a = [[ZERO; 4]; 4];
    let mut score = [0.0f64; NV];
    let mut ok = true;
    for e in 0..4 {
        for j in 0..4 {
            let mut enc = rc[e][j];
            for k in 0..NV {
                enc = enc.add(rb[e][j].g[k].mul(dz[k]));
                score[k] += rb[e][j].g[k].mag() * (b[k].hi - b[k].lo);
            }
            let enc = enc.meet(rb[e][j].v).meet(I { lo: -1.0, hi: 1.0 });
            if !enc.finite() {
                ok = false;
            }
            a[e][j] = enc.abs();
        }
    }
    if !ok {
        // cannot bound (e.g. |t|^2 touches 0): split the widest t coordinate
        let mut sc = [0.0; NV];
        for k in 0..3 {
            sc[k] = b[k].hi - b[k].lo;
        }
        return (Verdict::Open(sc), f64::INFINITY);
    }
    let one = I::pt(1.0);
    let two = I::pt(2.0);
    let mut u_l1 = ZERO;
    for e in 0..4 {
        u_l1 = u_l1.add(a[e][0]);
    }
    let base = two.mul(u_l1).sub(one); // 2||u||_1 - 1
    let mut gsum = ZERO;
    for e in 0..4 {
        gsum = gsum.add(a[e][0].mul(one.sub(a[e][0].sq()).sqrt_nonneg()));
    }
    let g_ub = base.sub(gsum).hi;
    if g_ub < 1.0 {
        return (Verdict::ClosedG, g_ub);
    }
    // F_a = sum_e a_e (2 - w_e),  F_b = 2||u||_1 - 1 - sum_e a_e ||m_e||_1
    let mut fa = ZERO;
    let mut cross = ZERO;
    for e in 0..4 {
        let m = a[e][1].add(a[e][2]).add(a[e][3]);
        let w = a[e][0].add(m);
        fa = fa.add(a[e][0].mul(two.sub(w)));
        cross = cross.add(a[e][0].mul(m));
    }
    let fb = base.sub(cross);
    let ub = fa.hi.min(fb.hi);
    if ub < 1.0 {
        return (Verdict::ClosedF, ub);
    }
    (Verdict::Open(score), ub)
}

// ---------------------------------------------------------------- driver
fn root() -> Bx {
    let t = I { lo: 0.0, hi: 1.0 };
    let s = I { lo: -SMAX, hi: SMAX };
    [t, t, t, s, s, s]
}

fn tasks(split: usize) -> Vec<Bx> {
    // uniform split of every coordinate into `split` pieces
    let r = root();
    let mut out = vec![];
    let total = split.pow(NV as u32);
    for idx in 0..total {
        let mut b = r;
        let mut m = idx;
        for k in 0..NV {
            let p = m % split;
            m /= split;
            let w = (r[k].hi - r[k].lo) / split as f64;
            let lo = if p == 0 { r[k].lo } else { r[k].lo + w * p as f64 };
            let hi = if p + 1 == split { r[k].hi } else { r[k].lo + w * (p + 1) as f64 };
            b[k] = I { lo, hi };
        }
        out.push(b);
    }
    out
}

#[derive(Default, Clone)]
struct Stats {
    boxes: u64,
    infeasible: u64,
    near: u64,
    closed_g: u64,
    closed_f: u64,
    max_depth: usize,
    fails: Vec<String>,
    max_ub_closed: f64,
}

fn run_task(b0: Bx, max_depth: usize) -> Stats {
    let mut st = Stats::default();
    let mut stack: Vec<(Bx, usize)> = vec![(b0, 0)];
    while let Some((b, d)) = stack.pop() {
        st.boxes += 1;
        st.max_depth = st.max_depth.max(d);
        let (v, ub) = check(&b);
        match v {
            Verdict::Infeasible => st.infeasible += 1,
            Verdict::Near => st.near += 1,
            Verdict::ClosedG => {
                st.closed_g += 1;
                st.max_ub_closed = st.max_ub_closed.max(ub);
            }
            Verdict::ClosedF => {
                st.closed_f += 1;
                st.max_ub_closed = st.max_ub_closed.max(ub);
            }
            Verdict::Open(score) => {
                if d >= max_depth {
                    if st.fails.len() < 5 {
                        st.fails.push(format!("{:?} ub={}", b.iter().map(|i| (i.lo, i.hi)).collect::<Vec<_>>(), ub));
                    } else {
                        st.fails.push(String::new());
                    }
                    continue;
                }
                let mut k = 0;
                for j in 1..NV {
                    if score[j] > score[k] {
                        k = j;
                    }
                }
                if !(score[k] > 0.0) {
                    // fall back to the widest coordinate
                    for j in 0..NV {
                        if b[j].hi - b[j].lo > b[k].hi - b[k].lo {
                            k = j;
                        }
                    }
                }
                let mid = 0.5 * (b[k].lo + b[k].hi);
                let mut b1 = b;
                let mut b2 = b;
                b1[k].hi = mid;
                b2[k].lo = mid;
                stack.push((b1, d + 1));
                stack.push((b2, d + 1));
            }
        }
    }
    st
}

fn selftest(n: usize) {
    // random boxes; random points inside must satisfy: R(point) orthogonal, F(point) <= ub of the box
    let mut seed: u64 = 0x9e3779b97f4a7c15;
    let mut rnd = move || {
        seed ^= seed << 13;
        seed ^= seed >> 7;
        seed ^= seed << 17;
        (seed >> 11) as f64 / (1u64 << 53) as f64
    };
    let mut worst = f64::NEG_INFINITY;
    let (mut tested, mut closed) = (0, 0);
    for _ in 0..n {
        let r = root();
        let w = [0.2, 0.05, 0.02, 0.005][(rnd() * 4.0) as usize % 4];
        let mut b = r;
        for k in 0..NV {
            let c = r[k].lo + (r[k].hi - r[k].lo) * rnd();
            b[k] = I { lo: c - w / 2.0, hi: c + w / 2.0 };
        }
        let (v, ub) = check(&b);
        if !matches!(v, Verdict::ClosedF | Verdict::ClosedG | Verdict::Open(_)) || !ub.is_finite() {
            continue;
        }
        tested += 1;
        if matches!(v, Verdict::ClosedF | Verdict::ClosedG) {
            closed += 1;
        }
        for _ in 0..20 {
            let mut z = [I::pt(0.0); NV];
            for k in 0..NV {
                z[k] = I::pt(b[k].lo + (b[k].hi - b[k].lo) * rnd());
            }
            let r = eval(&z);
            for i in 0..4 {
                for j in 0..4 {
                    let mut dot = 0.0;
                    for e in 0..4 {
                        dot += r[e][i].lo * r[e][j].lo;
                    }
                    let want = if i == j { 1.0 } else { 0.0 };
                    assert!((dot - want).abs() < 1e-9, "not orthogonal: {} {} {}", i, j, dot);
                }
            }
            let mut f = 0.0;
            for e in 0..4 {
                let w: f64 = (0..4).map(|j| r[e][j].lo.abs()).sum();
                f += r[e][0].lo.abs() * (2.0 - w);
            }
            worst = worst.max(f - ub);
        }
    }
    println!("{{\"selftest_boxes\": {}, \"closed\": {}, \"max F(point) - ub\": {:e}}}", tested, closed, worst);
    assert!(worst <= 0.0, "enclosure violated");
}

fn main() {
    let args: Vec<String> = std::env::args().collect();
    let get = |name: &str, def: &str| -> String {
        args.iter().position(|a| a == name).map(|i| args[i + 1].clone()).unwrap_or(def.to_string())
    };
    if args.iter().any(|a| a == "--selftest") {
        selftest(get("--n", "20000").parse().unwrap());
        return;
    }
    let jobs: usize = get("--jobs", "1").parse().unwrap();
    let split: usize = get("--split", "4").parse().unwrap();
    let max_depth: usize = get("--max-depth", "60").parse().unwrap();
    let log = get("--log", "m2bb_tasks.jsonl");
    let first: usize = get("--first", "0").parse().unwrap();
    let all = tasks(split);
    let last: usize = get("--last", &all.len().to_string()).parse().unwrap();
    // resume: skip task ids already in the log
    let mut done = HashSet::new();
    if let Ok(f) = std::fs::File::open(&log) {
        for line in BufReader::new(f).lines().map_while(Result::ok) {
            if let Some(p) = line.find("\"id\": ") {
                let rest = &line[p + 6..];
                let end = rest.find(',').unwrap_or(rest.len());
                if let Ok(id) = rest[..end].trim().parse::<usize>() {
                    done.insert(id);
                }
            }
        }
    }
    let todo: Vec<usize> = (first..last.min(all.len())).filter(|i| !done.contains(i)).collect();
    eprintln!("tasks {} (split {}), range {}..{}, already done {}, to do {}", all.len(), split, first, last, done.len(), todo.len());
    let all = Arc::new(all);
    let todo = Arc::new(todo);
    let next = Arc::new(AtomicUsize::new(0));
    let out = Arc::new(Mutex::new(OpenOptions::new().create(true).append(true).open(&log).unwrap()));
    let total = Arc::new(Mutex::new(Stats::default()));
    let t0 = Instant::now();
    let mut hs = vec![];
    for _ in 0..jobs {
        let (all, todo, next, out, total) = (all.clone(), todo.clone(), next.clone(), out.clone(), total.clone());
        hs.push(std::thread::spawn(move || loop {
            let i = next.fetch_add(1, Ordering::SeqCst);
            if i >= todo.len() {
                break;
            }
            let id = todo[i];
            let ts = Instant::now();
            let st = run_task(all[id], max_depth);
            let line = format!(
                "{{\"id\": {}, \"boxes\": {}, \"infeasible\": {}, \"near\": {}, \"closed_g\": {}, \"closed_f\": {}, \"max_depth\": {}, \"fails\": {}, \"max_ub_closed\": {}, \"seconds\": {:.2}, \"fail_boxes\": {:?}}}\n",
                id, st.boxes, st.infeasible, st.near, st.closed_g, st.closed_f, st.max_depth, st.fails.len(), st.max_ub_closed,
                ts.elapsed().as_secs_f64(), st.fails.iter().filter(|s| !s.is_empty()).collect::<Vec<_>>()
            );
            {
                let mut f = out.lock().unwrap();
                f.write_all(line.as_bytes()).unwrap();
                f.flush().unwrap();
            }
            let mut t = total.lock().unwrap();
            t.boxes += st.boxes;
            t.infeasible += st.infeasible;
            t.near += st.near;
            t.closed_g += st.closed_g;
            t.closed_f += st.closed_f;
            t.max_depth = t.max_depth.max(st.max_depth);
            t.fails.extend(st.fails);
        }));
    }
    for h in hs {
        h.join().unwrap();
    }
    let t = total.lock().unwrap();
    println!(
        "{{\"run_tasks\": {}, \"boxes\": {}, \"infeasible\": {}, \"near\": {}, \"closed_g\": {}, \"closed_f\": {}, \"max_depth\": {}, \"fails\": {}, \"seconds\": {:.1}}}",
        todo.len(), t.boxes, t.infeasible, t.near, t.closed_g, t.closed_f, t.max_depth, t.fails.len(), t0.elapsed().as_secs_f64()
    );
}
