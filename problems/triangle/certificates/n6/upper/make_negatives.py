"""Writes four negative controls from packing.json. Usage: python make_negatives.py"""
import json, copy
from fractions import Fraction as F
d = json.load(open("packing.json"))
def shift(sq, dx, dy):
    return [[[str(F(c[0][0]) + dx), c[0][1]], [str(F(c[1][0]) + dy), c[1][1]]] for c in sq]
def put(name, i, dx, dy):
    e = copy.deepcopy(d); e["squares"][i] = shift(d["squares"][i], dx, dy); json.dump(e, open(name, "w"), indent=1)
put("neg1_outside.json", 0, F(-1, 1000), 0)          # left base square leaves the triangle
put("neg2_overlap.json", 1, F(1, 1000), 0)           # right base square pushed into the pair on the right side
put("neg3_overlap_up.json", 1, 0, F(1, 1000))        # right base square pushed up into the pair on the left side
e = copy.deepcopy(d); v = F(2) - F(1, 1000)          # side shortened by 1/1000
tri = [[["0", "0"], ["0", "0"]], [[str(v), "4/3"], ["0", "0"]], [[str(v / 2), "2/3"], ["2", str(v / 2)]]]
e["container"] = {"kind": "equilateral_triangle", "side": [str(v), "4/3"], "vertices": tri}
json.dump(e, open("neg4_short_side.json", "w"), indent=1)
print("wrote 4 negative controls")
