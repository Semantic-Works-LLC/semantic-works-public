#!/bin/sh
# Builds build/BubbleHead.app with plain swiftc (no Xcode needed).
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"
APP="$HERE/build/BubbleHead.app"

rm -rf "$APP"
mkdir -p "$APP/Contents/MacOS"
swiftc -O -swift-version 5 -o "$APP/Contents/MacOS/BubbleHead" "$HERE"/*.swift
cp "$HERE/Info.plist" "$APP/Contents/Info.plist"
mkdir -p "$APP/Contents/Resources"
cp "$HERE"/assets/* "$APP/Contents/Resources/"

# A real signing identity keeps camera permission across rebuilds; ad-hoc
# signing makes macOS ask again after each build. Set BUBBLEHEAD_IDENTITY
# (e.g. in the git-ignored signing.local.env) or the first one found is used.
[ -f "$HERE/signing.local.env" ] && . "$HERE/signing.local.env"
if [ -z "$BUBBLEHEAD_IDENTITY" ]; then
    BUBBLEHEAD_IDENTITY="$(security find-identity -v -p codesigning 2>/dev/null \
        | grep -E 'Developer ID Application|Apple Development' | head -1 | sed -E 's/.*"(.*)"/\1/')"
fi
codesign --force --options runtime --entitlements "$HERE/entitlements.plist" \
    --sign "${BUBBLEHEAD_IDENTITY:--}" "$APP"
echo "Built $APP"
