# zorin.md — Fresh-Agent Handoff for EverpalTweaks 5.10 Work on ZorinOS / Ubuntu

> **Purpose:** Allow an agent with ZERO prior context on Linux (ZorinOS/Ubuntu 22.04+) to reproduce exactly how we reached the current state and continue the 5.10 kernel work.
> **Where you are:** Linux checkout of `https://github.com/FrontlXOX/EverpalTweaks` (on Windows it was `D:\EverpalTweaks`, on Linux it will be `~/EverpalTweaks` or `$REPO_ROOT`). Replace `$REPO_ROOT` accordingly.
> **Scope agreed:** Use Aqua 4.14 tree + 5.10 donor to produce a new bootable 5.10 tree for everpal. Vulkan 1.3 userspace port is DONE — do not re-port it.

---

## 1. System Identity (memorize this)

| Item | Value |
| :--- | :--- |
| Device | Xiaomi POCO M4 Pro 5G / Redmi Note 11S 5G (`everpal`), `22031116AI`, Board `S98016LA1`, India SKU |
| SoC | MediaTek Dimensity 810 5G (MT6833P / MT6833 family, TSMC 6nm) |
| CPU | 2x Cortex-A76 @ 2.40 GHz + 6x Cortex-A55 @ 2.00 GHz |
| GPU | ARM Mali-G57 MC2 Valhall v1, 2 shader cores, 950 MHz stock, 1068 MHz GED boost, Job Manager ONLY (`BASE_UK_VERSION_MAJOR 11`), NOT CSF |
| RAM | 4GB LPDDR4X Samsung KM5P9001DM-B424, MemTotal ~3.53 GB / 3709888 kB. Variants 6GB/8GB exist |
| Storage | 64GB UFS 2.2, ~48GB userdata |
| Display | 6.6" 90Hz FHD+ IPS 1080x2400, KTZ8863A, PWM 0-2047 |
| Audio | MT6359 codec + AW87389 mono SmartPA (no headtracking HAL, no ultrasound proximity HW) |
| OS | Android 16 Project Infinity / LineageOS 23.0 Base, `BP4A.251205.006`, patch 2026-09-01 |
| Current kernel | Linux `4.14.357-Aqua #3 SMP PREEMPT`, Clang 18, KernelSU `ksud 4.2.0-rc1` + Zygisk, SELinux Enforcing |
| Donor GPU stack | Redmi Note 13 5G (`gold`), HyperOS 3.0 `OS3.0.10.0.VNQCNXM_15.0`, DDK `r49p1-03bet0` |
| Primary remote | `https://github.com/FrontlXOX/EverpalTweaks` |

Authorship: Author & Maintainer Shovit Dutta. Collaborators Addster09 (device+kernel) x himanshuksr0007/Goku (bringup+memory). `module.prop author=FrontlXOX` ONLY in zips — never list FrontlXOX under Authors & Credits in docs.

Subsystems:
1. `src/package/MemoryMgmt/` — Zone Normal 374 MiB managed / 432 MiB spanned, ZRAM 3.58GB LZ4, `wsf=20`, `min_free 24/32/40MB`, `swap_free_low 2%`
2. `src/package/ThermalMgmt/` — AES-128-CBC key/IV `b"thermalopenssl.h"`, `sconfig 10` 55°C headroom, CCI 1.6GHz lock, GPU 50ms DVFS lock
3. `src/package/Vulkan13/` — hybrid decoupling, `libVK13_mali.so` + `libgpd1.so` + `libge2.so`, manifests `4206592`
4. `src/package/SpatialAudio/` — `immersive_out maxOpenCount=1 maxActiveCount=1`, DAP per-stream, speaker/headtracking off

Records: 2133 MC (+42.2%), 729 SC (+19.5%), 2736 3DMark (+8.7%), 4053 Physics (+20%), 1302 GPU (+20.6%).

---

## 2. Repo Layout (canonical)

