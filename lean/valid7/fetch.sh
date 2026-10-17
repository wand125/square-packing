#!/bin/bash
# Download the generated Lean sources of valid7-lean-v2 from the release and check every file against
# generated-sources.sha256.
#
#   ./fetch.sh DEST          (DEST: the `lean/` directory of a checkout of the library commit in README)
#
# The sources are unpacked into DEST/Sqpack/V7/.  Nothing is built here; run verify.py next.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
DEST="${1:?usage: fetch.sh LEAN_DIR}"
TAG=valid7-lean-v2
URL="https://github.com/wand125/square-packing/releases/download/$TAG"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
cd "$WORK"
while read -r sum name; do
  curl -fsSL -o "$name" "$URL/$name"
  echo "$sum  $name" | sha256sum -c --quiet -
done < "$HERE/release-assets.sha256"
if compgen -G "v7-sources.tar.zst.part*" > /dev/null; then cat v7-sources.tar.zst.part* > v7-sources.tar.zst; fi
mkdir -p "$DEST/Sqpack/V7"
zstd -dc v7-sources.tar.zst | tar xf - -C "$DEST"
(cd "$DEST" && sha256sum -c --quiet "$HERE/generated-sources.sha256")
echo "fetched and checked: $(wc -l < "$HERE/generated-sources.sha256") files"
