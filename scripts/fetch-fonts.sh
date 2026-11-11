#!/usr/bin/env bash
# Regenerate the self-hosted woff2 set from Fontsource (GDPR-clean, no Google CDN).
# Run when you want to add weights/subsets. Requires node/npm.
set -euo pipefail
DEST="$(cd "$(dirname "$0")/.." && pwd)/static/fonts"
TMP="$(mktemp -d)"; cd "$TMP"
npm pack @fontsource/dm-sans@5 @fontsource/cormorant-garamond@5 >/dev/null
for t in *.tgz; do tar -xzf "$t"; done
mkdir -p "$DEST"
for w in 400 500 600 700; do
  cp "package/files/dm-sans-latin-$w-normal.woff2"     "$DEST/"
  cp "package/files/dm-sans-latin-ext-$w-normal.woff2" "$DEST/"
done
cp package/files/cormorant-garamond-latin-600-normal.woff2     "$DEST/"
cp package/files/cormorant-garamond-latin-ext-600-normal.woff2 "$DEST/"
rm -rf "$TMP"
echo "Fonts refreshed in $DEST"
