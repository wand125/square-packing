use crate::{
    geometry::*,
    interval::I,
    json::{self, J},
    sha256,
};
use std::{
    fs::{self, File, OpenOptions},
    io::Write,
    path::{Path, PathBuf},
    time::{Instant, SystemTime, UNIX_EPOCH},
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
}
pub struct State {
    pub pending: Vec<Box6>,
    pub unresolved: Vec<Box6>,
    pub boxes: u64,
    pub leaves: [u64; 7],
    pub max_depth: u32,
    pub closed: f64,
    pub seconds: f64,
    pub started: f64,
    pub digest: String,
    pub rounds: u64,
    pub leaf_bytes: u64,
}
fn now() -> f64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap()
        .as_secs_f64()
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
    let x = std::array::from_fn(|i| {
        let pair = a[i].arr();
        assert_eq!(pair.len(), 2);
        let lo = pair[0].num();
        let hi = pair[1].num();
        assert!(
            lo <= hi && lo >= root.x[i].lo && hi <= root.x[i].hi,
            "box outside root"
        );
        I::new(lo, hi)
    });
    Box6 { x, depth }
}
fn atomic(path: &Path, bytes: &[u8]) {
    let tmp = path.with_extension("tmp");
    let mut f = File::create(&tmp).unwrap();
    f.write_all(bytes).unwrap();
    f.sync_all().unwrap();
    fs::rename(tmp, path).unwrap();
    File::open(path.parent().unwrap())
        .unwrap()
        .sync_all()
        .unwrap();
}
impl State {
    pub fn new() -> Self {
        Self {
            pending: vec![root()],
            unresolved: vec![],
            boxes: 0,
            leaves: [0; 7],
            max_depth: 0,
            closed: 0.,
            seconds: 0.,
            started: now(),
            digest: sha256::hash(b""),
            rounds: 0,
            leaf_bytes: 0,
        }
    }
    fn progress(&self, status: &str) -> String {
        format!("{{\"status\":\"{}\",\"closed_volume_fraction\":{},\"pending\":{},\"unresolved\":{},\"boxes\":{},\"leaves_by_reason\":{{\"point\":{},\"centre\":{},\"wall\":{},\"pair\":{},\"local\":{},\"unresolved\":{}}},\"max_depth\":{},\"seconds\":{},\"started\":{},\"updated\":{},\"digest\":\"{}\",\"rounds\":{},\"leaf_bytes\":{}}}",status,self.closed,self.pending.len(),self.unresolved.len(),self.boxes,self.leaves[1],self.leaves[2],self.leaves[3],self.leaves[5],self.leaves[6],self.leaves[0],self.max_depth,self.seconds,self.started,now(),self.digest,self.rounds,self.leaf_bytes)
    }
    fn save(&self, c: &Config, status: &str) {
        let p = self.progress(status);
        let chk=format!("{{\"version\":1,\"depth_cap\":{},\"keep\":{},\"progress\":{},\"pending\":[{}],\"unresolved\":[{}]}}",c.depth,if c.keep{1}else{0},p,self.pending.iter().map(box_json).collect::<Vec<_>>().join(","),self.unresolved.iter().map(box_json).collect::<Vec<_>>().join(","));
        atomic(&c.output.join("checkpoint.json"), chk.as_bytes());
        atomic(&c.output.join("progress.json"), p.as_bytes());
    }
    fn load(c: &Config) -> Self {
        let j = json::parse(&fs::read_to_string(c.output.join("checkpoint.json")).unwrap());
        assert_eq!(j.get("version").num(), 1.);
        assert_eq!(j.get("depth_cap").num(), c.depth as f64);
        assert_eq!(j.get("keep").num(), if c.keep { 1. } else { 0. });
        let p = j.get("progress");
        let reasons = p.get("leaves_by_reason");
        let mut leaves = [0; 7];
        for (i, name) in [
            (0, "unresolved"),
            (1, "point"),
            (2, "centre"),
            (3, "wall"),
            (5, "pair"),
            (6, "local"),
        ] {
            leaves[i] = reasons.get(name).uint();
        }
        let read_boxes = |key| {
            j.get(key)
                .arr()
                .iter()
                .map(|b| parse_box(b, u32::try_from(b.get("depth").uint()).unwrap()))
                .collect()
        };
        Self {
            pending: read_boxes("pending"),
            unresolved: read_boxes("unresolved"),
            boxes: p.get("boxes").uint(),
            leaves,
            max_depth: u32::try_from(p.get("max_depth").uint()).unwrap(),
            closed: p.get("closed_volume_fraction").num(),
            seconds: p.get("seconds").num(),
            started: p.get("started").num(),
            digest: p.get("digest").str().to_string(),
            rounds: p.get("rounds").uint(),
            leaf_bytes: p.get("leaf_bytes").uint(),
        }
    }
    pub fn round(&mut self, threads: usize, depth: u32) -> String {
        // r3: a round pops at most TASKS*SEEDS boxes; task k gets the k-th contiguous group of SEEDS and
        // runs its own depth-first search for at most BUDGET boxes. Tasks do not depend on the thread
        // count; their results are committed in task order, so the tree and records are deterministic.
        let count = (TASKS * SEEDS).min(self.pending.len());
        let batch: Vec<_> = (0..count).map(|_| self.pending.pop().unwrap()).collect();
        let tasks: Vec<Vec<Box6>> = batch.chunks(SEEDS).map(|c| c.to_vec()).collect();
        let outs: Vec<TaskOut> = std::thread::scope(|scope| {
            let per = (tasks.len() + threads - 1) / threads.max(1);
            let jobs: Vec<_> = tasks
                .chunks(per.max(1))
                .map(|part| scope.spawn(move || part.iter().map(|t| run_task(t, depth)).collect::<Vec<_>>()))
                .collect();
            jobs.into_iter().flat_map(|j| j.join().unwrap()).collect()
        });
        let mut records = String::new();
        let mut rest: Vec<Vec<Box6>> = vec![];
        for o in outs {
            self.boxes += o.boxes;
            self.max_depth = self.max_depth.max(o.max_depth);
            self.closed += o.closed;
            for r in 0..7 {
                self.leaves[r] += o.leaves[r];
            }
            self.unresolved.extend(o.unresolved);
            records.push_str(&o.records);
            rest.push(o.stack);
        }
        // Leftover stacks go back so that task 0's boxes are popped first next round.
        for st in rest.into_iter().rev() {
            self.pending.extend(st.into_iter());
        }
        let mut chain = self.digest.clone();
        chain.push_str(&records);
        self.digest = sha256::hash(chain.as_bytes());
        self.rounds += 1;
        records
    }
}
const TASKS: usize = 64;
const SEEDS: usize = 4;
const BUDGET: u64 = 4096;
struct TaskOut {
    boxes: u64,
    max_depth: u32,
    closed: f64,
    leaves: [u64; 7],
    unresolved: Vec<Box6>,
    records: String,
    stack: Vec<Box6>,
}
fn run_task(seeds: &[Box6], depth: u32) -> TaskOut {
    let mut o = TaskOut { boxes: 0, max_depth: 0, closed: 0., leaves: [0; 7], unresolved: vec![], records: String::new(), stack: vec![] };
    let mut stack: Vec<Box6> = seeds.iter().rev().cloned().collect();
    while o.boxes < BUDGET {
        let b = match stack.pop() {
            Some(b) => b,
            None => break,
        };
        let out = close(&b);
        o.boxes += 1;
        o.max_depth = o.max_depth.max(b.depth);
        let rule = out.as_ref().map(|x| x.rule).unwrap_or(0);
        if out.is_none() && b.depth < depth {
            let [l, r] = split(b);
            stack.push(r);
            stack.push(l);
            continue;
        }
        if rule == 0 {
            o.unresolved.push(b);
        } else {
            o.closed += 2f64.powi(-(b.depth as i32));
        }
        o.leaves[rule as usize] += 1;
        let points = out.map(|x| x.points).unwrap_or_default();
        o.records.push_str(&format!(
            "{}:{}:{}:{}\n",
            b.depth,
            rule,
            points.iter().map(|p| p.to_string()).collect::<Vec<_>>().join(","),
            b.x.iter().map(|i| format!("{:016x},{:016x}", i.lo.to_bits(), i.hi.to_bits())).collect::<Vec<_>>().join(",")
        ));
    }
    o.stack = stack;
    o
}
pub fn run(c: Config) {
    let base = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .canonicalize()
        .unwrap();
    let out = if c.output.is_absolute() {
        c.output.clone()
    } else {
        std::env::current_dir().unwrap().join(&c.output)
    };
    // Reject lexical traversal and protected archive before creating anything.
    assert!(!out
        .components()
        .any(|p| matches!(p, std::path::Component::ParentDir)));
    assert!(
        out.starts_with(&base) && !out.starts_with(base.join("stopped_v1")),
        "output must be under check2, outside stopped_v1"
    );
    let mut ancestor = out.as_path();
    while !ancestor.exists() {
        ancestor = ancestor.parent().unwrap();
    }
    let resolved = ancestor.canonicalize().unwrap();
    assert!(resolved.starts_with(&base) && !resolved.starts_with(base.join("stopped_v1")));
    fs::create_dir_all(&out).unwrap();
    let resolved = out.canonicalize().unwrap();
    assert!(resolved.starts_with(&base) && !resolved.starts_with(base.join("stopped_v1")));
    let c = Config {
        output: resolved,
        ..c
    };
    let start = Instant::now();
    let mut s = if c.resume {
        State::load(&c)
    } else {
        assert!(
            !c.output.join("checkpoint.json").exists(),
            "existing run requires --resume"
        );
        State::new()
    };
    let previous = s.seconds;
    let mut stream = if c.keep {
        let f = OpenOptions::new()
            .write(true)
            .create(true)
            .truncate(false)
            .open(c.output.join("leaves.txt"))
            .unwrap();
        if c.resume {
            assert!(f.metadata().unwrap().len() >= s.leaf_bytes);
            f.set_len(s.leaf_bytes).unwrap();
        } else {
            f.set_len(0).unwrap();
        }
        Some(f)
    } else {
        None
    };
    if let Some(f) = stream.as_mut() {
        use std::io::{Seek, SeekFrom};
        f.seek(SeekFrom::End(0)).unwrap();
    }
    let mut last_checkpoint = Instant::now();
    let mut last_progress = Instant::now();
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
        if last_checkpoint.elapsed().as_secs_f64() >= c.checkpoint_seconds {
            if let Some(f) = stream.as_mut() {
                f.sync_all().unwrap();
            }
            s.save(&c, "running");
            last_checkpoint = Instant::now();
            last_progress = Instant::now();
        } else if last_progress.elapsed().as_secs_f64() >= 5. {
            atomic(
                &c.output.join("progress.json"),
                s.progress("running").as_bytes(),
            );
            last_progress = Instant::now();
        }
    }
    s.seconds = previous + start.elapsed().as_secs_f64();
    let status = if s.pending.is_empty() {
        if s.unresolved.is_empty() {
            "complete"
        } else {
            "unresolved"
        }
    } else {
        "paused"
    };
    if let Some(f) = stream.as_mut() {
        f.sync_all().unwrap();
    }
    s.save(&c, status);
    println!("{}", s.progress(status));
}
