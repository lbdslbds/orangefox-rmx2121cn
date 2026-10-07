"""Verify kernel, device blobs and partition configuration before building."""
import hashlib
import json
import pathlib
import sys

tree = pathlib.Path(sys.argv[1])
provenance = json.loads(pathlib.Path(sys.argv[2]).read_text(encoding="utf-8"))
checked = []
for item in provenance["boot_components"]:
    paths = {"kernel": "prebuilt/kernel", "dtbo": "prebuilt/dtbo", "dtb": "prebuilt/dtb/mt6889.dtb"}
    path = tree / paths[item["name"]]
    assert hashlib.sha256(path.read_bytes()).hexdigest() == item["sha256"], str(path)
    checked.append(paths[item["name"]])
for item in provenance["binary_comparison"]:
    path = tree / "recovery/root" / item["path"]
    assert hashlib.sha256(path.read_bytes()).hexdigest() == item["sha256"], str(path)
    checked.append("recovery/root/" + item["path"])
board = (tree / "BoardConfig.mk").read_text()
assert "BOARD_RECOVERYIMAGE_PARTITION_SIZE := 134217728" in board
assert "BOARD_BOOT_HEADER_VERSION := 2" in board
assert "TW_INCLUDE_CRYPTO_FBE := true" in board
assert "TW_USE_FSCRYPT_POLICY := 1" in board
assert "TW_USE_LEGACY_BATTERY_SERVICES := true" in board
addon = tree / "prebuilt/Magisk-v30.7.apk"
assert hashlib.sha256(addon.read_bytes()).hexdigest() == "e0d32d2123532860f97123d927b1bb86c4e08e6fd8a48bfc6b5bee0afae9ebd5"
setup = (tree / "vendorsetup.sh").read_text()
assert "export FOX_MOVE_MAGISK_INSTALLER_TO_RAMDISK=1" in setup
assert "prebuilt/Magisk-v30.7.apk" in setup
fstab = (tree / "recovery/root/system/etc/recovery.fstab").read_text()
for name in ("system_ext", "my_manifest", "my_bigball"):
    assert f"{name} /{name} erofs" in fstab
assert "/dev/block/by-name/md_udc /metadata ext4" in fstab
print(json.dumps({"checked_files": len(checked), "checks_passed": True,
                  "compiled": False, "boot_tested": False}, indent=2))
