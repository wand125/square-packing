//! SPEC section 2: integer-tenths geometry and exact parsed-double densities.
use crate::interval::*;
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::{collections::BTreeMap, sync::OnceLock};
#[derive(Clone, Serialize)]
pub struct Piece {
    pub bounds: [[i32; 2]; 3],
    pub density: f64,
    pub dim: usize,
}
#[derive(Deserialize)]
struct Input {
    side: f64,
    closed: bool,
    pieces: Vec<Raw>,
}
#[derive(Deserialize)]
struct Raw {
    r#type: String,
    bounds: [[f64; 2]; 3],
    density: f64,
}
pub struct Measure {
    pub pieces: Vec<Piece>,
    pub groups: Vec<(usize, Option<(usize, usize)>)>,
    pub sigma: I,
    pub cell_depth: u32,
    pub receipt: serde_json::Value,
}
pub static DATA: OnceLock<Measure> = OnceLock::new();
fn key(p: &Piece) -> ([[i32; 2]; 3], usize, u64) {
    (p.bounds, p.dim, p.density.to_bits())
}
pub fn load(path: &str, scale: &str, cell_depth: u32) -> Measure {
    let bytes = std::fs::read(path).expect("measure read");
    let input: Input = serde_json::from_slice(&bytes).expect("measure JSON");
    assert!(input.side == 3. && input.closed, "side/closed check");
    let mut pieces = vec![];
    for p in input.pieces {
        assert!(p.density.is_finite());
        let bounds = p.bounds.map(|v| {
            v.map(|x| {
                let k = (10. * x).round();
                assert!(
                    x.is_finite() && (10. * x - k).abs() <= 1e-9 && (0. ..=30.).contains(&k),
                    "coordinate check"
                );
                k as i32
            })
        });
        assert!(bounds.iter().all(|v| v[0] <= v[1]));
        if p.density <= 0. {
            continue;
        }
        let dim = bounds.iter().filter(|v| v[0] < v[1]).count();
        assert!(
            dim < 3 && p.r#type == ["point", "line", "plane"][dim],
            "piece dimension"
        );
        pieces.push(Piece {
            bounds,
            density: p.density,
            dim,
        });
    }
    let mut multiset = BTreeMap::new();
    for p in &pieces {
        *multiset.entry(key(p)).or_insert(0usize) += 1;
    }
    for perm in [
        [0, 1, 2],
        [0, 2, 1],
        [1, 0, 2],
        [1, 2, 0],
        [2, 0, 1],
        [2, 1, 0],
    ] {
        for mask in 0..8 {
            let mut image = BTreeMap::new();
            for p in &pieces {
                let mut q = p.clone();
                q.bounds = std::array::from_fn(|w| {
                    let v = p.bounds[perm[w]];
                    if mask & (1 << w) == 0 {
                        v
                    } else {
                        [30 - v[1], 30 - v[0]]
                    }
                });
                *image.entry(key(&q)).or_insert(0usize) += 1;
            }
            assert_eq!(multiset, image, "check 1: symmetry failed");
        }
    }
    let mut used = vec![false; pieces.len()];
    let mut groups = vec![];
    let mut multiple = 0;
    let mut counts = [0usize; 3];
    for (i, p) in pieces.iter().enumerate() {
        let mut candidates = vec![];
        for w in 0..3 {
            if p.bounds[w][0] != p.bounds[w][1] {
                continue;
            }
            for sign in [-10, 10] {
                let mut q = p.clone();
                q.bounds[w][0] += sign;
                q.bounds[w][1] += sign;
                let found: Vec<_> = pieces
                    .iter()
                    .enumerate()
                    .filter(|(_, r)| key(r) == key(&q))
                    .map(|(j, _)| j)
                    .collect();
                assert!(found.len() <= 1, "ambiguous partner");
                if let Some(&j) = found.first() {
                    candidates.push((w, j, sign));
                }
            }
        }
        if candidates
            .iter()
            .map(|x| x.0)
            .collect::<std::collections::BTreeSet<_>>()
            .len()
            > 1
        {
            multiple += 1;
        }
        if used[i] {
            continue;
        }
        if let Some(&(w, j, sign)) = candidates.first() {
            if sign == 10 && !used[j] {
                used[i] = true;
                used[j] = true;
                groups.push((i, Some((j, w))));
                counts[p.dim] += 1;
            }
        }
    }
    for i in 0..pieces.len() {
        if !used[i] {
            groups.push((i, None));
        }
    }
    let mut total = ZERO;
    for p in &pieces {
        let mut v = I::p(p.density);
        for b in p.bounds {
            if b[0] != b[1] {
                v = v * I::rational((b[1] - b[0]) as f64, 10.);
            }
        }
        total = total + v;
    }
    let pq: Vec<_> = scale
        .split('/')
        .map(|s| s.parse::<u64>().expect("sigma p/q"))
        .collect();
    assert!(pq.len() == 2 && pq.iter().all(|&n| n > 0 && n <= 1u64 << 53));
    let sigma = I::rational(pq[0] as f64, pq[1] as f64);
    let scaled = sigma * total;
    let n_claim = scaled.lo.floor() + 1.;
    assert!(
        n_claim <= (1u64 << 53) as f64,
        "n_claim exceeds exact integer range"
    );
    assert!(scaled.hi < n_claim, "check 3: total straddles integer");
    let facts = pieces.iter().all(|p| {
        !(p.dim == 0 && p.bounds.iter().all(|b| b[0] % 10 == 0))
            && !(p.dim == 1
                && p.bounds
                    .iter()
                    .filter(|b| b[0] == b[1] && b[0] % 10 == 0)
                    .count()
                    == 2)
    });
    let receipt = serde_json::json!({"measure_sha256":format!("{:x}",Sha256::digest(&bytes)),"sigma":scale,"T":total,"scaled_T":scaled,"n_claim":n_claim as u64,"symmetry_check":true,"symmetries":48,"pair_counts_by_dimension":counts,"multiple_pair_axes":multiple,"pair_policy":"first axis, disjoint matching; remaining pieces single","v5b_facts":facts,"positive_counts":(0..3).map(|d|pieces.iter().filter(|p|p.dim==d).count()).collect::<Vec<_>>(),"density_bits":pieces.iter().map(|p|format!("{:016x}",p.density.to_bits())).collect::<Vec<_>>()});
    Measure {
        pieces,
        groups,
        sigma,
        cell_depth,
        receipt,
    }
}
