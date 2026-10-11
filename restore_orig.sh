#!/bin/bash
# Restore the original driver.
# Usage: sudo ./restore_orig.sh
set -u
BIN="/Applications/MSDisplayManager.app/Contents/Resources/MacUsbDisplay"
if [ ! -f "$BIN" ]; then
  BIN="$(mdfind -name MacUsbDisplay 2>/dev/null | grep -m1 'MSDisplayManager.app/Contents/Resources/MacUsbDisplay$')"
fi
[ -f "$BIN.orig" ] || { echo "no backup $BIN.orig"; exit 1; }
kill $(pgrep -f MacUsbDisplay) $(pgrep -f MSDisplayManager) 2>/dev/null
sleep 2
cp "$BIN.orig" "$BIN" && echo "original restored"
open -a MSDisplayManager
