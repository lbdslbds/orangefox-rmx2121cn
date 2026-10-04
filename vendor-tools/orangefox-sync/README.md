# Sync OrangeFox sources

## Fetch the sync tools

```sh
mkdir -p ~/OrangeFox_sync
cd ~/OrangeFox_sync
git clone https://gitlab.com/OrangeFox/sync.git
cd sync
```

SSH may also be used to fetch these tools: `git clone git@gitlab.com:OrangeFox/sync.git`.

Supported `--branch` values are `16.0`, `14.1` (experimental), and `12.1`.
Always supply an absolute checkout path to `--path`.

## Android 16: complete no-WLAN manifest

Use a new checkout for Android 16 rather than reusing a patched 12.1/14.1 tree:

```sh
cd ~/OrangeFox_sync/sync
./orangefox_sync.sh --branch 16.0 --path ~/fox_16.0
```

This uses `https://gitlab.com/OrangeFox/Manifest.git`, branch `fox_16.0`.
The script runs `repo init` and `repo sync` only: it does not apply local patches,
replace recovery projects, or clone additional repositories after syncing. It
never uses `--force-sync` on this route and stops with an error if init or sync
fails. Resolve the reported error before rerunning it; do not ignore sync errors.
The legacy `--ssh`/`USE_SSH` options do not change manifest project remotes.

The manifest owns the complete checkout, including:

- Official OrangeFox recovery (`OrangeFox/bootable/Recovery`, `fox_16.0`).
- Official OrangeFox vendor tree (`OrangeFox/vendor/recovery`, `main`).
- Required build dependencies, including foxcli and libvterm, with USB video retained.
- The Mondrian device tree at `device/xiaomi/mondrian` and its required common dependencies.

This release excludes WLAN, web-interface, and NAS dependencies. Do not add the
old WLAN projects or run the legacy post-sync patches/clones. Mondrian is already
included; no separate device-tree clone is needed.

The equivalent direct manifest workflow is:

```sh
mkdir -p ~/fox_16.0
cd ~/fox_16.0
repo init --depth=1 -u https://gitlab.com/OrangeFox/Manifest.git -b fox_16.0
repo sync -c -j4 --no-clone-bundle --no-tags
```

### Build Mondrian

After a successful sync and with the build-host prerequisites installed:

```sh
cd ~/fox_16.0
export FOX_BUILD_DEVICE=mondrian
source build/envsetup.sh
lunch twrp_mondrian-bp2a-eng
mka recoveryimage
```

### Update Android 16

```sh
cd ~/fox_16.0
repo sync -c -j4 --no-clone-bundle --no-tags
```

Or use the update helper:

```sh
~/OrangeFox_sync/sync/update_fox.sh --path ~/fox_16.0
```

The helper checks effective manifest ownership of `bootable/recovery` and
`vendor/recovery`, then uses `repo sync` for manifest-managed checkouts. It does
not run individual `git pull` commands on repo's detached project HEADs, and it
stops with an error if syncing fails. These rules also apply when the checkout
has a different directory name.

## Legacy Android 12.1 / 14.1: patched minimal manifests

These branches retain the existing minimal-manifest patching and separate
OrangeFox project-cloning workflow. For example:

```sh
cd ~/OrangeFox_sync/sync
./orangefox_sync.sh --branch 12.1 --path ~/fox_12.1
```

Substitute `14.1` and a separate destination for the experimental 14.1 branch.
Syncing can take a long time and requires substantial disk space. If syncing
gets stuck, interrupt it with Ctrl-C and rerun the script. To use SSH for the
separately cloned OrangeFox recovery and vendor projects, export `USE_SSH=1` or
pass `--ssh 1`. After the initial sync, clone your device trees before building.

### Update legacy checkouts

The helper retains the legacy `repo sync` plus individual project `git pull`
workflow:

```sh
~/OrangeFox_sync/sync/update_fox.sh --path ~/fox_12.1
```

To update manually:

```sh
cd ~/fox_12.1
repo sync # Legacy only: ignore errors relating to android_bootable_recovery.
cd bootable/recovery
git pull
cd ../../vendor/recovery
git pull
```

To update only the legacy recovery or vendor tree, run `git pull` in the
corresponding directory. To update only the legacy manifest projects, run
`repo sync` at the checkout root. Do not use these individual-project update
instructions for Android 16.

## Help and build prerequisites

```sh
cd ~/OrangeFox_sync/sync
./orangefox_sync.sh --help
./update_fox.sh --help
```

For build-host prerequisites and general build instructions, see
<https://wiki.orangefox.tech/en/dev/building>.
