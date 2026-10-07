#!/usr/bin/env bash
# Second-system check of a fine-net density certificate with sqverify-fast (proof_net branch).
#
#   fine_net_check.sh BINARY CANDIDATE.json OUTDIR
#
# 1. Runs every direction of the candidate's net (threads = nproc) with --confirm and
#    writes OUTDIR/receipt.json: status, direction count, net, candidate_digest, file and
#    input SHA-256, build digest, seconds. Exit 0 only for VERIFIED.
# 2. Control: the same candidate with every mass times 0.985 (total_mass rescaled), on 32
#    directions spread over the net; it must be REFUSED with an exact counterexample.
#    The control's result is in receipt.json under "control".
# Needs bash, python3 (standard library only) and the built binary.
set -euo pipefail
BIN=$1
CAND=$2
OUT=$3
mkdir -p "$OUT"
THREADS=$(nproc 2>/dev/null || sysctl -n hw.ncpu)

read -r N SIDE COUNT < <(python3 - "$CAND" <<'EOF'
import json, sys
from fractions import Fraction as F
d = json.load(open(sys.argv[1]))
L = F(d["L"])
print(d["n"], f"{L.numerator}/{L.denominator}", d["proof_net"]["last"] + 1)
EOF
)

start=$(date +%s)
set +e
"$BIN" --candidate "$CAND" --n "$N" --side "$SIDE" --directions all \
  --threads "$THREADS" --confirm > "$OUT/run.jsonl" 2> "$OUT/run.stderr"
main_exit=$?
set -e
main_seconds=$(( $(date +%s) - start ))

# Control: masses x 0.985.
python3 - "$CAND" "$OUT/control-mass0985.json" <<'EOF'
import json, sys
from fractions import Fraction as F
d = json.load(open(sys.argv[1]))
for r in d["rectangles"]:
    r["mass"] = str(F(r["mass"]) * F(985, 1000))
for p in d.get("points", []):
    p["mass"] = str(F(p["mass"]) * F(985, 1000))
d["total_mass"] = str(sum(F(x["mass"]) for x in d["rectangles"] + d.get("points", [])))
json.dump(d, open(sys.argv[2], "w"))
EOF
DIRS=$(python3 -c "import sys;c=int(sys.argv[1]);print(','.join(str(round(i*(c-1)/31)) for i in range(32)))" "$COUNT")
set +e
"$BIN" --candidate "$OUT/control-mass0985.json" --n "$N" --side "$SIDE" --directions "$DIRS" \
  --threads "$THREADS" --confirm > "$OUT/control.jsonl" 2> "$OUT/control.stderr"
control_exit=$?
set -e

python3 - "$CAND" "$OUT" "$main_exit" "$main_seconds" "$control_exit" "$COUNT" <<'EOF'
import hashlib, json, sys
cand, out, main_exit, seconds, control_exit, count = sys.argv[1:]
raw = open(cand, "rb").read()
d = json.loads(raw)
key = {k: d[k] for k in ["n", "L", "B", "rectangles", "points", "total_mass", "proof_net"]}
digest = hashlib.sha256(json.dumps(key, sort_keys=True, separators=(",", ":")).encode()).hexdigest()

def rows(path):
    return [json.loads(l) for l in open(path) if l.startswith("{")]

main = rows(f"{out}/run.jsonl")
dirs = [r for r in main if "r" in r]
summary = next((r for r in main if r.get("kind") == "sqverify-fast-summary/v1"), {})
control = rows(f"{out}/control.jsonl")
cdirs = [r for r in control if "r" in r]
csum = next((r for r in control if r.get("kind") == "sqverify-fast-summary/v1"), {})
refusals = [r for r in cdirs if r["verdict"] != "verified"]
receipt = {
    "status": summary.get("status", "ERROR"),
    "exit": int(main_exit),
    "n": d["n"], "L": d["L"], "B": d["B"], "proof_net": d["proof_net"],
    "directions_expected": int(count),
    "directions_checked": len(dirs),
    "directions_verified": sum(r["verdict"] == "verified" for r in dirs),
    "candidate_digest": digest,
    "file_sha256": hashlib.sha256(raw).hexdigest(),
    "input_sha256": summary.get("premises", {}).get("input_sha256"),
    "build": summary.get("build"),
    "seconds": int(seconds),
    "control": {
        "kind": "every mass x 0.985, 32 directions",
        "status": csum.get("status", "ERROR"),
        "exit": int(control_exit),
        "refused_directions": len(refusals),
        "exact_below_threshold": sum(
            bool((r.get("witness") or {}).get("exact_below_threshold")) for r in refusals
        ),
    },
}
ok = (
    receipt["status"] == "VERIFIED"
    and receipt["exit"] == 0
    and receipt["directions_verified"] == receipt["directions_expected"]
    and receipt["control"]["status"] == "REFUSED"
    and receipt["control"]["exact_below_threshold"] > 0
)
receipt["verdict"] = "PASS" if ok else "FAIL"
json.dump(receipt, open(f"{out}/receipt.json", "w"), indent=1)
print(json.dumps({k: receipt[k] for k in ("verdict", "status", "directions_verified", "directions_expected", "candidate_digest", "seconds")}))
print(json.dumps({"control": receipt["control"]}))
sys.exit(0 if ok else 1)
EOF
