#!/bin/bash
# Re-run the whole second check for n = 6.  Usage: ./run_all.sh [JOBS]
# Certificates: ../../certificates/n6 (or set N6_CERTS).  Python: $PYTHON (needs numpy, gmpy2, sympy, mpmath).
set -e
cd "$(dirname "$0")"
PY=${PYTHON:-python3}
J=${1:-6}
C=${N6_CERTS:-../../certificates/n6}
export N6_CERTS=$C
mkdir -p out
WIN=2,23/10,4999/10000,50001/100000
E=1/100000000
$PY cellgrid.py $C/loc3/cert_e1_100.json --n 6 --jobs $J --min-width 1/100000000000 --window $WIN,$E --out out/cert_e1_100.json > /dev/null
$PY sweepwin.py $C/loc3/cert_e1_100.json --window $WIN --E $E --out out/sweepwin_e1_100.json > /dev/null
for c in "cert_w_o1 5" "cert_w_o0_p13_auto 5" "cert_s3u2 4" "cert_o03d 4" "cert_o13b 4"; do
  set -- $c
  $PY cellgrid.py $C/stage2/$1.json --n $2 --jobs $J --out out/$1.json > /dev/null
done
$PY witness.py $C/stage2/cert_w_o1.json --obstacles 1 --D 1/100 --DTH 1/100 --jobs $J --out out/wit_w_o1.json > /dev/null
$PY witness.py $C/stage2/cert_w_o0_p13_auto.json --obstacles 0 --D 1/100 --DTH 1/100 --jobs $J --out out/wit_w_o0_p13_auto.json > /dev/null
$PY witness.py $C/stage2/cert_s3u2.json --obstacles 0,1 --D 41/2500 --DTH 3/250 --jobs $J --out out/wit_s3u2.json > /dev/null
$PY witness.py $C/stage2/cert_o03d.json --obstacles 0,3 --D 41/2500 --DTH 3/250 --jobs $J --out out/wit_o03d.json > /dev/null
$PY witness.py $C/stage2/cert_o13b.json --obstacles 1,3 --D 41/2500 --DTH 3/250 --chain 1:3/250 --jobs $J --out out/wit_o13b.json > /dev/null
$PY lemma2.py --out out/lemma2.json > /dev/null
$PY chain2.py > /dev/null
$PY - <<'PYEND'
import json, glob
for f in sorted(glob.glob('out/*.json')):
    r = json.load(open(f))
    st = r.get('status')
    if st is None and 'L1_pinwheel_C3' in r:
        st = 'see file'
    print(f, st)
PYEND
