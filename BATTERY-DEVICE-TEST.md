# RMX2121CN battery display correction (2026-10-06)

The battery display fix is verified on this physical device and current custom
ROM. Build 6 reported 100%+ while Android and the kernel reported 89-90%.
After decryption, the device init stops hwservicemanager; Health HAL discovery
fails and the upstream GUI reader substitutes 100% and charging.

Build 7 enables `TW_USE_LEGACY_BATTERY_SERVICES := true`, using the upstream
reader for `/sys/class/power_supply/battery/capacity` and `status`. Atomic DRM,
automatic decryption and fastbootd fixes remain intact. Source and image checks
require the direct reader configuration and compiled paths.

Build: [Actions 7, 37409696589](https://github.com/lbdslbds/orangefox-rmx2121cn/actions/runs/37409696589),
commit `08024619e4771e15a29dc23186c37c59b4113cd0`.

| Test | Result |
| --- | --- |
| Offline image/ZIP checks | Hashes, original kernel/DTB/DTBO, ZIP CRC, embedded image and RMX2121/RMX2121CN assertions passed |
| Recovery-only installation | Readback partition hash matches; other partitions untouched |
| Full battery, cold startup and return from fastbootd | Six samples per phase: GUI and kernel both 100%; false charging indicator removed |
| Actual battery lowered to 98%, cold startup and return from fastbootd | Six samples per phase: GUI and kernel both 98%, charging indicator matches kernel `Not charging`; no fake values injected |
| Display and touch | User confirmed 98% display, full screen, swiping and tapping normal |
| Automatic decryption and ADB | Cold startup and return from fastbootd passed without manual service/property changes |
| MTP | Same build passed download/upload hash checks before and after fastbootd; test files removed |
| Fastbootd | Userspace/product/logical-system/recovery-size queries and return to recovery passed without manual USB changes |
| Android boot | Final `sys.boot_completed=1`, boot mode normal; build 7 retained in recovery |

Image SHA256: `0f47ef0d4ed7fbdf7ef71aa01293c31196460ea05cb9b5bb6653e320676ac4e5`.

ZIP SHA256: `8fa1404e48ca4bee483358ab9d40a5f92fea5781c8897b868af15057045d5965`.

Reports and the 24 battery samples are in [reports/build-7](reports/build-7).
This verifies that the GUI follows real kernel readings; battery calibration and
all other ROM/credential combinations were not tested. The ZIP installer itself
was not executed; its embedded image matches the tested image. Actions annotations
were empty; Android source compiler warnings may remain. Raw device logs remain
local. Hardware-key investigation was deferred at the user's request. Original
TWRP and build 6 recovery backups remain available locally.
