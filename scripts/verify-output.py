"""Check recovery headers and original prebuilt hashes, then collect candidates."""
import gzip
import hashlib
import json
import pathlib
import shutil
import struct
import sys
import zipfile


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
            zip_reports.append({"file": path.name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                                "embedded_image": embedded, "installer_target_markers": markers})
    # Publish to Actions artifacts only after structural checks succeed.
    shutil.copy2(image_path, output / "OrangeFox-RMX2121CN-candidate.img")
    for path in archives:
        shutil.copy2(path, output / path.name)
    report = {"image": image_report, "installers": zip_reports,
              "structural_checks_passed": True, "boot_tested": False,
              "decryption_tested": False, "status": "Unverified test candidate"}
    (output / "image-check.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
