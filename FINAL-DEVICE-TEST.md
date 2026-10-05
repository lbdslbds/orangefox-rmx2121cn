# RMX2121CN 最终实机验证（2026-10-05）

当前这台 realme X7 Pro / RMX2121CN 的自制 ROM 下，约定的实机验证项目全部通过。
OrangeFox R12.0 FBEv1-CN Unofficial 保留新版 atomic DRM；最终镜像已留在 recovery 分区，Android 正常启动。

构建：[Actions 第 6 轮，37282885690](https://github.com/lbdslbds/orangefox-rmx2121cn/actions/runs/37282885690)。
编译提交：`cb23f7d0225a0262c8b34cf1f8665696bf0c27a9`。
当前系统声明 Android 17 / API 37，vendor 为 Android 12 / API 31，硬件平台 MT6889，独立 recovery 128 MiB。

| 验证项 | 结果与证据 |
| --- | --- |
| 镜像和 ZIP | 哈希、boot header、原始内核/DTB/DTBO、ZIP 内镜像一致性、CRC、RMX2121/RMX2121CN 断言通过 |
| 显示、触摸 | MTK atomic DRM 使用一个全宽 primary plane；用户确认全屏与触摸正常 |
| ADB | recovery root shell 正常，刷入的 recovery 分区哈希与最终镜像一致 |
| 冷启动自动解密 | ROM 属性在 DE 初始化前自动加载；用户 0 自动解密，用户确认正常文件名和打开已有文件；没有手动修正属性或重启解密服务 |
| MTP | 启动后及退出 fastbootd 后，52 字节测试文件均双向传输、SHA256 一致，测试文件已清理 |
| fastbootd | 无需手动改 USB 属性即可连接；`is-userspace=yes`、`product=RMX2121`、`is-logical:system=yes`、recovery 大小 `0x8000000` |
| 退出 fastbootd | `fastboot reboot recovery` 成功；返回后自动解密正常，MTP/ADB 恢复，Microsoft OS 描述符选项恢复为 1 |
| Android 启动 | 最终 OrangeFox 保留在 recovery，`sys.boot_completed=1`、`ro.bootmode=normal` |

镜像 SHA256：`def8f111567534b2fdb9b4ca1f53226fc59622331f7b760aef32626e96fbb8f7`。

安装 ZIP SHA256：`3f3f0ee1001a42e1a996341322e0095725647c44a1547635accbb51e0924bdf5`。

实际安装测试使用 bootloader fastboot，只刷写 recovery。ZIP 安装脚本做过离线检查，ZIP 内镜像就是实机验证的镜像；本轮未执行 ZIP 安装流程。fastbootd 测试仅查询状态和重启，没有刷写或擦除分区。

本次只验证上述设备与当前 ROM、凭据配置。原始设备日志仅保留本地；公开报告没有设备序列号、用户文件内容、凭据或密钥。离线报告位于 [reports/build-6](reports/build-6)，其中 `boot_tested=false` 指该离线检查本身，实机结果以本报告与 `device-test.json` 为准。

原 TWRP 的两个本地回退备份仍保留，SHA256 为 `82754800595758a987f05ec422b43f152c597c0eb5334a20847e5520462bb8c3`。

Windows fastbootd 接口需要匹配驱动。本机已安装来自 [Android 官方页面](https://developer.android.com/studio/run/win-usb) 的 Google USB Driver r13，安装前确认签名有效，未修改 INF 或关闭签名检查。驱动安装在电脑上，不属于手机镜像。

工作流使用固定官方 SHA 的 checkout/upload-artifact v7.0.1（Node 24），本轮 Actions annotations 为空；Android 源码自身仍有编译警告。
