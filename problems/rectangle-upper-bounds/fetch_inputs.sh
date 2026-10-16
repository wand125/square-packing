#!/bin/sh
# Fetch the inputs into ./inputs and check their sha256 (run from this folder; needs git, curl, tar, sha256sum).
set -eu
mkdir -p inputs/cf34
if [ ! -d inputs/evand-square-packing ]; then
  git clone --quiet https://github.com/evand/square-packing inputs/evand-square-packing
fi
git -C inputs/evand-square-packing checkout --quiet 2eb15455
cp inputs/evand-square-packing/s12/certificates/k2m4/K4_k008_family.txt inputs/
cp inputs/evand-square-packing/s12/certificates/k2m4/K4_k008_box9.txt inputs/
curl -sSfL -o inputs/cf34/interval_0.99_1.tar.gz \
  https://github.com/wand125/square-packing/releases/download/closed-form-v1/interval_0.99_1.tar.gz
tar xzf inputs/cf34/interval_0.99_1.tar.gz -C inputs/cf34 interval_0.99_1/family.json interval_0.99_1/family_right.json
sha256sum -c inputs.sha256
