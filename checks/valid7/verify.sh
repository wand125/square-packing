#!/bin/sh
# Re-check the published records of the Valid7 run (release records-v1) and run the mutant tests.
# Run from the repository root after: python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
set -e
PY=${PY:-.venv/bin/python}
URL=${URL:-https://github.com/wand125/valid7-independent-check/releases/download/records-v1}
mkdir -p runs
cd runs
for f in records.sha256 full.jsonl.gz full_b.jsonl.gz; do
  [ -f "$f" ] || curl -fsSL -o "$f" "$URL/$f"
done
if command -v sha256sum >/dev/null 2>&1; then SHA="sha256sum"; else SHA="shasum -a 256"; fi
echo "--- sha256 of the downloaded files"
grep 'jsonl.gz$' records.sha256 | $SHA -c -
echo "--- decompress and check the uncompressed files"
for f in full full_b; do [ -f $f.jsonl ] || gunzip -k $f.jsonl.gz; done
grep 'jsonl$' records.sha256 | $SHA -c -
cd ..
echo "--- check_record.py on both records (tiling of the whole domain, EMPTY leaves, Tier B leaves, rechecks)"
$PY src/check_record.py cover/L4_k02_box7.txt runs/full.jsonl runs/full_b.jsonl --recheck 2000 --recheck-b 300 | tee runs/check.out
grep -q '^RECORD OK$' runs/check.out
echo "--- mutant covers (each must be refused)"
PY=$PY sh tests/run_mutants.sh
echo "verify.sh: done (records OK; inspect the mutant results above: ok False / COUNTEREXAMPLE expected)"
