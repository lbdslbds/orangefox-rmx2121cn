# OrangeFox 云编译工程：realme X7 Pro / RMX2121CN

2026-10-06 补充检查发现第 6 轮电量显示固定为 100% 的问题，修复编译和实机验证进行中。
详见 [电量检查与修复](BATTERY-DEVICE-TEST.md)。下述第 6 轮验证范围不包括电量显示。

状态：**当前 RMX2121CN 自制 ROM 下，完整显示、触摸、ADB、冷启动自动解密、MTP、fastbootd 进出和 Android 启动均已实机通过。最终 OrangeFox 已留在 recovery 分区。**

已测试构建：[Actions 第 6 轮](https://github.com/lbdslbds/orangefox-rmx2121cn/actions/runs/37282885690)，
编译提交 `cb23f7d0225a0262c8b34cf1f8665696bf0c27a9`。
安装包为 `OrangeFox-R12.0_FBEv1-CN-Unofficial-RMX2121.zip`。
详见 [最终实机验证](FINAL-DEVICE-TEST.md)。离线报告、SHA256 和实机结果在 `reports/build-6/`。
该结果针对当前设备和 ROM；安装 ZIP 内镜像与实机验证的镜像完全一致。

适配目标是本机自制 ColorOS 移植 ROM：系统声明 Android 17 / API 37，vendor 为
Android 12 / API 31，内核 4.14.186+。设备为 A-only，独立 recovery 分区 128 MiB，
动态 super 分区，1080×2400 屏幕，FBE v1，Trustonic Keymaster 4.1。

## 使用 GitHub Actions

1. 将本目录的**全部内容**上传到 GitHub 仓库根目录，包含 `.github` 隐藏目录。
2. 打开仓库 **Actions → Build OrangeFox RMX2121CN → Run workflow**。
3. 等待工作流完成。下载本次运行底部的 **OrangeFox-RMX2121CN-运行编号** artifact。
4. artifact 是下载容器，需先解压。里面的 OrangeFox 安装 ZIP 才是 recovery 安装包。
   不要把整个 artifact ZIP 当作刷机包。
5. 若失败，查看 `sync.log`、`build.log`，保留第一处错误的上下文。

工作流手动触发，使用 `ubuntu-22.04` x64、4 并行任务、12 GiB swap，最长 350 分钟。
使用官方 `actions/checkout` 和 `actions/upload-artifact` v7.0.1（Node 24），固定完整提交 SHA。
它会清理 GitHub 临时虚拟机上的无关 SDK，并检查空间。源同步采用随工程打包的
官方 OrangeFox sync 脚本，选择 12.1 分支，不会因为系统显示 API 37 就切换到更高
编译分支。实际 OrangeFox 发布版本由官方源码决定。

构建前校验原始内核和 blobs；构建后检查 boot header v2、2048 页大小、128 MiB
大小限制、内核/DTB/DTBO 哈希、OrangeFox 标记、安装包内镜像一致性及设备名标记。
这些是离线检查，不能证明触摸、挂载、fastbootd 或解密工作正常。

工作流仅有 `contents: read` 权限，不需要个人 token、SSH 密码或 GitHub secrets。
结果上传 Actions artifacts，不创建 GitHub Release。公开仓库的标准 runner 当前可
免费使用；保留 artifact 14 天。GitHub 的资源限制可能导致同步或构建失败。

参考：[GitHub runner 规格](https://docs.github.com/en/actions/reference/runners/github-hosted-runners)、
[OrangeFox 编译说明](https://wiki.orangefox.tech/dev/building)。

## 设备树来源和改动

基础是 [zeng-github01 的 RMX2121 TWRP 设备树](https://github.com/zeng-github01/android_device_realme_RMX2121)，
分支 `twrp-12.1_cn`，提交 `f18bb09091104cdfc92417c111037110de924327`。
原始 README 保存在 `device/realme/RMX2121/UPSTREAM-README.md`。

其内核、DTB、DTBO 与本地 TWRP 镜像备份完全一致；93/94 个预编译二进制/固件
与备份一致。不同的是 fastboot HAL，采用公开设备树当前版本，需实机验证。
init、USB、VINTF 文本配置存在上游版本差异；这些配置采用公开设备树版本。
首次实机测试已确认当前 recovery 分区与备份相同，候选可启动且 ADB 正常，但用户
报告左黑右显示的半屏问题。解密在原 TWRP 和候选中均未确认成功；详见
[首次测试记录](FIRST-DEVICE-TEST.md)。首版候选不能作为稳定版本使用。

当前构建保留新版 atomic DRM，通过 `scripts/patch-mtk-drm.py` 为 MediaTek 驱动选择
支持当前屏幕 CRTC 的一个全宽主平面，由内核处理硬件 dual-pipe 分割，避免 SDE
默认两个用户态平面的半屏异常。补丁严格检查输入源码哈希，并保存输出哈希，
第 4 轮已实机确认完整显示与触摸。`vendor-tools/recovery-legacy-drm/` 的旧版 TeamWin 实现只保留
作对照，当前构建不使用。安装 ZIP 接受 RMX2121 和 RMX2121CN，产物检查会核对完整断言。

新增 `vendorsetup.sh`，导出 OrangeFox 所需配置，使用 vanilla 模式和 Keymaster 4.1。
移除 TWRP 的 Y/H 偏移，设置 OrangeFox 2400 屏幕高度。为本地移植 ROM 增加
system_ext、my_manifest、my_bigball 的 ext4/EROFS logical 挂载项。原始 fstab/flags 保留。运行时在 userdata DE 初始化前只读读取系统版本和 SPL，
配置内存属性并重启 Keymaster/keystore2；移除设备和通用 init 重复的 fastboot USB action。
第 5 轮已确认自动解密成功。fastboot 模式关闭不兼容的 Microsoft OS 描述符，
ADB/MTP 模式恢复该选项；第 6 轮已确认无需手动 USB 属性修改即可连接 fastbootd 并返回。
沿用 recovery 最小源码清单需要的 `ALLOW_MISSING_DEPENDENCIES=true`；实际编译目标
及镜像仍需通过构建和产物检查。移除了无源码、且预编译设备 blobs 未引用的
`ashmemd_aidl_interface-cpp` 和 `libashmemd_client` 两项历史依赖。

来源、镜像哈希和比较结果在 `provenance.json`。官方 sync 脚本提交为
`53a303ecfb622c516082d3e61dbaa7d9f02f0120`，原版文件保存在
`vendor-tools/orangefox-sync/`。此副本修正了一处 vendor/twrp 补丁路径：
`patch-vendor-twrp-fox_12.1.diff` 实际在 `patches/` 子目录。构建脚本在加载 AOSP
envsetup 时允许可选初始化脚本返回非零，然后核查 lunch/mka 函数并严格检查编译结果。
每次构建保存实际源码 manifest 和 recovery/vendor 提交，
用于重现源码状态。官方源分支会继续变化，后续构建不保证与首次完全相同。

已有的版权声明保留。OrangeFox 源码按其原始许可证使用；对外发布修改后的成品时，
应同时保留并提供相应源码和修改，预编译内核的对应源码也需要由其原提供者确认。

## 本地 Linux 编译入口

在已经安装 Android recovery 编译依赖、`repo` 和 Java 11 的 **x86_64 Linux 普通用户**下：

```bash
bash scripts/sync-sources.sh "$HOME/fox_12.1"
bash scripts/build.sh "$HOME/fox_12.1"
```

`prepare-runner.sh` 只允许在 GitHub 托管临时 runner 上执行，不能用于个人电脑。
ARM 树莓派/OpenWrt 不适用于这条编译流程。

实机测试步骤和限制见 [TESTING.md](TESTING.md)。
