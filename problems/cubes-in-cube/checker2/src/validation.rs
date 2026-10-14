use crate::{geometry::*, interval::*, search::State, sha256};
const S: f64 = 2. + std::f64::consts::FRAC_1_SQRT_2;
type M = [[f64; 3]; 3];
struct Rng(u64);
impl Rng {
    fn f(&mut self) -> f64 {
        self.0 ^= self.0 << 13;
        self.0 ^= self.0 >> 7;
        self.0 ^= self.0 << 17;
        (self.0 >> 11) as f64 / (1u64 << 53) as f64
    }
}
fn mul(a: M, b: M) -> M {
    std::array::from_fn(|i| std::array::from_fn(|j| (0..3).map(|k| a[i][k] * b[k][j]).sum()))
}
fn rot(x: [f64; 6]) -> M {
    let (sa, ca) = x[0].sin_cos();
    let (sb, cb) = x[1].sin_cos();
    let (sg, cg) = x[2].sin_cos();
    mul(
        mul(
            [[ca, -sa, 0.], [sa, ca, 0.], [0., 0., 1.]],
            [[cb, 0., sb], [0., 1., 0.], [-sb, 0., cb]],
        ),
        [[cg, -sg, 0.], [sg, cg, 0.], [0., 0., 1.]],
    )
}
fn center(r: M, x: [f64; 6]) -> [f64; 3] {
    std::array::from_fn(|w| {
        let h = r[w].iter().map(|v| v.abs()).sum::<f64>() * 0.5;
        h + x[w + 3] * (S - 2. * h)
    })
}
fn mask(r: M, c: [f64; 3], tol: f64) -> u8 {
    let mut bits = 0;
    for p in 0..8 {
        if (0..3).all(|i| {
            let t: f64 = (0..3)
                .map(|w| r[w][i] * ((if p & (1 << w) == 0 { 1. } else { S - 1. }) - c[w]))
                .sum();
            t.abs() <= 0.5 + tol
        }) {
            bits |= 1 << p;
        }
    }
    bits
}
fn small(x: [f64; 6], radius: f64) -> Box6 {
    let root = root();
    Box6 {
        x: std::array::from_fn(|i| {
            I::new(
                (x[i] - radius).max(root.x[i].lo),
                (x[i] + radius).min(root.x[i].hi),
            )
        }),
        depth: 0,
    }
}
fn sample(b: &Box6, o: &Outcome, rng: &mut Rng, n: usize) {
    for k in 0..n {
        let x = std::array::from_fn(|i| {
            let u = match k {
                0 => 0.5,
                1 => 0.,
                2 => 1.,
                _ => rng.f(),
            };
            b.x[i].lo + u * b.x[i].width()
        });
        let r = rot(x);
        let c = center(r, x);
        let m = mask(r, c, 1e-12);
        assert!(
            o.points.iter().any(|&p| m & (1 << p) != 0),
            "false closure: {:?}, {:?}, sample {:?}, mask {}",
            b,
            o,
            x,
            m
        );
    }
}
fn angles(r: M) -> [f64; 3] {
    let beta = r[2][2].clamp(-1., 1.).acos();
    let (alpha, gamma) = if beta.sin().abs() > 1e-12 {
        (r[1][2].atan2(r[0][2]), r[2][1].atan2(-r[2][0]))
    } else if r[2][2] > 0. {
        (r[1][0].atan2(r[0][0]), 0.)
    } else {
        ((-r[1][0]).atan2(-r[0][0]), 0.)
    };
    [
        alpha.rem_euclid(2. * std::f64::consts::PI),
        beta,
        gamma.rem_euclid(std::f64::consts::FRAC_PI_2),
    ]
}
fn perms() -> Vec<[usize; 3]> {
    vec![
        [0, 1, 2],
        [0, 2, 1],
        [1, 0, 2],
        [1, 2, 0],
        [2, 0, 1],
        [2, 1, 0],
    ]
}
fn det(r: M) -> f64 {
    r[0][0] * (r[1][1] * r[2][2] - r[1][2] * r[2][1])
        - r[0][1] * (r[1][0] * r[2][2] - r[1][2] * r[2][0])
        + r[0][2] * (r[1][0] * r[2][1] - r[1][1] * r[2][0])
}
fn cover(b: Box6, cap: u32, rng: &mut Rng, counts: &mut [u64; 7]) -> bool {
    if let Some(o) = close(&b) {
        counts[o.rule as usize] += 1;
        sample(&b, &o, rng, 8);
        true
    } else if b.depth == cap {
        false
    } else {
        let [l, r] = split(b);
        cover(l, cap, rng, counts) && cover(r, cap, rng, counts)
    }
}
pub fn run() {
    let start = std::time::Instant::now();
    assert_eq!(crate::json::parse("9007199254740993").uint(), 9007199254740993);
    assert_eq!(crate::json::parse("18446744073709551615").uint(), u64::MAX);
    let mut rng = Rng(0x9e3779b97f4a7c15);
    assert_eq!(
        sha256::hash(b""),
        "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    );
    assert_eq!(
        sha256::hash(b"abc"),
        "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
    );
    assert_eq!(
        sha256::hash(&vec![b'a'; 1000000]),
        "cdc76e5c9914fb9281a1c7e284d73e67f1809a48a497200e046d39ccc7112cd0"
    );
    // Both constants lie in [1/2,1), so x = mantissa * 2^-53.
    let mant = |x: f64| ((x.to_bits() & ((1u64 << 52) - 1)) | (1u64 << 52)) as u128;
    assert!(mant(INV_SQRT2.lo).pow(2) < 1u128 << 105);
    assert!(mant(INV_SQRT2.hi).pow(2) > 1u128 << 105);
    for _ in 0..10000 {
        let lo = rng.f() * 2. * std::f64::consts::PI;
        let hi = (lo + rng.f() * 0.1).min(2. * std::f64::consts::PI);
        let (s, c) = sincos(I::new(lo, hi));
        for x in [lo, (lo + hi) * 0.5, hi] {
            assert!(s.lo <= x.sin() && x.sin() <= s.hi);
            assert!(c.lo <= x.cos() && x.cos() <= c.hi);
        }
    }
    println!("arithmetic: SHA-256 3 vectors; inverse sqrt enclosure exact; 10000 trig intervals / 30000 samples");
    let mut counts = [0u64; 7];
    let mut closed = [0; 2];
    for group in 0..2 {
        let n = if group == 0 { 100000 } else { 20000 };
        for k in 0..n {
            let mut x = [
                rng.f() * 2. * std::f64::consts::PI,
                rng.f() * std::f64::consts::PI,
                rng.f() * std::f64::consts::FRAC_PI_2,
                rng.f() * 0.5,
                rng.f() * 0.5,
                rng.f() * 0.5,
            ];
            if group == 1 {
                x[3 + k % 3] = 0.;
            }
            let b = small(x, 1e-9);
            if let Some(o) = close(&b) {
                closed[group] += 1;
                counts[o.rule as usize] += 1;
                sample(&b, &o, &mut rng, 5);
            }
        }
        println!(
            "random group {group}: {n} boxes, {} closed, zero false closures",
            closed[group]
        );
    }
    println!("random leaves by rule: {:?}", counts);
    let mut individual = [0u64; 7];
    for _ in 0..20000 {
        let x = [
            rng.f() * 2. * std::f64::consts::PI,
            rng.f() * std::f64::consts::PI,
            rng.f() * std::f64::consts::FRAC_PI_2,
            rng.f() * 0.5,
            rng.f() * 0.5,
            rng.f() * 0.5,
        ];
        let b = small(x, 1e-6);
        for rule in [1, 2, 3, 5, 6] {
            if let Some(o) = close_filtered(&b, 1 << rule) {
                individual[rule as usize] += 1;
                sample(&b, &o, &mut rng, 5);
            }
        }
    }
    for rule in [1, 2, 3, 5, 6] {
        assert!(individual[rule] > 0, "unexercised rule {rule}");
    }
    println!(
        "individual rules on 20000 additional boxes: {:?}; 5 samples/closure, zero false closures",
        individual
    );

    let v = std::f64::consts::FRAC_1_SQRT_2;
    let rx = [[1., 0., 0.], [0., v, -v], [0., v, v]];
    let mut p0_counts = [0u64; 7];
    let mut p0_boxes = 0;
    for wp in perms() {
        for cp in perms() {
            for signs in 0..8 {
                let r = std::array::from_fn(|w| {
                    std::array::from_fn(|i| {
                        rx[wp[w]][cp[i]] * if signs & (1 << i) == 0 { 1. } else { -1. }
                    })
                });
                if det(r) < 0. {
                    continue;
                }
                let angle = angles(r);
                let mut x = [angle[0], angle[1], angle[2], 0.5, 0.5, 0.5];
                for w in 0..3 {
                    if wp[w] == 0 {
                        x[w + 3] = 0.;
                    }
                }
                for radius in [1e-4, 1e-3, 1e-2] {
                    let b = small(x, radius);
                    let o = close(&b).unwrap_or_else(|| {
                        panic!(
                            "P0 box did not close: {:?}, wp {:?}, cp {:?}, signs {}",
                            b, wp, cp, signs
                        )
                    });
                    p0_counts[o.rule as usize] += 1;
                    sample(&b, &o, &mut rng, 67);
                    p0_boxes += 1;
                }
            }
        }
    }
    println!(
        "P0: {p0_boxes} boxes, rule counts {:?}, 67 samples/box, zero false closures",
        p0_counts
    );
    let cases = [
        ("corner", [0., 0., 0., 0., 0., 0.]),
        ("face x=1 and wall x=0", [0., 0., 0., 0., 0.35, 0.4]),
        ("face-diagonal opposite faces", {
            let a = angles(rx);
            [a[0], a[1], a[2], 0., 0.5, 0.5]
        }),
        ("axis-aligned centre", [0., 0., 0., 0.5, 0.5, 0.5]),
    ];
    for (name, x) in cases {
        let mut cs = [0; 7];
        assert!(
            cover(small(x, 0.01), 24, &mut rng, &mut cs),
            "degenerate {name} unresolved"
        );
        println!("degenerate {name}: closed at depth <=24, counts {:?}", cs);
    }
    for _ in 0..10000 {
        let x = [
            rng.f() * 2. * std::f64::consts::PI,
            rng.f() * std::f64::consts::PI,
            rng.f() * 2. * std::f64::consts::PI,
            rng.f(),
            rng.f(),
            rng.f(),
        ];
        let r = rot(x);
        let c = center(r, x);
        let m = mask(r, c, 0.);
        let mut rr = r;
        let mut cc = c;
        let mut flips = 0;
        for w in 0..3 {
            if x[w + 3] > 0.5 {
                flips |= 1 << w;
                cc[w] = S - c[w];
                for i in 0..3 {
                    rr[w][i] = -rr[w][i];
                }
            }
        }
        if det(rr) < 0. {
            for row in &mut rr {
                row[2] = -row[2];
            }
        }
        let a = angles(rr);
        let reduced = rot([a[0], a[1], a[2], 0., 0., 0.]);
        let mm = mask(reduced, cc, 0.);
        for p in 0..8 {
            assert_eq!(
                (m >> p) & 1,
                (mm >> (p ^ flips)) & 1,
                "symmetry mask mismatch"
            );
        }
    }
    println!("symmetry: 10000 poses, all 8 containment bits preserved under reflections and Euler reduction");
    let mut s1 = State::new();
    let mut s2 = State::new();
    for _ in 0..80 {
        s1.round(1, 24);
        s2.round(2, 24);
    }
    assert_eq!(s1.boxes, s2.boxes);
    assert_eq!(s1.leaves, s2.leaves);
    assert_eq!(s1.digest, s2.digest);
    println!(
        "thread determinism: 80 rounds, boxes {}, digest {}",
        s1.boxes, s1.digest
    );
    println!(
        "validation passed; seconds {}",
        start.elapsed().as_secs_f64()
    );
}
