# 自动解密和 fastbootd 诊断（2026-10-05）

构建 [37275097258](https://github.com/lbdslbds/orangefox-rmx2121cn/actions/runs/37275097258)，
镜像 SHA256 `daccda0460ce9ae39875117ec9d242d2609e2cb9ff095b1b0910885c0b1a2cff`。

- 使用官方 checkout/upload-artifact v7.0.1，构建成功，Actions annotations 为空。Android 源码自身仍有编译警告。
- 内核、DTB、DTBO、ZIP 内镜像、设备断言、解密 helper 和编译后的 hook 均通过本地校验。
- 首次启动脚本加载 ROM release 17 和 platform/vendor SPL 2026-09-01；DE 初始化及用户 0 自动解密成功，无需手动改属性或重启解密服务。
- 用户确认全屏、触摸、正常文件名及打开已知文件均正常。ADB root 和 recovery 分区镜像哈希通过。
- MTP 自动启用；一个 52 字节公开测试文件双向传输后 SHA256 一致，测试文件已从手机移除。
- 原始 fastbootd 启动仍不能枚举 USB。新日志确认只有设备的单一绑定 action，fastbootd 已打开 FunctionFS 端点，因此去除重复绑定还不足以解决问题。
- 在内存中将 gadget `os_desc/use` 改为 0 后，Windows 能枚举 Google VID/PID 的 fastboot 接口，但报错 28（缺驱动）。Google 官方 USB Driver r13 的有效签名和 INF 支持该硬件 ID；安装后 fastboot CLI 连接成功。
- 只读查询确认 `is-userspace: yes`、`product: RMX2121`、`is-logical:system: yes`、`partition-size:recovery: 0x8000000`；`fastboot reboot recovery` 成功。fastbootd 中没有进行分区刷写或擦除。

下一版仅在 fastboot 的 USB 绑定前关闭不兼容的 Microsoft OS 描述符，并在 ADB/MTP 模式恢复该选项。保留新版 MTK atomic DRM 和自动解密修复。仍需重新编译、验证未手动改属性的 fastbootd 进出和 Android 启动；当前不标为全部验证完成。

Windows 驱动由 [Android 官方页面](https://developer.android.com/studio/run/win-usb) 下载，安装前确认 Google 签名有效。驱动和原始设备日志只保存在本地，不随公开设备树发布。
