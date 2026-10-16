#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "$0")/.."
if (( $# > 1 )); then
  echo "Usage: scripts/fetch.sh [local-generated-sources.tar.xz]" >&2
  exit 2
fi
if (( $# == 1 )); then
  exec python3 scripts/sources.py "$1"
fi
asset=generated-sources.tar.xz
url=https://github.com/wand125/square-packing/releases/download/closed-form-lean-layer-a-v1/$asset
trap 'rm -f -- "$asset.part"' EXIT
curl --fail --location --proto '=https' --tlsv1.2 --output "$asset.part" "$url"
python3 scripts/sources.py "$asset.part"
mv -- "$asset.part" "$asset"
