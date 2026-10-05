# 新版 atomic DRM 测试（2026-10-05）

构建 `37269606683`，镜像 SHA256 `332fa1b5d4c6587bed9ce28ddde0b4fcbac064ef9ee35742604b0e0cb0dc34ab`。

- 新版 atomic DRM 成功选择 primary plane 29、CRTC 63，1080×2400。用户确认全屏和触摸正常。
- ADB root shell、刷入镜像哈希检查通过。
- 首次启动仍不能解密。临时将内存中的 release/SPL 改为实际 ROM 的值并重启 Keymaster、keystore2、recovery 后，自动使用默认凭据解密成功；用户确认正常文件名和文件可打开。四个持久 DE 密钥文件前后 SHA256 完全一致。
- 解密期间运行系统属性为 release 17、platform/vendor SPL 2026-09-01；没有设置未来日期，也没有修改用户的锁屏凭据或持久密钥。
- 一个 61 字节公开测试文件通过 MTP 双向传输，读回 SHA256 与源文件一致；测试文件已从手机移除。
- 能进入 OrangeFox fastboot 页面，但 PC 没有 fastboot 连接，不能标为通过。日志显示通用 init.rc 和设备 init.recovery.usb.rc 对同一 fastboot 条件重复绑定 USB；临时重绑定诊断后手机重启到了 Android，系统正常启动。

下一版在 `Setup_Fstab_Partitions` 开始时运行设备脚本：只读挂载系统、读取 ROM 版本与 SPL、配置内存属性并重启 Keymaster/keystore2，然后才允许 userdata 的 DE 初始化。移除通用 init 中与设备树重复的两个 fastboot action，保留设备树的单一实现。以上持久修复仍需重新编译和首次启动测试。

原始日志仅保存在本地；不得发布设备密钥、凭据或私人文件。
