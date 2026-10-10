//! Receipt equality and fallback regressions for streaming verification.
use std::fs;
use std::io::Write;
use std::path::{Path, PathBuf};
use std::process::Command;
use std::sync::atomic::{AtomicUsize, Ordering};

use flate2::{Compression, read::MultiGzDecoder, write::GzEncoder};
use serde_json::{Value, json};
use sha2::{Digest, Sha256};

fn fixtures() -> PathBuf {
    Path::new(env!("CARGO_MANIFEST_DIR")).join("tests/fixtures")
}

fn invoke(directory: &Path, cells: bool, stream: bool, threads: usize) -> (i32, Value, String) {
    let mut command = Command::new(env!("CARGO_BIN_EXE_n17bb-verify"));
    command
        .arg(directory)
        .args(["--threads", &threads.to_string()]);
    if cells {
        let path = fixtures().join("v3-cells.json");
        let digest = format!(
            "{:x}",
            Sha256::digest(fs::read(&path).expect("valid regression fixture and verifier output"))
        );
        command
            .arg("--cells")
            .arg(path)
            .args(["--cells-sha256", &digest]);
    }
    if stream {
        command.arg("--stream");
    }
    let output = command
        .output()
        .expect("valid regression fixture and verifier output");
    let mut receipt: Value = serde_json::from_slice(&output.stdout)
        .expect("valid regression fixture and verifier output");
    receipt
        .as_object_mut()
        .expect("valid regression fixture and verifier output")
        .remove("seconds");
    (
        output
            .status
            .code()
            .expect("valid regression fixture and verifier output"),
        receipt,
        String::from_utf8(output.stderr).expect("valid regression fixture and verifier output"),
    )
}

fn compare(directory: &Path, cells: bool, fallback: bool, threads: usize) -> Value {
    let classic = invoke(directory, cells, false, threads);
    let stream = invoke(directory, cells, true, threads);
    assert_eq!(classic.0, stream.0, "{}", directory.display());
    assert_eq!(classic.1, stream.1, "{}", directory.display());
    assert_eq!(
        stream.2.contains("stream fallback:"),
        fallback,
        "{}: {}",
        directory.display(),
        stream.2
    );
    stream.1
}

#[test]
fn every_retained_fixture_has_identical_receipts() {
    for entry in fs::read_dir(fixtures()).expect("valid regression fixture and verifier output") {
        let path = entry
            .expect("valid regression fixture and verifier output")
            .path();
        if !path.is_dir() {
            continue;
        }
        let name = path
            .file_name()
            .expect("valid regression fixture and verifier output")
            .to_str()
            .expect("valid regression fixture and verifier output");
        let pass = matches!(name, "small-certificate" | "v3-angle" | "v3-tighten");
        for threads in [1, 2] {
            compare(&path, name.starts_with("v3-"), !pass, threads);
        }
    }
}