```text
$REPO_ROOT/
├── AGENTS.md, README.md, CHANGELOG.md, LICENSE, zorin.md (this file)
└── src/
    ├── scripts/ builder.py autobench.py benchpull.py build_kernel.sh decouple_libge2.py decrypt_thermal.py dumpboot.py synctrees.py verifydevice.py
    ├── trees/ device_xiaomi_everpal/ kernel/ kernel-5.10/ upstream-device/ vendor_xiaomi_everpal/
    ├── modules/ *.zip companions + Kaeru/ + ResukiSU/
    └── package/
        ├── templates/ AnyKernel3/ META-INF/ SpatialAudio/ Vulkan13/
        ├── MemoryMgmt/ README.md patch.patch package/MemoryMgmt.zip docs/memory-mgmt.txt
        ├── ThermalMgmt/ README.md patch.patch package/ThermalMgmt.zip docs/thermal-mgmt.txt benchmark_history.txt history.db vendor_configs/
        ├── Vulkan13/ README.md patch.patch package/Vulkan13-KernelSU.zip docs/vulkan-mgmt.txt
        └── SpatialAudio/ README.md patch.patch package/SpatialAudio.zip docs/spatial-audio.txt
```

Rules: zips ONLY in `src/package/*/package/` (exception `src/modules/` companions). Scripts ONLY in `src/scripts/` (exception `src/modules/ResukiSU/` verbatim). Never commit `.env`, tokens, `__pycache__`, `*.db-wal`, `SESSION_TRANSCRIPT.md`, `transcript_archive.jsonl.gz`.

---

## 3. Current State (what we proved read-only on Windows)

### 3.1 Vulkan 1.3 — DONE, do not touch
- Dual-stack: stock `libGLES_mali.so` r32p1 for SurfaceFlinger + standalone `libVK13_mali.so` r49p1 + `vulkan.mali.so` stub.
- Linker fixes: `libgpd1.so` exports `GpuAuxBlitAHardwareBuffer` (Bionic GnuHash bit-exact), donor `libged.so` 101KB superset provides `ged_fr_swd_frame_destroy/mark_frame`.
- Config: `mali_platform.config PLATFORM_AGT_FREQUENCY_KHZ=13000`, AFBC `gpu.xml dpu.xml dpu_aeu.xml vpu.xml cam.xml`, manifests `4206592 (0x00403000 Vulcan 1.3.0)`.
- Verified: `dumpsys gpu: vulkanVersion=4206592 createdVulkanDevice=1 vkLoadingFailureCount=0`, VulkanMod 100%, 2736/4053 3DMark.
- Output: `src/package/Vulkan13/package/Vulkan13-KernelSU.zip` (~90M).

### 3.2 Aqua 4.14 — BROKEN at HEAD, fix first on Linux
- Tree: `src/trees/kernel`, remote `https://github.com/FrontlXOX/android_kernel_xiaomi_mt6833.git`, branch `lineage-24.0`, `Makefile: VERSION=4 PATCHLEVEL=14 SUBLEVEL=357 EXTRAVERSION=-Aqua`.
- Defconfig: `arch/arm64/configs/everpal_defconfig` (487 lines): `L223 CONFIG_MTK_GPU_SUPPORT=y`, `L224 CONFIG_MTK_GPU_VERSION="mali valhall r44p0"`, `L419 CONFIG_ION=y`, `CONFIG_MACH_MT6833=y`, `CONFIG_MTK_PLATFORM="mt6853"`.
- **Mismatch:** `drivers/misc/mediatek/gpu/gpu_mali/mali_valhall/` contains `mali-r25p0/ r27p0/ r28p0/ r30p0/ r32p0/ r32p1/` — NO `mali-r44p0/`. Kbuild chain `gpu/Makefile → gpu_mali/Makefile (valhall) → mali_valhall/Makefile (r44p0)` fails. HEAD `91ddd80 🦋 [FEAT]: update CONFIG_MTK_GPU_VERSION to mali valhall r44p0` broke build. No `drivers/gpu/arm/` (only `drm/ host1x/ ipu-v3/`).
- Good: `platform/mt6833/{Kbuild,mali_kbase_config_mt6833.c,mali_kbase_config_platform.h}` present in r32p1, `mali_kbase_mem_linux.c` ION backend present, JM `BASE_UK_VERSION_MAJOR 11` confirmed.
- Builder: `src/scripts/build_kernel.sh` uses `KERNEL_DIR=src/trees/kernel`, `DEFCONFIG=everpal_defconfig`, ZyC Clang 22.0.0 auto-wget to `~/toolchains/ZyC-clang-22.0.0`, `CC=clang LD=ld.lld`, `make O=out ARCH=arm64 CC="ccache clang" LLVM=1 LLVM_IAS=1 CROSS_COMPILE=aarch64-linux-gnu- CROSS_COMPILE_ARM32=arm-linux-gnueabi- KCFLAGS="-Wno-error=default-const-init-var-unsafe" Image.gz dtbs`. `--vulkan` calls `builder.py --vulkan --kernel out/arch/arm64/boot/Image.gz [--dtbo out/arch/arm64/boot/dtbo.img]`.

