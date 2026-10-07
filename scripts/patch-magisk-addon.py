"""Require pinned integrity for bundled Magisk, retain other ZIP signature policy."""
import hashlib
import json
import pathlib
import sys

root = pathlib.Path(sys.argv[1])
path = root / "twrpinstall/twinstall.cpp"
data = path.read_bytes().replace(b"\r\n", b"\n")
expected = "7c7c27e8d7ed0a8f48132482364bf82bed46e3a34be3534c996d0e71aff1686e"
if hashlib.sha256(data).hexdigest() != expected:
    raise ValueError("Upstream installer changed; review bundled Magisk policy")
text = data.decode()
text = text.replace('#include "twinstall.h"\n', '#include "twinstall.h"\n#include "rmx2121_magisk.h"\n')
anchor = '\tif (zip_verify) {\n\t\tgui_msg("verify_zip_sig=Verifying zip signature...");'
if text.count(anchor) != 1:
    raise ValueError("Missing signature policy anchor")
text = text.replace(anchor, '''    // RMX2121: the bundled APK is not signed with the ROM's OTA keys.
    // Authenticate the exact mapped package, without changing user settings.
    if (Rmx2121PinnedMagiskPath(path, DataManager::GetIntValue(FOX_INSTALL_PREBUILT_ZIP) == 1)) {
        if (!Rmx2121VerifyPinnedMagisk(package.get())) {
            gui_err("magisk_integrity_fail=Bundled Magisk integrity verification failed!");
            return INSTALL_CORRUPT;
        }
        gui_msg("magisk_integrity_ok=Bundled Magisk SHA256 verified.");
        zip_verify = 0;
    }

''' + anchor)
path.write_bytes(text.encode())
header = pathlib.Path(__file__).with_name("rmx2121_magisk.h")
(path.parent / header.name).write_bytes(header.read_bytes())
print(json.dumps({"upstream_sha256": expected,
                  "patched_sha256": hashlib.sha256(text.encode()).hexdigest(),
                  "policy_header_sha256": hashlib.sha256(header.read_bytes()).hexdigest(),
                  "ordinary_zip_signature_setting_unchanged": True,
                  "bundled_magisk_integrity_always_required": True,
                  "root_install_tested": False}, indent=2))
