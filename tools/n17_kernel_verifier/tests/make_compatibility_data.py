"""Regenerate compatibility tables with CPython 3.14 / Unicode 16 only."""
import json
import random
import re
import struct
import sys
import unicodedata
from pathlib import Path

assert sys.version_info[:2]==(3,14), 'use python3.14'
assert unicodedata.unidata_version=='16.0.0'
CRATE=Path(__file__).resolve().parents[1]
OUT=CRATE/'tests/data'
starts=[n for n in range(0x110000) if unicodedata.decimal(chr(n),None)==0]
p=CRATE/'src/exact.rs'
s=p.read_text()
s=re.sub(r'const STARTS: &\[u32\] = &\[.*?\];', 'const STARTS: &[u32] = &['+', '.join(hex(n) for n in starts)+'];',s,flags=re.S)
p.write_text(s)
ranges=[];start=None
for n in range(0x110000):
    bad=not chr(n).isprintable()
    if bad and start is None:start=n
    if not bad and start is not None:ranges.append((start,n-1));start=None
if start is not None:ranges.append((start,0x10ffff))
s='//! CPython 3.14 / Unicode 16.0.0 non-printable ranges, for str repr only.\n'
s+='pub fn printable(c: u32) -> bool {\n    const RANGES: &[(u32,u32)] = &[\n'
s+=''.join(f'        (0x{a:x},0x{b:x}),\n' for a,b in ranges)
s+='    ];\n    let i=RANGES.partition_point(|&(_,end)|end<c);\n    !RANGES.get(i).is_some_and(|&(start,_)|start<=c)\n}\n'
(CRATE/'src/unicode_repr.rs').write_text(s)
cases=[]
for seed,n,k in [(0,10,5),(1,100,6),(12345,1000,10),(-1,100,6),(2**100+123,40,30),(12345,21,5),(12345,22,5),(987654321,85,6),(987654321,86,6),(42,1000,100),(0,0,0),(7,10,10)]:
    cases.append([str(seed),n,k,random.Random(seed).sample(range(n),k)])
(OUT/'sampling.json').write_text(json.dumps(cases,indent=1)+'\n')
vals=[0.1,1e-5,1e16,1.5e300,-0.0,1e-4,1e15,1e23,2.2250738585072014e-308,5e-324,1.7976931348623157e308,1000000000000000128.0]
rng=random.Random(32810)
for _ in range(4000):
    f=struct.unpack('>d',rng.getrandbits(64).to_bytes(8,'big'))[0]
    if abs(f)!=float('inf') and f==f:vals.append(f)
(OUT/'floats.json').write_text(json.dumps([[struct.pack('>d',f).hex(),repr(f)] for f in vals],indent=1)+'\n')
print(f'CPython {sys.version.split()[0]}: Unicode {unicodedata.unidata_version}; {len(cases)} sampling cases; {len(vals)} finite float cases.')
