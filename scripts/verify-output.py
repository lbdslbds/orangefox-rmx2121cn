"""Check recovery headers and original prebuilt hashes, then collect candidates."""
import gzip
import hashlib
import json
import pathlib
import re
import shutil
import stat
import struct
import sys
import zipfile


def ramdisk_files(archive):
    files = {}
    pos = 0
    while pos + 110 <= len(archive):
        if archive[pos:pos + 6] not in (b"070701", b"070702"):
            raise ValueError("Invalid newc entry")
        fields = [int(archive[pos + 6 + i * 8:pos + 14 + i * 8], 16) for i in range(13)]
        name = archive[pos + 110:pos + 110 + fields[11] - 1].decode()
        pos = (pos + 110 + fields[11] + 3) & ~3
        contents = archive[pos:pos + fields[6]]
        pos = (pos + fields[6] + 3) & ~3
        if name == "TRAILER!!!":
            return files
        if stat.S_ISREG(fields[1]):
            files[name.removeprefix("./")] = contents
    raise ValueError("Missing newc trailer")


def inspect_runtime(data, expected_script):
    ksize, rsize, page = (struct.unpack_from("<I", data, offset)[0] for offset in (8, 16, 36))
    offset = page + (ksize + page - 1) // page * page
    files = ramdisk_files(gzip.decompress(data[offset:offset + rsize]))
    helper = "system/bin/rmx2121-keymaster-props.sh"
    if files.get(helper) != expected_script:
        raise ValueError("ROM property helper missing or differs from source")
    if ("/system/bin/sh /" + helper).encode() not in files["system/bin/recovery"]:
        raise ValueError("Pre-decryption runtime hook absent from compiled recovery")
    battery_paths = (b"/sys/class/power_supply/battery/capacity",
                     b"/sys/class/power_supply/battery/status")
    if not all(path in files["system/bin/recovery"] for path in battery_paths):
        raise ValueError("Direct battery capacity/status reader absent from recovery")
    generic = files["system/etc/init/hw/init.rc"].decode()
    device_usb = files["init.recovery.usb.rc"].decode()
    device_hal = files["init.recovery.mt6889.rc"].decode()
    if "on property:sys.usb.config=fastboot\n    start fastbootd\n" in generic:
        raise ValueError("Duplicate generic fastboot service action remains")
    if "on property:sys.usb.config=fastboot && property:sys.usb.ffs.ready=1 && property:sys.usb.configfs=1" in generic:
        raise ValueError("Duplicate generic fastboot USB binding remains")
    if device_hal.count("    restart fastbootd\n") != 1:
        raise ValueError("Missing single device fastboot service action")
    if device_usb.count("property:sys.usb.config=fastboot && property:sys.usb.configfs=1") != 1:
        raise ValueError("Missing single device fastboot USB binding")
    fastboot_actions = [block for block in device_usb.split("\non ")
                        if "property:sys.usb.config=fastboot" in block.splitlines()[0]]
    if len(fastboot_actions) != 1 or "write /config/usb_gadget/g1/os_desc/use 0" not in fastboot_actions[0]:
        raise ValueError("Fastboot USB must disable unsupported Microsoft OS descriptors")
    return {"helper_sha256": hashlib.sha256(expected_script).hexdigest(),
            "pre_decryption_hook_present": True, "single_fastboot_usb_action": True,
            "fastboot_ms_os_descriptors_disabled": True,
            "direct_battery_reader_present": True}


