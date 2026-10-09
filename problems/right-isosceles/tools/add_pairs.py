"""Add every pair of certificate points at exact distance 1 as a chord pair (Lemma P of the checker).
Usage: python3 add_pairs.py in.json out.json"""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "checker"))
from q2 import Q2
c = json.load(open(sys.argv[1]))
P = [(Q2.parse(p["x"]), Q2.parse(p["y"])) for p in c["points"]]
pairs = []
for i in range(len(P)):
    for j in range(i + 1, len(P)):
        dx, dy = P[j][0] - P[i][0], P[j][1] - P[i][1]
        if dx * dx + dy * dy == Q2(1):
            pairs.append([i, j])
c["pairs"] = pairs
json.dump(c, open(sys.argv[2], "w"), indent=1)
print(len(pairs), "pairs:", pairs)
