"""Writes the five negative controls from n37_packing.json. Usage: python make_negatives.py"""
import json, copy
from fractions import Fraction as F
d = json.load(open("n37_packing.json"))
def shift(sq, dx, dy):
    return [[[str(F(c[0][0]) + dx), c[0][1]], [str(F(c[1][0]) + dy), c[1][1]]] for c in sq]
def put(name, i, dx, dy):
    e = copy.deepcopy(d); e["squares"][i] = shift(d["squares"][i], dx, dy); json.dump(e, open(name, "w"), indent=1)
put("neg1_outside.json", 0, F(-1, 1000), 0)          # bottom-left square leaves the triangle
put("neg2_overlap_row.json", 9, 0, F(-1, 1000))      # second-row square overlaps the bottom row
put("neg4_block.json", 36, 0, F(-1, 100))            # left-block square overlaps its neighbour
put("neg5_rblock.json", 20, 0, F(-1, 100))           # right-block square overlaps its neighbour
e = copy.deepcopy(d); v = F(9) - F(1, 1000)          # side shortened by 1/1000
tri = [[["0", "0"], ["0", "0"]], [[str(v), "2/3"], ["0", "0"]], [[str(v / 2), "1/3"], ["1", str(v / 2)]]]
e["triangle"] = tri; e["side"] = [str(v), "2/3"]
e["container"] = {"kind": "equilateral_triangle", "side": [str(v), "2/3"], "vertices": tri}
json.dump(e, open("neg3_short_side.json", "w"), indent=1)
print("wrote 5 negative controls")
