use m4b_cert1::{
    bound::{self, Box6, Reason},
    search::{self, Node},
};
use serde::{Deserialize, Serialize};
use serde_json::json;
use sha2::{Digest, Sha256};
use std::{
    collections::BTreeMap,
    fs::{self, File, OpenOptions},
    io::{self, BufRead, Read, Write},
    path::{Path, PathBuf},
    time::{Instant, SystemTime, UNIX_EPOCH},
};
#[derive(Serialize, Deserialize)]
struct State {
    version: u32,
    metadata: serde_json::Value,
    max_depth: u32,
    lemmas: [u64; 6],
    root: Box6,
    frontier: Vec<Node>,
    unresolved: Vec<Node>,
    boxes: u64,
    reasons: BTreeMap<Reason, u64>,
    closed: BTreeMap<u32, u64>,
    seconds: f64,
    started: f64,
    status: String,
    leaf_bytes: u64,
    leaf_sha256: String,
    /// Per-round chained digest h <- sha256(h_hex || round leaf bytes). Deterministic (rounds are),
    /// survives resume without the leaf file, so the full stream need not be stored.
    #[serde(default)]
    leaf_chain: String,
    /// Write leaves.jsonl too (only with --keep-leaves; 1.9 GB per 2 minutes on the full root).
    #[serde(default)]
    keep_leaves: bool,
}
fn epoch() -> f64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap()
        .as_secs_f64()
}
fn atomic(path: &Path, bytes: &[u8]) {
    let tmp = path.with_extension("tmp");
    let mut f = File::create(&tmp).unwrap();
    f.write_all(bytes).unwrap();
    f.sync_all().unwrap();
    fs::rename(tmp, path).unwrap();
}
fn save(out: &Path, s: &State, full: bool) {
    if full {
        atomic(
            &out.join("checkpoint.json"),
            &serde_json::to_vec(s).unwrap(),
        );
    }
    let covered: f64 = s
        .closed
        .iter()
        .map(|(d, n)| *n as f64 * 2f64.powi(-(*d as i32)))
        .sum();
    let mut depths = s.closed.clone();
    for n in &s.unresolved {
        *depths.entry(n.depth()).or_default() += 1;
    }
    let p = json!({"enclosure":"mean-value-1","status":s.status,"closed_volume_fraction":covered,"pending":s.frontier.len(),
        "unresolved":s.unresolved.len(),"boxes":s.boxes,"leaves_by_reason":s.reasons,
        "leaf_depth_histogram":depths,"closed_by_depth":s.closed,"seconds":s.seconds,"started":s.started,"updated":epoch(),
        "leaf_sha256":s.leaf_sha256,"leaf_bytes":s.leaf_bytes,"leaf_chain":s.leaf_chain,"keep_leaves":s.keep_leaves,
        "volume_measure":"initial parameter rectangle (includes outside fundamental domain)","checkpoint":full,"max_depth":s.max_depth,"lemma_types":["S","F","W","M","P","P_prime"],"lemma_contributions":s.lemmas,"metadata":s.metadata});
    atomic(
        &out.join("progress.json"),
        &serde_json::to_vec_pretty(&p).unwrap(),
    );
    if full {
        atomic(
            &out.join("receipt.json"),
            &serde_json::to_vec_pretty(&p).unwrap(),
        );
    }
}
fn batch() {
    let mut out = io::BufWriter::new(io::stdout().lock());
    for l in io::stdin().lock().lines() {
        let v: serde_json::Value = serde_json::from_str(&l.unwrap()).unwrap();
        let b: Box6 = serde_json::from_value(v["box"].clone()).unwrap();
        writeln!(
            out,
            "{}",
            serde_json::to_string(&if let Some(y)=v.get("enclosures") {json!({"quantities":bound::enclosures(&b,serde_json::from_value(y.clone()).unwrap())})}else if let Some(y)=v.get("cell") {json!({"rules":bound::rule_flags(&b,serde_json::from_value(y.clone()).unwrap(),v["axis"].as_u64().unwrap() as usize)})}else{serde_json::to_value(bound::evaluate(&b,v["domain"].as_bool().unwrap_or(false),!v["full"].as_bool().unwrap_or(false))).unwrap()})
                .unwrap()
        )
        .unwrap();
        out.flush().unwrap();
    }
}
fn main() {
    let args: Vec<String> = std::env::args().collect();
    let flag = |k: &str| args.iter().any(|a| a == k);
    let val = |k: &str, d: &str| {
        args.iter()
            .position(|a| a == k)
            .map(|i| args.get(i + 1).expect("missing value").clone())
            .unwrap_or(d.into())
    };
    let server = flag("--server");
    let threads: usize = val("--threads", "1").parse().unwrap();
    let seconds: f64 = val("--seconds", "60").parse().unwrap();
    assert!(
        !cfg!(target_os = "macos") || !server,
        "--server is not permitted on macOS"
    );
    assert!(threads >= 1 && threads <= if server { 64 } else { 2 });
    assert!(
        seconds.is_finite() && seconds > 0. && seconds <= if server { 14. * 86400. } else { 1200. }
    );
    let cell_depth: u32 = val("--cell-depth", "6").parse().unwrap();
    assert!(cell_depth <= 16);
    let measure = m4b_cert1::measure::load(
        &val("--measure", "../measure.json"),
        &val("--sigma", "27/20"),
        cell_depth,
    );
    m4b_cert1::measure::DATA
        .set(measure)
        .ok()
        .expect("measure initialized twice");
    if flag("--measure-info") {
        println!("{}", m4b_cert1::measure::DATA.get().unwrap().receipt);
        return;
    }
    if flag("--sample-box") {
        let value: serde_json::Value = serde_json::from_str(&val("--sample-box", "")).unwrap();
        let b: Box6 = serde_json::from_value(if value.is_array() {
            value
        } else {
            value["box"].clone()
        })
        .unwrap();
        println!(
            "{}",
            serde_json::to_string(&bound::bound(&b, false)).unwrap()
        );
        return;
    }
    if flag("--batch") {
        batch();
        return;
    }
    for a in args.iter().filter(|a| a.starts_with("--")) {
        assert!(
            [
                "--measure",
                "--sigma",
                "--cell-depth",
                "--max-depth",
                "--unresolved-list",
                "--threads",
                "--seconds",
                "--depth",
                "--output",
                "--resume",
                "--server",
                "--rounds",
                "--checkpoint-seconds",
                "--keep-leaves"
            ]
            .contains(&a.as_str()),
            "unknown option {a}"
        );
    }
    let depth: u32 = val("--max-depth", &val("--depth", "180")).parse().unwrap();
    assert!(depth <= 300);
    let rounds: u64 = val("--rounds", "18446744073709551615").parse().unwrap();
    let cp_seconds: f64 = val("--checkpoint-seconds", "10").parse().unwrap();
    assert!(cp_seconds.is_finite() && cp_seconds >= 1. && cp_seconds <= 300.);
    let base = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .canonicalize()
        .unwrap();
    let out = base.join(val("--output", "run"));
    assert!(
        out.starts_with(&base)
            && !out
                .components()
                .any(|c| matches!(c, std::path::Component::ParentDir))
    );
    let mut ancestor = out.as_path();
    while !ancestor.exists() {
        ancestor = ancestor.parent().unwrap();
    }
    assert!(ancestor.canonicalize().unwrap().starts_with(&base));
    fs::create_dir_all(&out).unwrap();
    let out = out.canonicalize().unwrap();
    assert!(out.starts_with(&base));
    // Refuse symlinked artifact files as well as escaped output directories.
    for name in [
        "checkpoint.json",
        "checkpoint.tmp",
        "progress.json",
        "progress.tmp",
        "receipt.json",
        "receipt.tmp",
        "leaves.jsonl",
        "writer.lock",
    ] {
        if let Ok(m) = fs::symlink_metadata(out.join(name)) {
            assert!(!m.file_type().is_symlink(), "symlink artifact");
        }
    }
    let lock = out.join("writer.lock");
    let mut lockfile = OpenOptions::new()
        .write(true)
        .create_new(true)
        .open(&lock)
        .expect(
        "output already locked; after a crash verify no writer remains before removing writer.lock",
    );
    writeln!(lockfile, "{}", std::process::id()).unwrap();
    struct Lock(PathBuf);
    impl Drop for Lock {
        fn drop(&mut self) {
            let _ = fs::remove_file(&self.0);
        }
    }
    let _lock = Lock(lock);
    let resume = flag("--resume");
    let mut sources = BTreeMap::new();
    for (name, bytes) in [
        ("Cargo.toml", include_bytes!("../Cargo.toml").as_slice()),
        ("Cargo.lock", include_bytes!("../Cargo.lock").as_slice()),
        ("src/main.rs", include_bytes!("main.rs").as_slice()),
        ("src/lib.rs", include_bytes!("lib.rs").as_slice()),
        ("src/dual.rs", include_bytes!("dual.rs").as_slice()),
        ("src/interval.rs", include_bytes!("interval.rs").as_slice()),
        ("src/bound.rs", include_bytes!("bound.rs").as_slice()),
        ("src/measure.rs", include_bytes!("measure.rs").as_slice()),
        ("src/search.rs", include_bytes!("search.rs").as_slice()),
        ("validate.py", include_bytes!("../validate.py").as_slice()),
    ] {
        assert_eq!(
            bytes,
            fs::read(base.join(name)).unwrap(),
            "source differs from compiled binary: {name}"
        );
        sources.insert(name, format!("{:x}", Sha256::digest(bytes)));
    }
    let metadata = json!({"binary_sha256":format!("{:x}",Sha256::digest(fs::read(std::env::current_exe().unwrap()).unwrap())),"system":1,"fundamental_domain":"sorted quaternion (x >= y >= |z|, x, y >= 0, |x_i| <= sqrt2 - 1, sum |x_i| <= 1; 24 cube rotations x 48 container symmetries) x u_0 <= 1/2","measure":m4b_cert1::measure::DATA.get().unwrap().receipt,"cell_depth":cell_depth,"max_depth":depth,"threads":threads,"source_sha256":sources,"rustc":String::from_utf8(std::process::Command::new("rustc").arg("--version").output().unwrap().stdout).unwrap().trim(),"command_line":args.iter().map(|a|if Path::new(a).is_absolute(){Path::new(a).file_name().unwrap().to_string_lossy().into_owned()}else{a.clone()}).collect::<Vec<_>>()});
    let mut s: State = if resume {
        let s: State =
            serde_json::from_slice(&fs::read(out.join("checkpoint.json")).unwrap()).unwrap();
        assert_eq!(s.version, 2);
        assert_eq!(
            s.metadata["measure"], metadata["measure"],
            "resume measure mismatch"
        );
        assert_eq!(
            s.metadata["binary_sha256"], metadata["binary_sha256"],
            "resume binary mismatch"
        );
        assert_eq!(
            s.metadata["source_sha256"], metadata["source_sha256"],
            "resume source mismatch"
        );
        assert_eq!(s.metadata["cell_depth"], metadata["cell_depth"]);
        assert_eq!(s.metadata["max_depth"], metadata["max_depth"]);
        assert!(bound::valid(&s.root));
        s
    } else {
        assert!(
            !out.join("checkpoint.json").exists() && !out.join("leaves.jsonl").exists(),
            "use --resume"
        );
        State {
            version: 2,
            metadata: metadata.clone(),
            max_depth: 0,
            lemmas: [0; 6],
            root: bound::root(),
            frontier: vec![Node::root()],
            unresolved: vec![],
            boxes: 0,
            reasons: BTreeMap::new(),
            closed: BTreeMap::new(),
            seconds: 0.,
            started: epoch(),
            status: "running".into(),
            leaf_bytes: 0,
            leaf_sha256: format!("{:x}", Sha256::digest([])),
            leaf_chain: format!("{:x}", Sha256::digest([])),
            keep_leaves: flag("--keep-leaves"),
        }
    };
    s.metadata = metadata;
    let mut hasher = Sha256::new();
    if resume && s.keep_leaves {
        let f = File::open(out.join("leaves.jsonl")).unwrap();
        assert!(f.metadata().unwrap().len() >= s.leaf_bytes);
        let mut reader = f.take(s.leaf_bytes);
        let mut buf = [0u8; 65536];
        loop {
            let n = reader.read(&mut buf).unwrap();
            if n == 0 {
                break;
            }
            hasher.update(&buf[..n]);
        }
        assert_eq!(
            format!("{:x}", hasher.clone().finalize()),
            s.leaf_sha256,
            "committed leaf stream corrupt"
        );
        OpenOptions::new()
            .write(true)
            .open(out.join("leaves.jsonl"))
            .unwrap()
            .set_len(s.leaf_bytes)
            .unwrap();
    }
    let mut leaf_file = if s.keep_leaves {
        Some(
            OpenOptions::new()
                .create(true)
                .append(true)
                .open(out.join("leaves.jsonl"))
                .unwrap(),
        )
    } else {
        None
    };
    let start = Instant::now();
    let old = s.seconds;
    let mut cp = start;
    let mut progress = start;
    s.status = "running".into();
    save(&out, &s, true);
    for _ in 0..rounds {
        if s.frontier.is_empty() || start.elapsed().as_secs_f64() >= seconds {
            break;
        }
        // At most 128 tasks, each at most sixty-four nodes, irrespective of frontier size or N (10/15: was 16,
        // which kept at most 16 threads busy). Threads pick tasks dynamically; results are committed in task order,
        // so the tree, the leaf order and the digest do not depend on N or on the assignment.
        let take = s.frontier.len().min(128);
        let at = s.frontier.len() - take;
        let tasks: Vec<Node> = s.frontier.split_off(at);
        let root = s.root;
        let next = std::sync::atomic::AtomicUsize::new(0);
        let mut results = std::thread::scope(|scope| {
            let run = || {
                let mut r = vec![];
                loop {
                    let i = next.fetch_add(1, std::sync::atomic::Ordering::Relaxed);
                    if i >= tasks.len() {
                        break r;
                    }
                    r.push((i, search::chunk(tasks[i].clone(), root, depth)));
                }
            };
            let handles: Vec<_> = (1..threads.min(tasks.len()).max(1)).map(|_| scope.spawn(run)).collect();
            let mut r = run();
            for h in handles {
                r.extend(h.join().unwrap());
            }
            r
        });
        results.sort_by_key(|(i, _)| *i);
        let mut round = s.leaf_chain.clone().into_bytes();
        for (_, r) in results {
            s.boxes += r.boxes;
            for n in r
                .frontier
                .iter()
                .chain(r.unresolved.iter())
                .chain(r.leaves.iter().map(|l| &l.node))
            {
                s.max_depth = s.max_depth.max(n.depth());
            }
            s.frontier.extend(r.frontier);
            s.unresolved.extend(r.unresolved);
            for l in r.leaves {
                *s.reasons.entry(l.result.reason).or_default() += 1;
                if l.result.reason != Reason::Unresolved {
                    *s.closed.entry(l.node.depth()).or_default() += 1;
                }
                if l.result.reason == Reason::Bound {
                    for k in 0..6 {
                        s.lemmas[k] += l.result.lemmas[k];
                    }
                }
                let mut bytes =
                    serde_json::to_vec(&json!({"node":l.node,"result":{"reason":l.result.reason}}))
                        .unwrap();
                bytes.push(b'\n');
                if let Some(f) = leaf_file.as_mut() {
                    f.write_all(&bytes).unwrap();
                    hasher.update(&bytes);
                }
                round.extend_from_slice(&bytes);
                s.leaf_bytes += bytes.len() as u64;
            }
        }
        s.leaf_chain = format!("{:x}", Sha256::digest(&round));
        s.seconds = old + start.elapsed().as_secs_f64();
        if s.keep_leaves {
            s.leaf_sha256 = format!("{:x}", hasher.clone().finalize());
        }
        if cp.elapsed().as_secs_f64() >= cp_seconds {
            if let Some(f) = &leaf_file {
                f.sync_all().unwrap();
            }
            save(&out, &s, true);
            cp = Instant::now();
            progress = cp;
        } else if progress.elapsed().as_secs_f64() >= 10. {
            save(&out, &s, false);
            progress = Instant::now();
        }
    }
    s.seconds = old + start.elapsed().as_secs_f64();
    s.status = if s.frontier.is_empty() {
        if s.unresolved.is_empty() {
            "complete"
        } else {
            "unresolved"
        }
    } else {
        "paused"
    }
    .into();
    if s.keep_leaves {
        s.leaf_sha256 = format!("{:x}", hasher.finalize());
    }
    if let Some(f) = &leaf_file {
        f.sync_all().unwrap();
    }
    save(&out, &s, true);
    if flag("--unresolved-list") {
        let file = base.join(val("--unresolved-list", "unresolved.jsonl"));
        assert!(
            !file
                .components()
                .any(|c| matches!(c, std::path::Component::ParentDir))
                && file
                    .parent()
                    .unwrap()
                    .canonicalize()
                    .unwrap()
                    .starts_with(&base)
        );
        if let Ok(m) = fs::symlink_metadata(&file) {
            assert!(!m.file_type().is_symlink());
        }
        let mut f = io::BufWriter::new(File::create(file).unwrap());
        for (kind, nodes) in [("unresolved", &s.unresolved), ("pending", &s.frontier)] {
            for n in nodes {
                // Pending regions are also included to make a stopped trial reviewable.
                let b = n.bounds(s.root);
                let result = bound::bound(&b, false);
                writeln!(
                    f,
                    "{}",
                    json!({"kind":kind,"node":n,"box":b,"result":result})
                )
                .unwrap();
            }
        }
    }
    println!(
        "{}",
        String::from_utf8(fs::read(out.join("progress.json")).unwrap()).unwrap()
    );
}
