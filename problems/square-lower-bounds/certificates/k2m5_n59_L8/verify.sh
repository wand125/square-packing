#!/bin/sh
# Re-check s(59) = 8: fetch Evan Daniel's checkers at a pinned commit (not bundled), verify their hashes,
# check the cover's exact total and D4 invariance, and run the sweeps.
#
#   sh verify.sh <new work directory> [threads] [--full] [--zm]
#
#   default : zmx2 cert --d4                 (6,400 roots; a few minutes on 8 threads)
#   --full  : also zmx2 cert --full          (51,200 roots, no symmetry assumed; ~30 CPU-min)
#   --zm    : also zm_mixed.py --d4 --cert-mode at depth 24 over all 102,400 roots (~126 CPU-h), then the one
#             root it leaves uncertified at depth 24, re-run alone at depth 34 (~1 CPU-h); both checked exactly
#             by check_records.py
#   always  : the shipped zm_mixed records are checked exactly by check_records.py (standard library only)
#
# Needs git, Python 3 with numpy, and Rust >= 1.86 (cargo; set CARGO to choose a toolchain).
set -eu
UPSTREAM_URL=https://github.com/evand/square-packing.git
UPSTREAM_COMMIT=b91d70b6ed314624c1434b628a9c7bf9a132c743
ZMX2_RS=6b7f0f79466bf25c9a85f8fe2f3866de734935f0521ea188136818c2fb5b3fed
ZM_MIXED=ee3e2915349b8795128417bca6414b205d526db9f01f88cd4cd32c32e8d760ac
MIXED_COVER=bb89de15ecf5821dd7e1a36ebab8a50d792a406b7fb0f5cb38059f99ef74aae5
ZEROMARGIN=640fe453c1a32f4aa580ca2b1261c6406923a4d7c131f65604a432c7fc2086ab

HERE=$(cd "$(dirname "$0")" && pwd)
WORK=${1:?usage: sh verify.sh <new work directory> [threads] [--full] [--zm]}
shift
THREADS=8
FULL=0
ZM=0
for arg in "$@"; do
  case "$arg" in
    --full) FULL=1 ;;
    --zm) ZM=1 ;;
    *) THREADS=$arg ;;
  esac
done
CARGO=${CARGO:-cargo}
[ ! -e "$WORK" ] || { echo "refusing existing path: $WORK" >&2; exit 2; }
if command -v sha256sum >/dev/null; then sha() { sha256sum "$1" | cut -d' ' -f1; }; else sha() { shasum -a 256 "$1" | cut -d' ' -f1; }; fi

(cd "$HERE" && if command -v sha256sum >/dev/null; then sha256sum -c SHA256SUMS; else shasum -a 256 -c SHA256SUMS; fi)
COVER="$HERE/n59_mixed_cover_8.txt"

# the shipped zm_mixed records: every root certified at depth 24 except R, whose 6 boxes lie inside R; R at depth 34
python3 "$HERE/check_records.py" "$COVER" "$HERE/zm_mixed_d4/roots.jsonl.gz" "$HERE/zm_mixed_root/roots.jsonl"
# the shipped zmx2 per-root logs: every root present once, uncert 0, capped 0
for spec in zmx2_d4:6400 zmx2_full:51200; do
  python3 - "$HERE/${spec%%:*}/roots_log.txt.gz" "${spec##*:}" <<'PYEOF'
import gzip, re, sys
pat = re.compile(r'ROOT (\d+) pass (\d+) root (\S+) boxes (\d+) cert (\d+) empty (\d+) uncert (\d+) maxdepth (\d+) capped (\d+) ms (\d+)')
rows = [pat.fullmatch(s) for s in gzip.open(sys.argv[1], 'rt').read().splitlines() if s.startswith('ROOT ')]
n = int(sys.argv[2])
assert all(rows) and len(rows) == n and len({(r[1], r[2]) for r in rows}) == n
assert all(int(r[7]) == 0 and int(r[9]) == 0 for r in rows)
print(sys.argv[1].split('/')[-2], f'(shipped): {n} roots, uncertified 0, capped 0')
PYEOF
done

