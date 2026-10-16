#!/bin/sh
# Run the four checks (after ./fetch_inputs.sh) and write their outputs to receipts/. Python 3 standard library only.
set -eu
mkdir -p receipts
python3 checker/k2m4_rect_check.py inputs/K4_k008_family.txt inputs/K4_k008_box9.txt > receipts/k2m4_rect_check.out
python3 checker/validate_rect.py inputs/cf34/interval_0.99_1/family.json > receipts/validate_rect.out
python3 indep-checker/rect_k2m4_indep.py > receipts/rect_k2m4_indep.out
python3 indep-checker/rect_r1r2_indep.py > receipts/rect_r1r2_indep.out
tail -n 1 receipts/k2m4_rect_check.out receipts/validate_rect.out receipts/rect_k2m4_indep.out
grep SUMMARY receipts/rect_r1r2_indep.out
