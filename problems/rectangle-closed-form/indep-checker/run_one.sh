#!/bin/bash
# One chunk: pair level family record part name est (tab separated). Writes out/<name>.json only when the
# checker finished (exit 0 = all leaves accepted, 1 = a refusal; both are final). Anything else leaves no output.
set -u
H=${SEAM_WORK:-$PWD}
IFS=$'\t' read -r pair lev fam rec part name est <<< "$1"
[ -f "$H/out/$name.json" ] && exit 0
export RAYON_NUM_THREADS=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
echo "$(date -u '+%F %T') start $name" >> "$H/status.log"
nice -n 10 "$H/bin/seamleaf" "$H/inputs/indep_seam_inputs/$fam" "$H/inputs/indep_seam_inputs/$rec" \
  --out "$H/out/$name.json.tmp" --threads 1 --part "$part" > "$H/logs/$name.log" 2>&1
rc=$?
if [ $rc -eq 0 ] || [ $rc -eq 1 ]; then
  mv -f "$H/out/$name.json.tmp" "$H/out/$name.json"
  echo "$(date -u '+%F %T') end $name rc=$rc" >> "$H/status.log"
else
  rm -f "$H/out/$name.json.tmp"
  echo "$(date -u '+%F %T') FAIL $name rc=$rc" >> "$H/status.log"
fi
