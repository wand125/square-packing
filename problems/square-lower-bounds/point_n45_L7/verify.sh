#!/usr/bin/env bash
# Build Evan Daniel's zmx2 at the pinned commit (unmodified) and check cover.txt over the whole D4 domain.
# Usage (from point_n45_L7): bash verify.sh <new work directory> [threads]
# Needs git, Python 3, and Rust >= 1.86 (set CARGO=/path/to/cargo to choose a toolchain).
set -euo pipefail
UPSTREAM_URL=https://github.com/evand/square-packing.git
UPSTREAM_COMMIT=6e1223cf7ef2be4c70baaa36c0e7e7197076735a
ZMX2_SOURCE_SHA256=6b7f0f79466bf25c9a85f8fe2f3866de734935f0521ea188136818c2fb5b3fed
HERE=$(cd "$(dirname "$0")" && pwd)
WORK=${1:?usage: bash verify.sh <new work directory> [threads]}
THREADS=${2:-4}
CARGO=${CARGO:-cargo}
[ ! -e "$WORK" ] || { echo "refusing existing path: $WORK" >&2; exit 2; }
if command -v sha256sum >/dev/null; then sha() { sha256sum "$1" | cut -d' ' -f1; }; else sha() { shasum -a 256 "$1" | cut -d' ' -f1; }; fi

python3 "$HERE/check_cover.py"
git clone -q "$UPSTREAM_URL" "$WORK/upstream"
git -C "$WORK/upstream" checkout -q "$UPSTREAM_COMMIT"
[ "$(git -C "$WORK/upstream" rev-parse HEAD)" = "$UPSTREAM_COMMIT" ]
V="$WORK/upstream/s12/verify2"
[ "$(sha "$V/src/bin/zmx2.rs")" = "$ZMX2_SOURCE_SHA256" ] || { echo "zmx2.rs differs" >&2; exit 1; }
"$CARGO" build --release --manifest-path "$V/Cargo.toml" --bin zmx2 > "$WORK/build.txt" 2>&1 || { tail -20 "$WORK/build.txt"; exit 1; }
Z="$V/target/release/zmx2"
{ echo "upstream $UPSTREAM_COMMIT"; "$CARGO" --version; rustc --version 2>/dev/null || true; uname -sm
  echo "zmx2 binary sha256 $(sha "$Z")"; echo "cover sha256 $(sha "$HERE/cover.txt")"; } | tee "$WORK/toolchain.txt"
# zmx2 exits nonzero when the cover is not D4-invariant; also require the exact success line
"$Z" d4 "$HERE/cover.txt" > "$WORK/d4.txt" 2>&1
cat "$WORK/d4.txt"
grep -q '^D4: measure invariant' "$WORK/d4.txt"
"$Z" cert "$HERE/cover.txt" --d4 --pair-points --threads "$THREADS" --log "$WORK/roots.txt" > "$WORK/run.txt" 2>&1
tail -2 "$WORK/run.txt"
grep -q '^VERIFIED-D4:' "$WORK/run.txt"
! grep -q 'NOT VERIFIED' "$WORK/run.txt"
python3 - "$WORK/roots.txt" <<'PY'
import re, sys
pat = re.compile(r'ROOT (\d+) pass (\d+) root (\S+) boxes (\d+) cert (\d+) empty (\d+) uncert (\d+) maxdepth (\d+) capped (\d+) ms (\d+)')
rows = [pat.fullmatch(s) for s in open(sys.argv[1]).read().splitlines() if s.startswith('ROOT ')]
assert all(rows) and len(rows) == 4900 and len({(r[1], r[2]) for r in rows}) == 4900
assert all(int(r[7]) == 0 and int(r[9]) == 0 for r in rows)
print('ROOTS_OK 4900 roots, uncertified 0, capped 0')
PY
# optional: compare root by root with the shipped reference run (same root set and per-root box counts)
if [ -f "$HERE/reference/roots.txt" ]; then
  python3 - "$HERE/reference/roots.txt" "$WORK/roots.txt" <<'PY'
import re, sys
pat = re.compile(r'ROOT (\d+) pass (\d+) root (\S+) boxes (\d+) cert (\d+) empty (\d+) uncert (\d+)')
def load(p):
    return {(m[1], m[2], m[3]): m.groups()[3:] for m in map(pat.match, open(p)) if m}
a, b = load(sys.argv[1]), load(sys.argv[2])
assert a.keys() == b.keys(), 'root sets differ'
diff = sum(a[k] != b[k] for k in a)
print(f'REFERENCE: {len(a)} roots compared, {diff} with different box counts')
PY
fi
echo N45_POINT_COVER_VERIFIED
