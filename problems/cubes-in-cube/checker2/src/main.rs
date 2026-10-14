mod geometry;
mod interval;
mod json;
mod search;
mod sha256;
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
    };
    let mut batch = false;
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
            "--depth" => {
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
            match geometry::close(&b) {
                Some(o) => println!("{{\"rule\":{},\"points\":{:?}}}", o.rule, o.points),
                None => println!("{{\"rule\":0,\"points\":[]}}"),
            }
        }
        return;
    }
    search::run(c);
}
