#!/usr/bin/env bash
set -euo pipefail
project_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
target=${1:?Usage: bash scripts/sync-sources.sh /absolute/new/build/directory}
[[ "$target" == /* && "$target" != / ]] || { echo "An absolute build path is required" >&2; exit 1; }
[[ "$(uname -s)" == Linux && "$(uname -m)" == x86_64 ]] || { echo "x86_64 Linux is required" >&2; exit 1; }
(( EUID != 0 )) || { echo "Build as a normal user, not root" >&2; exit 1; }
if [[ -e "$target" ]] && [[ -n "$(ls -A -- "$target")" ]]; then
  echo "Use a new empty build directory. Existing sources will not be overwritten." >&2
  exit 1
fi
command -v repo >/dev/null
cd "$project_dir/vendor-tools/orangefox-sync"
# The bundled official script resolves its patch paths from the current dir.
bash ./orangefox_sync.sh --branch 12.1 --path "$target"
test -f "$target/build/envsetup.sh"
test -f "$target/bootable/recovery/orangefox.mk"
test -d "$target/vendor/recovery"
