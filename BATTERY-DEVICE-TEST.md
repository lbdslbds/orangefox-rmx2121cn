# RMX2121CN battery display correction (2026-10-06)

Build 6's core display, decryption, USB and Android boot checks remain valid.
An additional battery check reproduced a separate issue: Android and the kernel
reported 90%, while OrangeFox reported `tw_battery=100` and `100%+`.

The device init stops hwservicemanager after decryption. Health HAL discovery
then fails, and the upstream GUI battery reader substitutes 100% and charging
for an unknown result. The kernel's
`/sys/class/power_supply/battery/capacity` and `status` remain readable and report
the actual level and charging state.

The correction enables the upstream direct sysfs battery reader through
`TW_USE_LEGACY_BATTERY_SERVICES := true`. This changes only the GUI battery
source. The atomic DRM, pre-decryption hook and fastbootd fixes remain intact.
Source and image checks require the direct reader configuration and its compiled
capacity/status paths.

Build: [Actions 7, 37409696589](https://github.com/lbdslbds/orangefox-rmx2121cn/actions/runs/37409696589),
commit `08024619e4771e15a29dc23186c37c59b4113cd0`. The candidate was installed
using bootloader fastboot, writing only recovery; readback partition SHA256
matches the candidate. Offline checks passed. Source commits match build 6.

Cold startup and return from fastbootd each passed six read-only comparisons:
GUI and kernel both reported 100%, and the GUI correctly removed its charging
indicator when the kernel reported `Not charging`. Automatic decryption, MTP
roundtrips, fastbootd read-only queries and return to recovery passed. No manual
USB or decryption modifications were needed.

Status: partial validation. The real battery was fully charged during these
checks, so a below-100% level is still required to prove that the display is no
longer fixed at 100%. The user offered to lower the actual battery for another
test. Android boot completed normally; final display/touch confirmation remains
pending. No fake battery values were injected.

Image SHA256: `0f47ef0d4ed7fbdf7ef71aa01293c31196460ea05cb9b5bb6653e320676ac4e5`.

ZIP SHA256: `8fa1404e48ca4bee483358ab9d40a5f92fea5781c8897b868af15057045d5965`.

Reports: [reports/build-7](reports/build-7). The ZIP installer itself was not
executed. Raw logs remain local. Hardware-key investigation was deferred at the
user's request.