### 3.3 5.10 donor — PURE DONOR, does not boot everpal
- Path: `src/trees/kernel-5.10`, remote `https://github.com/MillenniumOSS/kernel_millennium_mt6789-common.git`, branch `vic`, `Makefile: VERSION=5 PATCHLEVEL=10 SUBLEVEL=243`, HEAD `d92da041e Merge ASB-2025-10-06_12-5.10`, shallow/grafted (1 commit), dirty 13 files (`include/uapi/linux/netfilter/*`, `net/netfilter/xt_*`, `tools/memory-model/litmus`).
- Type: GKI 5.10 + MTK (`build.config.gki*`, `build.config.mtk.aarch64`, `arch/arm64/configs/gki_defconfig + mgk_64_k510*`, `android/abi_gki_aarch64_mtk`).
- Has MT6833: `arch/arm64/configs/mgk_64_k510*: CONFIG_MTK_DCM_MT6789/MT6833, PINCTRL_MT6789/MT6833, MTK_GPU_MT6789/MT6833_SUPPORT, SND_SOC_MT6833, COMMON_CLK_MT6833*`, `arch/arm64/boot/dts/mediatek/mt6833.dts mt6833-clkitg.dtsi cust_mt6833_*`, `drivers/gpu/mediatek/gpu_mali/mali_valhall/mali-r32p1/.../platform/{mt6833,mt6853,mt6885,mt6893,mtk_platform_common}/`, `drivers/misc/mediatek/` full.
- Mali: path-versioned `mali-r32p1`, `.../midgard/include/uapi/.../jm/mali_kbase_jm_ioctl.h:123-124 MAJOR 11 MINOR 31`, `csf/... MAJOR 1 MINOR 5` (unused).
- Missing everpal: `grep everpal arch/arm64/boot/dts/mediatek` = 0 hits, no `everpal_defconfig`. Shipped Xiaomi board is `k6789v1_64.dts (hardware="mt8781")` + `xiaomi-mt6789-common.dtsi` + `yunluo-mt6789-camera/display` — MT6789 yunluo sibling, NOT everpal.

---

## 4. How We Reached Here (reproduce exactly)

You must re-verify before building. All read-only.

**Step 0 — List docs (skip trees):**
```bash
# glob **/*.md, exclude src/trees/
ls *.md src/package/*/README.md src/package/templates/AnyKernel3/README.md
# Read: AGENTS.md README.md CHANGELOG.md src/package/{MemoryMgmt,ThermalMgmt,Vulkan13,SpatialAudio}/README.md src/package/templates/AnyKernel3/README.md
```

**Step 1 — Read build infra:**
```bash
cat src/scripts/build_kernel.sh
ls src/trees/ # device_xiaomi_everpal kernel kernel-5.10 upstream-device vendor_xiaomi_everpal
cat src/package/Vulkan13/docs/vulkan-mgmt.txt
sed -n '1,100p' src/scripts/builder.py; grep -n "kernel\|dtbo\|blobs" src/scripts/builder.py | head -40
```

**Step 2 — Delegate audits (Sub-Agent First Policy per AGENTS.md Rule 12):**
Parent must NOT edit before sub-agents report. Spawn 2 `explore` sub-agents:
- Agent A prompt: "Read-only audit src/trees/kernel-5.10: README.md 100 lines, glob arch/arm64/configs/* + arch/arm64/boot/dts/mediatek/*6833* + drivers/gpu/mediatek/.../platform/mt6833*, grep BASE_UK_VERSION_MAJOR, bash read-only `git -C src/trees/kernel-5.10 remote -v; branch --show-current; log --oneline -5`, report everpal hits."
- Agent B prompt: "Read-only audit 4.14: list src/trees/kernel top, find everpal_defconfig, report CONFIG_MTK_GPU_VERSION/CONFIG_ION/Makefile version, trace builder.py --kernel/--dtbo/--blobs injection, check drivers/gpu/arm absence + drivers/misc/mediatek/gpu/gpu_mali/mali_valhall/ versions + platform/mt6833 + mali_kbase_mem_linux.c + JM MAJOR, bash read-only `git -C src/trees/kernel remote -v; branch --show-current; log --oneline -5; ls src/package/Vulkan13/package/`."
- Synthesize: 5.10 = donor with mt6833 glue but no everpal board; 4.14 = r44p0 mismatch break.

