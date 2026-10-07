#!/bin/bash
cd ~/check2
./target/release/hexs2 --cert stage1_cert.json --threads 16 --max-depth 80 --out full.jsonl 2> full.stderr
echo "exit $?" >> full.stderr
./target/release/hexs2 --cert stage1_cert.json --k 1 --threads 1 --max-depth 45 --side-scale 1.01 --no-lemma --out neg.jsonl 2> neg.stderr
echo DONE > done.flag