def inspect_image(data, provenance):
    if len(data) < 2048 or len(data) > 134217728 or data[:8] != b"ANDROID!":
        raise ValueError("Invalid recovery format or partition size")
    ksize, kaddr, rsize, raddr, ssize, _, tags, page, version, _ = struct.unpack_from("<10I", data, 8)
    if (version, page, kaddr, raddr, tags) != (2, 2048, 1074266112, 1204289536, 1271398400):
        raise ValueError("Recovery header does not match the working TWRP baseline")
    align = lambda n: (n + page - 1) // page * page
    ramdisk_offset = page + align(ksize)
    dtbo_size, dtbo_offset, _ = struct.unpack_from("<IQI", data, 1632)
    dtb_size, dtb_addr = struct.unpack_from("<IQ", data, 1648)
    dtb_offset = ramdisk_offset + align(rsize) + align(ssize) + align(dtbo_size)
    pieces = {"kernel": (page, ksize), "dtbo": (dtbo_offset, dtbo_size), "dtb": (dtb_offset, dtb_size)}
    hashes = {}
    for item in provenance["boot_components"]:
        offset, size = pieces[item["name"]]
        if size <= 0 or offset + size > len(data):
            raise ValueError("Truncated " + item["name"])
        digest = hashlib.sha256(data[offset:offset + size]).hexdigest()
        if digest != item["sha256"]:
            raise ValueError("Unexpected prebuilt " + item["name"])
        hashes[item["name"]] = digest
    if dtb_addr != 1271398400 or ramdisk_offset + rsize > len(data):
        raise ValueError("Invalid DTB address or ramdisk length")
    ramdisk = gzip.decompress(data[ramdisk_offset:ramdisk_offset + rsize])
    if not ramdisk.startswith((b"070701", b"070702")):
        raise ValueError("Expected newc recovery ramdisk")
    if b"OrangeFox" not in ramdisk and b"orangefox" not in ramdisk:
        raise ValueError("OrangeFox branding absent from ramdisk")
    return {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(),
            "header_version": version, "page_size": page, "ramdisk_size": rsize,
            "boot_components": hashes, "orangefox_marker_present": True}


def main():
    product, provenance_path, output = map(pathlib.Path, sys.argv[1:])
    provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
    output.mkdir(parents=True, exist_ok=True)
    image_path = product / "recovery.img"
    if not image_path.exists():
        images = list(product.glob("OrangeFox*.img"))
        if len(images) != 1:
            raise ValueError("Cannot determine the build's recovery image")
        image_path = images[0]
    image_report = inspect_image(image_path.read_bytes(), provenance)
    helper = provenance_path.parent / "device/realme/RMX2121/recovery/root/system/bin/rmx2121-keymaster-props.sh"
    runtime_report = inspect_runtime(image_path.read_bytes(), helper.read_bytes())
    archives = sorted(product.glob("OrangeFox*.zip"))
    if not archives:
        raise ValueError("Official OrangeFox installer ZIP was not generated")
    zip_reports = []
    for path in archives:
        with zipfile.ZipFile(path) as archive:
            bad = archive.testzip()
            if bad:
                raise ValueError("ZIP CRC failure: " + bad)
            names = archive.namelist()
            images = [n for n in names if pathlib.PurePosixPath(n).name == "recovery.img"]
            if len(images) != 1:
                raise ValueError("Expected exactly one recovery.img in " + path.name)
            embedded = inspect_image(archive.read(images[0]), provenance)
            if embedded["sha256"] != image_report["sha256"]:
                raise ValueError("Installer image differs from the output recovery image")
            installer_files = [n for n in names if n.startswith("META-INF/") and n.endswith(("update-binary", "updater-script"))]
            markers = {n: b"RMX2121" in archive.read(n) for n in installer_files}
            if not any(markers.values()):
                raise ValueError("RMX2121 target is absent from the installer scripts")
            installer = archive.read("META-INF/com/google/android/update-binary").decode("utf-8")
            target = re.search(r'^TARGET_DEVICE="([^"]+)"$', installer, re.M)
            alternatives = re.search(r'^TARGET_DEVICE_ALT="([^"]*)"$', installer, re.M)
            if not target or target.group(1) != "RMX2121" or not alternatives:
                raise ValueError("Unexpected installer device assertions")
            accepted = {target.group(1), *re.split(r"[,\s]+", alternatives.group(1))}
            accepted.discard("")
            if accepted != {"RMX2121", "RMX2121CN"}:
                raise ValueError("Installer must accept only RMX2121 and RMX2121CN")
            zip_reports.append({"file": path.name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                                "embedded_image": embedded, "installer_target_markers": markers,
                                "accepted_devices": sorted(accepted)})
    # Publish to Actions artifacts only after structural checks succeed.
    shutil.copy2(image_path, output / "OrangeFox-RMX2121CN-candidate.img")
    for path in archives:
        shutil.copy2(path, output / path.name)
    report = {"image": image_report, "runtime": runtime_report, "installers": zip_reports,
              "structural_checks_passed": True, "boot_tested": False,
              "decryption_tested": False, "status": "Unverified test candidate"}
    (output / "image-check.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
