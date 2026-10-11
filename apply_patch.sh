#!/bin/bash
# Apply the 1024x600 patch to the installed driver (Intel + Apple Silicon).
# Usage: sudo ./apply_patch.sh
set -u
BIN="/Applications/MSDisplayManager.app/Contents/Resources/MacUsbDisplay"
if [ ! -f "$BIN" ]; then
  BIN="$(mdfind -name MacUsbDisplay 2>/dev/null | grep -m1 'MSDisplayManager.app/Contents/Resources/MacUsbDisplay$')"
fi
DIR="$(cd "$(dirname "$0")" && pwd)"
[ -f "$BIN" ] || { echo "driver not installed: $BIN"; exit 1; }

echo "== stop driver =="
kill $(pgrep -f MacUsbDisplay) $(pgrep -f MSDisplayManager) 2>/dev/null
sleep 2

if [ ! -f "$BIN.orig" ]; then
  cp "$BIN" "$BIN.orig" && echo "backup: $BIN.orig"
else
  echo "backup already present"
fi

echo "== archive in Documents =="
ARCH="$HOME/Documents/MSDisplayDriverBackup"
mkdir -p "$ARCH"
VER="$(date +%Y%m%d)"
cp "$BIN.orig" "$ARCH/MacUsbDisplay.orig-$VER" 2>/dev/null
echo "archive: $ARCH/"

echo "== byte patch =="
python3 "$DIR/patch_table.py" "$BIN" || exit 1

echo "== ad-hoc sign =="
codesign -s - -f "$BIN" || { echo "sign failed, restoring"; cp "$BIN.orig" "$BIN"; exit 1; }
codesign -v "$BIN" && echo "SIGN-OK"
cp "$BIN" "$ARCH/MacUsbDisplay.native-1024x600-$VER" 2>/dev/null
echo "patched archived: $ARCH/"

echo "== restart driver =="
open -a MSDisplayManager
echo "done: check System Settings > Displays for the 1024x600 mode"
