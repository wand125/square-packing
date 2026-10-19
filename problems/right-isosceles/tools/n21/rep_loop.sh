#!/bin/bash
# screen (inner + wall, 60 angles) <-> monotone repair of n21_fr, scaled to 20.99 after each repair
cd "$(dirname "$0")/.."
cp n21/n21_fr.json n21/rep_cur.json; lists=()
for it in 1 2 3 4 5 6; do
  python3 - <<'PY'
import json
from fractions import Fraction as F
c=json.load(open('n21/rep_cur.json')); t=sum(F(p['w']) for p in c['points']); s=F(2099,100)/t
for p in c['points']: p['w']=str(F(p['w'])*s)
json.dump(c,open('n21/rep_cur_s.json','w'),indent=1); print('total before scaling', float(t))
PY
  python3 n21/inner_screen.py n21/rep_cur_s.json 16 1 n21/is_$it.json | head -1
  python3 n21/wall_screen.py n21/rep_cur_s.json 16 1 n21/ws_$it.json | head -1
  n=$(python3 -c "import json;print(len(json.load(open('n21/is_$it.json')))+len(json.load(open('n21/ws_$it.json'))))"); echo "iter $it bad $n"
  [ "$n" = "0" ] && exit 0
  lists+=(n21/is_$it.json n21/ws_$it.json)
  python3 n21/repair_inside.py n21/n21_fr.json n21/rep_cur.json 1.0 25200 "${lists[@]}" | tail -2
done
