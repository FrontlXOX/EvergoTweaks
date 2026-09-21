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

## 4b. 5.10 Port Manifest (Windows-verified 2026-09-21 — thinker to builder)

> Builder: execute in listed order. All source paths are 4.14 Aqua (`src/trees/kernel`, submodule `FrontlXOX/android_kernel_xiaomi_mt6833`, branch `lineage-24.0`); all target paths are the NEW tree branched from 5.10 donor (`src/trees/kernel-5.10`, submodule `MillenniumOSS/kernel_millennium_mt6789-common`, branch `vic`). NEVER commit tree edits to the superproject — trees are submodules (`ignore = dirty`); new-tree work lives in its own repo/branch (`android_kernel_xiaomi_everpal-5.10`, branch `everpal-5.10`). Every row below was verified read-only on Windows — receipts included.

### P0 — Boot set (no boot without these)

| # | What | Source (4.14, verified) | Target (5.10) | Action |
|---|------|------------------------|---------------|--------|
| 1 | k16a display panels | `drivers/gpu/drm/panel/panel-k16a-36-02-0a-vdo.c` + `panel-k16a-42-02-0b-vdo.c` (+Kconfig/Makefile entries, `everpal_defconfig:327-329` `DRM_PANEL_K16A_*=y` + `LCM_CUST_COMMON=y` + `VIRTUAL_VDO=y`) | `drivers/gpu/drm/panel/` + Kconfig | PORT both drivers + symbols. Receipt: both files exist in 4.14; 5.10 has zero `K16A` (only `panel-truly-*`). Note 5.10 DRM is slim upstream V2 (~20 files, no `mtk_panel_ext`/writeback) — adapt panel glue, do not copy the whole 4.14 `drm/mediatek` fork (100+ files). |
| 2 | Board DTS | `arch/arm64/boot/dts/mediatek/evergo.dts` (651 lines, `Copyright XiaoMi 2021`): `dsi0` panel1 `k16a_36_02_0a_vdo` + panel2 `k16a_42_02_0b_vdo` (pm pio136, bl pio87, rst pio86, bias pio137/138, `lcd_dvdd=mt_pmic_vcn13`, L347-382), `fpsensor_fp_eint` pio18 (L633-641), includes `cust_evergo_camera` + `evergo/cust.dtsi` + `sia81xx` + `sc8551` + `ln8000` + `irtx_led` (L643-649) | New `arch/arm64/boot/dts/mediatek/mt6833-everpal.dts` on 5.10 `mt6833.dts` base + `Makefile` `dtb-y` entry | PORT + ADAPT. SoC base differs (4.14: mcupm/dvfsp/eem/upower/ion-carveout; 5.10: scpsys/dvfsrc/ssmr/lastbus/dfd) — keep everpal nodes (DSI/panel/fpsensor/accdet/mt6360 intr pio10-11), drop legacy SoC nodes. Receipt: 5.10 `Makefile` lists only `mt6789.dtb` (L17) — you must add the new dtb or nothing compiles it. `evergo/cust.dtsi` + `k6833v1_64/cust.dtsi` resolve to zero files repo-wide (external vendor overlay) — recreate minimal or stub, never block on them. |
| 3 | Board overlay + touch/camera DTS | `k6833v1_64.dts` (330, plugin: chosen videolfb, mt6360, LCD bias/RST/TE, dsi0, accdet, GPS) + `cust_mt6833_touch_*.dtsi` (8 variants: nt36xxx/nt36672c_1080x2400/ilitek9882/ft3518_1080x2400/alpha_720x1600/120hz/1080x2300/1080x2280) + `cust_mt6833_msdc` + `cust_mt6833_camera` + `cust_mt6833_alpha_camera` + `cust_mt6833v1_64_mt6317_camera` + `cust_evergo_camera.dtsi` + `sia81xx.dtsi` | Same DTS dir in new tree | PORT. Receipt: 5.10 keeps only 2 `cust_mt6833_for_6789_touch_*` + `cust_mt6833_msdc/camera` — the 6 everpal touch variants, alpha/mt6317 camera, `cust_evergo_camera`, `sia81xx` are absent. |
| 4 | Battery tables | `bat_setting/mt6833_battery_table2.dtsi` + `mt6833_battery_table.dtsi` + `mt6833_battery_prop.dtsi` + `mt6833_battery_prop_dim2_ext.dtsi` + `battery_S98016_CWD_4V45_5000mah.dtsi` + `battery_S98016_CMX_4V45_5000mah.dtsi` | Same dir in new tree | PORT all six. Receipt: 4.14 list confirmed; 5.10 has `mt6833_battery_*` but not `table2` nor `S98016` 5000mAh. |
| 5 | Touch framework | `drivers/input/touchscreen/mediatek/*` (14 files: `mtk_tpd.c`, `tpd_setting.c`, `pd_*.c/h`, Makefile, Kconfig) | `drivers/input/touchscreen/mediatek/` (absent in 5.10) | PORT framework OR adapt board to upstream `goodix.c` — your call on Linux after reading both. Receipt: 4.14 dir listed; 5.10 has no `mediatek*` under touchscreen. 5.10 DTS has only `touch compatible="goodix,touch"` stub. Defconfig touch string is identical both sides (`GT9886 GT9896S NT36672C`), so Kconfig needs no change, driver backend does. |
| 6 | Audio machine (rename, NOT copy) | `sound/soc/mediatek/mt6833/mt6833-mt6359.c` (1226 lines, `#include ../../codecs/mt6359.h`, `everpal_defconfig:344` `SND_SOC_MT6833_MT6359=y` + `:106/:304` `MT6359P` PMIC/regulator) | Existing 5.10 `sound/soc/mediatek/mt6833/mt6833-mt6359p.c` (1228 lines, `compatible="mediatek,mt6833-mt6359p-sound"`) | RENAME/ADAPT in place: `compatible` → `mt6833-mt6359p-sound`, enable `SND_SOC_MT6359P_ACCDET=m` (`mgk_64_k510_defconfig:237` already has it) + `SND_SOC_MT6833_MT6359P=m` (`:241`), handle `y`→`m` load order (ramdisk). Same MT6359P silicon both sides — Kconfig rename, not new HW. Amp tables differ (`SIA8109/AW87XXX/RT5509` vs `RT5512`) — port `sia81xx.dtsi` with row 3. |
| 7 | Defconfig fragment | `arch/arm64/configs/everpal_defconfig` (487 lines): `:44` `MACH_MT6833=y`, `:67-68` `APPENDED_DTB_IMAGE(_NAMES=mediatek/mt6833)`, `:100-101` `MTK_PLATFORM="mt6853"` + `ARCH_MTK_PROJECT="k6833v1_64"`, `:158` `CONSYS_6833=y`-only, `:168` `MD1=22`, `:166` `FM MT6631`, `:224` `GPU_VERSION r44p0`, `:344` audio, `:327-329` panels, `:419-420` `ION/MTK_ION=y`, `:65` CMDLINE | New `arch/arm64/configs/everpal_5.10_defconfig` based on `mgk_64_k510_defconfig` (604 lines) | ADAPT, never copy: keep `MTK_GPU_MT6833_SUPPORT=m` (`:218`), `SND_SOC_MT6833(_MT6359P)=m` (`:240-241`), `DMABUF_HEAPS_MTK_MM/SYSTEM/DEBUG=m` (`:15-17`, ION replacement — decide ION-shim vs dmabuf migrate), touch string (`:106`), `MT6360` family (`=m` vs 4.14 `=y`). Drop `MACH_*`/`MTK_PLATFORM`/`GPU_VERSION` string style (absent in 5.10 by design). Re-add single-chip `CONSYS_6833` preference, `MD1`, FM chip, CMDLINE per board need. |
| 8 | Conflict cleanup | — | `drivers/gpu/mediatek/gpu_mali/mali_valhall/mali-r32p1/drivers/gpu/arm/midgard/csf/ipa_control/mali_kbase_csf_ipa_control.c:278,327,384` | RESOLVE 3x `<<<<<<< HEAD` markers BEFORE first build. Receipt: grep-confirmed on Windows. (CSF unused on G57/JM — resolve by keeping donor side, do not delete the file.) |
| 9 | Git hygiene | — | `src/trees/kernel-5.10` (`vic`, shallow/grafted 1 commit, 13 dirty: `include/uapi/linux/netfilter/*`, `net/netfilter/xt_*`, `tools/memory-model/litmus`) | `fetch --unshallow`, `checkout --` the 13 dirty files, THEN `checkout -b everpal-5.10 vic`. Never branch dirty/shallow. |

