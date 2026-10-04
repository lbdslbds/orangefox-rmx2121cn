# 第一版实机测试

编译产物仍是候选版。此工程不包含自动刷机或格式化脚本。

1. 在刷写前读取并保存**手机当前已安装的 TWRP recovery 分区**，确认文件长度和
   SHA256。本机旧 `platform-tools/recovery.img` 可作对照，不能直接假定是当前安装版本。
   保留可用的 TWRP 回退路径和重要数据备份。
2. 核对 Actions 运行结果、SHA256SUMS.txt、image-check.json 和安装包内的设备断言。
   这版只针对 RMX2121CN 的现有分区布局和 vendor；ROM 冒用的供体型号不是硬件身份。
3. 由当前 TWRP 安装**artifact 解压后内层的 OrangeFox 安装 ZIP**，随后进入 recovery。
   这一步应在候选版通过检查并明确安排实机测试后进行。不要刷写 super、boot、
   preloader、lk、TEE 或修改 vbmeta 来试图解决 recovery 问题。
4. 首次仅测试启动、触摸、亮度、ADB，以及输入锁屏凭据后能否看见内部存储的
   正常目录和一个已知文件。不要用 Format Data 代替解密问题诊断。
5. 再检查 MTP、OTG 和进入/退出 fastbootd。进入 fastbootd 本身不能证明刷写功能，
   先只读取状态。挂载逻辑分区时留意新增的 system_ext/my_manifest/my_bigball。
6. 保存 `/tmp/recovery.log`、`adb logcat -d`、`adb shell dmesg`，记录锁屏凭据类型，
   不公开密码、解密密钥或个人文件内容。原始日志可能包含设备识别信息。

待查：公开树 /data 的 recovery.fstab 使用 f2fs，而 twrp.flags 中仍存在 ext4 和
metadata keydirectory 的历史配置。这版保留上游 baseline；如果出现 0 MB 或解密
错误，结合实际挂载和 Keymaster/TEE 日志定位，不直接更改加密参数。

OrangeFox 官方的安装方法见
https://wiki.orangefox.tech/guides/installing_orangefox 。
