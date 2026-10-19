#!/bin/bash
# n=21: LP (lp_repair.py, resumable) <-> float_bb over all poses, until float_bb finds no deficit pose.
# Core 0 only, 1 thread.  Rerun after a restart: the LP resumes from lp1_poses.json, finished iterations are skipped.
cd "${RUNDIR:-.}"   # the run directory (a cloud VM in our run)
ulimit -v 8000000
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
R="taskset -c 0 nice -n 10 python3"
for k in $(seq 2 20); do
  [ -e iter$k.done ] && continue
  $R lp_repair.py base_empty.json n21_rep$k.json --rounds 400 --save lp1_state.json --poses-out lp1_poses.json --resume lp1_poses.json >> lp1.log 2>&1 || exit 1
  echo "iter $k float_bb start ep=$(date +%s)" >> fbb.log
  $R float_bb.py n21_rep$k.json seeds$k.json 40 200000 0 >> fbb.log 2>&1 || exit 1
  m=$(python3 addseeds.py lp1_poses.json seeds$k.json)
  echo "iter $k seeds $m ep=$(date +%s)" >> fbb.log
  touch iter$k.done
  if [ "$m" = "0" ]; then cp n21_rep$k.json n21_final.json; touch DONE_LOOP; exit 0; fi
done
