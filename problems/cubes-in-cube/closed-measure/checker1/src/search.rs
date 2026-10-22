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
    let _ = parent;
    (0..6)
        .filter(|&j| n.levels[j] < 50 && root[j].width() > 0.)
        .min_by_key(|&j| (n.levels[j], j))
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
    while out.boxes < 1 {
        let Some(n) = out.frontier.pop() else { break };
        let mut r = bound::bound(&n.bounds(root), true);
        out.boxes += 1;
        if r.reason != Reason::Split {
            out.leaves.push(Leaf { node: n, result: r });
            continue;
        }
        if n.depth() >= depth {
            r.reason = Reason::Unresolved;
            out.unresolved.push(n.clone());
            out.leaves.push(Leaf { node: n, result: r });
            continue;
        }
        if let Some(j) = choose(&n, root, &r) {
            for child in n.children(j).into_iter().rev() {
                out.frontier.push(child);
            }
        } else {
            r.reason = Reason::Unresolved;
            out.unresolved.push(n.clone());
            out.leaves.push(Leaf { node: n, result: r });
        }
    }
    out
}
