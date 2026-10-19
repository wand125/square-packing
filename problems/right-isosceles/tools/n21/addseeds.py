"""Append float_bb seeds ([cx, cy, theta]) to a lp_repair pose file.  Prints the number added.
Usage: python3 addseeds.py poses.json seeds.json"""
import json, os, sys
P, S = sys.argv[1], sys.argv[2]
d = json.load(open(P)); s = json.load(open(S))
d["poses"] += [list(map(float, p)) for p in s]
json.dump(d, open(P + ".tmp", "w")); os.replace(P + ".tmp", P)
print(len(s))
