# OrangeFox candidate device tree for realme X7 Pro (RMX2121CN)

Status: source preparation only. Not compiled, not boot-tested, not flashable yet.
Base: zeng-github01/android_device_realme_RMX2121, twrp-12.1_cn.
Use the official OrangeFox 12.1 sync process and `twrp_RMX2121-eng`.
See the package-level README for commands and validation status.

The upstream kernel/DTB/DTBO and TEE/keymaster binaries match the existing
local TWRP backup. Upstream init/USB, crypto libraries, security-patch values
and fstab flags are retained as a baseline; this does not prove runtime
decryption of the local Android 17 / Android 12 vendor combination.

Changes: OrangeFox exports, removal of TWRP-only screen offsets, strict
dependency checking, and fstab entries for system_ext/my_manifest/my_bigball.
Original copyright and license notices are preserved.
