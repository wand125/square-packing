use crate::{
    bound::{self, Box6, Reason},
    interval::*,
};
use serde::{Deserialize, Serialize};
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Node {
    pub grid: [u64; 6],
    pub levels: [u32; 6],
    pub path: String,
}
impl Node {
    pub fn root() -> Self {
        Self {
            grid: [0; 6],
            levels: [0; 6],
            path: String::new(),
        }
    }
    pub fn depth(&self) -> u32 {
        self.levels.iter().sum()
    }
    pub fn bounds(&self, root: Box6) -> Box6 {
        std::array::from_fn(|j| {
            if self.levels[j] == 0 {
                return root[j];
            }
            let scale = 2f64.powi(-(self.levels[j] as i32));
            let span = I::p(root[j].hi) - I::p(root[j].lo);
            let lo = I::p(root[j].lo) + span * I::p(self.grid[j] as f64 * scale);
            let hi = I::p(root[j].lo) + span * I::p((self.grid[j] + 1) as f64 * scale);
            I::new(lo.lo.max(root[j].lo), hi.hi.min(root[j].hi))
        })
    }
    pub fn children(&self, j: usize) -> [Self; 2] {
        assert!(self.levels[j] < 50);
        std::array::from_fn(|side| {
            let mut n = self.clone();
            n.grid[j] = 2 * n.grid[j] + side as u64;
            n.levels[j] += 1;
            n.path.push(if side == 0 { '0' } else { '1' });
            n
        })
    }
}
pub fn choose(n: &Node, root: Box6, parent: &bound::Result) -> Option<usize> {
    let b = n.bounds(root);
    let reference = bound::bound(&b.map(|v| I::p(v.mid())), false);
    let dominant = (0..3)
        .max_by(|&i, &j| {
            (reference.scores[i] - parent.scores[i])
                .total_cmp(&(reference.scores[j] - parent.scores[j]))
        })
        .unwrap();
    let widths: [f64; 6] = std::array::from_fn(|j| b[j].width() / root[j].width());
    let widest = widths.into_iter().fold(0., f64::max);
    let mut best = None;
    let mut key = (f64::NEG_INFINITY, f64::NEG_INFINITY, -1.);
    for j in 0..6 {
        if n.levels[j] >= 50 || widths[j] < widest / 8. {
            continue;
        }
        let mut score = f64::INFINITY;
        let mut total = f64::INFINITY;
        for child in n.children(j) {
            let r = bound::bound(&child.bounds(root), true);
            if r.reason != Reason::Split {
                continue;
            }
            score = score.min(r.scores[dominant]);
            total = total.min(r.scores.into_iter().fold(f64::NEG_INFINITY, f64::max));
        }
        let candidate = (score, total, widths[j]);
        if candidate > key {
            key = candidate;
            best = Some(j);
        }
    }
    best
}
#[derive(Serialize, Deserialize)]
pub struct Leaf {
    pub node: Node,
    pub result: bound::Result,
}
pub struct Chunk {
    pub frontier: Vec<Node>,
    pub unresolved: Vec<Node>,
    pub leaves: Vec<Leaf>,
    pub boxes: u64,
}
/// Fixed node quota; no wall-clock decisions inside a chunk. Scheduling cannot change receipt order.
pub fn chunk(n: Node, root: Box6, depth: u32) -> Chunk {
    let mut out = Chunk {
        frontier: vec![n],
        unresolved: vec![],
        leaves: vec![],
        boxes: 0,
    };
    while out.boxes < 64 {
        let Some(n) = out.frontier.pop() else { break };
        let r = bound::bound(&n.bounds(root), true);
        out.boxes += 1;
        if r.reason != Reason::Split {
            out.leaves.push(Leaf { node: n, result: r });
            continue;
        }
        if n.depth() >= depth {
            out.unresolved.push(n);
            continue;
        }
        if let Some(j) = choose(&n, root, &r) {
            for child in n.children(j).into_iter().rev() {
                out.frontier.push(child);
            }
        } else {
            out.unresolved.push(n);
        }
    }
    out
}
