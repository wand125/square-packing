#!/bin/bash
# Build the leaf files of one dataset with at most P Lean processes at a time, then the rest.
#
#   scripts/build_data.sh M9 4
#
# Each leaf file takes about 9 GB of memory, and Lake has no option to limit parallel jobs, so the
# leaf modules are built one Lake invocation each.  Run from the lean/ directory.
set -euo pipefail
N=$1
P=${2:-4}
lake build "Sqtri.Data.$N.Base"
ls "Sqtri/Data/$N"/Leaves*.lean | sed -E "s|Sqtri/Data/$N/(Leaves[0-9]+)\.lean|Sqtri.Data.$N.\1|" |
  xargs -P "$P" -I{} lake build {}
lake build "Sqtri.Data.$N.All"
