#!/bin/sh
# Re-check the published records of the ValidTilt9 run (release records-tilt9-v1).
# Run from the repository root after: python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
# Needs about 6 GB of memory; the Tier B re-certifications take a few minutes each.
set -e
PY=${PY:-.venv/bin/python}
URL=${URL:-https://github.com/wand125/valid7-independent-check/releases/download/records-tilt9-v1}
SEED=${SEED:-}
mkdir -p runs/tilt9
cd runs/tilt9
for f in records.sha256 tilt9_a.jsonl.gz tilt9_b.jsonl.gz tilt9_c.jsonl.gz; do
  [ -f "$f" ] || curl -fsSL -o "$f" "$URL/$f"
done
if command -v sha256sum >/dev/null 2>&1; then SHA="sha256sum"; else SHA="shasum -a 256"; fi
echo "--- sha256 of the downloaded files"
grep 'jsonl.gz$' records.sha256 | $SHA -c -
echo "--- decompress and check the uncompressed files"
for f in tilt9_a tilt9_b tilt9_c; do [ -f $f.jsonl ] || gunzip -k $f.jsonl.gz; done
grep 'jsonl$' records.sha256 | $SHA -c -
cd ../..
echo "--- check_record.py --claim tilt on the three records (tiling of the region, EMPTY leaves, rechecks)"
$PY src/check_record.py cover/K4_k008_box9.txt runs/tilt9/tilt9_a.jsonl runs/tilt9/tilt9_b.jsonl runs/tilt9/tilt9_c.jsonl \
    --claim tilt --recheck 2000 --recheck-b 20 ${SEED:+--seed $SEED} | tee runs/tilt9/check.out
grep -q '^RECORD OK$' runs/tilt9/check.out
echo "verify_tilt9.sh: done (RECORD OK)"
