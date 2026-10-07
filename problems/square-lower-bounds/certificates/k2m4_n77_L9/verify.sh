#!/usr/bin/env bash
# Re-check s(77) = 9: fetch Evan Daniel's checkers at a pinned commit (not bundled), verify their hashes,
# check the cover's exact total and D4 invariance, and run the full sweeps.
#
#   bash verify.sh <new work directory> [threads] [--full] [--zm]
#
#   default : zmx2 cert --d4 --pair-points            (8,100 roots; ~20 min on 16 threads)
#   --full  : also zmx2 cert --full --pair-points      (64,800 roots, no symmetry assumed; ~2.5 h)
#   --zm    : also zm_mixed.py cert --d4 --cert-mode   (129,600 roots, exact rationals; ~94 CPU-h)
#
# Needs git, Python 3 with numpy, and Rust >= 1.86 (cargo; set CARGO to choose a toolchain).
set -euo pipefail
UPSTREAM_URL=https://github.com/evand/square-packing.git
UPSTREAM_COMMIT=b91d70b6ed314624c1434b628a9c7bf9a132c743
ZMX2_RS=6b7f0f79466bf25c9a85f8fe2f3866de734935f0521ea188136818c2fb5b3fed
ZM_MIXED=ee3e2915349b8795128417bca6414b205d526db9f01f88cd4cd32c32e8d760ac
MIXED_COVER=bb89de15ecf5821dd7e1a36ebab8a50d792a406b7fb0f5cb38059f99ef74aae5
ZEROMARGIN=640fe453c1a32f4aa580ca2b1261c6406923a4d7c131f65604a432c7fc2086ab

HERE=$(cd "$(dirname "$0")" && pwd)
WORK=${1:?usage: bash verify.sh <new work directory> [threads] [--full] [--zm]}
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
COVER="$HERE/n77_mixed_cover_9.txt"

git clone -q "$UPSTREAM_URL" "$WORK/upstream"
git -C "$WORK/upstream" checkout -q "$UPSTREAM_COMMIT"
U="$WORK/upstream/s12"
[ "$(sha "$U/verify2/src/bin/zmx2.rs")" = "$ZMX2_RS" ]
[ "$(sha "$U/search/zm_mixed.py")" = "$ZM_MIXED" ]
[ "$(sha "$U/search/mixed_cover.py")" = "$MIXED_COVER" ]
[ "$(sha "$U/search/zeromargin.py")" = "$ZEROMARGIN" ]
echo "upstream checkers at $UPSTREAM_COMMIT: hashes OK"

# exact total < 77 with the upstream reader
(cd "$U/search" && python3 - "$COVER" <<'EOF'
import sys
from fractions import Fraction
import mixed_cover as MC
cv = MC.load(sys.argv[1])
MC.validate(cv)
t = MC.total(cv)
assert Fraction(t) < 77, t
print('total', t, '=', float(t), '< 77')
EOF
)

"$CARGO" build --release --manifest-path "$U/verify2/Cargo.toml" --bin zmx2 > "$WORK/build.txt" 2>&1 || { tail -20 "$WORK/build.txt"; exit 1; }
Z="$U/verify2/target/release/zmx2"
{ echo "upstream $UPSTREAM_COMMIT"; "$CARGO" --version; rustc --version 2>/dev/null || true; uname -sm
  echo "zmx2 binary sha256 $(sha "$Z")"; echo "cover sha256 $(sha "$COVER")"; } | tee "$WORK/toolchain.txt"
"$Z" d4 "$COVER" > "$WORK/d4check.txt" 2>&1
cat "$WORK/d4check.txt"
grep -q '^D4: measure invariant' "$WORK/d4check.txt"

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

"$Z" cert "$COVER" --d4 --pair-points --threads "$THREADS" --log "$WORK/zmx2_d4_roots.txt" > "$WORK/zmx2_d4_run.txt" 2>&1
tail -2 "$WORK/zmx2_d4_run.txt"
grep -q '^VERIFIED-D4:' "$WORK/zmx2_d4_run.txt" && ! grep -q 'NOT VERIFIED' "$WORK/zmx2_d4_run.txt"
check_roots "$WORK/zmx2_d4_roots.txt" 8100

if [ "$FULL" = 1 ]; then
  "$Z" cert "$COVER" --full --pair-points --threads "$THREADS" --log "$WORK/zmx2_full_roots.txt" > "$WORK/zmx2_full_run.txt" 2>&1
  tail -2 "$WORK/zmx2_full_run.txt"
  grep -q '^VERIFIED: ' "$WORK/zmx2_full_run.txt" && ! grep -q 'NOT VERIFIED' "$WORK/zmx2_full_run.txt"
  check_roots "$WORK/zmx2_full_roots.txt" 64800
fi

if [ "$ZM" = 1 ]; then
  (cd "$U/search" && python3 -u zm_mixed.py cert "$COVER" --d4 --cert-mode --disj --depth 24 --pitch 1/20 --ubins 16 \
     --nproc "$THREADS" --resume "$WORK/zm_mixed_roots.jsonl" --manifest "$WORK/zm_mixed_manifest.json") > "$WORK/zm_mixed_run.txt" 2>&1
  tail -3 "$WORK/zm_mixed_run.txt"
  grep -q '^VERIFIED-D4' "$WORK/zm_mixed_run.txt" && ! grep -q 'NOT VERIFIED' "$WORK/zm_mixed_run.txt"
fi
echo N77_COVER_VERIFIED
