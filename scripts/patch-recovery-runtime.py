"""Run ROM property setup before DE keys and remove duplicate fastboot USB actions."""
import hashlib
import json
import pathlib
import sys

ROOT = pathlib.Path(sys.argv[1])
EXPECTED = {
    "partitionmanager.cpp": "12105816ea9d1f4aa8dc3621b41737584de7c698f02bbaff70a0d1495a772aaa",
    "etc/init.rc": "d6eb97edb36a2af18b9243df3cce976745ad0a35c0e8edd1072fb29ca1eb07a8",
}


def read_source(name):
    data = (ROOT / name).read_bytes().replace(b"\r\n", b"\n")
    if name in EXPECTED and hashlib.sha256(data).hexdigest() != EXPECTED[name]:
        raise ValueError("Upstream runtime source changed; review patch: " + name)
    return data.decode()


partition = read_source("partitionmanager.cpp")
anchor = "void TWPartitionManager::Setup_Fstab_Partitions(bool Display_Error) {\n"
if partition.count(anchor) != 1:
    raise ValueError("Missing pre-decryption hook anchor")
partition = partition.replace(anchor, anchor + '''        // RMX2121: the current ROM's Keymaster version/SPL must be configured
        // before Partition_Post_Processing attempts systemwide DE keys.
        if (TWFunc::Exec_Cmd("/system/bin/sh /system/bin/rmx2121-keymaster-props.sh") != 0) {
            LOGERR("RMX2121: could not prepare Keymaster ROM properties\\n");
        }
''')
(ROOT / "partitionmanager.cpp").write_bytes(partition.encode())

init = read_source("etc/init.rc")
blocks = [
    "on property:sys.usb.config=fastboot\n    start fastbootd\n",
    '''on property:sys.usb.config=fastboot && property:sys.usb.ffs.ready=1 && property:sys.usb.configfs=1
    write /config/usb_gadget/g1/idProduct 0x4EE0
    write /config/usb_gadget/g1/configs/b.1/strings/0x409/configuration "fastboot"
    symlink /config/usb_gadget/g1/functions/ffs.fastboot /config/usb_gadget/g1/configs/b.1/f1
    write /config/usb_gadget/g1/UDC ${sys.usb.controller}
    setprop sys.usb.state ${sys.usb.config}
''',
]
original_init_hash = hashlib.sha256(init.encode()).hexdigest()
for block in blocks:
    if init.count(block) != 1:
        raise ValueError("Fastboot init changed upstream; review duplicate removal")
    init = init.replace(block, "# RMX2121 fastboot action supplied once by device init.\n")
(ROOT / "etc/init.rc").write_bytes(init.encode())
print(json.dumps({
    "partitionmanager_upstream_sha256": EXPECTED["partitionmanager.cpp"],
    "partitionmanager_patched_sha256": hashlib.sha256(partition.encode()).hexdigest(),
    "init_upstream_sha256": original_init_hash,
    "init_patched_sha256": hashlib.sha256(init.encode()).hexdigest(),
    "changes": ["ROM properties before DE initialization", "single device fastboot USB action"],
    "device_test_passed": False,
}, indent=2))
