use crate::{
    geometry::*,
    interval::I,
    json::{self, J},
    sha256,
};
use std::{
    fs::{self, File, OpenOptions},
    io::{Seek, SeekFrom, Write},
    path::{Path, PathBuf},
    time::Instant,
};
pub struct Config {
    pub threads: usize,
    pub seconds: f64,
    pub depth: u32,
    pub output: PathBuf,
    pub resume: bool,
    pub checkpoint_seconds: f64,
    pub keep: bool,
    pub rounds: u64,
    pub cell_depth: u32,
    pub unresolved_list: Option<PathBuf>,
}
pub fn box_json(b: &Box6) -> String {
    format!(
        "{{\"box\":[{}],\"depth\":{}}}",
        b.x.iter()
            .map(|v| format!("[{},{}]", v.lo, v.hi))
            .collect::<Vec<_>>()
            .join(","),
        b.depth
    )
}
pub fn parse_box(j: &J, depth: u32) -> Box6 {
    let a = j.get("box").arr();
    assert_eq!(a.len(), 6);
    let root = root();
    Box6 {
        x: std::array::from_fn(|i| {
            let p = a[i].arr();
            assert_eq!(p.len(), 2);
            let lo = p[0].num();
            let hi = p[1].num();
            assert!(lo <= hi && lo >= 0. && hi <= root.x[i].hi);
            I::new(lo, hi)
        }),
        depth,
    }
}
fn atomic(p: &Path, s: &str) {
    safe_file(p);
    let tmp = p.with_extension("tmp");
    safe_file(&tmp);
    let mut f = File::create(&tmp).unwrap();
    f.write_all(s.as_bytes()).unwrap();
    f.sync_all().unwrap();
    fs::rename(tmp, p).unwrap();
    File::open(p.parent().unwrap()).unwrap().sync_all().unwrap();
}
pub fn safe_file(p: &Path) {
    let base = Path::new(env!("CARGO_MANIFEST_DIR"))
        .canonicalize()
        .unwrap();
    let p = if p.is_absolute() {
        p.to_path_buf()
    } else {
        std::env::current_dir().unwrap().join(p)
    };
    assert!(!p
        .components()
        .any(|c| matches!(c, std::path::Component::ParentDir)));
    assert!(p.starts_with(&base), "output must be inside checker2");
    let mut a = p.as_path();
    while !a.exists() {
        a = a.parent().unwrap();
    }
    assert!(
        a.canonicalize().unwrap().starts_with(base),
        "output symlink escapes checker2"
    );
}
fn quote(s: &str) -> String {
    format!(
        "\"{}\"",
        s.replace('\\', "\\\\")
            .replace('"', "\\\"")
            .replace('\n', "\\n")
    )
}
fn sources() -> String {
    let base = Path::new(env!("CARGO_MANIFEST_DIR"));
    let mut paths: Vec<_> = fs::read_dir(base.join("src"))
        .unwrap()
        .map(|e| e.unwrap().path())
        .filter(|p| p.extension().is_some_and(|e| e == "rs"))
        .collect();
    for p in [
        "Cargo.toml",
        "Cargo.lock",
        "integration.py",
        "stress_random.py",
        "stress_p0.py",
    ] {
        paths.push(base.join(p));
    }
    paths.sort();
    paths
        .iter()
        .map(|p| {
            format!(
                "{}:{}",
                quote(p.strip_prefix(base).unwrap().to_str().unwrap()),
                quote(&sha256::hash(&fs::read(p).unwrap()))
            )
        })
        .collect::<Vec<_>>()
        .join(",")
}
fn fingerprint() -> String {
    sha256::hash(format!("{} {}", sources(), crate::measure::data().metadata()).as_bytes())
}
fn provenance() -> String {
    let r = std::process::Command::new("rustc")
        .arg("--version")
        .output()
        .unwrap();
    let cmd = std::env::args()
        .map(|v| quote(&v.replace(env!("CARGO_MANIFEST_DIR"), ".")))
        .collect::<Vec<_>>()
        .join(",");
    format!(
        "\"source_sha256\":{{{}}},\"rustc\":{},\"command_line\":[{}]",
        sources(),
        quote(String::from_utf8_lossy(&r.stdout).trim()),
        cmd
    )
}
pub struct State {
    pub pending: Vec<Box6>,
    pub unresolved: Vec<Box6>,
    pub boxes: u64,
    pub leaves: [u64; 3],
    pub lemmas: [u64; 6],
    pub max_depth: u32,
    pub closed: f64,
    pub seconds: f64,
    pub digest: String,
    pub rounds: u64,
    pub leaf_bytes: u64,
    pub histogram: [u64; 257],
}
impl State {
    pub fn new() -> Self {
        Self {
            pending: vec![root()],
            unresolved: vec![],
            boxes: 0,
            leaves: [0; 3],
            lemmas: [0; 6],
            max_depth: 0,
            closed: 0.,
            seconds: 0.,
            digest: sha256::hash(b""),
            rounds: 0,
            leaf_bytes: 0,
            histogram: [0; 257],
        }
    }
    pub fn progress(&self, status: &str) -> String {
        format!("{{\"status\":\"{}\",\"pending\":{},\"unresolved\":{},\"boxes\":{},\"max_depth\":{},\"leaves_by_rule\":{{\"bound\":{},\"outside\":{},\"unresolved\":{}}},\"closed_volume_fraction\":{},\"leaf_chain\":\"{}\",\"seconds\":{},\"rounds\":{},\"leaf_bytes\":{},\"lemma_counts\":{:?},\"depth_histogram\":{:?}}}",status,self.pending.len(),self.unresolved.len(),self.boxes,self.max_depth,self.leaves[1],self.leaves[2],self.leaves[0],self.closed,self.digest,self.seconds,self.rounds,self.leaf_bytes,self.lemmas,self.histogram)
    }
    fn save(&self, c: &Config, status: &str) {
        let p = self.progress(status);
        let chk=format!("{{\"version\":2,\"fingerprint\":\"{}\",\"depth_cap\":{},\"cell_depth\":{},\"keep\":{},\"progress\":{},\"pending\":[{}],\"unresolved\":[{}]}}",fingerprint(),c.depth,c.cell_depth,c.keep,p,self.pending.iter().map(box_json).collect::<Vec<_>>().join(","),self.unresolved.iter().map(box_json).collect::<Vec<_>>().join(","));
        atomic(&c.output.join("checkpoint.json"), &chk);
        atomic(&c.output.join("progress.json"), &p);
    }
    fn load(c: &Config) -> Self {
        let j = json::parse(&fs::read_to_string(c.output.join("checkpoint.json")).unwrap());
        assert_eq!(j.get("version").uint(), 2);
        assert_eq!(j.get("fingerprint").str(), fingerprint());
        assert_eq!(j.get("depth_cap").uint(), c.depth as u64);
        assert_eq!(j.get("cell_depth").uint(), c.cell_depth as u64);
        assert_eq!(j.get("keep").boolean(), c.keep);
        let p = j.get("progress");
        let read = |key| {
            j.get(key)
                .arr()
                .iter()
                .map(|b| parse_box(b, b.get("depth").uint().try_into().unwrap()))
                .collect()
        };
        Self {
            pending: read("pending"),
            unresolved: read("unresolved"),
            boxes: p.get("boxes").uint(),
            leaves: [
                p.get("leaves_by_rule").get("unresolved").uint(),
                p.get("leaves_by_rule").get("bound").uint(),
                p.get("leaves_by_rule").get("outside").uint(),
            ],
            lemmas: std::array::from_fn(|i| p.get("lemma_counts").arr()[i].uint()),
            max_depth: p.get("max_depth").uint().try_into().unwrap(),
            closed: p.get("closed_volume_fraction").num(),
            seconds: p.get("seconds").num(),
            digest: p.get("leaf_chain").str().to_string(),
            rounds: p.get("rounds").uint(),
            leaf_bytes: p.get("leaf_bytes").uint(),
            histogram: std::array::from_fn(|i| p.get("depth_histogram").arr()[i].uint()),
        }
    }
    pub fn round(&mut self, threads: usize, depth: u32) -> String {
        // Fixed batch, independent of worker count. Commit all results in input order.
        let n = 4.min(self.pending.len());
        let batch: Vec<_> = (0..n).map(|_| self.pending.pop().unwrap()).collect();
        let outs: Vec<_> = std::thread::scope(|scope| {
            let jobs: Vec<_> = batch
                .chunks(n.div_ceil(threads).max(1))
                .map(|part| {
                    scope.spawn(move || {
                        part.iter()
                            .map(|b| if outside(b) { None } else { close(b) })
                            .collect::<Vec<_>>()
                    })
                })
                .collect();
            jobs.into_iter().flat_map(|j| j.join().unwrap()).collect()
        });
        let mut records = String::new();
        let mut children = vec![];
        for (b, o) in batch.into_iter().zip(outs) {
            self.boxes += 1;
            self.max_depth = self.max_depth.max(b.depth);
            if !outside(&b) && o.is_none() && b.depth < depth {
                let [l, r] = split(b);
                children.push([r, l]);
                continue;
            }
            let rule = if outside(&b) {
                self.closed += 2f64.powi(-(b.depth as i32));
                2
            } else if let Some(o) = o {
                self.closed += 2f64.powi(-(b.depth as i32));
                for i in 0..6 {
                    self.lemmas[i] += o.counts[i];
                }
                1
            } else {
                self.unresolved.push(b);
                0
            };
            self.leaves[rule] += 1;
            self.histogram[b.depth as usize] += 1;
            records.push_str(&format!(
                "{}:{}::{}\n",
                b.depth,
                ["unresolved", "bound", "outside"][rule],
                b.x.iter()
                    .map(|i| format!("{:016x},{:016x}", i.lo.to_bits(), i.hi.to_bits()))
                    .collect::<Vec<_>>()
                    .join(",")
            ));
        }
        for v in children.into_iter().rev() {
            self.pending.extend(v);
        }
        self.digest = sha256::hash(format!("{}{}", self.digest, records).as_bytes());
        self.rounds += 1;
        records
    }
}
pub fn run(c: Config) {
    safe_file(&c.output);
    fs::create_dir_all(&c.output).unwrap();
    let start = Instant::now();
    let mut s = if c.resume {
        State::load(&c)
    } else {
        assert!(!c.output.join("checkpoint.json").exists(), "use --resume");
        State::new()
    };
    let previous = s.seconds;
    let mut stream = if c.keep {
        let p = c.output.join("leaves.txt");
        safe_file(&p);
        let mut f = OpenOptions::new()
            .create(true)
            .truncate(false)
            .write(true)
            .open(p)
            .unwrap();
        if c.resume {
            assert!(f.metadata().unwrap().len() >= s.leaf_bytes);
        }
        f.set_len(s.leaf_bytes).unwrap();
        f.seek(SeekFrom::End(0)).unwrap();
        Some(f)
    } else {
        None
    };
    let mut checkpoint = Instant::now();
    s.save(&c, "running");
    while !s.pending.is_empty()
        && s.rounds < c.rounds
        && start.elapsed().as_secs_f64() < c.seconds - 0.25
    {
        let records = s.round(c.threads, c.depth);
        if let Some(f) = stream.as_mut() {
            f.write_all(records.as_bytes()).unwrap();
            s.leaf_bytes += records.len() as u64;
        }
        s.seconds = previous + start.elapsed().as_secs_f64();
        if checkpoint.elapsed().as_secs_f64() >= c.checkpoint_seconds {
            if let Some(f) = stream.as_mut() {
                f.sync_all().unwrap();
            }
            s.save(&c, "running");
            checkpoint = Instant::now();
        }
    }
    s.seconds = previous + start.elapsed().as_secs_f64();
    let status = if !s.pending.is_empty() {
        "paused"
    } else if !s.unresolved.is_empty() {
        "unresolved"
    } else {
        "complete"
    };
    if let Some(f) = stream.as_mut() {
        f.sync_all().unwrap();
    }
    s.save(&c, status);
    let p = s.progress(status);
    let receipt = format!(
        "{},\"enclosure\":\"mean-value-1\",\"fundamental_domain\":\"Delta x gamma in [0, pi/2] (u sorted, 48 container symmetries; quarter turn about the third cube axis)\",\"threads\":{},\"max_depth_cap\":{},\"cell_depth\":{}, {}, {} }}",
        &p[..p.len() - 1],
        c.threads,
        c.depth,
        c.cell_depth,
        crate::measure::data().metadata(),
        provenance()
    );
    atomic(&c.output.join("receipt.json"), &receipt);
    if let Some(path) = &c.unresolved_list {
        safe_file(path);
        let mut f = File::create(path).unwrap();
        for b in &s.unresolved {
            writeln!(
                f,
                "{{\"region\":{},\"bound\":{}}}",
                box_json(b),
                bound(b).json()
            )
            .unwrap();
        }
    }
    println!("{}", receipt);
}