**Step 3 — Confirm git + outputs (read-only):**
```bash
git -C src/trees/kernel remote -v; git -C src/trees/kernel branch --show-current; git -C src/trees/kernel log --oneline -5
git -C src/trees/kernel-5.10 remote -v; git -C src/trees/kernel-5.10 branch --show-current; git -C src/trees/kernel-5.10 log --oneline -5
ls -lh src/package/Vulkan13/package/
grep -rn "BASE_UK_VERSION_MAJOR" src/trees/kernel-5.10/drivers/gpu/mediatek/gpu_mali/mali_valhall/mali-r32p1/ | head
ls src/trees/kernel/drivers/misc/mediatek/gpu/gpu_mali/mali_valhall/
ls src/package/templates/Vulkan13/
```

If all match §3, you are at the same point we were on Windows. Proceed to §5.

---

## 5. Linux Work Plan (ZorinOS/Ubuntu 22.04+)

### Phase 0 — Bootstrap (one-time)
```bash
sudo apt install -y build-essential bc bison flex libssl-dev libelf-dev python3 ccache aarch64-linux-gnu-gcc arm-linux-gnueabi-gcc device-tree-compiler lz4 wget curl zip unzip git
git config --global user.name "YourName"; git config --global user.email "you@example.com"
# Unshallow donor + clean dirty tree BEFORE branching:
git -C src/trees/kernel-5.10 fetch --unshallow || true
git -C src/trees/kernel-5.10 status --short # expect 13 modified netfilter/litmus
git -C src/trees/kernel-5.10 checkout -- include/uapi/linux/netfilter net/netfilter tools/memory-model || git -C src/trees/kernel-5.10 stash
adb --version; python3 --version
```

### Phase 1 — Fix 4.14 baseline (proves toolchain, 30-60 min)
1. Decide r44p0 vs r32p1: `ls src/trees/kernel/drivers/misc/mediatek/gpu/gpu_mali/mali_valhall/` — if no `mali-r44p0`, either vendor it or `git revert 91ddd80` / set `CONFIG_MTK_GPU_VERSION="mali valhall r32p1"` in `everpal_defconfig`.
2. `bash src/scripts/build_kernel.sh --clean` (kernel-only, no --vulkan yet). Expect `out/arch/arm64/boot/Image.gz`.
3. Only then `bash src/scripts/build_kernel.sh --vulkan` → `src/package/Vulkan13/package/Vulkan13-KernelSU.zip` + CRC verify via `builder.py --all`.

### Phase 2 — Create new 5.10-everpal tree (do NOT overwrite Aqua/donor)
```bash
# New repo under FrontlXOX, e.g. android_kernel_xiaomi_everpal-5.10, branch everpal-5.10 from vic
git -C src/trees/kernel-5.10 checkout -b everpal-5.10 vic
# Port from Aqua 4.14 (source of truth for board):
git -C src/trees/kernel log --oneline -- arch/arm64/configs/everpal_defconfig arch/arm64/boot/dts/mediatek/ | head -20
# Create arch/arm64/configs/everpal_5.10_defconfig by adapting mgk_64_k510 + everpal deltas:
# - Keep MT6833 clocks, SND_SOC_MT6833 (donor defaults to MT6366/MT6359P — verify MT6359!), COMMON_CLK_MT6833, WALT, freezer
# - ION vs dma_heap: 5.10 deprecates /dev/ion — check CONFIG_ION in donor; if absent, migrate or carry ION shim
# Create arch/arm64/boot/dts/mediatek/mt6833-everpal.dts from mt6833.dts + Aqua panel/touch/camera deltas + cust_mt6833_* (DO NOT copy yunluo-mt6789)
# Verify: panel KTZ8863A 90Hz PWM 0-2047, touch, UFS2.2, MT6359 audio, wlan/bt, cam/display
```

