//! SPEC §2: exact tenths, exact binary64 densities, all 48 symmetries.
use crate::{interval::*, json, sha256};
use std::{collections::BTreeMap, sync::OnceLock};
#[derive(Clone, Debug)]
pub struct Piece {
    pub b: [[i32; 2]; 3],
    pub rho: f64,
    pub dim: usize,
}
pub struct Measure {
    pub pieces: Vec<Piece>,
    pub pairs: Vec<(usize, usize, usize)>,
    pub singles: Vec<usize>,
    pub total: I,
    pub sigma: I,
    pub rational: String,
    pub claim: u64,
    pub hash: String,
    pub multi: usize,
    pub facts: [bool; 2],
}
pub static DATA: OnceLock<Measure> = OnceLock::new();
pub fn data() -> &'static Measure {
    DATA.get().unwrap()
}
pub fn tenth(k: i32) -> I {
    if k % 10 == 0 {
        I::pt((k / 10) as f64)
    } else {
        I::pt(k as f64).div_pos(10.)
    }
}
fn key(p: &Piece) -> (usize, [[i32; 2]; 3], u64) {
    (p.dim, p.b, p.rho.to_bits())
}
pub fn read(path: &str, ratio: &str) -> Measure {
    let raw = std::fs::read(path).unwrap();
    let hash = sha256::hash(&raw);
    let j = json::parse(std::str::from_utf8(&raw).unwrap());
    assert_eq!(j.get("side").num(), 3.);
    assert!(j.get("closed").boolean());
    let mut pieces = vec![];
    for p in j.get("pieces").arr() {
        let rho = p.get("density").num();
        if rho <= 0. {
            continue;
        }
        let a = p.get("bounds").arr();
        assert_eq!(a.len(), 3);
        let b = std::array::from_fn(|w| {
            let v = a[w].arr();
            assert_eq!(v.len(), 2);
            let r = std::array::from_fn(|i| {
                let x = v[i].num() * 10.;
                assert!(x >= 0. && x <= 30. && (x - x.round()).abs() <= 1e-9);
                x.round() as i32
            });
            assert!(r[0] <= r[1]);
            r
        });
        let dim = b.iter().filter(|x| x[0] < x[1]).count();
        assert!(dim < 3);
        assert_eq!(p.get("type").str(), ["point", "line", "plane"][dim]);
        pieces.push(Piece { b, rho, dim });
    }
    let mut map = BTreeMap::new();
    for p in &pieces {
        *map.entry(key(p)).or_insert(0usize) += 1;
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
                q.b = std::array::from_fn(|w| {
                    let v = p.b[perm[w]];
                    if mask & (1 << w) == 0 {
                        v
                    } else {
                        [30 - v[1], 30 - v[0]]
                    }
                });
                *image.entry(key(&q)).or_insert(0usize) += 1;
            }
            assert_eq!(map, image, "check 1 symmetry failed");
        }
    }
    let mut used = vec![false; pieces.len()];
    let mut pairs = vec![];
    let mut multi = 0;
    for p in &pieces {
        let axes = (0..3)
            .filter(|&w| {
                p.b[w][0] == p.b[w][1]
                    && [-10, 10].iter().any(|&shift| {
                        let mut q = p.clone();
                        q.b[w][0] += shift;
                        q.b[w][1] += shift;
                        pieces.iter().any(|r| key(r) == key(&q))
                    })
            })
            .count();
        if axes > 1 {
            multi += 1;
        }
    }
    for (i, p) in pieces.iter().enumerate() {
        let mut candidates = vec![];
        for w in 0..3 {
            if p.b[w][0] != p.b[w][1] {
                continue;
            }
            let mut q = p.clone();
            q.b[w][0] += 10;
            q.b[w][1] += 10;
            let found: Vec<_> = pieces
                .iter()
                .enumerate()
                .filter(|(_, r)| key(r) == key(&q))
                .map(|(j, _)| j)
                .collect();
            assert!(found.len() <= 1, "ambiguous partner");
            if let Some(&j) = found.first() {
                candidates.push((j, w));
            }
        }
        for (j, w) in candidates {
            if !used[i] && !used[j] {
                used[i] = true;
                used[j] = true;
                pairs.push((i, j, w));
                break;
            }
        }
    }
    let singles = (0..pieces.len()).filter(|&i| !used[i]).collect();
    let total = pieces.iter().fold(ZERO, |s, p| {
        s + I::pt(p.rho)
            * p.b
                .iter()
                .filter(|v| v[0] < v[1])
                .fold(ONE, |s, v| s * tenth(v[1] - v[0]))
    });
    let v: Vec<_> = ratio.split('/').collect();
    assert_eq!(v.len(), 2);
    let p: u64 = v[0].parse().unwrap();
    let q: u64 = v[1].parse().unwrap();
    assert!(p > 0 && q > 0 && p <= 1 << 53 && q <= 1 << 53);
    let sigma = I::pt(p as f64).div_pos(q as f64);
    let st = total * sigma;
    assert!(
        st.hi < (1u64 << 53) as f64,
        "claim must be exactly representable"
    );
    let claim = st.lo.floor() as u64 + 1;
    assert!(st.hi < claim as f64, "total straddles claim");
    let facts = [
        pieces.iter().filter(|p| p.dim == 1).all(|p| {
            p.b.iter()
                .filter(|v| v[0] == v[1] && v[0] % 10 == 0)
                .count()
                < 2
        }),
        pieces
            .iter()
            .filter(|p| p.dim == 0)
            .all(|p| p.b.iter().any(|v| v[0] % 10 != 0)),
    ];
    Measure {
        pieces,
        pairs,
        singles,
        total,
        sigma,
        rational: format!("{p}/{q}"),
        claim,
        hash,
        multi,
        facts,
    }
}
impl Measure {
    pub fn metadata(&self) -> String {
        let counts: Vec<_> = (0..3)
            .map(|d| self.pieces.iter().filter(|p| p.dim == d).count())
            .collect();
        format!("\"sigma\":\"{}\",\"T\":[{},{}],\"n_claim\":{},\"measure_sha256\":\"{}\",\"symmetries_checked\":48,\"piece_counts\":{:?},\"pairs\":{},\"unpaired\":{},\"multiple_partner_axes\":{},\"partner_policy\":\"first available axis\",\"v5b_facts\":{:?},\"density_bits\":{:?}",self.rational,self.total.lo,self.total.hi,self.claim,self.hash,counts,self.pairs.len(),self.singles.len(),self.multi,self.facts,self.pieces.iter().map(|p|p.rho.to_bits()).collect::<Vec<_>>())
    }
}
