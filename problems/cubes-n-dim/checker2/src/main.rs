//! Independent quaternion/interval checker. See README for the proof obligations.
use std::{
    collections::BTreeMap,
    fs::{File, OpenOptions},
    io::{BufRead, BufReader, Write},
    sync::{
        Arc, Mutex,
        atomic::{AtomicUsize, Ordering},
    },
    time::Instant,
};

#[derive(Clone, Copy, Debug)]
struct I {
    lo: f64,
    hi: f64,
}
impl I {
    fn new(lo: f64, hi: f64) -> Self {
        assert!(lo.is_finite() && hi.is_finite() && lo <= hi);
        Self { lo, hi }
    }
    fn pt(x: f64) -> Self {
        Self::new(x, x)
    }
    fn add(self, b: Self) -> Self {
        Self::new((self.lo + b.lo).next_down(), (self.hi + b.hi).next_up())
    }
    fn neg(self) -> Self {
        Self::new(-self.hi, -self.lo)
    }
    fn sub(self, b: Self) -> Self {
        self.add(b.neg())
    }
    fn mul(self, b: Self) -> Self {
        let v = [
            self.lo * b.lo,
            self.lo * b.hi,
            self.hi * b.lo,
            self.hi * b.hi,
        ];
        Self::new(
            v.iter().copied().fold(f64::INFINITY, f64::min).next_down(),
            v.iter()
                .copied()
                .fold(f64::NEG_INFINITY, f64::max)
                .next_up(),
        )
    }
    fn sq(self) -> Self {
        let a = self.abs();
        Self::new(
            if a.lo == 0.0 {
                0.0
            } else {
                (a.lo * a.lo).next_down().max(0.0)
            },
            (a.hi * a.hi).next_up(),
        )
    }
    fn recip(self) -> Self {
        assert!(self.lo > 0.0);
        Self::new((1.0 / self.hi).next_down(), (1.0 / self.lo).next_up())
    }
    fn sqrt(self) -> Self {
        assert!(self.lo >= 0.0);
        Self::new(
            self.lo.sqrt().next_down().max(0.0),
            self.hi.sqrt().next_up(),
        )
    }
    fn abs(self) -> Self {
        if self.lo >= 0.0 {
            self
        } else if self.hi <= 0.0 {
            self.neg()
        } else {
            Self::new(0.0, (-self.lo).max(self.hi))
        }
    }
    fn meet(self, b: Self) -> Self {
        Self::new(self.lo.max(b.lo), self.hi.min(b.hi))
    }
    fn contains(self, x: f64) -> bool {
        self.lo <= x && x <= self.hi
    }
}
#[derive(Clone, Copy)]
struct D {
    v: I,
    g: [I; 6],
}
impl D {
    fn c(x: f64) -> Self {
        Self {
            v: I::pt(x),
            g: [I::pt(0.0); 6],
        }
    }
    fn var(v: I, k: usize) -> Self {
        let mut a = Self::c(0.0);
        a.v = v;
        a.g[k] = I::pt(1.0);
        a
    }
    fn add(self, b: Self) -> Self {
        Self {
            v: self.v.add(b.v),
            g: std::array::from_fn(|k| self.g[k].add(b.g[k])),
        }
    }
    fn neg(self) -> Self {
        Self {
            v: self.v.neg(),
            g: self.g.map(I::neg),
        }
    }
    fn mul(self, b: Self) -> Self {
        Self {
            v: self.v.mul(b.v),
            g: std::array::from_fn(|k| self.g[k].mul(b.v).add(self.v.mul(b.g[k]))),
        }
    }
    fn sq(self) -> Self {
        Self {
            v: self.v.sq(),
            g: self.g.map(|g| I::pt(2.0).mul(self.v).mul(g)),
        }
    }
    fn invsqrt(self) -> Self {
        let v = self.v.sqrt().recip();
        let factor = I::pt(-0.5).mul(v).mul(self.v.recip());
        Self {
            v,
            g: self.g.map(|g| g.mul(factor)),
        }
    }
}
type Mat = [[I; 4]; 4];
// Hamilton multiplication: (a0,av)(b0,bv)=(a0b0-av.bv,a0bv+b0av+av x bv).
fn qm(a: [D; 4], b: [D; 4]) -> [D; 4] {
    let mut c = [D::c(0.0); 4];
    for i in 0..4 {
        for j in 0..4 {
            let (k, s) = basis(i, j);
            let v = a[i].mul(b[j]);
            c[k] = c[k].add(if s == 1 { v } else { v.neg() });
        }
    }
    c
}
fn basis(i: usize, j: usize) -> (usize, i32) {
    if i == 0 {
        (j, 1)
    } else if j == 0 {
        (i, 1)
    } else if i == j {
        (0, -1)
    } else if (i, j) == (1, 2) {
        (3, 1)
    } else if (i, j) == (2, 3) {
        (1, 1)
    } else if (i, j) == (3, 1) {
        (2, 1)
    } else {
        let (k, s) = basis(j, i);
        (k, -s)
    }
}
fn raw(z: [D; 6], faces: (usize, usize)) -> [[D; 4]; 4] {
    let mut p = [D::c(1.0); 4];
    let mut q = p;
    let mut k = 0;
    for (v, f) in [(&mut p, faces.0), (&mut q, faces.1)] {
        for (j, x) in v.iter_mut().enumerate() {
            if j != f {
                *x = z[k];
                k += 1;
            }
        }
    }
    let pn = p.iter().fold(D::c(0.0), |s, x| s.add(x.sq()));
    let qn = q.iter().fold(D::c(0.0), |s, x| s.add(x.sq()));
    let scale = pn.mul(qn).invsqrt();
    for x in &mut q[1..] {
        *x = x.neg();
    }
    let mut r = [[D::c(0.0); 4]; 4];
    for j in 0..4 {
        let mut e = [D::c(0.0); 4];
        e[j] = D::c(1.0);
        let col = qm(qm(p, e), q);
        for i in 0..4 {
            r[i][j] = col[i].mul(scale);
        }
    }
    r
}
#[derive(Clone, Copy, Debug)]
struct Box6 {
    z: [I; 6],
    depth: u32,
}
fn entries(b: Box6, faces: (usize, usize)) -> Mat {
    let all = raw(std::array::from_fn(|k| D::var(b.z[k], k)), faces);
    let c = b.z.map(|x| x.lo + (x.hi - x.lo) * 0.5);
    let center = raw(c.map(D::c), faces);
    std::array::from_fn(|i| {
        std::array::from_fn(|j| {
            let mut mv = center[i][j].v;
            for k in 0..6 {
                mv = mv.add(all[i][j].g[k].mul(b.z[k].sub(I::pt(c[k]))));
            }
            all[i][j].v.meet(mv).meet(I::new(-1.0, 1.0))
        })
    })
}
fn fbound(r: Mat) -> I {
    r.iter().fold(I::pt(0.0), |sum, row| {
        let w = row.iter().fold(I::pt(0.0), |s, x| s.add(x.abs()));
        let slack = I::pt(2.0).sub(w).meet(I::new(0.0, 2.0));
        sum.add(row[0].abs().mul(slack))
    })
}
fn discard(r: Mat) -> bool {
    (0..4).any(|i| r[i][0].hi < 0.0)
        || (0..3).any(|i| r[i][0].hi < r[i + 1][0].lo)
        || r[0][1].hi < 0.0
        || r[0][2].hi < 0.0
        || (1..3).any(|j| r[0][j].abs().hi < r[0][j + 1].abs().lo)
}
fn near(r: Mat) -> bool {
    // Compare against an UPPER enclosure of exact 2/3, never its nearest float.
    let threshold = I::pt(2.0).mul(I::pt(3.0).recip()).hi;
    (0..4).any(|i| r[i][0].abs().sq().lo >= threshold)
}
const GRID: usize = 4;
const PER_FACE: usize = 4096;
const TASKS: usize = 16 * PER_FACE;
const VERSION: &str = "m2check2-v1";
fn task_box(id: usize) -> ((usize, usize), Box6) {
    let face = id / PER_FACE;
    let mut n = id % PER_FACE;
    let z = std::array::from_fn(|_| {
        let a = n % GRID;
        n /= GRID;
        I::new(-1.0 + a as f64 * 0.5, -0.5 + a as f64 * 0.5)
    });
    ((face / 4, face % 4), Box6 { z, depth: 0 })
}
#[derive(Default, Clone, Debug)]
struct Stats {
    boxes: u64,
    discarded: u64,
    near: u64,
    closed: u64,
    max_depth: u32,
    fails: u64,
    seconds: f64,
}
impl Stats {
    fn leaves(&self) -> u64 {
        self.discarded + self.near + self.closed + self.fails
    }
    fn add(&mut self, s: &Self) {
        self.boxes += s.boxes;
        self.discarded += s.discarded;
        self.near += s.near;
        self.closed += s.closed;
        self.fails += s.fails;
        self.max_depth = self.max_depth.max(s.max_depth);
        self.seconds += s.seconds;
    }
    fn fields(&self) -> String {
        format!(
            "\"boxes\":{},\"discarded\":{},\"near\":{},\"closed\":{},\"max_depth\":{},\"fails\":{},\"seconds\":{}",
            self.boxes,
            self.discarded,
            self.near,
            self.closed,
            self.max_depth,
            self.fails,
            self.seconds
        )
    }
}
fn sample(b: Box6, reason: &str) -> String {
    format!(
        "{{\"reason\":\"{}\",\"depth\":{},\"box\":[{}]}}",
        reason,
        b.depth,
        b.z.map(|z| format!("[{},{}]", z.lo, z.hi)).join(",")
    )
}
fn run_task(id: usize, max_depth: u32, seconds: f64) -> (Stats, Vec<String>) {
    let (faces, b) = task_box(id);
    let start = Instant::now();
    let mut stack = vec![b];
    let mut s = Stats::default();
    let mut examples = Vec::new();
    while let Some(b) = stack.pop() {
        s.boxes += 1;
        s.max_depth = s.max_depth.max(b.depth);
        let reason = if start.elapsed().as_secs_f64() >= seconds {
            Some("time_limit")
        } else {
            let r = entries(b, faces);
            if discard(r) && discard(r.map(|row| row.map(I::neg))) {
                s.discarded += 1;
                continue;
            }
            if near(r) {
                s.near += 1;
                continue;
            }
            if fbound(r).hi < 1.0 {
                s.closed += 1;
                continue;
            }
            if b.depth >= max_depth {
                Some("max_depth")
            } else {
                None
            }
        };
        if let Some(reason) = reason {
            s.fails += 1;
            if examples.len() < 4 {
                examples.push(sample(b, reason));
            }
            continue;
        }
        // Longest side, cyclic tie-breaking: bounded aspect ratio without starving coordinates.
        let k = (0..6)
            .map(|offset| (offset + b.depth as usize) % 6)
            .max_by(|&a, &c| (b.z[a].hi - b.z[a].lo).total_cmp(&(b.z[c].hi - b.z[c].lo)))
            .unwrap();
        let mid = b.z[k].lo + (b.z[k].hi - b.z[k].lo) * 0.5;
        if mid <= b.z[k].lo || mid >= b.z[k].hi {
            s.fails += 1;
            if examples.len() < 4 {
                examples.push(sample(b, "precision_limit"));
            }
            continue;
        }
        let mut l = b;
        let mut r = b;
        l.depth += 1;
        r.depth += 1;
        l.z[k].hi = mid;
        r.z[k].lo = mid;
        stack.push(r);
        stack.push(l);
    }
    s.seconds = start.elapsed().as_secs_f64();
    assert_eq!(s.boxes, 2 * s.leaves() - 1);
    (s, examples)
}
// A small strict JSON reader for our append-only journal (no external crates).
#[derive(Debug)]
enum J {
    N(String),
    S(String),
    A(Vec<J>),
    O(BTreeMap<String, J>),
}
struct Parser<'a> {
    s: &'a [u8],
    p: usize,
}
impl<'a> Parser<'a> {
    fn ws(&mut self) {
        while self.p < self.s.len() && self.s[self.p].is_ascii_whitespace() {
            self.p += 1;
        }
    }
    fn take(&mut self, c: u8) -> Result<(), String> {
        self.ws();
        if self.s.get(self.p) == Some(&c) {
            self.p += 1;
            Ok(())
        } else {
            Err("malformed JSON".into())
        }
    }
    fn string(&mut self) -> Result<String, String> {
        self.take(b'"')?;
        let start = self.p;
        while let Some(&c) = self.s.get(self.p) {
            if c == b'"' {
                let v = std::str::from_utf8(&self.s[start..self.p])
                    .map_err(|_| "non UTF-8")?
                    .to_owned();
                self.p += 1;
                return Ok(v);
            }
            if c == b'\\' || c < 32 {
                return Err("unsupported JSON string".into());
            }
            self.p += 1;
        }
        Err("unterminated string".into())
    }
    fn value(&mut self) -> Result<J, String> {
        self.ws();
        match self.s.get(self.p) {
            Some(b'"') => Ok(J::S(self.string()?)),
            Some(b'{') => {
                self.p += 1;
                let mut map = BTreeMap::new();
                self.ws();
                if self.s.get(self.p) == Some(&b'}') {
                    self.p += 1;
                    return Ok(J::O(map));
                }
                loop {
                    let key = self.string()?;
                    self.take(b':')?;
                    let val = self.value()?;
                    if map.insert(key, val).is_some() {
                        return Err("duplicate JSON key".into());
                    }
                    self.ws();
                    if self.s.get(self.p) == Some(&b'}') {
                        self.p += 1;
                        break;
                    }
                    self.take(b',')?;
                }
                Ok(J::O(map))
            }
            Some(b'[') => {
                self.p += 1;
                let mut a = Vec::new();
                self.ws();
                if self.s.get(self.p) == Some(&b']') {
                    self.p += 1;
                    return Ok(J::A(a));
                }
                loop {
                    a.push(self.value()?);
                    self.ws();
                    if self.s.get(self.p) == Some(&b']') {
                        self.p += 1;
                        break;
                    }
                    self.take(b',')?;
                }
                Ok(J::A(a))
            }
            Some(b'-' | b'0'..=b'9') => {
                let start = self.p;
                while self.p < self.s.len()
                    && matches!(
                        self.s[self.p],
                        b'0'..=b'9' | b'-' | b'+' | b'.' | b'e' | b'E'
                    )
                {
                    self.p += 1;
                }
                let v = std::str::from_utf8(&self.s[start..self.p]).unwrap();
                let f = v.parse::<f64>().map_err(|_| "bad number")?;
                if !f.is_finite() {
                    return Err("nonfinite number".into());
                }
                Ok(J::N(v.to_owned()))
            }
            _ => Err("unexpected JSON token".into()),
        }
    }
}
fn journal(line: &str, depth: u32) -> Result<(usize, Stats), String> {
    let mut p = Parser {
        s: line.as_bytes(),
        p: 0,
    };
    let j = p.value()?;
    p.ws();
    if p.p != p.s.len() {
        return Err("trailing JSON data".into());
    }
    let J::O(m) = j else {
        return Err("expected object".into());
    };
    let num = |k: &str| -> Result<u64, String> {
        match m.get(k) {
            Some(J::N(v)) => v.parse().map_err(|_| format!("bad integer {k}")),
            _ => Err(format!("missing {k}")),
        }
    };
    if !matches!(m.get("version"),Some(J::S(v)) if v==VERSION)
        || num("grid")? != GRID as u64
        || num("depth_limit")? != depth as u64
    {
        return Err("journal configuration/version mismatch".into());
    }
    let id = usize::try_from(num("task")?).map_err(|_| "bad task")?;
    if id >= TASKS {
        return Err("task out of range".into());
    }
    let seconds = match m.get("seconds") {
        Some(J::N(v)) => v.parse::<f64>().map_err(|_| "bad seconds")?,
        _ => return Err("missing seconds".into()),
    };
    let s = Stats {
        boxes: num("boxes")?,
        discarded: num("discarded")?,
        near: num("near")?,
        closed: num("closed")?,
        max_depth: u32::try_from(num("max_depth")?).map_err(|_| "bad depth")?,
        fails: num("fails")?,
        seconds,
    };
    // Bound counters before additions, including malicious/corrupted journal input.
    if [s.boxes, s.discarded, s.near, s.closed, s.fails]
        .iter()
        .any(|&n| n > u64::MAX / (16 * TASKS as u64))
        || s.boxes == 0
        || s.leaves() == 0
        || s.seconds < 0.0
        || s.max_depth > depth
        || s.boxes != 2 * s.leaves() - 1
    {
        return Err("invalid counters/tree identity".into());
    }
    let Some(J::A(samples)) = m.get("fail_boxes") else {
        return Err("missing fail_boxes".into());
    };
    if samples.len() != s.fails.min(4) as usize {
        return Err("invalid failure sample count".into());
    }
    for sample in samples {
        let J::O(b) = sample else {
            return Err("bad fail box".into());
        };
        if !matches!(b.get("reason"),Some(J::S(r)) if ["time_limit","max_depth","precision_limit"].contains(&r.as_str()))
        {
            return Err("bad failure reason".into());
        }
        let Some(J::A(z)) = b.get("box") else {
            return Err("missing box".into());
        };
        if z.len() != 6 {
            return Err("bad box dimension".into());
        }
        for x in z {
            let J::A(ends) = x else {
                return Err("bad interval".into());
            };
            if ends.len() != 2 {
                return Err("bad interval".into());
            }
            let mut a = Vec::new();
            for e in ends {
                let J::N(v) = e else {
                    return Err("bad endpoint".into());
                };
                a.push(v.parse::<f64>().map_err(|_| "bad endpoint")?);
            }
            if a[0] < -1.0 || a[1] > 1.0 || a[0] > a[1] {
                return Err("invalid interval".into());
            }
        }
    }
    Ok((id, s))
}
#[derive(Clone)]
struct Options {
    jobs: usize,
    first: usize,
    last: usize,
    depth: u32,
    seconds: f64,
    log: String,
    selftest: bool,
}
fn options() -> Result<Option<Options>, String> {
    let mut o = Options {
        jobs: 1,
        first: 0,
        last: TASKS,
        depth: 60,
        seconds: 8.0,
        log: "m2check2.jsonl".into(),
        selftest: false,
    };
    let mut args = std::env::args().skip(1);
    while let Some(arg) = args.next() {
        if arg == "--help" {
            println!(
                "m2check2 [--selftest] [--jobs N] [--first ID] [--last ID_EXCLUSIVE] [--max-depth N] [--task-seconds S] [--log FILE]\n16 face pairs x 4096 tasks = {TASKS}. Default task cap 8 seconds; unresolved leaves FAIL. Full run is never implicit in selftest."
            );
            return Ok(None);
        }
        if arg == "--selftest" {
            o.selftest = true;
            continue;
        }
        let val = args
            .next()
            .ok_or_else(|| format!("missing value for {arg}"))?;
        match arg.as_str() {
            "--jobs" => o.jobs = val.parse().map_err(|_| "bad jobs")?,
            "--first" => o.first = val.parse().map_err(|_| "bad first")?,
            "--last" => o.last = val.parse().map_err(|_| "bad last")?,
            "--max-depth" => o.depth = val.parse().map_err(|_| "bad depth")?,
            "--task-seconds" => o.seconds = val.parse().map_err(|_| "bad seconds")?,
            "--log" => o.log = val,
            _ => return Err(format!("unknown option {arg}")),
        }
    }
    if o.jobs == 0
        || o.jobs > 256
        || o.first >= o.last
        || o.last > TASKS
        || o.depth > 120
        || !o.seconds.is_finite()
        || o.seconds <= 0.0
        || o.seconds > 3600.0
    {
        return Err("invalid range/options (task-seconds must be in (0,3600], depth <=120)".into());
    }
    Ok(Some(o))
}
fn execute(o: Options) -> Result<bool, String> {
    if o.selftest {
        selftest();
        println!(
            "{{\"selftest\":true,\"selftest_passed\":true,\"tasks\":0,\"tasks_total\":{TASKS},\"fails\":0,\"ok\":false}}"
        );
        return Ok(true);
    }
    let start = Instant::now();
    let mut done = BTreeMap::new();
    match File::open(&o.log) {
        Ok(f) => {
            for (n, line) in BufReader::new(f).lines().enumerate() {
                let line = line.map_err(|e| e.to_string())?;
                let (id, s) =
                    journal(&line, o.depth).map_err(|e| format!("{}:{}: {e}", o.log, n + 1))?;
                if done.insert(id, s).is_some() {
                    return Err(format!("duplicate task {id} in log"));
                }
            }
        }
        Err(e) if e.kind() == std::io::ErrorKind::NotFound => {}
        Err(e) => return Err(e.to_string()),
    }
    // Refuse a non-newline-terminated journal: appending would splice two records.
    if let Ok(bytes) = std::fs::read(&o.log) {
        if !bytes.is_empty() && bytes.last() != Some(&b'\n') {
            return Err("journal ends without newline; inspect/remove the interrupted last line before resuming".into());
        }
    }
    let queue: Vec<_> = (o.first..o.last)
        .filter(|i| !done.contains_key(i))
        .collect();
    let skipped = o.last - o.first - queue.len();
    println!(
        "tasks_total={TASKS} selected=[{},{}) queued={} skipped={} jobs={}",
        o.first,
        o.last,
        queue.len(),
        skipped,
        o.jobs
    );
    let log = OpenOptions::new()
        .create(true)
        .append(true)
        .open(&o.log)
        .map_err(|e| e.to_string())?;
    let state = Arc::new(Mutex::new((log, done)));
    let cursor = AtomicUsize::new(0);
    std::thread::scope(|scope| -> Result<(), String> {
        let mut handles = Vec::new();
        for _ in 0..o.jobs {
            let state = state.clone();
            let queue = &queue;
            let cursor = &cursor;
            let o = &o;
            handles.push(scope.spawn(move ||->Result<(),String>{loop{let k=cursor.fetch_add(1,Ordering::Relaxed);let Some(&id)=queue.get(k) else{break};let (s,samples)=run_task(id,o.depth,o.seconds);
                let line=format!("{{\"version\":\"{VERSION}\",\"grid\":{GRID},\"depth_limit\":{},\"task\":{}, {},\"fail_boxes\":[{}]}}\n",o.depth,id,s.fields(),samples.join(","));
                let mut state=state.lock().map_err(|_|"journal lock poisoned")?;state.0.write_all(line.as_bytes()).map_err(|e|e.to_string())?;state.0.flush().map_err(|e|e.to_string())?;state.1.insert(id,s);
            }Ok(())}));
        }
        for h in handles {
            h.join().map_err(|_| "worker panicked")??;
        }
        Ok(())
    })?;
    let state = state.lock().map_err(|_| "journal lock poisoned")?;
    let mut total = Stats::default();
    for s in state.1.values() {
        total.add(s);
    }
    let tasks = state.1.len();
    let tree = total.boxes == 2 * total.leaves() - tasks as u64;
    let ok = total.fails == 0 && tasks == TASKS && tree;
    println!(
        "tree identity: {} = 2 * {} - {} : {}",
        total.boxes,
        total.leaves(),
        tasks,
        tree
    );
    println!(
        "{{\"tasks\":{tasks},\"tasks_total\":{TASKS},\"new_tasks\":{},\"skipped\":{skipped},{},\"wall_seconds\":{},\"tree_identity\":{tree},\"ok\":{ok}}}",
        queue.len(),
        total.fields(),
        start.elapsed().as_secs_f64()
    );
    Ok(ok)
}
fn main() {
    match options().and_then(|o| match o {
        Some(o) => execute(o).map(Some),
        None => Ok(None),
    }) {
        Ok(Some(false)) => std::process::exit(2),
        Ok(_) => {}
        Err(e) => {
            eprintln!("error: {e}");
            println!("{{\"ok\":false,\"error\":true}}");
            std::process::exit(1);
        }
    }
}