### Phase 3 — Mali decision (keep simple)
- Donor already has `mali-r32p1` JM 11.31 + `platform/mt6833/` — reuse as-is. JM-only, ignore CSF (G710/G615/G720 only).
- 4.14 shims doc (`src/package/Vulkan13/README.md` §5: `access_ok(VERIFY_READ)` 3-arg, retain ION `mali_kbase_mem_linux.c`, guard `dma_fence_set_deadline`, `platform/mt6833` glue) is for 4.14 — on 5.10 verify if still needed (likely NOT, since donor is native 5.10).
- Do NOT chase r44p0 kernel driver unless Vulkan ICD demands it — current r49p1 ICD works in userspace on JM.

### Phase 4 — Build + test loop
```bash
make O=out ARCH=arm64 everpal_5.10_defconfig
make -j$(nproc) O=out ARCH=arm64 CC="ccache clang" LLVM=1 LLVM_IAS=1 CROSS_COMPILE=aarch64-linux-gnu- CROSS_COMPILE_ARM32=arm-linux-gnueabi- Image.gz dtbs
python3 src/scripts/builder.py --vulkan --kernel out/arch/arm64/boot/Image.gz --dtbo out/arch/arm64/boot/dtbo.img
# Boot: fastboot boot out/arch/arm64/boot/Image.gz (or AnyKernel3 zip via recovery)
adb wait-for-device; adb logcat -d | head -200; dmesg | grep -i mali
adb shell "getprop sys.thermal.mode; cat /sys/class/thermal/thermal_message/sconfig"
adb shell dumpsys gpu | grep -E "vulkanVersion|createdVulkanDevice|vkLoadingFailure"
python3 src/scripts/verifydevice.py
python3 src/scripts/autobench.py --cpu-only # then --gpu-only after CPU stable
```
- KernelSU/SUSFS for 5.10 ≠ 4.14 patches (`susfs_patch_to_4.14.patch` will NOT apply) — fetch 5.10 variants separately.
- Non-GKI `Image.gz+dtbo` via AnyKernel3 fits current ROM; GKI `vendor_boot` only if ROM moves to GKI.

### Traps (never violate)
1. NEVER `echo.*> /proc/driver/thermal/set_sspm_big_limit_threshold` — 84% IPI spinloop.
2. NEVER alter `mtk-cl-backlight` cooling to non-0 — black screen.
3. NEVER map `sconfig 14` (YouTube 1.04/1.12GHz clamp) — use `sconfig 10`.
4. After `adb reboot`, always `adb wait-for-device` + tail `adb logcat` for bootloop/AVC.

---

## 6. Definition of Done for New Tree
- [ ] 4.14 `build_kernel.sh --clean` passes (r44p0 mismatch resolved)
- [ ] New repo `android_kernel_xiaomi_everpal-5.10` branch `everpal-5.10` pushes to FrontlXOX GitHub (GitHub primacy, no GitLab)
- [ ] `everpal_5.10_defconfig` + `mt6833-everpal.dts` boot to `sys.boot_completed=1`
- [ ] `dumpsys gpu` still `4206592/1/0`, `verifydevice.py` passes clocks/ZRAM/sconfig
- [ ] `builder.py --all` CRC passes, zips only in `src/package/*/package/`
- [ ] `convo.txt` prepared if reporting to Goku/Addster09 (compact Telegram style, emojis, zero fluff)
- [ ] Benchmark URL updated across docs if new record (`compare/<NEW>?baseline=380539`)

## 7. Quick Verify Commands (non-destructive)
```bash
adb shell "getprop sys.thermal.mode; cat /sys/class/thermal/thermal_message/sconfig"
adb shell "cat /sys/devices/system/cpu/cpu*/cpufreq/scaling_cur_freq"
adb shell "cat /proc/zoneinfo | grep -E 'Node|min|low|high'"
adb shell "cat /proc/swaps; cat /proc/meminfo | grep -E 'MemTotal|MemFree|MemAvailable|SwapTotal|SwapFree'"
adb logcat -d -s lmkd
python src/scripts/decrypt_thermal.py --batch src/package/ThermalMgmt/docs/vendor_configs/
```

## 8. Commit Convention
`<emoji> [<TYPE>]: <description>` — e.g. `git commit -m "🦋 [FEAT]: add everpal 5.10 defconfig"`. Group per-tree, stage only intended files, never commit `.env`/`bun.lock` edits/`data/`/`__pycache__`. Pre-commit: `builder.py --all` + `git diff --stat`.
