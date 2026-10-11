#!/usr/bin/env python3
"""Byte-patch MacUsbDisplay mode allowlist (entry idx2 -> 1024x600 preset 0x96).
Usage: python3 patch_table.py <binary-file>  (in place, with pre/post asserts)
Covers x86_64 and arm64 (both slices, universal binary).
"""
import sys
import os

import hashlib

ENTRY = bytes.fromhex("960740057b020004580201147017a000170028000500")
assert len(ENTRY) == 22
KNOWN_STOCK_SHA256 = "6d12a75f99ba413a5a4badeed68721432b426b81b30671340fa9df4191d54521"
X86_TAB = 0xE62D0          # table fileoff, x86_64 slice (slice @0x4000)
ARM_TAB = 0x3279E0         # table abs offset, arm64 slice (slice @2375680)
IDX = 2

OLD_PREFIX = bytes.fromhex("9605")


def patch(path, force=False):
    d = bytearray(open(path, "rb").read())
    slots = {"x86_64": X86_TAB + IDX * 0x16, "arm64": ARM_TAB + IDX * 0x16}
    if all(bytes(d[s:s + 22]) == ENTRY for s in slots.values()):
        print("nothing to do (already patched)")
        return
    digest = hashlib.sha256(d).hexdigest()
    if digest != KNOWN_STOCK_SHA256 and not force:
        raise SystemExit(
            f"unexpected file (sha256 {digest[:16]}...): "
            f"stopping, use --force if you know what you are doing")
    changed = False
    for name, slot in (("x86_64", X86_TAB + IDX * 0x16),
                       ("arm64", ARM_TAB + IDX * 0x16)):
        cur = bytes(d[slot:slot + 22])
        if cur == ENTRY:
            print(f"{name}: already patched, skipping")
            continue
        assert cur.startswith(OLD_PREFIX), f"{name}: expected idx2 2560x1440, found {cur.hex()}"
        d[slot:slot + 22] = ENTRY
        changed = True
        print(f"{name}: patched @{slot:#x}")
    if not changed:
        print("nothing to do (already patched)")
        return
    open(path, "wb").write(d)

    # archive a copy in Documents right after patching
    import datetime
    import shutil
    arch = os.path.expanduser("~/Documents/MSDisplayDriverBackup")
    os.makedirs(arch, exist_ok=True)
    tag = datetime.date.today().strftime("%Y%m%d")
    base = os.path.basename(path)
    shutil.copy(path, os.path.join(arch, f"{base}.{tag}"))
    orig = path + ".orig"
    if os.path.isfile(orig):
        shutil.copy(orig, os.path.join(arch, os.path.basename(orig) + f".{tag}"))
    print(f"archived in {arch}/")
    shutil.copy(os.path.abspath(__file__), os.path.join(arch, "patch_table.py"))
    with open(os.path.join(arch, "Readme.txt"), "w") as f:
        f.write(
            f"1024x600 MacUsbDisplay patch ({tag})\n"
            f"patched source: {os.path.abspath(path)}\n"
            f"install target: /Applications/MSDisplayManager.app/Contents/Resources/MacUsbDisplay\n"
            f"original backup: {os.path.abspath(orig)}\n"
            f"allowlist entry idx2 -> 1024x600@60 preset 0x96 (x86_64+arm64)\n"
            f"manual reinstall: sudo cp {base}.{tag} "
            f"/Applications/MSDisplayManager.app/Contents/Resources/MacUsbDisplay && "
            f"sudo codesign -s - -f /Applications/MSDisplayManager.app/Contents/Resources/MacUsbDisplay\n"
            f"restore: sudo cp {os.path.basename(orig)}.{tag} "
            f"/Applications/MSDisplayManager.app/Contents/Resources/MacUsbDisplay\n"
        )
    print("Readme.txt + script archived")


if __name__ == "__main__":
    import subprocess
    default = "/Applications/MSDisplayManager.app/Contents/Resources/MacUsbDisplay"
    arg = sys.argv[1] if len(sys.argv) > 1 else default
    if not os.path.isfile(arg):
        try:
            out = subprocess.run(["mdfind", "-name", "MacUsbDisplay"],
                                 capture_output=True, text=True, timeout=30).stdout
            cand = [l for l in out.splitlines()
                    if l.endswith("MSDisplayManager.app/Contents/Resources/MacUsbDisplay")]
            if cand:
                arg = cand[0]
                print(f"found: {arg}")
        except Exception as e:
            print(f"search failed: {e}")
    patch(arg, force="--force" in sys.argv)
