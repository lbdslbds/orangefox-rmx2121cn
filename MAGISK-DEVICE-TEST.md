# Built-in Magisk addon correction (2026-10-07)

The physical device's built-in installer points to
`/sdcard/Fox/FoxFiles/Magisk.zip`, but that file and `uninstall.zip` were missing.
Build 7's image contains magiskboot, which is a boot-image tool rather than the
Magisk installer. The installer addon exists only in the OrangeFox installation
ZIP. Prior device testing installed the recovery image directly and did not run
the ZIP installer, so the addon files were never deployed.

The current device's missing addon files were restored using the unmodified
official Magisk 30.7 APK (ZIP format), SHA256
`e0d32d2123532860f97123d927b1bb86c4e08e6fd8a48bfc6b5bee0afae9ebd5`.
Both installed package files match the official release asset digest. This only
deploys addon files; it does not execute Magisk or modify boot.

The persistent correction enables `FOX_MOVE_MAGISK_INSTALLER_TO_RAMDISK=1` and
pins the official package with `FOX_USE_SPECIFIC_MAGISK_ZIP`. The built-in GUI
then uses `/FFiles/OF_Magisk`, making the installer available after image-only
installation and independent of external FoxFiles. Source/image checks require
the pinned package, GUI path and uninstall alias.

After deployment the user reached the built-in installer, then reported a ZIP
signature error. Logs show `tw_signed_zip_verify=1` and OTA-key verification
failure before executing the installer. The boot partition hash still matches
its pre-test backup. The official APK is not an OTA ZIP signed with the ROM's
OTA keys.

The installer correction authenticates only the built-in ramdisk Magisk install
and uninstall paths against the pinned official package size and SHA256. It
hashes the same mapped package used by the installer. Tampered bundles are
rejected even with ordinary signature verification disabled. The user setting
and normal ZIP/OTA verification remain unchanged. Native C++ tests accept the
official asset and reject altered, truncated and unreadable content plus
non-built-in or external paths.

Status: current addon files restored; rebuilt-image and device tests pending.
Actual root installation is not yet tested. Existing recovery-only
testing scope does not authorize running an installer that writes boot. Battery,
atomic DRM, decryption and USB fixes are retained. Raw device logs remain local.

Official package/source: [Magisk v30.7](https://github.com/topjohnwu/Magisk/releases/tag/v30.7).
Magisk documents recovery installation as a deprecated method that requires a
boot ramdisk: [official installation documentation](https://topjohnwu.github.io/Magisk/install.html).
