# 首次实机测试（2026-10-05）

测试对象是构建运行 `37208417799` 的 R12.0 候选镜像。

- 已从实际 recovery 分区读取 SHA256，确认与 TWRP 备份一致。
- Bootloader fastboot 可连接，设备已解锁，独立 recovery 分区大小 128 MiB。
- 候选镜像经 fastboot 写入 recovery 后成功启动，ADB root shell 正常；分区哈希与候选一致。
- Windows 枚举到 MTP 接口；尚未验证实际文件传输。
- 用户报告右半屏有画面、左半屏黑色。启动日志报告 1080×2400，使用 atomic DRM 路径。
- 当前 DRM 代码缺少 SDE topology 属性时默认两个 layer mixer，并将每个平面的宽度设为屏幕的一半。该逻辑是半屏异常的优先排查对象。
- TWRP 基线和 OrangeFox 都出现 `fscrypt_initialize_systemwide_keys returned fail`；内部存储常见目录无法读取。没有证明解密成功，也不能把问题归因于 OrangeFox。
- ZIP 的断言只接受 RMX2121，而当前 TWRP 的 ro.product.device 是 RMX2121CN；首次使用镜像测试，没有安装这个 ZIP。
- 半屏问题出现后回刷原 TWRP。未格式化或擦除数据，未刷写 boot、super、vbmeta 等其他分区。

修复候选保留当前 OrangeFox atomic DRM backend：识别 MediaTek 驱动后，选择支持当前 CRTC 的 primary plane，使用全屏宽度，让内核处理硬件 dual-pipe 分割；不套用 SDE 的用户态分平面逻辑。补丁在 `scripts/patch-mtk-drm.py`，按输入源码哈希校验，构建保存补丁后哈希。没有可用主平面时返回失败，允许现有图形层尝试其他 backend。

官方 ZIP 的可接受机型明确限定为 RMX2121/RMX2121CN。这些改动需要重新编译和实机验证。旧 TeamWin DRM 源码只保留作后续对照，当前构建不使用它。

原始日志仅保存在本地，不随公开工程上传。