struct Certificate {
    directory: PathBuf,
    manifest: Value,
    nodes: Vec<Value>,
}
impl Certificate {
    fn new(fixture: &str) -> Self {
        static SERIAL: AtomicUsize = AtomicUsize::new(0);
        let directory = std::env::temp_dir().join(format!(
            "n17-stream-{}-{}",
            std::process::id(),
            SERIAL.fetch_add(1, Ordering::Relaxed)
        ));
        fs::create_dir(&directory).expect("valid regression fixture and verifier output");
        let source = fixtures().join(fixture);
        for entry in fs::read_dir(&source).expect("valid regression fixture and verifier output") {
            let entry = entry.expect("valid regression fixture and verifier output");
            fs::copy(entry.path(), directory.join(entry.file_name()))
                .expect("valid regression fixture and verifier output");
        }
        let readme = fs::read_to_string(source.join("README.txt"))
            .expect("valid regression fixture and verifier output");
        let name = readme
            .lines()
            .last()
            .expect("valid regression fixture and verifier output")
            .split(':')
            .next_back()
            .expect("valid regression fixture and verifier output")
            .trim()
            .trim_end_matches(".json.gz");
        let manifest = Self::read(&directory, name);
        let nodes = manifest["chunks"]
            .as_array()
            .expect("valid regression fixture and verifier output")
            .iter()
            .flat_map(|chunk| {
                Self::read(
                    &directory,
                    chunk
                        .as_str()
                        .expect("valid regression fixture and verifier output"),
                )["nodes"]
                    .as_array()
                    .expect("valid regression fixture and verifier output")
                    .clone()
            })
            .collect();
        Self {
            directory,
            manifest,
            nodes,
        }
    }
    fn read(directory: &Path, name: &str) -> Value {
        serde_json::from_reader(MultiGzDecoder::new(
            fs::File::open(directory.join(format!("{name}.json.gz")))
                .expect("valid regression fixture and verifier output"),
        ))
        .expect("valid regression fixture and verifier output")
    }
    fn write(&self, name: &str, value: &Value) {
        let file = fs::File::create(self.directory.join(format!("{name}.json.gz")))
            .expect("valid regression fixture and verifier output");
        let mut gzip = GzEncoder::new(file, Compression::fast());
        gzip.write_all(
            &serde_json::to_vec(value).expect("valid regression fixture and verifier output"),
        )
        .expect("valid regression fixture and verifier output");
        gzip.finish()
            .expect("valid regression fixture and verifier output");
    }
    fn save(&mut self, separate: bool) {
        let chunks: Vec<_> = if separate {
            self.nodes.iter().cloned().map(|n| vec![n]).collect()
        } else {
            vec![self.nodes.clone()]
        };
        let names: Vec<_> = chunks
            .iter()
            .enumerate()
            .map(|(i, nodes)| {
                let name = format!("stream-test-{i}");
                self.write(&name, &json!({"nodes":nodes}));
                name
            })
            .collect();
        self.manifest["chunks"] = json!(names);
        self.write("stream-manifest", &self.manifest);
        fs::write(
            self.directory.join("README.txt"),
            "manifest: stream-manifest\n",
        )
        .expect("valid regression fixture and verifier output");
    }
}
impl Drop for Certificate {
    fn drop(&mut self) {
        fs::remove_dir_all(&self.directory).expect("valid regression fixture and verifier output");
    }
}

#[test]
fn all_structural_fallbacks_reproduce_classic_receipts() {
    for case in [
        "duplicate",
        "late-parent",
        "absent-parent",
        "closed-parent",
        "excess-child",
        "multiple-roots",
        "missing-root",
        "pending",
        "malformed",
        "bad-id",
        "bad-parent",
        "open-final",
        "open-split",
        "angle-point",
        "child-state",
        "complete",
        "header",
        "trig",
        "chunk-error",
    ] {
        let mut cert = Certificate::new("small-certificate");
        let leaf = cert
            .nodes
            .iter()
            .position(|n| !n["closed"].is_null())
            .expect("valid regression fixture and verifier output");
        match case {
            "duplicate" => cert.nodes.push(cert.nodes[leaf].clone()),
            "late-parent" => cert.nodes.swap(0, 1),
            "absent-parent" => cert.nodes[1]["parent"] = json!(u64::MAX),
            "closed-parent" | "excess-child" => {
                let mut node = cert.nodes[leaf].clone();
                node["id"] = json!(u64::MAX);
                node["parent"] = if case == "closed-parent" {
                    cert.nodes[leaf]["id"].clone()
                } else {
                    cert.nodes[0]["id"].clone()
                };
                cert.nodes.push(node);
            }
            "multiple-roots" => cert.nodes[leaf]["parent"] = Value::Null,
            "missing-root" => cert.nodes.clear(),
            "pending" => {
                cert.nodes.pop();
            }
            "malformed" => {
                cert.nodes[0]
                    .as_object_mut()
                    .expect("valid regression fixture and verifier output")
                    .remove("windows");
            }
            "bad-id" => cert.nodes[0]["id"] = json!(-1),
            "bad-parent" => cert.nodes[1]["parent"] = json!("bad"),
            "open-final" => cert.nodes[0]["final"] = Value::Null,
            "open-split" => cert.nodes[0]["split"] = Value::Null,
            "angle-point" => cert.nodes[0]["split"] = json!({"angle":[0,"100/1"]}),
            "child-state" => cert.nodes[1]["windows"] = json!([[999, "0/1", "1/1"]]),
            "complete" => cert.manifest["summary"]["complete"] = json!(false),
            "header" => cert.manifest["header"]["cap"] = json!("999/1"),
            "trig" => {
                cert.write(
                    "bad-trig",
                    &json!({"trig":{"0/1":["0/1","0/1","0/1","0/1","0/1","0/1"]}}),
                );
                cert.manifest["trig"] = json!("bad-trig");
            }
            "chunk-error" => {}
            _ => unreachable!(),
        }
        cert.save(false);
        if case == "chunk-error" {
            fs::write(cert.directory.join("stream-test-0.json.gz"), b"broken gzip")
                .expect("valid regression fixture and verifier output");
        }
        compare(&cert.directory, false, true, 2);
    }
}