// Floating point routines below are testing only: never used for proof decisions.
type FM = [[f64; 4]; 4];
fn qfloat(a: [f64; 4], b: [f64; 4]) -> [f64; 4] {
    let mut c = [0.0; 4];
    for i in 0..4 {
        for j in 0..4 {
            let (k, s) = basis(i, j);
            c[k] += s as f64 * a[i] * b[j];
        }
    }
    c
}
fn rotation(p: [f64; 4], q: [f64; 4]) -> FM {
    let norm = (p.iter().map(|x| x * x).sum::<f64>() * q.iter().map(|x| x * x).sum::<f64>()).sqrt();
    let qc = [q[0], -q[1], -q[2], -q[3]];
    let mut r = [[0.0; 4]; 4];
    for j in 0..4 {
        let mut e = [0.0; 4];
        e[j] = 1.0;
        let v = qfloat(qfloat(p, e), qc);
        for i in 0..4 {
            r[i][j] = v[i] / norm;
        }
    }
    r
}
fn ffloat(r: FM) -> f64 {
    r.iter()
        .map(|row| row[0].abs() * (2.0 - row.iter().map(|x| x.abs()).sum::<f64>()))
        .sum()
}
fn det(mut a: FM) -> f64 {
    let mut d = 1.0;
    for k in 0..4 {
        let p = (k..4)
            .max_by(|&i, &j| a[i][k].abs().total_cmp(&a[j][k].abs()))
            .unwrap();
        if a[p][k].abs() < 1e-20 {
            return 0.0;
        }
        if p != k {
            a.swap(p, k);
            d = -d;
        }
        d *= a[k][k];
        for i in k + 1..4 {
            let t = a[i][k] / a[k][k];
            for j in k + 1..4 {
                a[i][j] -= t * a[k][j];
            }
        }
    }
    d
}
fn orthogonal(r: FM) {
    for i in 0..4 {
        for j in 0..4 {
            let t = (0..4).map(|k| r[k][i] * r[k][j]).sum::<f64>();
            assert!((t - if i == j { 1.0 } else { 0.0 }).abs() < 2e-12);
        }
    }
    assert!((det(r) - 1.0).abs() < 2e-12);
}
struct Rng(u64);
impl Rng {
    fn unit(&mut self) -> f64 {
        self.0 ^= self.0 << 13;
        self.0 ^= self.0 >> 7;
        self.0 ^= self.0 << 17;
        (self.0 >> 11) as f64 / (1u64 << 53) as f64
    }
    fn signed(&mut self) -> f64 {
        2.0 * self.unit() - 1.0
    }
    fn q(&mut self) -> [f64; 4] {
        let mut a = std::array::from_fn(|_| self.signed());
        let n = a.iter().map(|x| x * x).sum::<f64>().sqrt();
        for v in &mut a {
            *v /= n;
        }
        a
    }
}
fn point(z: [f64; 6], faces: (usize, usize)) -> FM {
    let mut p = [1.0; 4];
    let mut q = p;
    let mut k = 0;
    for (v, f) in [(&mut p, faces.0), (&mut q, faces.1)] {
        for (j, x) in v.iter_mut().enumerate() {
            if j != f {
                *x = z[k];
                k += 1;
            }
        }
    }
    rotation(p, q)
}
fn reduce(mut r: FM) -> FM {
    for row in &mut r {
        if row[0] < 0.0 {
            for x in row {
                *x = -*x;
            }
        }
    }
    r.sort_by(|a, b| b[0].total_cmp(&a[0]));
    let mut cols = [1, 2, 3];
    cols.sort_by(|&i, &j| r[0][j].abs().total_cmp(&r[0][i].abs()));
    let old = r;
    for i in 0..4 {
        for j in 0..3 {
            r[i][j + 1] = old[i][cols[j]];
        }
    }
    for j in 1..=2 {
        if r[0][j] < 0.0 {
            for row in &mut r {
                row[j] = -row[j];
            }
        }
    }
    if det(r) < 0.0 {
        for row in &mut r {
            row[3] = -row[3];
        }
    }
    r
}
// Independent SO(4) samples: Gram-Schmidt random columns, followed by determinant fix.
fn random_so(rng: &mut Rng) -> FM {
    let mut r = [[0.0; 4]; 4];
    for j in 0..4 {
        let mut v = rng.q();
        for k in 0..j {
            let dot = (0..4).map(|i| v[i] * r[i][k]).sum::<f64>();
            for i in 0..4 {
                v[i] -= dot * r[i][k];
            }
        }
        let n = v.iter().map(|x| x * x).sum::<f64>().sqrt();
        if n < 1e-5 {
            return random_so(rng);
        }
        for i in 0..4 {
            r[i][j] = v[i] / n;
        }
    }
    if det(r) < 0.0 {
        for row in &mut r {
            row[3] = -row[3];
        }
    }
    r
}
// Coefficient matrices form an orthogonal basis of all 4x4 matrices (norm squared 4).
fn recover(r: FM) -> ([f64; 4], [f64; 4]) {
    let mut a = [[0.0; 4]; 4];
    for i in 0..4 {
        for j in 0..4 {
            let mut p = [0.0; 4];
            let mut q = p;
            p[i] = 1.0;
            q[j] = 1.0;
            let m = rotation(p, q);
            a[i][j] = (0..4)
                .flat_map(|x| (0..4).map(move |y| r[x][y] * m[x][y]))
                .sum::<f64>()
                / 4.0;
        }
    }
    let k = (0..4)
        .max_by(|&i, &j| {
            a[i].iter()
                .map(|x| x * x)
                .sum::<f64>()
                .total_cmp(&a[j].iter().map(|x| x * x).sum::<f64>())
        })
        .unwrap();
    let n = a[k].iter().map(|x| x * x).sum::<f64>().sqrt();
    let q = a[k].map(|x| x / n);
    let p = std::array::from_fn(|i| (0..4).map(|j| a[i][j] * q[j]).sum());
    (p, q)
}
fn selftest() {
    let mut rng = Rng(0x91b4c789abcd1234);
    let mut negative_charts = 0;
    for _ in 0..500 {
        let r = random_so(&mut rng);
        orthogonal(r);
        let (p, q) = recover(r);
        let rr = rotation(p, q);
        let both = rotation(p.map(|x| -x), q.map(|x| -x));
        for i in 0..4 {
            for j in 0..4 {
                assert!((r[i][j] - rr[i][j]).abs() < 2e-11);
                assert_eq!(rr[i][j], both[i][j]);
            }
        }
        let reduced = reduce(r);
        orthogonal(reduced);
        assert!((ffloat(r) - ffloat(reduced)).abs() < 2e-14);
        for i in 0..4 {
            assert!(reduced[i][0] >= 0.0);
            if i < 3 {
                assert!(reduced[i][0] >= reduced[i + 1][0]);
            }
        }
        assert!(reduced[0][1] >= 0.0 && reduced[0][2] >= 0.0);
        assert!(
            reduced[0][1].abs() >= reduced[0][2].abs()
                && reduced[0][2].abs() >= reduced[0][3].abs()
        );
        let (p, q) = recover(reduced);
        let fp = (0..4)
            .max_by(|&i, &j| p[i].abs().total_cmp(&p[j].abs()))
            .unwrap();
        let fq = (0..4)
            .max_by(|&i, &j| q[i].abs().total_cmp(&q[j].abs()))
            .unwrap();
        let chart = rotation(p.map(|x| x / p[fp]), q.map(|x| x / q[fq]));
        let sign = if p[fp] * q[fq] < 0.0 {
            negative_charts += 1;
            -1.0
        } else {
            1.0
        };
        for i in 0..4 {
            for j in 0..4 {
                assert!((chart[i][j] * sign - reduced[i][j]).abs() < 2e-11);
            }
        }
    }
    for face in 0..16 {
        for trial in 0..64 {
            let z = std::array::from_fn(|_| {
                let c = rng.signed();
                let w = if trial == 0 {
                    2.0
                } else {
                    0.5 * rng.unit().powi(3)
                };
                I::new((c - w).max(-1.0), (c + w).min(1.0))
            });
            let b = Box6 { z, depth: 0 };
            let r = entries(b, (face / 4, face % 4));
            let bound = fbound(r);
            for sample in 0..10 {
                let x = std::array::from_fn(|k| {
                    if sample == 0 {
                        z[k].lo
                    } else if sample == 1 {
                        z[k].hi
                    } else {
                        z[k].lo + (z[k].hi - z[k].lo) * rng.unit()
                    }
                });
                let rp = point(x, (face / 4, face % 4));
                orthogonal(rp);
                for i in 0..4 {
                    for j in 0..4 {
                        assert!(
                            r[i][j].contains(rp[i][j]),
                            "entry outside interval: {:?} {}",
                            r[i][j],
                            rp[i][j]
                        );
                    }
                }
                assert!(ffloat(rp) <= bound.hi, "F exceeds interval bound");
                if near(r) {
                    assert!(rp.iter().map(|row| row[0] * row[0]).fold(0.0, f64::max) >= 2.0 / 3.0);
                }
            }
        }
    }
    println!(
        "selftest: 500 independent SO(4) recoveries, determinant/orthogonality, double-cover and symmetry tests passed ({negative_charts} canonical rotations required negative chart sign)"
    );
    println!(
        "selftest: 1024 random boxes, 10240 point/corner entry and F enclosure checks passed (all 16 face pairs)"
    );
}
#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn randomized_geometry_and_enclosures() {
        selftest();
    }
    #[test]
    fn interval_edges() {
        let z = I::pt(0.0);
        assert!(z.add(z).contains(0.0));
        assert_eq!(I::new(-2.0, 3.0).sq().lo, 0.0);
        assert!(I::pt(2.0).sqrt().sq().contains(2.0));
        assert!(I::pt(3.0).recip().mul(I::pt(3.0)).contains(1.0));
        assert!(!I::new(-1.0, 1.0).abs().contains(-0.1));
        assert!(!near([[I::pt(0.0); 4]; 4]));
    }
    #[test]
    fn task_partition() {
        assert_eq!(GRID.pow(6), PER_FACE);
        for id in 0..TASKS {
            let (f, b) = task_box(id);
            assert!(f.0 < 4 && f.1 < 4);
            for z in b.z {
                assert_eq!(z.hi - z.lo, 0.5);
                assert!(z.lo >= -1.0 && z.hi <= 1.0);
            }
        }
    }
    #[test]
    fn failure_and_tree() {
        let (s, b) = run_task(0, 0, 8.0);
        assert_eq!(s.boxes, 2 * s.leaves() - 1);
        assert_eq!(s.fails, 1);
        assert_eq!(b.len(), 1);
        let line = format!(
            "{{\"version\":\"{VERSION}\",\"grid\":4,\"depth_limit\":0,\"task\":0,{},\"fail_boxes\":[{}]}}",
            s.fields(),
            b.join(",")
        );
        assert_eq!(journal(&line, 0).unwrap().1.fails, 1);
        assert!(journal(&line, 1).is_err());
        assert!(journal(&(line + "garbage"), 0).is_err());
    }
    #[test]
    fn constraints() {
        let mut r = [[I::pt(0.0); 4]; 4];
        assert!(!discard(r));
        r[1][0] = I::pt(1.0);
        assert!(discard(r));
        r[1][0] = I::pt(0.0);
        r[0][1] = I::pt(-0.2);
        assert!(discard(r));
        r[0][1] = I::pt(0.2);
        r[0][2] = I::pt(0.3);
        assert!(discard(r));
    }
    #[test]
    fn reduction_ties_and_zeros() {
        let h = 0.5;
        let hadamard: FM = [[h, h, h, h], [h, -h, h, -h], [h, h, -h, -h], [h, -h, -h, h]];
        let perm: FM = [
            [0.0, 0.0, -1.0, 0.0],
            [0.0, 1.0, 0.0, 0.0],
            [-1.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 1.0],
        ];
        let mut cases = vec![perm];
        for flip in 0..16u32 {
            // sign patterns of the rows of the Hadamard matrix, det fixed by column 4
            let mut r = hadamard;
            for i in 0..4 {
                if flip >> i & 1 == 1 {
                    r[i] = r[i].map(|x| -x);
                }
            }
            if det(r) < 0.0 {
                for row in &mut r {
                    row[3] = -row[3];
                }
            }
            cases.push(r);
        }
        for r in cases {
            let s = reduce(r);
            assert!((det(s) - 1.0).abs() < 1e-12);
            assert!((ffloat(s) - ffloat(r)).abs() < 1e-12);
            assert!(!discard(s.map(|row| row.map(I::pt))), "reduced tie/zero case violates C1-C3: {:?}", s);
        }
    }
    #[test]
    fn time_cap_is_failure() {
        let (s, samples) = run_task(0, 60, f64::MIN_POSITIVE);
        assert_eq!(s.boxes, 1);
        assert_eq!(s.fails, 1);
        assert!(samples[0].contains("time_limit"));
    }
    #[test]
    fn near_and_f_closing() {
        let id = rotation([1.0, 0.0, 0.0, 0.0], [1.0, 0.0, 0.0, 0.0]).map(|row| row.map(I::pt));
        assert!(near(id));
        let spread = rotation([0.5; 4], [1.0, 0.0, 0.0, 0.0]).map(|row| row.map(I::pt));
        assert!(!near(spread));
        assert!(fbound(spread).hi < 1.0);
        let crossing = [[I::new(-1.0, 1.0); 4]; 4];
        assert!(!near(crossing));
        assert!(!discard(crossing));
        assert!(fbound(crossing).hi >= 1.0);
    }
    #[test]
    fn resume_and_corrupt_journal() {
        let path = std::env::temp_dir().join(format!(
            "m2check2-test-{}-{}.jsonl",
            std::process::id(),
            std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap()
                .as_nanos()
        ));
        let o = Options {
            jobs: 2,
            first: 0,
            last: 2,
            depth: 0,
            seconds: 8.0,
            log: path.to_str().unwrap().into(),
            selftest: false,
        };
        assert!(!execute(o.clone()).unwrap());
        let first = std::fs::read_to_string(&path).unwrap();
        assert_eq!(first.lines().count(), 2);
        assert!(!execute(o.clone()).unwrap());
        assert_eq!(first, std::fs::read_to_string(&path).unwrap());
        let mut different = o.clone();
        different.depth = 1;
        assert!(execute(different).is_err());
        std::fs::write(&path, first.trim_end()).unwrap();
        assert!(execute(o.clone()).is_err());
        std::fs::write(&path, format!("{first}{first}")).unwrap();
        assert!(execute(o.clone()).is_err());
        let corrupt = first
            .lines()
            .next()
            .unwrap()
            .replace("\"fails\":1", "\"fails\":0");
        assert!(journal(&corrupt, 0).is_err());
        std::fs::remove_file(path).unwrap();
    }
}