### P1 — Post-boot features (boot first, then these)

| # | What | Source (4.14) | Target | Action |
|---|------|---------------|--------|--------|
| 10 | Fingerprint | `drivers/input/fingerprint/fpc1542/mtk_spi.c` + `goodix/gf_spi_tee.c` (+Kconfig/Makefile) | `drivers/input/fingerprint/` (entire dir absent in 5.10) | PORT after boot. Loss = feature, not boot blocker. |
| 11 | Vibrator/haptics/sensors | `mediatek,vibrator` node + `USB_TRANCEVIBRATOR=y` (`:390`) + `MTK_SENSOR_SUPPORT/SENSORHUB=y`, `evergo.dts` AW8697 pio132 | Upstream equivalents | PORT after boot. |
| 12 | Camera sensors | `CUSTOM_KERNEL_IMGSENSOR="s5kjn1/ov50c40/ov16a1q/imx355..."` (`:120`) | Donor lists `s5kjd1/imx519/imx586/...` | PORT sensor drivers after boot. |
| 13 | NFC/GPS/chargers | `st21nfc` i2c3, GPS ELNA gpio140/91, `MT6360_PMU/CHARGER/FLED` (`=y` vs donor `=m`), `WL2866D` | Same | PORT/adapt after boot. |

### Sufficiency limits (read this before promising a boot)

