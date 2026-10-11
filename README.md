# MSDisplay 1024x600 native (macOS)

USB display `345f:9132` (MacroSilicon MS912x chip, `070-USB-LCD` 1024x600 panel)
used on macOS with the official `MSDisplayManager` / `MacUsbDisplay` v3.3.9.70 driver.

## Problem

The driver only offers up to 800x600: its internal mode allowlist lacks the native
1024x600, and the EDID filter drops the native DTD (range descriptor inconsistent
with the real timing). The chip stays armed at 800x600.

## Solution

One allowlist entry (the useless 2560x1440 mode) is replaced with the native timing
`1024x600 / 1344x635 @60Hz` (chip preset `0x96`, derived from the device's flash
`CONFIG.INI`). 26 bytes total, 13 per slice (x86_64 + arm64).
The display flash is untouched; only the local driver file changes,
with backup and ad-hoc signing.

## Requirements

- Intel or Apple Silicon Mac, MacroSilicon driver installed
- Python3, signing tools present (Xcode CLT: `xcode-select --install`)
- `sudo`

## Reference driver

- File: `MacroSilicon_UsbDisplay_V3.3.9.70_20260827_1353.pkg`
- URL: `http://www.macrosilicon.com/download/USBDisplay/macOS/Installer/MacroSilicon_UsbDisplay_V3.3.9.70_20260827_1353.pkg`
- SHA256 pkg: `7114ff7f08bd30e801ac3803e4747c1475eeea2d307405a20703314a186728a6`
- SHA256 inner `MacUsbDisplay`: `6d12a75f99ba413a5a4badeed68721432b426b81b30671340fa9df4191d54521`

Use this file: the patch looks for exact bytes other versions may not have.

## What the patch changes (26 bytes)

In the internal mode allowlist (a table of 20 entries of 22 bytes, present in both
the x86_64 and arm64 slices) entry 2 (`2560x1440`, useless on this panel) is
replaced with native. Entry layout, little-endian:

| Byte | Field | Our value | Notes for other resolutions |
|---|---|---|---|
| 0 | chip mode preset | `0x96` | from `CONFIG.INI` (VIC) or standard table |
| 1 | polarity | `0x07` | bit0 progressive, bit1 H+, bit2 V+ |
| 2-3 | htotal | 1344 | |
| 4-5 | vtotal | 635 | |
| 6-7 | hactive (width) | 1024 | |
| 8-9 | vactive (height) | 600 | |
| 10-11 | pixclk /10kHz | 5121 (=51.21MHz) | must give `pixclk*10k/htotal/vtotal` = refresh |
| 12-13 | vfreq /100Hz | 6000 (=60Hz) | must match the computed refresh |
| 14-15 | hoffset | 160 | back porch + sync |
| 16-17 | voffset | 23 | back porch + sync |
| 18-19 | hsync | 40 | |
| 20-21 | vsync | 5 | |

Resulting entry: `96 07 40 05 7B 02 00 04 58 02 01 14 70 17 A0 00 17 00 28 00 05 00`.
For another resolution recompute the fields (same driver validity rules)
and change the table address in `patch_table.py` if another slot is needed.

## From CONFIG.INI to bytes (real example)

```
;            VIC   Polarity    Total        Active      Freq        Offset      Sync
;                             H     V      H    V     clk    V     H     V     H     V
RESOLUTION:  150,     7,     1344, 635,   1024, 600,  5121, 6000,  160, 23,   40,   5
```

| INI value | Meaning | Record byte |
|---|---|---|
| 150 = `0x96` | VIC = chip mode preset | `[0]` |
| 7 = `0x07` | polarity (progressive+H++V+) | `[1]` |
| 1344 | htotal -> `0x40 0x05` | `[2:4]` |
| 635 | vtotal -> `0x7B 0x02` | `[4:6]` |
| 1024 | hactive -> `0x00 0x04` | `[6:8]` |
| 600 | vactive -> `0x58 0x02` | `[8:10]` |
| 5121 | pixclk x10kHz -> `0x01 0x14` | `[10:12]` |
| 6000 | vfreq x100Hz -> `0x70 0x17` | `[12:14]` |
| 160 | hoffset -> `0xA0 0x00` | `[14:16]` |
| 23 | voffset -> `0x17 0x00` | `[16:18]` |
| 40 | hsync -> `0x28 0x00` | `[18:20]` |
| 5 | vsync -> `0x05 0x00` | `[20:22]` |

## Patch install

```bash
sudo ./apply_patch.sh
```

Open `MSDisplayManager`, approve Screen Recording if asked, in
System Settings > Displays select `1024x600` on the USB display.

- Restore binary: `sudo ./restore_orig.sh`
- Full driver removal: `sudo ./uninstall.sh` (backups kept)

Driver updates overwrite the patch: rerun the script.

## Notes

- Never patch with the driver running (apply stops it by itself).
- On Apple Silicon: approve in Privacy and first launch from GUI.
- The display flash is untouched (only Mac RAM + local file).

## Files

- `patch_table.py` - byte patch (idempotent, SHA256 gate, backup to
  `~/Documents/MSDisplayDriverBackup/`)
- `apply_patch.sh` - backup, patch, ad-hoc sign, relaunch driver
- `restore_orig.sh` - restore the original binary
- `uninstall.sh` - remove app, LaunchAgent and preferences

## Credits

Analysis based on the open-source `rhgndf/ms912x` (Linux) driver for the HID
protocol (`0xA6` write, `0xB5` read, `0xF5` flash read) and the UYVY bulk format.