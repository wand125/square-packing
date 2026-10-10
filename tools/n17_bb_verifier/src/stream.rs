//! PASS-only streaming verification; all irregular input returns to the classic path.
use super::{
    Check, NodeVerifier, Options, array, compact, expected_children, id, index, rational,
    rationals, read_named, state, text,
};
use rayon::prelude::*;
use serde_json::{Value, json};
use std::collections::BTreeMap;
use std::collections::{HashMap, HashSet};
use std::sync::Arc;

struct Live {
    node: Value,
    parent: Arc<Value>,
    depth: usize,
    expected: usize,
    children: Vec<String>,
}

#[derive(Default)]
struct Stream {
    live: HashMap<u64, Live>,
    seen: HashSet<u64>,
    roots: usize,
    closed: u64,
    tightening: u64,
    reasons: BTreeMap<String, u64>,
    max_depth: usize,
    peak_live: usize,
}

fn validate(node: &Value, manifest: &Value) -> Check<()> {
    for key in ["id", "parent", "angles", "windows", "closed"] {
        if node.get(key).is_none() {
            return Err(format!("malformed node: missing {key}"));
        }
    }
    let special = node["closed"] == "angle" || node["split"].get("tighten").is_some();
    if special && manifest["schema"] != "n17-subpattern-bb-certificate/v3" {
        return Err("schema: v3 feature in v1 tree".into());
    }
    if node["closed"] == "angle" && (node["final"].is_null() || !node["split"].is_null()) {
        return Err("T3: angle closure needs final and no split".into());
    }
    if manifest["schema"] == "n17-subpattern-bb-certificate/v3"
        && node["closed"].is_null()
        && !node["split"].is_null()
    {
        let split = node["split"].as_object().ok_or("T2: invalid split kind")?;
        if split.len() != 1
            || !split
                .keys()
                .all(|k| matches!(k.as_str(), "angle" | "pair" | "tighten"))
        {
            return Err("T2: invalid split kind".into());
        }
    }

    Ok(())
}

impl Stream {
    fn arrive(&mut self, node: &Value, manifest: &Value) -> Check<Option<Arc<Value>>> {
        validate(node, manifest)?;
        let ident = id(&node["id"])?;
        if !self.seen.insert(ident) {
            return Err(format!("duplicate node id {ident}"));
        }
        let (depth, parent) = if node["parent"].is_null() {
            self.roots += 1;
            if self.roots != 1 {
                return Err("multiple roots".into());
            }
            (0, None)
        } else {
            let parent_id = id(&node["parent"])?;
            let live = self
                .live
                .get_mut(&parent_id)
                .ok_or("parent not live (unarrived, closed, or already complete)")?;
            let depth = live.depth + 1;
            let parent = Arc::clone(&live.parent);
            live.children
                .push(state(node, live.node["split"].get("angle").is_none())?);
            if live.children.len() > live.expected {
                return Err("too many children".into());
            }
            if live.children.len() == live.expected {
                live.children.sort();
                if live.children != expected_children(&live.node)? {
                    return Err("T2: split children mismatch".into());
                }
            }
            (depth, Some(parent))
        };
        self.max_depth = self.max_depth.max(depth);
        if node["closed"].is_null() {
            if node["split"].is_null() || node["final"].is_null() {
                return Err("T3: open node has no split or final".into());
            }
            if let Some(split) = node["split"].get("angle") {
                let s = index(&split[0])?;
                let interval = array(&node["angles"])?
                    .get(s)
                    .ok_or("angle split index outside node")?;
                let a = rational(&split[1])?;
                let span = rationals::<2>(interval)?;
                if a < span[0] || a > span[1] {
                    return Err("T2: angle split point outside the interval".into());
                }
            }
            // Use the same compact projection as the classic path, including removal of E.
            // Interning is local so no JSON from retired nodes survives in a global arena.
            let mut values = compact::Values::default();
            let compact = compact::Node::new(node, &mut values);
            let retained = compact.json(&values);
            let expected = expected_children(&retained)?.len();
            if expected > 0 {
                self.live.insert(
                    ident,
                    Live {
                        parent: Arc::new(compact.parent(&values)),
                        node: retained,
                        depth,
                        expected,
                        children: vec![],
                    },
                );
                self.peak_live = self.peak_live.max(self.live.len());
            }
        } else {
            self.closed += 1;
            *self
                .reasons
                .entry(text(&node["closed"])?.into())
                .or_default() += 1;
        }
        if node["split"].get("tighten").is_some() {
            self.tightening += 1;
        }
        Ok(parent)
    }

    fn retire_checked(&mut self) {
        self.live
            .retain(|_, node| node.children.len() != node.expected);
    }

    fn finish(&self, manifest: &Value) -> Check<()> {
        if self.roots != 1 {
            return Err("missing root".into());
        }
        if !self.live.is_empty() {
            return Err("pending children at end".into());
        }
        if manifest["schema"] == "n17-subpattern-bb-certificate/v3" {
            for (key, count) in [
                ("nodes", self.seen.len() as u64),
                ("leaves", self.closed),
                ("tighten_nodes", self.tightening),
                ("angle_leaves", *self.reasons.get("angle").unwrap_or(&0)),
            ] {
                if manifest["summary"]
                    .get(key)
                    .is_some_and(|v| *v != json!(count))
                {
                    return Err(format!("summary.{key} mismatch"));
                }
            }
        }
        if manifest["summary"]["complete"] != true {
            return Err("summary.complete is false".into());
        }
        Ok(())
    }
}

