#!/bin/sh
# Build Evan Daniel's zmx2 at the pinned commit (unmodified) and check cover.txt over the whole D4 domain.
# Usage (from point_n61_L8): sh verify.sh <new work directory> [threads]
# Needs git, Python 3, and Rust >= 1.86 (set CARGO=/path/to/cargo to choose a toolchain).
set -eu
UPSTREAM_URL=https://github.com/evand/square-packing.git
UPSTREAM_COMMIT=6e1223cf7ef2be4c70baaa36c0e7e7197076735a
ZMX2_SOURCE_SHA256=6b7f0f79466bf25c9a85f8fe2f3866de734935f0521ea188136818c2fb5b3fed
HERE=$(cd "$(dirname "$0")" && pwd)
WORK=${1:?usage: sh verify.sh <new work directory> [threads]}
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
"$CARGO" build --release --manifest-path "$V/Cargo.toml" --bin zmx2 > "$WORK/build.log" 2>&1 || { tail -20 "$WORK/build.log"; exit 1; }
Z="$V/target/release/zmx2"
"$Z" d4 "$HERE/cover.txt" | tee "$WORK/d4.log"
grep -q 'invariant' "$WORK/d4.log"
"$Z" cert "$HERE/cover.txt" --d4 --pair-points --threads "$THREADS" --log "$WORK/roots.log" > "$WORK/run.log" 2>&1
tail -2 "$WORK/run.log"
grep -q '^VERIFIED-D4:' "$WORK/run.log"
! grep -q 'NOT VERIFIED' "$WORK/run.log"
python3 - "$WORK/roots.log" <<'PY'
import re, sys
pat = re.compile(r'ROOT (\d+) pass (\d+) root (\S+) boxes (\d+) cert (\d+) empty (\d+) uncert (\d+) maxdepth (\d+) capped (\d+) ms (\d+)')
rows = [pat.fullmatch(s) for s in open(sys.argv[1]).read().splitlines() if s.startswith('ROOT ')]
assert all(rows) and len(rows) == 6400 and len({(r[1], r[2]) for r in rows}) == 6400
assert all(int(r[7]) == 0 and int(r[9]) == 0 for r in rows)
print('ROOTS_OK 6400 roots, uncertified 0, capped 0')
PY
echo N61_POINT_COVER_VERIFIED
