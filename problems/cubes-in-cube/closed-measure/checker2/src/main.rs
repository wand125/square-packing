mod dual;
mod geometry;
mod interval;
mod json;
mod measure;
mod search;
mod sha256;
mod symmetry;
mod validation;
use std::{
    io::{self, BufRead},
    path::PathBuf,
};
fn main() {
    let args: Vec<String> = std::env::args().skip(1).collect();
    let mut c = search::Config {
        threads: 1,
        seconds: 60.,
        depth: 72,
        output: PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("run"),
        resume: false,
        checkpoint_seconds: 10.,
        keep: false,
        rounds: u64::MAX,
        cell_depth: 6,
        unresolved_list: None,
    };
    let mut batch = false;
    let mut sample = None;
    let mut ratio = "27/20".to_string();
    let mut measure_path = "../measure.json".to_string();
    let mut data_only = false;
    let mut validate = false;
    let mut server = false;
    let mut i = 0;
    while i < args.len() {
        match args[i].as_str() {
            "--threads" => {
                i += 1;
                c.threads = args[i].parse().unwrap();
            }
            "--seconds" => {
                i += 1;
                c.seconds = args[i].parse().unwrap();
            }
            "--depth" | "--max-depth" => {
                i += 1;
                c.depth = args[i].parse().unwrap();
            }
            "--output" => {
                i += 1;
                c.output = PathBuf::from(&args[i]);
            }
            "--checkpoint-seconds" => {
                i += 1;
                c.checkpoint_seconds = args[i].parse().unwrap();
            }
            "--rounds" => {
                i += 1;
                c.rounds = args[i].parse().unwrap();
            }
            "--sigma" => {
                i += 1;
                ratio = args[i].clone();
            }
            "--measure" => {
                i += 1;
                measure_path = args[i].clone();
            }
            "--check-data" => data_only = true,
            "--cell-depth" => {
                i += 1;
                c.cell_depth = args[i].parse().unwrap();
            }
            "--sample-box" => {
                i += 1;
                sample = Some(args[i].clone());
            }
            "--unresolved-list" => {
                i += 1;
                c.unresolved_list = Some(PathBuf::from(&args[i]));
            }
            "--resume" => c.resume = true,
            "--keep-leaves" => c.keep = true,
            "--batch" => batch = true,
            "--validate" => validate = true,
            "--server" => server = true,
            _ => panic!("unknown option {}", args[i]),
        }
        i += 1;
    }
    assert!(
        c.threads > 0
            && c.seconds.is_finite()
            && c.seconds > 0.25
            && c.checkpoint_seconds.is_finite()
            && c.checkpoint_seconds > 0.
            && c.depth <= 256
    );
    if cfg!(target_os = "macos") {
        assert!(!server, "--server is forbidden on macOS");
        assert!(
            c.threads <= 2 && c.seconds <= 1200.,
            "Mac limit: 2 threads, 1200 seconds"
        );
    } else if !server {
        assert!(
            c.threads <= 2 && c.seconds <= 1200.,
            "use --server to lift limits"
        );
    }
    let m = measure::read(&measure_path, &ratio);
    assert_eq!(
        m.hash, "565dbf5dd0059aa90929e4151d85fafdeef002a1b9e9aaf83f2e6243b2d393e0",
        "measure hash mismatch"
    );
    measure::DATA.set(m).ok().unwrap();
    if data_only {
        println!("{{{}}}", measure::data().metadata());
        return;
    }
    if let Some(s) = sample {
        let j = json::parse(&s);
        println!("{}", geometry::bound(&search::parse_box(&j, 0)).json());
        return;
    }
    if validate {
        validation::run();
        return;
    }
    if batch {
        for line in io::stdin().lock().lines() {
            let line = line.unwrap();
            if line.trim().is_empty() {
                continue;
            }
            let j = json::parse(&line);
            let b = search::parse_box(&j, 0);
            let outside = geometry::outside(&b);
            let result = if outside {
                // Zero is a valid mass lower bound; no geometric work is needed.
                "{\"L\":0,\"contributions\":[0,0,0],\"lemma_counts\":[0,0,0,0,0,0]}".to_string()
            } else {
                geometry::bound(&b).json()
            };
            println!("{},\"outside\":{}}}", &result[..result.len() - 1], outside);
        }
        return;
    }
    search::run(c);
}
