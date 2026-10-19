//! seamleaf: replay every leaf of one closed-form record against one family with cfcheck's leaf tests.
//!
//! Checks per root (cfcheck::record): line syntax, empty `uncert` and `f3d`, known kinds, positive widths,
//! no root crossing u = 0, the bisection tiling of the root by its leaves, root delta inside [d0, d1]; then
//! every leaf by `cfcheck::leaf::check` (with `stage_b::local_family` for the kinds cfcheck localizes).
//! It does NOT check the Cartesian product of roots: seam records cover a subset of the window, and their
//! coverage is checked separately (seam_check2.py). The family's `seam` provenance key is removed before
//! cfcheck parses the family (cfcheck refuses unknown keys); nothing else is changed. Output: one JSON report with the hashes, root boxes,
//! counts by kind, refusals and per-kind timing.
//!
//! usage: seamleaf <family.json> <record.rec> --out <report.json> [--threads N] [--part K/M]
//!        timing only: [--every K] [--only-kind KIND --max-leaves N]
use cfcheck::{family::Family, record, Result};
use rayon::prelude::*;
use serde_json::json;
use sha2::{Digest, Sha256};
use std::collections::BTreeMap;
use std::io::{BufRead, BufReader};
use std::time::Instant;

fn sha(path: &str) -> String {
    let bytes = std::fs::read(path).expect("read");
    format!("{:x}", Sha256::digest(&bytes))
}

fn s(q: &cfcheck::rat::Q) -> String {
    let (n, d) = (q.numer(), q.denom());
    if d == num_bigint_one() {
        n.to_string()
    } else {
        format!("{}/{}", n, d)
    }
}

fn num_bigint_one() -> num_bigint::BigInt {
    num_bigint::BigInt::from(1)
}

struct Out {
    line: usize,
    kinds: BTreeMap<String, (u64, f64)>,
    refusal: Option<String>,
}

fn replay(family: &Family, root: &record::Root) -> Out {
    let mut out = Out { line: root.line, kinds: BTreeMap::new(), refusal: None };
    let boxes: Vec<_> = root.leaves.iter().map(|l| l.bounds.clone()).collect();
    if !record::tiling(&root.bounds, &boxes) {
        out.refusal = Some("leaves do not tile the root (bisection tree)".into());
        return out;
    }
    if root.bounds[6] < family.d0 || root.bounds[7] > family.d1 {
        out.refusal = Some("root delta outside the family interval".into());
        return out;
    }
    let local = cfcheck::stage_b::local_family(family, &root.bounds);
    for l in &root.leaves {
        let f = if l.kind == "CORE" || l.kind.starts_with("CORE1:") || l.kind.starts_with("B3") || l.kind == "B4U" {
            &local
        } else {
            family
        };
        let t = Instant::now();
        let r: Result<()> = match std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| {
            cfcheck::leaf::check(f, &l.bounds, &l.kind)
        })) {
            Ok(v) => v,
            Err(_) => Err(cfcheck::refuse("panic in leaf test")),
        };
        let e = out.kinds.entry(l.kind.clone()).or_insert((0, 0.0));
        e.0 += 1;
        e.1 += t.elapsed().as_secs_f64();
        if let Err(err) = r {
            out.refusal = Some(format!("{} leaf refused: {}", l.kind, err.reason));
            return out;
        }
    }
    out
}

fn replay_leaves_only(family: &Family, root: &record::Root) -> Out {
    // timing mode: the tiling is not checked (the root holds one sampled leaf)
    let mut out = Out { line: root.line, kinds: BTreeMap::new(), refusal: None };
    let local = cfcheck::stage_b::local_family(family, &root.bounds);
    for l in &root.leaves {
        let f = if l.kind == "CORE" || l.kind.starts_with("CORE1:") || l.kind.starts_with("B3") || l.kind == "B4U" { &local } else { family };
        let t = Instant::now();
        let r = cfcheck::leaf::check(f, &l.bounds, &l.kind);
        let e = out.kinds.entry(l.kind.clone()).or_insert((0, 0.0));
        e.0 += 1;
        e.1 += t.elapsed().as_secs_f64();
        if let Err(err) = r { out.refusal = Some(format!("{} leaf refused: {}", l.kind, err.reason)); }
    }
    out
}