Manifest rows 1-9 are the complete KNOWN delta — necessary, not sufficient. These unknowns can only resolve in the Linux build→boot loop, not by more Windows reading:

1. Kconfig drift: 4.14 symbols (`MACH_*`, `MTK_PLATFORM`, `GPU_VERSION` string, `ION/MTK_ION`, `PSEUDO_M4U`, `FPSGO`, `BORE/WALT`, `LTO_THIN`) may not exist in 5.10. `olddefconfig` will prompt or silently drop — review every delta, never blindly `-y`.
2. DTS phandle drift: evergo nodes reference `mt_pmic_vcn13_ldo_reg`, pio pins, `mtkfb/dsi0/accdet`, `chosen videolfb` — some labels/phandles differ or absent in 5.10 `mt6833.dtsi` (scpsys/dvfsrc/ssmr vs mcupm/dvfsp/eem). Expect DTC errors; fix iteratively. `evergo/cust.dtsi` is external — stub it, never block on it.
3. Panel API drift: k16a drivers call 4.14 `mtk_panel_ext` APIs missing from 5.10 slim DRM V2 — copy alone may not compile; adaptation likely.
4. Module load order: audio/touch/GPU as `=m` must be in vendor ramdisk with correct `modules.load` order or first boot has no sound/input (still boots via ADB — keep `adb wait-for-device` path open).
5. ROM-side coupling: `device_xiaomi_everpal` (Lineage 23.0) + vendor DLKM + sepolicy target 4.14 — a 5.10 kernel may break WiFi/BT DLKM, `modules.load`, or AVB/`vendor_boot` layout. Kernel booting ≠ ROM booting.
6. Baseline unproven: 4.14 HEAD itself is build-broken (`r44p0` mismatch, §3.2) — fix and build 4.14 FIRST to prove the toolchain before judging 5.10 failures.

Builder rule: after each failure, append the error + fix to this file's execution-order log (thinker updates the manifest; builder never silently diverges). A boot is declared only at `sys.boot_completed=1` + `dumpsys gpu 4206592/1/0` + `verifydevice.py` pass.

### SKIP (decided, do not revisit without new evidence)

- CSF firmware/interfaces (G57 is JM-only, `MAJOR 11` both trees).
- `KTZ8863A` driver hunt (zero hits in both trees — backlight is `disp_pwm` + LCM bias GPIO, nothing to port).
- `r44p0` kernel-driver chase (4.14 `everpal_defconfig:224` asks `r44p0` but only `r25p0-r32p1` vendored — that HEAD is build-broken; on 5.10 keep donor `r32p1-00bet2` + JM, userspace r49p1 ICD is decoupled and verified).
- Copying `yunluo*`/`k6789v1_64.dts` as everpal base (MT6789/MT8781 sibling, wrong audio/panel/GPIO) — reference only.
- `sconfig 14`, `set_sspm_big_limit_threshold`, `mtk-cl-backlight` (hardware traps, AGENTS.md).

### Builder execution order (your checklist)

1. §5 Phase 0 + 0b (toolchain, BUILD partition, swap).
2. Row 9 git hygiene → Row 8 conflict cleanup → verify `git status --short` clean in new branch.
3. Row 7 defconfig → `make O=out ARCH=arm64 everpal_5.10_defconfig` must exit 0 before any DTS work.
4. Rows 2-4 DTS + `Makefile dtb-y` → `make ... dtbs` must produce the new `.dtb`.
5. Rows 1+5 panels + touch → `make ... Image.gz`.
6. Row 6 audio (`=m`) → modules build, ramdisk order check.
7. `builder.py --vulkan --kernel out/.../Image.gz --dtbo out/.../dtbo.img` → flash → `dumpsys gpu` expect `4206592/1/0` → `verifydevice.py` → `autobench.py --cpu-only`.
8. Rows 10-13 features. Commit per-tree with `<emoji> [TYPE]:` convention; update Geekbench compare URL across docs on any new record.

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

### Phase 0b — Build-host storage (ASK USER FIRST, then execute)

> Fresh agent: ASK via question tool before touching disks. Settled design: pendrive = OS only, ALL builds live on a dedicated 64GB ext4 partition carved from D. Host audit below is ground truth from Windows (2026-09-21) — re-verify letters on Linux, NVMe naming differs (`nvme0n1pX`, NOT `sdX`).