#[test]
fn v3_schema_helpers_and_all_summary_counters_fall_back() {
    for case in [
        "schema",
        "angle-final",
        "angle-split",
        "split-kind",
        "target-helper",
        "nodes",
        "leaves",
        "tighten_nodes",
        "angle_leaves",
        "widen_eliminated",
        "drop_window",
    ] {
        let mut cert = Certificate::new("v3-tighten");
        match case {
            "schema" => cert.manifest["schema"] = json!("unsupported"),
            "angle-final" => cert.nodes[1]["final"] = Value::Null,
            "angle-split" => cert.nodes[1]["split"] = json!({"angle":[0,"1/1"]}),
            "split-kind" => cert.nodes[0]["split"]["unknown"] = json!(1),
            "target-helper" => cert.nodes[0]["split"]["tighten"] = json!([]),
            "widen_eliminated" => cert.nodes[0]["split"]["tighten"][0][0][2] = json!("100/1"),
            "drop_window" => cert.nodes[1]["windows"] = json!([[0, "0/1", "1/1"]]),
            key => cert.manifest["summary"][key] = json!(999),
        }
        cert.save(false);
        compare(&cert.directory, true, true, 2);
    }
}

#[test]
fn parent_metadata_survives_chunk_boundaries_and_sparse_ids() {
    for fixture in ["small-certificate", "v3-tighten"] {
        let mut cert = Certificate::new(fixture);
        for node in &mut cert.nodes {
            node["id"] = json!(
                u64::MAX
                    - node["id"]
                        .as_u64()
                        .expect("valid regression fixture and verifier output")
            );
            if let Some(parent) = node["parent"].as_u64() {
                node["parent"] = json!(u64::MAX - parent);
            }
        }
        cert.save(true);
        let receipt = compare(&cert.directory, fixture.starts_with("v3"), false, 2);
        assert_eq!(receipt["status"], "PASS");
        // The root has been retired in an earlier chunk: a later extra child
        // must fall back, even though the classic available set keeps open IDs.
        let mut extra = cert.nodes.last().expect("last node").clone();
        extra["id"] = json!(0);
        extra["parent"] = cert.nodes[0]["id"].clone();
        cert.nodes.push(extra);
        cert.save(true);
        compare(&cert.directory, fixture.starts_with("v3"), true, 2);
    }
}

#[test]
fn stream_refuses_sample_mode() {
    let output = Command::new(env!("CARGO_BIN_EXE_n17bb-verify"))
        .arg(fixtures().join("small-certificate"))
        .args(["--stream", "--node-ids", "unused.json"])
        .output()
        .expect("valid regression fixture and verifier output");
    assert_eq!(output.status.code(), Some(2));
    assert!(
        String::from_utf8(output.stderr)
            .expect("valid regression fixture and verifier output")
            .contains("--stream cannot be combined with --node-ids")
    );
}