fn main() {
    let args: Vec<String> = std::env::args().collect();
    let opt = |k: &str| args.iter().position(|a| a == k).map(|i| args[i + 1].clone());
    let (fam_path, rec_path) = (&args[1], &args[2]);
    let out_path = opt("--out").expect("--out required");
    let threads: usize = opt("--threads").map(|v| v.parse().unwrap()).unwrap_or(1);
    let every: usize = opt("--every").map(|v| v.parse().unwrap()).unwrap_or(1);
    // timing mode only (partial): check just the leaves of one kind, at most N of them, spread over the record
    let only_kind = opt("--only-kind");
    let max_leaves: usize = opt("--max-leaves").map(|v| v.parse().unwrap()).unwrap_or(usize::MAX);
    // --part K/M: this run checks the roots with index % M == K (all M parts together cover the record once)
    let (pk, pm): (usize, usize) = opt("--part")
        .map(|v| { let mut it = v.split('/').map(|x| x.parse().unwrap()); (it.next().unwrap(), it.next().unwrap()) })
        .unwrap_or((0, 1));
    assert!(pm >= 1 && pk < pm, "bad --part");
    rayon::ThreadPoolBuilder::new().num_threads(threads).build_global().unwrap();
    let mut raw: serde_json::Value = serde_json::from_slice(&std::fs::read(fam_path).unwrap()).unwrap();
    // The seam family's provenance object (source families, S, n, extra) is not part of the closed-form family
    // format and does not carry measure; it is checked by seam_check2.py (item 1). Only this one key is removed.
    let seam_meta = raw.as_object_mut().and_then(|o| o.remove("seam")).is_some();
    let family = match Family::parse(raw) {
        Ok(f) => f,
        Err(e) => {
            eprintln!("family refused: {}", e.reason);
            std::process::exit(2);
        }
    };
    let file = std::fs::File::open(rec_path).unwrap();
    let mut roots = vec![];
    let mut parse_refusals = vec![];
    let mut headers = 0usize;
    for (i, line) in BufReader::new(file).lines().enumerate() {
        let line = line.unwrap();
        if line.trim().is_empty() {
            continue;
        }
        let v: serde_json::Value = match serde_json::from_str(&line) {
            Ok(v) => v,
            Err(e) => {
                parse_refusals.push(json!([i + 1, format!("json: {e}")]));
                continue;
            }
        };
        match record::parse_root(&v, i + 1) {
            Ok(Some(r)) => roots.push(r),
            Ok(None) => headers += 1,
            Err(e) => parse_refusals.push(json!([i + 1, e.reason])),
        }
    }
    let t0 = Instant::now();
    let chosen: Vec<&record::Root> = roots.iter().enumerate()
        .filter(|(i, _)| i % pm == pk && (i / pm) % every == 0).map(|(_, r)| r).collect();
    let chosen_leaves: usize = chosen.iter().map(|r| r.leaves.len()).sum();
    let outs: Vec<Out> = if let Some(k) = &only_kind {
        let mut picked = vec![];
        let all: Vec<(&record::Root, &record::Leaf)> = roots.iter()
            .flat_map(|r| r.leaves.iter().filter(|l| &l.kind == k).map(move |l| (r, l))).collect();
        let step = (all.len() / max_leaves.max(1)).max(1);
        for (r, l) in all.iter().step_by(step).take(max_leaves) {
            picked.push(record::Root { bounds: r.bounds.clone(), leaves: vec![(*l).clone()], line: r.line });
        }
        picked.par_iter().map(|r| replay_leaves_only(&family, r)).collect()
    } else {
        chosen.par_iter().map(|r| replay(&family, r)).collect()
    };
    let mut kinds: BTreeMap<String, (u64, f64)> = BTreeMap::new();
    let mut refusals: Vec<serde_json::Value> = parse_refusals;
    for o in &outs {
        for (k, (n, t)) in &o.kinds {
            let e = kinds.entry(k.clone()).or_insert((0, 0.0));
            e.0 += n;
            e.1 += t;
        }
        if let Some(r) = &o.refusal {
            refusals.push(json!([o.line, r]));
        }
    }
    let leaves_total: usize = roots.iter().map(|r| r.leaves.len()).sum();
    let checked: u64 = kinds.values().map(|v| v.0).sum();
    let root_boxes: Vec<Vec<String>> = if pm == 1 { roots.iter().map(|r| r.bounds.iter().map(s).collect()).collect() } else { vec![] };
    let ok = refusals.is_empty() && every == 1 && only_kind.is_none() && checked as usize == chosen_leaves;
    let report = json!({
        "family": fam_path, "family_sha256": sha(fam_path),
        "record": rec_path, "record_sha256": sha(rec_path),
        "seam_metadata_removed": seam_meta, "headers": headers, "roots": roots.len(), "leaves": leaves_total,
        "checked_leaves": checked, "every": every, "threads": threads,
        "part": [pk, pm], "part_roots": chosen.len(), "part_leaves": chosen_leaves,
        "kinds": kinds.iter().map(|(k, v)| (k.clone(), json!({"leaves": v.0, "seconds": v.1}))).collect::<serde_json::Map<_, _>>(),
        "refusals": refusals, "wall_seconds": t0.elapsed().as_secs_f64(),
        "root_boxes": root_boxes, "ok": ok, "partial": every != 1 || only_kind.is_some(),
    });
    std::fs::write(&out_path, serde_json::to_string(&report).unwrap()).unwrap();
    println!("{} roots {} leaves {} checked {} refusals {} ok {} partial {} wall {:.1}s",
             rec_path, roots.len(), leaves_total, checked, report["refusals"].as_array().unwrap().len(), ok, every != 1,
             t0.elapsed().as_secs_f64());
    std::process::exit(if refusals.is_empty() { 0 } else { 1 });
}
