//! Independent floating evaluator: directly intersect each support with six cube faces.
use crate::{geometry::*, interval::*, measure::data, sha256};
struct Rng(u64);
impl Rng {
    fn f(&mut self) -> f64 {
        self.0 ^= self.0 << 13;
        self.0 ^= self.0 >> 7;
        self.0 ^= self.0 << 17;
        (self.0 >> 11) as f64 / (1u64 << 53) as f64
    }
}
pub fn rotation_float(x: [f64; 6]) -> [[f64; 3]; 3] {
    let (a, b, g) = (x[0], x[1], x[2]);
    let (sa, ca) = a.sin_cos();
    let (sb, cb) = b.sin_cos();
    let (sg, cg) = g.sin_cos();
    [
        [ca * cb * cg - sa * sg, -ca * cb * sg - sa * cg, ca * sb],
        [sa * cb * cg + ca * sg, -sa * cb * sg + ca * cg, sa * sb],
        [-sb * cg, sb * sg, cb],
    ]
}
pub fn mass(x: [f64; 6]) -> f64 {
    let r = rotation_float(x);
    let c: [f64; 3] = std::array::from_fn(|w| {
        let h = r[w].iter().map(|v| v.abs()).sum::<f64>() * 0.5;
        h + x[w + 3] * (3. - 2. * h)
    });
    mass_pose(r, c)
}
fn mass_pose(r: [[f64; 3]; 3], c: [f64; 3]) -> f64 {
    let mut mass = 0.;
    for p in &data().pieces {
        let axes: Vec<_> = (0..3).filter(|&w| p.b[w][0] != p.b[w][1]).collect();
        let base: [f64; 3] = std::array::from_fn(|w| p.b[w][0] as f64 / 10.);
        let t: [f64; 3] = std::array::from_fn(|i| (0..3).map(|w| r[w][i] * (base[w] - c[w])).sum());
        let area = match axes.len() {
            0 => {
                if t.iter().all(|v| v.abs() <= 0.5 + 1e-14) {
                    1.
                } else {
                    0.
                }
            }
            1 => {
                let w = axes[0];
                let mut lo: f64 = 0.;
                let mut hi = (p.b[w][1] - p.b[w][0]) as f64 / 10.;
                for i in 0..3 {
                    let a = r[w][i];
                    if a == 0. {
                        if t[i].abs() > 0.5 + 1e-14 {
                            hi = -1.;
                        }
                    } else {
                        let a1 = (-0.5 - t[i]) / a;
                        let a2 = (0.5 - t[i]) / a;
                        lo = lo.max(a1.min(a2));
                        hi = hi.min(a1.max(a2));
                    }
                }
                (hi - lo).max(0.)
            }
            _ => {
                let u = axes[0];
                let v = axes[1];
                let l = (p.b[u][1] - p.b[u][0]) as f64 / 10.;
                let h = (p.b[v][1] - p.b[v][0]) as f64 / 10.;
                let mut poly = vec![[0., 0.], [l, 0.], [l, h], [0., h]];
                for i in 0..3 {
                    for sign in [-1., 1.] {
                        let mut q = vec![];
                        for j in 0..poly.len() {
                            let a = poly[j];
                            let b = poly[(j + 1) % poly.len()];
                            let f = sign * (t[i] + r[u][i] * a[0] + r[v][i] * a[1]) - 0.5;
                            let g = sign * (t[i] + r[u][i] * b[0] + r[v][i] * b[1]) - 0.5;
                            if f <= 0. {
                                q.push(a);
                            }
                            if (f < 0. && g > 0.) || (f > 0. && g < 0.) {
                                let z = f / (f - g);
                                q.push([a[0] + z * (b[0] - a[0]), a[1] + z * (b[1] - a[1])]);
                            }
                        }
                        poly = q;
                    }
                }
                let mut a = 0.;
                for j in 0..poly.len() {
                    let u = poly[j];
                    let v = poly[(j + 1) % poly.len()];
                    a += u[0] * v[1] - u[1] * v[0];
                }
                a.abs() * 0.5
            }
        };
        mass += p.rho * area;
    }
    mass
}
pub fn run() {
    mean_value_test();
    let start = std::time::Instant::now();
    let mut rng = Rng(0xace123456789);
    assert_eq!(
        sha256::hash(b"abc"),
        "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
    );
    assert_eq!(
        sha256::hash(b""),
        "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    );
    for _ in 0..10000 {
        let lo = rng.f() * 6.2;
        let hi = lo + rng.f() * 0.08;
        let (s, c) = sincos(I::new(lo, hi));
        for x in [lo, (lo + hi) * 0.5, hi] {
            assert!(s.lo <= x.sin() && x.sin() <= s.hi);
            assert!(c.lo <= x.cos() && x.cos() <= c.hi);
        }
    }
    println!("SHA-256 vectors and 10000 trig intervals: passed");
    let root = root();
    let mut nonzero = 0;
    let mut precise_rechecks = 0;
    let mut counts = [0u64; 6];
    let mut rule_tests = [0u64; 6];
    for _ in 0..200 {
        let x = std::array::from_fn(|i| rng.f() * root.x[i].hi);
        let b = Box6 {
            x: x.map(I::pt),
            depth: 0,
        };
        let v = bound(&b).lower;
        let r = rotation_float(x);
        let u = [x[3], x[4], x[5]];
        for perm in crate::symmetry::PERMUTATIONS {
            for mask in 0..8 {
                let (rr, uu) = crate::symmetry::image(r, u, perm, mask);
                let image = crate::symmetry::euler(rr, uu);
                let canonical = crate::symmetry::canonical(rr, uu);
                for y in [image, canonical] {
                    let other = bound(&Box6 {
                        x: y.map(I::pt),
                        depth: 0,
                    })
                    .lower;
                    assert!(
                        (v - other).abs() <= 1e-9,
                        "48-image/canonical bound mismatch {} {} {:?} {:?} {}",
                        v,
                        other,
                        x,
                        perm,
                        mask
                    );
                }
            }
        }
    }
    println!("48 images and their u-sorted canonical representatives: 200 degenerate boxes, tolerance 1e-9; zero failures");
    orbit_test();
    for k in 0..20000 {
        let mut x = std::array::from_fn(|i| rng.f() * root.x[i].hi);
        if k % 4 == 0 {
            x[3 + k % 3] = 0.;
        }
        if k % 4 == 1 {
            x[0] = 0.;
            x[1] = 0.;
            x[2] = 0.;
            let angle = rng.f() * 1.5;
            match (k / 4) % 3 {
                0 => {
                    x[0] = std::f64::consts::FRAC_PI_2;
                    x[1] = angle;
                }
                1 => x[1] = angle,
                _ => x[0] = angle,
            };
            for i in 3..6 {
                x[i] = [0., 0.2, 0.25, 0.45, 0.5][(k + i) % 5];
            }
        }
        let radius = 10f64.powf(-8. + rng.f() * 6.);
        let b = Box6 {
            x: std::array::from_fn(|i| {
                I::new((x[i] - radius).max(0.), (x[i] + radius).min(root.x[i].hi))
            }),
            depth: 0,
        };
        let lower = bound(&b);
        if lower.lower > 0. {
            nonzero += 1;
        }
        for i in 0..6 {
            counts[i] += lower.counts[i];
        }
        for sample in 0..50 {
            let v = std::array::from_fn(|i| {
                b.x[i].lo + b.x[i].width() * if sample == 0 { 0.5 } else { rng.f() }
            });
            let mut actual = mass(v) * data().sigma.mid();
            if actual < lower.lower - 1e-12 {
                // Near-parallel support intersections amplify binary64 pose
                // errors. Re-evaluate independently at 80 decimal digits;
                // never relax the specified 1e-12 acceptance tolerance.
                let result=std::process::Command::new("python3").arg("-c").arg("import sys,json; from stress_random import precise_mass; print(precise_mass(json.loads(sys.argv[1])))").arg(format!("{:?}",v)).current_dir(env!("CARGO_MANIFEST_DIR")).output().unwrap();
                assert!(result.status.success(), "precise evaluator failed");
                actual = String::from_utf8(result.stdout)
                    .unwrap()
                    .trim()
                    .parse::<f64>()
                    .unwrap()
                    * data().sigma.mid();
                precise_rechecks += 1;
            }
            assert!(
                actual >= lower.lower - 1e-12,
                "false bound {:?} {} {} sample {:?}",
                b,
                lower.lower,
                actual,
                v
            );
        }
        // Test each affine rule separately on a random point of a random support.
        let pose = pose(&b);
        let p = &data().pieces[k % data().pieces.len()];
        let y: [f64; 3] = std::array::from_fn(|w| {
            (p.b[w][0] as f64 + rng.f() * (p.b[w][1] - p.b[w][0]) as f64) / 10.
        });
        for pair in [
            None,
            (0..3).find(|&w| p.b[w][0] == p.b[w][1] && p.b[w][0] <= 20),
        ] {
            for (rule, conditions) in rules(&pose, p, pair) {
                if conditions
                    .iter()
                    .all(|f| f.enclosure(p, y.map(I::pt), &pose.delta).hi <= 0.)
                {
                    rule_tests[rule] += 1;
                    let r = rotation_float(x);
                    let c: [f64; 3] = std::array::from_fn(|w| {
                        let h = r[w].iter().map(|v| v.abs()).sum::<f64>() * 0.5;
                        h + x[w + 3] * (3. - 2. * h)
                    });
                    let inside = |y: [f64; 3]| {
                        (0..3).all(|i| {
                            (0..3).map(|w| r[w][i] * (y[w] - c[w])).sum::<f64>().abs()
                                <= 0.5 + 1e-12
                        })
                    };
                    let mut yy = y;
                    if let Some(w) = pair {
                        yy[w] += 1.;
                    }
                    assert!(inside(y) || (pair.is_some() && inside(yy)), "rule {}", rule);
                }
            }
        }
        if k % 2000 == 1999 {
            eprintln!(
                "validation: {} boxes, {} seconds",
                k + 1,
                start.elapsed().as_secs_f64()
            );
        }
    }
    println!("80-digit near-parallel rechecks: {}", precise_rechecks);
    assert!(rule_tests.iter().all(|&v| v > 0), "unexercised rule");
    println!("Individual rule witnesses {:?}", rule_tests);
    println!("20000 boxes / 1000000 sampled poses: zero failures; positive bounds {}; lemma contributions {:?}; seconds {}",nonzero,counts,start.elapsed().as_secs_f64());
}

// Independent scalar formula checks, one sample on each of 10,000 random
// boxes for EVERY indexed quantity; includes boxes crossing |R| cusps.
pub fn mean_value_test() {
    use crate::dual::D;
    let mut rng = Rng(0x1234abcd9876);
    let mut tested = 0;
    for n in 0..10000 {
        let root = root();
        let b = Box6 {
            x: std::array::from_fn(|k| {
                let m = if n % 4 == 0 && k < 3 {
                    0.
                } else {
                    rng.f() * root.x[k].hi
                };
                let width = 0.001 + rng.f() * 0.2;
                I::new((m - width).max(0.), (m + width).min(root.x[k].hi))
            }),
            depth: 0,
        };
        let p = pose(&b);
        let piece = &data().pieces[n % data().pieces.len()];
        let x = std::array::from_fn(|k| b.x[k].lo + rng.f() * b.x[k].width());
        let y: [f64; 3] = std::array::from_fn(|w| {
            (piece.b[w][0] as f64 + rng.f() * (piece.b[w][1] - piece.b[w][0]) as f64) / 10.
        });
        let r = rotation_float(x);
        let h: [f64; 3] = std::array::from_fn(|w| r[w].iter().map(|v| v.abs()).sum::<f64>() * 0.5);
        let c: [f64; 3] = std::array::from_fn(|w| h[w] + x[w + 3] * (3. - 2. * h[w]));
        let t: [f64; 3] = std::array::from_fn(|i| (0..3).map(|w| r[w][i] * (y[w] - c[w])).sum());
        let mut check = |label: &str, f: Aff, value: f64| {
            let e = f.enclosure(piece, y.map(I::pt), &p.delta);
            assert!(
                e.lo <= value && value <= e.hi,
                "{} sample {}: {:?} does not contain {}",
                label,
                n,
                e,
                value
            );
            let (a, centre, y0) = f.centred(piece, &p.delta);
            let centred = (0..3).fold(centre, |v, w| v + a[w] * (I::pt(y[w]) - y0[w]));
            assert!(
                centred.lo <= value && value <= centred.hi,
                "centred polygon enclosure {}",
                label
            );
            let (a, base) = f.local(piece, &p.delta);
            let local = (0..3).fold(base, |v, w| {
                v + a[w] * (I::pt(y[w]) - crate::measure::tenth(piece.b[w][0]))
            });
            assert!(
                local.lo <= value && value <= local.hi,
                "local polygon enclosure {}",
                label
            );
            tested += 1;
        };
        let scalar = |d: D| Aff {
            a: [D::constant(ZERO); 3],
            b: d,
        };
        for i in 0..3 {
            check("T", p.t[i], t[i]);
        }
        for w in 0..3 {
            let mut a = [D::constant(ZERO); 3];
            a[w] = D::constant(ONE);
            check(
                "F lower",
                Aff {
                    a,
                    b: -ONE - p.u[w] * (I::pt(3.) - I::pt(2.) * p.h[w]),
                },
                y[w] - 1. - x[w + 3] * (3. - 2. * h[w]),
            );
            a[w] = D::constant(-ONE);
            check(
                "F upper",
                Aff {
                    a,
                    b: -ONE + I::pt(3.) * p.u[w] + I::pt(2.) * p.h[w] * (ONE - p.u[w]),
                },
                -y[w] - 1. + 3. * x[w + 3] + 2. * h[w] * (1. - x[w + 3]),
            );
            for k in 0..3 {
                check("d", scalar(p.r[w][k]), r[w][k]);
                check("abs d", scalar(p.r[w][k].abs()), r[w][k].abs());
                check("translated T", p.t[k].shift(p.r[w][k]), t[k] + r[w][k]);
                for j in 0..3 {
                    if j != k {
                        let ch = p.t[j].scale(p.r[w][k]).sub(p.t[k].scale(p.r[w][j]));
                        let cv = r[w][k] * t[j] - r[w][j] * t[k];
                        check("chord", ch, cv);
                        for sign in [-1., 1.] {
                            check(
                                "full chord",
                                ch.scale(I::pt(sign))
                                    .shift(HALF * (p.r[w][j].abs() - p.r[w][k].abs())),
                                sign * cv + 0.5 * (r[w][j].abs() - r[w][k].abs()),
                            );
                            check(
                                "M",
                                p.t[j].scale(I::pt(sign)).shift(p.r[w][j].abs() - HALF),
                                sign * t[j] + r[w][j].abs() - 0.5,
                            );
                        }
                    }
                }
            }
        }
    }
    println!("mean-value-1: 10000 random boxes, 10000 samples of every indexed T, translated T, d, |d|, chord, full-chord, F and M quantity; {} containment checks; zero failures",tested);
}

// Separate RNG preserves the existing soundness test's random sample stream.
fn orbit_test() {
    let mut rng = Rng(0xa248123456789);
    for _ in 0..10000 {
        let mut x = std::array::from_fn(|i| rng.f() * root().x[i].hi);
        for w in 3..6 {
            x[w] = rng.f();
        }
        let y = crate::symmetry::canonical(rotation_float(x), [x[3], x[4], x[5]]);
        assert!(y[3] >= 0. && y[3] <= y[4] && y[4] <= y[5] && y[5] <= 0.5);
        for k in 0..3 {
            assert!(y[k] >= 0. && y[k] <= root().x[k].hi);
        }
        let original = mass(x);
        let representative = mass(y);
        assert!(
            (original - representative).abs() <= 1e-9,
            "orbit mass mismatch {:?} {:?}: {} {}",
            x,
            y,
            original,
            representative
        );
    }
    println!("Amendment 2: 10000 random full-domain poses, canonical domain membership and independent floating mass equality to 1e-9; zero failures");
}
