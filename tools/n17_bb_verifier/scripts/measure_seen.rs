//! Standalone sparse-ID table measurement (no certificate or verifier state).
//! rustc -O scripts/measure_seen.rs -o target/measure-seen
//! /usr/bin/time -l target/measure-seen 1000000
use std::collections::HashSet;

fn main() {
    let count: u64 = std::env::args()
        .nth(1)
        .unwrap_or_else(|| "1000000".into())
        .parse()
        .expect("node count");
    let mut seen = HashSet::new();
    for i in 0..count {
        assert!(seen.insert(u64::MAX - i * 1009));
    }
    let buckets = (seen.capacity() * 8 / 7).next_power_of_two();
    println!(
        "nodes={} capacity={} estimated_bytes={} bytes_per_node={:.3}",
        seen.len(),
        seen.capacity(),
        buckets * 9 + 16,
        (buckets * 9 + 16) as f64 / count as f64
    );
    std::hint::black_box(&seen);
}
