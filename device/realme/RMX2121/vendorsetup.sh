#!/usr/bin/env bash
# OrangeFox candidate for RMX2121CN, legacy FBE v1 / Trustonic 4.1.
# These variables must be exported before lunch and the build command.
export FOX_BUILD_DEVICE=RMX2121
export FOX_TARGET_DEVICES="RMX2121,RMX2121CN"
export FOX_VARIANT=FBEv1-CN
export TARGET_ARCH=arm64
export FOX_VANILLA_BUILD=1
# Keep the built-in addon available after recovery-only image installation.
export FOX_MOVE_MAGISK_INSTALLER_TO_RAMDISK=1
export FOX_USE_SPECIFIC_MAGISK_ZIP="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)/prebuilt/Magisk-v30.7.apk"
export OF_DEFAULT_KEYMASTER_VERSION=4.1
export OF_SCREEN_H=2400
export OF_ALLOW_DISABLE_NAVBAR=0
export OF_DEFAULT_TIMEZONE="CST-8"
# No FOX_AB_DEVICE / FOX_VIRTUAL_AB_DEVICE: this device is A-only.
# Do not add a decryption SDK cutoff: this ROM uses SDK 37 with vendor 31.