impl Drop for Stream {
    fn drop(&mut self) {
        // HashSet uses 8-byte keys plus one control byte per bucket; capacity is
        // 7/8 of bucket count (small tables rounded up). Include the control tail.
        let buckets = (self.seen.capacity() * 8 / 7).next_power_of_two();
        eprintln!(
            "stream stats: peak_live={} seen_ids={} seen_capacity={} seen_bytes_estimate={} nodes={}",
            self.peak_live,
            self.seen.len(),
            self.seen.capacity(),
            buckets * 9 + 16,
            self.seen.len()
        );
    }
}

pub(super) fn check(
    options: &Options,
    manifest: &Value,
    verifier: &NodeVerifier,
    mut counts: BTreeMap<String, u64>,
    receipt: &mut Value,
) -> Check<()> {
    let mut stream = Stream::default();
    let pool = rayon::ThreadPoolBuilder::new()
        .num_threads(options.threads)
        .build()
        .map_err(|e| e.to_string())?;
    for chunk in array(&manifest["chunks"])? {
        let data = read_named(&options.directory, text(chunk)?)?;
        let nodes = array(&data["nodes"])?;
        let parents = nodes
            .iter()
            .map(|node| stream.arrive(node, manifest))
            .collect::<Check<Vec<_>>>()?;
        let results: Vec<_> = pool.install(|| {
            nodes
                .par_iter()
                .zip(&parents)
                .map(|(node, parent)| verifier.check_node(node, parent.as_deref()))
                .collect()
        });
        for (ticks, result) in results {
            result?;
            for (key, count) in ticks {
                *counts.entry(key).or_default() += count;
            }
        }
        // Retire only after every child in this chunk has passed check_node.
        stream.retire_checked();
    }
    stream.finish(manifest)?;
    receipt["nodes"] = json!(stream.seen.len());
    receipt["closed_leaves"] = json!(stream.closed);
    receipt["max_depth"] = json!(stream.max_depth);
    receipt["reasons"] = json!(stream.reasons);
    receipt["checked_nodes"] = json!(stream.seen.len());
    receipt["node_failures"] = json!(0);
    receipt["counts"] = json!(counts);
    receipt["status"] = json!("PASS");
    receipt["failure_count"] = json!(0);
    receipt["failures"] = json!([]);
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    fn tree_nodes() -> Vec<Value> {
        let tree = crate::tree_tests::split_tree();
        tree.index
            .iter()
            .map(|(&id, node)| {
                let mut value = node.json(&tree.values);
                value["id"] = json!(id);
                value["parent"] = if id == 0 { Value::Null } else { json!(0) };
                value
            })
            .collect()
    }

    fn walk(nodes: &[Value]) -> Check<Stream> {
        let mut stream = Stream::default();
        let manifest =
            json!({"schema":"n17-subpattern-bb-certificate/v1", "summary":{"complete":true}});
        for node in nodes {
            stream.arrive(node, &manifest)?;
        }
        stream.retire_checked();
        stream.finish(&manifest)?;
        Ok(stream)
    }

    #[test]
    fn existing_angle_tree_and_sparse_ids() {
        let mut nodes = tree_nodes();
        for right in [2, u64::MAX] {
            nodes[2]["id"] = json!(right);
            let stream = walk(&nodes).expect("partition");
            assert_eq!(stream.closed, 2);
            assert_eq!(stream.max_depth, 1);
            assert_eq!(stream.peak_live, 1);
            assert!(stream.live.is_empty());
        }
        nodes[2]["angles"][0][0] = json!("3/2");
        assert!(walk(&nodes).is_err());
    }

    #[test]
    fn existing_closed_child_and_pair_trees() {
        let mut nodes = tree_nodes();
        let mut child = nodes[1].clone();
        child["id"] = json!(3);
        child["parent"] = json!(1);
        nodes.push(child);
        assert!(walk(&nodes).is_err());
        nodes.pop();
        nodes[0]["windows"] = json!([[12, "0/1", "1/1"], [2, "0/1", "2/1"]]);
        nodes[0]["split"] = json!({"pair":[2,[["0/1","1/1"],["1/1","2/1"]]]});
        for i in 1..=2 {
            nodes[i]["angles"] = nodes[0]["angles"].clone();
            nodes[i]["windows"] = json!([
                [
                    2,
                    if i == 1 { "0/1" } else { "1/1" },
                    if i == 1 { "1/1" } else { "2/1" }
                ],
                [12, "0/1", "1/1"]
            ]);
        }
        assert_eq!(walk(&nodes).expect("numeric pair ordering").closed, 2);
    }

    #[test]
    fn hash_set_sparse_memory_budget() {
        let seen: HashSet<u64> = (0..100_000_u64).map(|i| u64::MAX - i * 1009).collect();
        let buckets = (seen.capacity() * 8 / 7).next_power_of_two();
        assert!(buckets * 9 + 16 < seen.len() * 64);
    }
}
