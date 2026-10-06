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

Status: correction prepared; replacement build and physical-device validation
pending. Validation must compare the GUI level and charging indicator with
kernel nodes after cold startup and after returning from fastbootd, then confirm
Android still boots. Raw logs remain local. Hardware-key investigation was
deferred at the user's request.
