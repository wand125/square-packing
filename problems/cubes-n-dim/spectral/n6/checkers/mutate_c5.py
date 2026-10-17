"""Broken-copy test for check_c5.py: each mutation of the valid C5 tree must be rejected.
usage: python3 -I mutate_c5.py positive_c5_exact_tree.json.gz   (writes temporary files to the current directory)"""
import gzip, json, os, subprocess, sys
from fractions import Fraction as Fr

here = os.path.dirname(os.path.abspath(__file__))
R = json.load(gzip.open(sys.argv[1]))
i = next(k for k, x in enumerate(R) if x[0] == "f")
j = next(k for k, x in enumerate(R) if x[0] == "s" and k > 100)

def m_h(R2): R2[i][1][0] = str(Fr(R2[i][1][0]) + Fr(1, 20))
def m_fa(R2): R2[i] = ["a"]
def m_sa(R2): R2[j] = ["a"]
def m_tr(R2): R2.pop()
def m_edge(R2): R2[0] = ["s", 4, 1]

bad = 0
tests = [("flow parameter changed", m_h), ("flow leaf relabelled analytic", m_fa), ("split replaced by an analytic leaf", m_sa),
         ("missing last record", m_tr), ("first split on a different edge", m_edge)]
for name, mut in tests:
    R2 = json.loads(json.dumps(R)); mut(R2)
    p = "mutated_c5_tree.json.gz"; open(p, "wb").write(gzip.compress(json.dumps(R2).encode()))
    r = subprocess.run([sys.executable, "-I", os.path.join(here, "check_c5.py"), p], capture_output=True, text=True)
    os.remove(p)
    if "PASS" in r.stdout:
        print(f"{name}: ACCEPTED (bad)"); bad += 1
    else:
        print(f"{name}: rejected ({(r.stderr.strip().splitlines() or ['?'])[-1][:80]})")
print(f"{len(tests) - bad} of {len(tests)} broken copies rejected")
sys.exit(1 if bad else 0)
