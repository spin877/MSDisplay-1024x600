#!/bin/bash
# Uninstall the MacroSilicon USB display driver.
# Usage: sudo ./uninstall.sh
# Keeps backups in ~/Documents/MSDisplayDriverBackup untouched.
set -u

echo "== stop driver =="
kill $(pgrep -f MacUsbDisplay) $(pgrep -f MSDisplayManager) 2>/dev/null
sleep 2

echo "== remove app and agent =="
rm -rf /Applications/MSDisplayManager.app
rm -f /Library/LaunchAgents/com.macrosilicon.usbdisplay.plist

echo "== remove preferences =="
rm -f "$HOME/Library/Preferences/com.macrosilicon.displaymanager.plist"

echo "== verify =="
pgrep -fl "MacUsbDisplay|MSDisplayManager" && echo "still running: reboot if needed"
ls -d /Applications/MSDisplayManager.app 2>/dev/null && echo "app still present"
ls /Library/LaunchAgents/com.macrosilicon.usbdisplay.plist 2>/dev/null && echo "agent still present"
echo "done. Backups in ~/Documents/MSDisplayDriverBackup are kept."