Host D-drive audit (Windows `Get-Volume`/`Get-Partition`/`Get-CimInstance`, read-only):
- Host: AMD Ryzen 7 4800H 8C/16T, RAM 16557912064 bytes (~16GB) — 16GB build profile confirmed.
- Disk 0: NVMe SAMSUNG 512GB, GPT. P1 200MB EFI, P2 16MB MSR, P3 C 129GB NTFS `AtlasOS` (73GB free), P4 902MB recovery NTFS, P5 D 381GB NTFS `Nemotron` (339GB free).
- NO 64GB volume exists today; NO USB disk attached during audit. User's "D 64GB" = 64GB to be carved from D's free space, NOT an existing partition. NEVER format whole D.
- CRITICAL: repo checkout lives at `D:\EverpalTweaks` — ON D ITSELF. Formatting all of D would destroy the repo + ~40GB user data. Only touch the NEW 64GB partition.
- D is NTFS: kernel `out/` (~25-30GB) + swapfile + ccache (5-10GB) + ZyC Clang (~5GB) CANNOT live on NTFS (symlinks/x-perms/case fail). Native ext4 required.

Questions to ask user on Linux:
1. Confirm RAM (default `16GB`)? `8GB or less` (SSD swap mandatory, go 24-32GB) / `16GB` (16GB SSD swap safety net) / `32GB+` (small 8GB swap or none).
2. Confirm the 64GB carve: `Shrink D by 64GB in Windows Disk Management first` (do this BEFORE Zorin if not done — leave as unallocated), then in Zorin format ONLY the new unallocated block as ext4 `BUILD`. If user refuses to shrink, fallback: D stays NTFS zip-drop only.
3. Confirm mount root (default `/mnt/build`)? Only change if occupied.

Key truth: the new 64GB ext4 holds the swapfile + `out/` + ccache + toolchains + optionally the repo clone. No ZRAM stage — 16GB host RAM carries the build, SSD swap is overflow insurance only. Pendrive stays lean: OS + scripts only.

- Blessed path — 64GB BUILD partition (pendrive OS-only):
```bash
# 0. In Windows first (if not done): Disk Management → shrink D (Nemotron) by 65536 MB → leave Unallocated. Reboot into Zorin.
lsblk -o NAME,SIZE,FSTYPE,LABEL,MOUNTPOINT  # expect: nvme0n1p5 NTFS Nemotron ~355GiB, nvme0n1p6 unallocated ~64GB (new), sda/sdb = USB pendrive — NEVER wipe nvme0n1p3 (C) / p5 (D) / USB
sudo mkfs.ext4 -L BUILD /dev/nvme0n1p6      # ONLY the NEW 64GB partition — triple-check with SIZE + no LABEL
sudo mkdir -p /mnt/build && sudo mount /dev/disk/by-label/BUILD /mnt/build
sudo fallocate -l 16G /mnt/build/swapfile && sudo chmod 600 /mnt/build/swapfile && sudo mkswap /mnt/build/swapfile && sudo swapon /mnt/build/swapfile
echo -e "vm.swappiness=10\nvm.vfs_cache_pressure=75" | sudo tee /etc/sysctl.d/99-everpal-build.conf
mkdir -p /mnt/build/{out,ccache,toolchains,work}
# Option A (recommended): clone repo onto BUILD so EVERYTHING lives there:
# git clone https://github.com/FrontlXOX/EverpalTweaks.git /mnt/build/EverpalTweaks  # then $REPO_ROOT=/mnt/build/EverpalTweaks
# Option B (pendrive checkout): keep repo on USB, redirect heavy dirs to BUILD:
ln -sfn /mnt/build/out $REPO_ROOT/src/trees/kernel/out
export CCACHE_DIR=/mnt/build/ccache
free -h; swapon --show; df -h /mnt/build
```
- Fallback only if user says D must stay NTFS untouched: D = zip-drop only. Swap + `out/`+`ccache` stay on USB persistence ext4 (tight — prune `out/` often), copy finished `*.zip` to D NTFS mount. NEVER place `out/` or `swapfile` directly on NTFS.
- SSD wear: negligible for kernel builds. Speed win BUILD-ext4 (NVMe) vs USB stick is 3-10x on link. Per-boot on live USB: re-run `mount + swapon` (keep a `~/bin/mount-build.sh` on persistence).

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
# - Keep MT6833 clocks, SND_SOC_MT6833_MT6359P (donor has it as =m alongside MT6789_MT6366 — see §4b row 6 for the MT6359→MT6359P rename), COMMON_CLK_MT6833, WALT, freezer
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
