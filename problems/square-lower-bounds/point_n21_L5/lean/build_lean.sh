#!/bin/sh
# Overlay the point-only n21 Lean files onto Evan Daniel's pinned Lean project and build.
# Usage (from point_n21_L5/lean): sh build_lean.sh <new work directory>
set -eu
UPSTREAM_URL=https://github.com/evand/square-packing.git
UPSTREAM_COMMIT=6e1223cf7ef2be4c70baaa36c0e7e7197076735a
SQPACK_SHA256=094c02f94b50aa123a2be8b61cf1655189f148b7f8f1ef2d6364dcf64b10ab6a
CANDIDATE_SHA256=84a7dae793f05ff72de52ddcd3058e8518c1f84c461f94d11305adefe6137679

HERE=$(cd "$(dirname "$0")" && pwd)
WORK=${1:?usage: sh build_lean.sh <new work directory>}
[ ! -e "$WORK" ] || { echo "refusing existing path: $WORK" >&2; exit 2; }
if command -v sha256sum >/dev/null; then sha() { sha256sum "$1" | cut -d' ' -f1; }; else sha() { shasum -a 256 "$1" | cut -d' ' -f1; }; fi

git clone -q "$UPSTREAM_URL" "$WORK/upstream"
git -C "$WORK/upstream" checkout -q "$UPSTREAM_COMMIT"
[ "$(git -C "$WORK/upstream" rev-parse HEAD)" = "$UPSTREAM_COMMIT" ]
P="$WORK/upstream/s12/lean"
[ "$(sha "$P/Sqpack.lean")" = "$SQPACK_SHA256" ] || { echo "upstream Sqpack.lean differs" >&2; exit 1; }
for f in N21Pts.lean N21PtsAxioms.lean N21PtsData.lean; do
  [ ! -e "$P/Sqpack/$f" ] || { echo "upstream already has $f" >&2; exit 1; }
  cp "$HERE/Sqpack/$f" "$P/Sqpack/$f"
done
cp "$HERE/scripts/gen_n21pts_data.py" "$P/scripts/gen_n21pts_data.py"
printf 'import Sqpack.N21Pts\nimport Sqpack.N21PtsAxioms\n' >> "$P/Sqpack.lean"

CAND="$HERE/../certificates/n21-original.txt"
[ "$(sha "$CAND")" = "$CANDIDATE_SHA256" ]
(cd "$P" && python3 scripts/gen_n21pts_data.py --source "$CAND" --check)
if grep -rn -e 'sorry' -e 'native_decide' -e '^axiom' "$P/Sqpack/N21Pts.lean" "$P/Sqpack/N21PtsData.lean"; then
  echo "forbidden construct in overlay" >&2; exit 1
fi
(cd "$P" && lake exe cache get && lake build) > "$WORK/build.log" 2>&1 || { tail -30 "$WORK/build.log"; exit 1; }
grep -q 'Build completed successfully' "$WORK/build.log"
(cd "$P" && lake env lean Sqpack/N21PtsAxioms.lean) > "$WORK/axioms.log" 2>&1
cat "$WORK/axioms.log"
[ "$(grep -c "depends on axioms: \[propext, Classical.choice, Quot.sound\]" "$WORK/axioms.log")" = 2 ]
echo LEAN_OVERLAY_BUILD_VERIFIED
