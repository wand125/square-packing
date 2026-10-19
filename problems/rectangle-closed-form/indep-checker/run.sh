#!/bin/bash
# Runs every chunk of jobs.tsv not yet done, 24 at a time; DONE when every chunk has its out/<name>.json.
set -u
H=${SEAM_WORK:-$PWD}
cd "$H"
mkdir -p out logs
echo "$(date -u '+%F %T') run.sh start pid $$" >> status.log
tr '\n' '\0' < jobs.tsv | xargs -0 -P 24 -n 1 bash "$H/run_one.sh"
n=$(wc -l < jobs.tsv); d=$(ls out/*.json 2>/dev/null | wc -l)
echo "$(date -u '+%F %T') run.sh end: $d of $n chunks" >> status.log
[ "$d" -eq "$n" ] && date -u '+%F %T' > DONE