git clone -q "$UPSTREAM_URL" "$WORK/upstream"
git -C "$WORK/upstream" checkout -q "$UPSTREAM_COMMIT"
U="$WORK/upstream/s12"
[ "$(sha "$U/verify2/src/bin/zmx2.rs")" = "$ZMX2_RS" ]
[ "$(sha "$U/search/zm_mixed.py")" = "$ZM_MIXED" ]
[ "$(sha "$U/search/mixed_cover.py")" = "$MIXED_COVER" ]
[ "$(sha "$U/search/zeromargin.py")" = "$ZEROMARGIN" ]
echo "upstream checkers at $UPSTREAM_COMMIT: hashes OK"

# exact total < 59 with the upstream reader
(cd "$U/search" && python3 - "$COVER" <<'EOF'
import sys
from fractions import Fraction
import mixed_cover as MC
cv = MC.load(sys.argv[1])
MC.validate(cv)
t = MC.total(cv)
assert Fraction(t) < 59, t
print('total', t, '=', float(t), '< 59')
EOF
)

"$CARGO" build --release --manifest-path "$U/verify2/Cargo.toml" --bin zmx2 > "$WORK/build.log" 2>&1 || { tail -20 "$WORK/build.log"; exit 1; }
Z="$U/verify2/target/release/zmx2"
"$Z" d4 "$COVER" | tee "$WORK/d4check.log"
grep -q 'invariant' "$WORK/d4check.log"

check_roots() {  # log file, expected number of roots
  python3 - "$1" "$2" <<'EOF'
import re, sys
pat = re.compile(r'ROOT (\d+) pass (\d+) root (\S+) boxes (\d+) cert (\d+) empty (\d+) uncert (\d+) maxdepth (\d+) capped (\d+) ms (\d+)')
rows = [pat.fullmatch(s) for s in open(sys.argv[1]).read().splitlines() if s.startswith('ROOT ')]
n = int(sys.argv[2])
assert all(rows) and len(rows) == n and len({(r[1], r[2]) for r in rows}) == n
assert all(int(r[7]) == 0 and int(r[9]) == 0 for r in rows)
print(f'{n} roots, uncertified 0, capped 0')
EOF
}

"$Z" cert "$COVER" --d4 --threads "$THREADS" --log "$WORK/zmx2_d4.roots" > "$WORK/zmx2_d4.log" 2>&1
tail -2 "$WORK/zmx2_d4.log"
grep -q '^VERIFIED-D4:' "$WORK/zmx2_d4.log" && ! grep -q 'NOT VERIFIED' "$WORK/zmx2_d4.log"
check_roots "$WORK/zmx2_d4.roots" 6400

if [ "$FULL" = 1 ]; then
  "$Z" cert "$COVER" --full --threads "$THREADS" --log "$WORK/zmx2_full.roots" > "$WORK/zmx2_full.log" 2>&1
  tail -2 "$WORK/zmx2_full.log"
  grep -q '^VERIFIED: ' "$WORK/zmx2_full.log" && ! grep -q 'NOT VERIFIED' "$WORK/zmx2_full.log"
  check_roots "$WORK/zmx2_full.roots" 51200
fi

if [ "$ZM" = 1 ]; then
  ZARGS="--d4 --cert-mode --disj --chain-from 0 --pitch 1/20 --ubins 16"
  # 1. all roots at depth 24 (expected: every root certified except R, which leaves 6 boxes inside R)
  (cd "$U/search" && python3 -u zm_mixed.py cert "$COVER" $ZARGS --depth 24 --nproc "$THREADS" \
     --resume "$WORK/zm_all.jsonl" --manifest "$WORK/zm_all_manifest.json") > "$WORK/zm_all.log" 2>&1 || true
  tail -10 "$WORK/zm_all.log"
  # 2. the root R alone at depth 34
  (cd "$U/search" && python3 -u zm_mixed.py cert "$COVER" $ZARGS --depth 34 --nproc 1 \
     --cx-lo 27/20 --cx-hi 7/5 --cy-lo 13/10 --cy-hi 27/20 --u-lo 1/4 --u-hi 9/32 \
     --resume "$WORK/zm_R.jsonl" --manifest "$WORK/zm_R_manifest.json") > "$WORK/zm_R.log" 2>&1
  tail -3 "$WORK/zm_R.log"
  # 3. the same exact check as for the shipped records, on the fresh records
  python3 "$HERE/check_records.py" "$COVER" "$WORK/zm_all.jsonl" "$WORK/zm_R.jsonl"
fi
echo N59_COVER_VERIFIED
