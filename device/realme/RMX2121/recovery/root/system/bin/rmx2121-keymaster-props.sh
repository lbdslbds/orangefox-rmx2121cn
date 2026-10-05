#!/system/bin/sh
# Match the installed ROM before any DE key operation; only in-memory props change.
set -eu
rom_prop=/system_root/system/build.prop
mounted_here=0
services_stopped=0
rom_mount=/tmp/rmx2121-romprops
cleanup() {
    if [ "$mounted_here" = 1 ]; then umount "$rom_mount"; fi
}
finish() {
    cleanup
    if [ "$services_stopped" = 1 ]; then
        setprop ctl.start vendor.keymaster-4-1-trustonic
        setprop ctl.start keystore2
    fi
}
trap finish EXIT
if [ ! -r "$rom_prop" ]; then
    mkdir -p "$rom_mount"
    mount -t erofs -o ro /dev/block/mapper/system "$rom_mount" 2>/dev/null ||
        mount -t ext4 -o ro /dev/block/mapper/system "$rom_mount"
    mounted_here=1
    rom_prop="$rom_mount/system/build.prop"
fi
[ -r "$rom_prop" ] || exit 1
read_prop() {
    while IFS= read -r line || [ -n "$line" ]; do
        case "$line" in "$1="*) printf '%s\n' "${line#*=}"; return 0;; esac
    done < "$2"
}
release=$(read_prop ro.build.version.release "$rom_prop")
platform_patch=$(read_prop ro.build.version.security_patch "$rom_prop")
case "$release" in ''|*[!0-9.]*) echo 'RMX2121: unsupported ROM release'; exit 1;; esac
valid_patch() {
    case "$1" in [12][0-9][0-9][0-9]-[01][0-9]-[0-3][0-9]) return 0;; *) return 1;; esac
}
valid_patch "$platform_patch" || exit 1
vendor_patch=''
for vendor_prop in /vendor/build.prop /vendor/etc/build.prop /odm/etc/build.prop; do
    if [ -r "$vendor_prop" ]; then vendor_patch=$(read_prop ro.vendor.build.security_patch "$vendor_prop"); fi
    [ -z "$vendor_patch" ] || break
done
# The tested custom ROM overrides vendor SPL to the platform SPL. Prefer a
# real vendor property when present; this fallback reproduces the proven values.
if [ -z "$vendor_patch" ]; then vendor_patch="$platform_patch"; fi
valid_patch "$vendor_patch" || exit 1
cleanup
mounted_here=0
stop_service() {
    setprop ctl.stop "$1"
    tick=0
    while [ "$tick" -lt 30 ]; do
        [ "$(getprop "init.svc.$1")" != running ] && return 0
        sleep 0.1
        tick=$((tick + 1))
    done
    return 1
}
services_stopped=1
stop_service keystore2
stop_service vendor.keymaster-4-1-trustonic
resetprop -n ro.build.version.release "$release"
resetprop -n ro.build.version.security_patch "$platform_patch"
resetprop -n ro.vendor.build.security_patch "$vendor_patch"
setprop ctl.start vendor.keymaster-4-1-trustonic
setprop ctl.start keystore2
services_stopped=0
sleep 1
echo "RMX2121 Keymaster props: release=$release platform_spl=$platform_patch vendor_spl=$vendor_patch"
