#!/usr/bin/env bash
set -eo pipefail
project_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
build_root=${1:?Usage: bash scripts/build.sh /absolute/fox_12.1}
[[ "$build_root" == /* && "$build_root" != / ]] || exit 1
[[ "$(uname -s)" == Linux && "$(uname -m)" == x86_64 ]] || { echo "x86_64 Linux is required" >&2; exit 1; }
(( EUID != 0 )) || { echo "Build as a normal user, not root" >&2; exit 1; }
test -f "$build_root/bootable/recovery/orangefox.mk"
test -d "$build_root/vendor/recovery"
# This MT6889 kernel works with the legacy KMS path; the newer SDE-style
# atomic backend splits the display into planes and rendered only the right half.
legacy_drm="$project_dir/vendor-tools/recovery-legacy-drm/graphics_drm.cpp"
printf '%s  %s\n' c6cfe03470b9b141bfc7659b4e119921878a18c0b59759be96b465bbee272b73 "$legacy_drm" | sha256sum --check --status
cp "$legacy_drm" "$build_root/bootable/recovery/minuitwrp/graphics_drm.cpp"
destination="$build_root/device/realme/RMX2121"
if [[ -e "$destination" ]]; then
  diff -qr "$project_dir/device/realme/RMX2121" "$destination" || {
    echo "Existing device tree differs. Review and update it explicitly." >&2
    exit 1
  }
else
  mkdir -p "$build_root/device/realme"
  cp -a "$project_dir/device/realme/RMX2121" "$destination"
fi
# The upstream files are tracked as 0644; restore executable HAL binaries.
find "$destination/recovery/root/vendor/bin" -type f -exec chmod 0755 {} +
output_dir=${ARTIFACT_DIR:-"$project_dir/artifacts"}
mkdir -p "$output_dir"
python3 "$project_dir/scripts/verify-source.py" "$destination" "$project_dir/provenance.json" > "$output_dir/source-check.json"
cp "$project_dir/vendor-tools/recovery-legacy-drm/PROVENANCE.json" "$output_dir/graphics-source.json"
cd "$build_root"
export FOX_BUILD_DEVICE=RMX2121
export LC_ALL=C
export ALLOW_MISSING_DEPENDENCIES=true
# AOSP envsetup is not compatible with nounset; intentionally leave it off.
set +e
source build/envsetup.sh
envsetup_status=$?
set -e
# envsetup includes optional vendor scripts whose final tests can return 1.
# Check the API we actually need; lunch and compilation still fail normally.
declare -F lunch mka >/dev/null
if (( envsetup_status != 0 )); then
  echo "envsetup returned $envsetup_status; lunch/mka are defined, continuing to lunch."
fi
source "$destination/vendorsetup.sh"
if [[ "${FOX_AB_DEVICE:-0}" != 0 || "${FOX_VIRTUAL_AB_DEVICE:-0}" != 0 || "${FOX_VENDOR_BOOT_RECOVERY:-0}" != 0 ]]; then
  echo "Unexpected A/B or vendor_boot recovery configuration" >&2
  exit 1
fi
unset OF_SKIP_FBE_DECRYPTION OF_SKIP_FBE_DECRYPTION_SDKVERSION
lunch twrp_RMX2121-eng
repo manifest -r -o "$output_dir/manifest.xml"
{
  for path in bootable/recovery vendor/recovery vendor/twrp; do
    printf '%s ' "$path"
    git -C "$path" rev-parse HEAD
  done
} > "$output_dir/source-commits.txt"
env | sort | sed -n '/^FOX_/p; /^OF_/p' > "$output_dir/orangefox-vars.txt"
# Avoid a disk-heavy ccache on standard GitHub runners.
export USE_CCACHE=0
mka adbd recoveryimage -j"${JOBS:-4}"
product="$build_root/out/target/product/RMX2121"
python3 "$project_dir/scripts/verify-output.py" "$product" "$project_dir/provenance.json" "$output_dir"
cp "$project_dir/provenance.json" "$output_dir/provenance.json"
cp "$project_dir/TESTING.md" "$output_dir/TESTING.md"
(cd "$output_dir" && sha256sum ./*.img ./*.zip > SHA256SUMS.txt)
