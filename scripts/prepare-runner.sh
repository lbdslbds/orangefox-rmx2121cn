#!/usr/bin/env bash
set -euo pipefail

# Cleanup is intentionally restricted to GitHub's disposable x64 VM.
[[ "${GITHUB_ACTIONS:-}" == true && "${RUNNER_ENVIRONMENT:-}" == github-hosted ]] || {
  echo "Run this script only on a GitHub-hosted Actions runner." >&2
  exit 1
}
[[ "$(uname -s)" == Linux && "$(uname -m)" == x86_64 ]] || exit 1
mkdir -p "$ARTIFACT_DIR"
{ uname -a; free -h; df -h /; } > "$ARTIFACT_DIR/runner-before.txt"

# Fixed paths for unrelated SDKs; no user paths or source directories.
sudo rm -rf -- /usr/share/dotnet /usr/local/lib/android /opt/ghc /opt/hostedtoolcache/CodeQL
sudo apt-get clean
sudo apt-get update
sudo env DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
  git-core gnupg flex bison build-essential zip unzip curl ca-certificates \
  zlib1g-dev gcc-multilib g++-multilib libc6-dev-i386 lib32ncurses-dev \
  x11proto-core-dev libx11-dev lib32z1-dev libgl1-mesa-dev libxml2-utils \
  xsltproc fontconfig bc ccache liblz4-tool libncurses-dev libsdl1.2-dev \
  libssl-dev lzop pngcrush schedtool squashfs-tools imagemagick libbz2-dev \
  python3 python-is-python3 openjdk-11-jdk rsync

export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
echo "JAVA_HOME=$JAVA_HOME" >> "$GITHUB_ENV"
mkdir -p "$HOME/bin"
curl --fail --location --retry 3 https://storage.googleapis.com/git-repo-downloads/repo -o "$HOME/bin/repo"
chmod 0755 "$HOME/bin/repo"
echo "$HOME/bin" >> "$GITHUB_PATH"
# Only configure repo's commit identity inside this throwaway VM.
git config --global user.name OrangeFox-CI
git config --global user.email orangefox-ci@example.invalid

# Keep a bounded swap file for memory peaks on standard runners.
[[ ! -e /mnt/orangefox.swap ]] || { echo "Swap path already exists" >&2; exit 1; }
sudo fallocate -l 12G /mnt/orangefox.swap
sudo chmod 0600 /mnt/orangefox.swap
sudo mkswap /mnt/orangefox.swap
sudo swapon /mnt/orangefox.swap
available_kb=$(df -Pk "$GITHUB_WORKSPACE" | awk 'END {print $4}')
if (( available_kb < 55 * 1024 * 1024 )); then
  echo "Insufficient disk after cleanup: need at least 55 GiB for this checkout and build." >&2
  df -h /
  exit 1
fi
{ free -h; df -h / /mnt; java -version; } > "$ARTIFACT_DIR/runner-after.txt" 2>&1
