"""Reconcile the #413 roster with the upstream admitted ledger and the distance-two tail, using upstream tools only.
  python reconcile_413.py ROWS.json PARTITION.json LEDGER_MAIN.yaml LEDGER_PR404.yaml OUT.json   (from packing/ of upstream main)
ROWS.json: [{"row": n, "cells": [...], "status": "..."}]. Every count is the upstream census's (states of the cover,
D4 orbits by selector.count_orbits); the alive set is the survivors of the ledger's admitted entries."""
import json, sys
import yaml
sys.path.insert(0, ".")
from devtools import census_n17_certified as cen
from devtools import select_n17_sub_patterns as sel
rows = json.load(open(sys.argv[1])); part = json.load(open(sys.argv[2]))
cover = cen.cover_context(); G = cover.geometry.group; names = list(cover.geometry.names)
def admitted(path):
    led = yaml.safe_load(open(path))
    return [(e["name"], cen.class_mask(cover, e["cells"], e["name"]), e["cells"]) for e in led["entries"] if e["status"] == "admitted"]
def alive_after(masks):
    return sel.survivors(cover.states, sorted({i for m in masks for i in sel.orbit(m, G)}))
def contains(big, small):  # some D4 image of `small` lies inside `big` (both as masks)
    return any((big & img) == img for img in sel.orbit(small, G))
main = admitted(sys.argv[3]); pr = admitted(sys.argv[4])
alive_main = alive_after([m for _, m, _ in main]); alive_pr = alive_after([m for _, m, _ in pr])
base_main = cen.count(cover, [m for _, m, _ in main]); base_pr = cen.count(cover, [m for _, m, _ in pr])
tail = [o for o in part["orbits"] if o["distance"] == 2]
assert len(tail) == 95 and sum(o["orbit_size"] for o in tail) == 744, (len(tail), sum(o["orbit_size"] for o in tail))
out = {"base_main": base_main, "base_pr404": base_pr, "admitted_main": len(main), "admitted_pr404": len(pr), "rows": []}
row_masks = []
for r in rows:
    m = cen.class_mask(cover, r["cells"], f"row {r['row']}"); row_masks.append(m)
    canon_cells = [names[i] for i in sel.cells_of(m)]
    rel = []
    for name, e, cells in main:
        a, b = contains(m, e), contains(e, m)
        if a or b: rel.append({"entry": name, "relation": "equal" if a and b else ("row contains entry" if a else "row inside entry")})
    rel_pr = [{"entry": name, "relation": "row contains entry" if contains(m, e) else "row inside entry"}
              for name, e, _ in pr if (name not in {x for x, _, _ in main}) and (contains(m, e) or contains(e, m))]
    hit = [o for o in tail if contains(o["mask"], m)]
    out["rows"].append({**r, "canonical_d4_mask": m, "canonical_cells": canon_cells, "arity": len(canon_cells),
                        "overlap_main": rel, "overlap_pr404_extra": rel_pr,
                        "tail_orbits": len(hit), "tail_states": sum(o["orbit_size"] for o in hit), "tail_masks": [o["mask"] for o in hit],
                        "alone_main": cen.removal(cover, alive_main, m), "alone_pr404": cen.removal(cover, alive_pr, m)})
allm = [m for _, m, _ in main] + row_masks
out["union_main"] = cen.count(cover, allm)
out["union_pr404"] = cen.count(cover, [m for _, m, _ in pr] + row_masks)
tail_any = [o for o in tail if any(contains(o["mask"], m) for m in row_masks)]
out["tail_union"] = {"orbits": len(tail_any), "states": sum(o["orbit_size"] for o in tail_any)}
# rows made redundant by other rows (some D4 image of another row inside it)
for i, r in enumerate(out["rows"]):
    r["contains_other_rows"] = [out["rows"][j]["row"] for j, mj in enumerate(row_masks) if j != i and contains(row_masks[i], mj)]
json.dump(out, open(sys.argv[5], "w"), indent=1)
print(json.dumps({k: v for k, v in out.items() if k != "rows"}))
