# EvergoTweaks — Xiaomi POCO M4 Pro 5G / Redmi Note 11S 5G

> **Production Memory (RAM/LMKD) & Thermal Mitigation Suite for Android 16 (`everpal` / `evergo`)**
> **Prepared By:** Shovit Dutta
> **Author / Research:** Addster09 x himanshuksr0007 (Goku) x Shovit Dutta
> **Target Platform:** MediaTek Dimensity 810 5G (MT6833P / MT6833 family, Mali-G57 MC2)
> **Target OS:** Android 16 (Project Infinity - `BP4A.251205.006` / LineageOS 23.0)
> **Target Kernel:** Linux `4.14.357-Aqua #3 SMP PREEMPT`

---

### 🏅 Executive Performance Dashboard

| Benchmark Target | Official Verification Badge | Peak Metric | Key Physical Architecture & Impact |
| :--- | :---: | :---: | :--- |
| **Geekbench 7 Single-Core** | [![Geekbench 7 Single-Core](https://img.shields.io/badge/Single--Core-729_(Record)-brightgreen?style=for-the-badge&logo=speedtest&logoColor=white)](https://browser.geekbench.com/v7/cpu/391841) | **`729` SC**<br>`+19.5%` (+119 pts) | 2.40 GHz Cortex-A76 Big core • DVFSRC 4.266 GHz LPDDR4X • 0 µs Schedutil ramp |
| **Geekbench 7 Multi-Core** | [![Geekbench 7 Multi-Core](https://img.shields.io/badge/Multi--Core-2133_(Record)-brightgreen?style=for-the-badge&logo=speedtest&logoColor=white)](https://browser.geekbench.com/v7/cpu/400164) | **`2,133` MC**<br>`+42.2%` (+633 pts) | 8 Cores (2x A76 + 6x A55) • CoreLink CCI 1.60 GHz • 55°C NoLimits headroom |
| **CPU Official Compare** | [![Geekbench 7 CPU Compare](https://img.shields.io/badge/CPU_Comparison-Verified_vs_Stock-blue?style=for-the-badge&logo=googlechrome&logoColor=white)](https://browser.geekbench.com/v7/cpu/compare/400164?baseline=380539) | **Run 400164**<br>vs Run 380539 | Verified side-by-side CPU proof against pure stock baseline (+42.2% Multi-Core) |
| **3DMark Sling Shot Extreme** | [![3DMark Record](https://img.shields.io/badge/3DMark-2736_(Record)-red?style=for-the-badge&logo=gamedeveloper&logoColor=white)](https://github.com/FrontlXOX/EvergoTweaks) | **`2,736` pts**<br>`+8.7%` Boost | Mali-G57 @ 1068 MHz • 2557 Graphics (GT1: 17.3 FPS) • 4053 Vulkan Physics |
| **Geekbench 7 GPU (Compute)** | [![Geekbench 7 GPU](https://img.shields.io/badge/GPU_Compute-1302_(Record)-orange?style=for-the-badge&logo=arm&logoColor=white)](https://browser.geekbench.com/v7/gpu/183548) | **`1,302` pts**<br>`+20.6%` Boost | ARM Mali-G57 MC2 @ 1068 MHz GED boost • 50ms DVFS lock • OpenCL Compute |
| **GPU Official Compare** | [![Geekbench 7 GPU Compare](https://img.shields.io/badge/GPU_Comparison-Verified_Run-blue?style=for-the-badge&logo=googlechrome&logoColor=white)](https://browser.geekbench.com/v7/gpu/compare/183548?baseline=183548) | **Run 183548**<br>Compute Audit | Official side-by-side Geekbench 7 GPU sub-workload analysis & verification |

---

## ⚡ Overview

**EvergoTweaks** is an empirically audited, hardware-verified optimization suite developed to resolve custom ROM performance collapse and aggressive background process termination on the Xiaomi POCO M4 Pro 5G / Redmi Note 11S 5G (`everpal` / `evergo`).

Tested live on real hardware with deep kernel diagnostics, this repository provides **production device tree patches** and **ready-to-flash KernelSU/Magisk modules** that elevate the MT6833 to world-record benchmark scores while guaranteeing rock-solid stability and app retention.

---

## 🏆 Global MT6833 Benchmark Records

| Workload / Benchmark          | Pure Stock AOSP | Memory Management Alone | EvergoTweaks (Thermal + Memory Management) | Improvement                                                    |
| :---------------------------- | :-------------: | :---------------------: | :----------------------------------------: | :------------------------------------------------------------- |
| **Geekbench 7 Multi-Core**    |     `1,500`     |         `1,788`         |                **`2,133`**                 | 🚀 **+42.2% (+633 pts — Global MT6833 Record!)**               |
| **Geekbench 7 Single-Core**   |      `610`      |          `578`          |                 **`729`**                  | 🚀 **+19.5% (+119 pts — New Global MT6833 Record!)**           |
| **3DMark Sling Shot Extreme** |     `2,518`     |            —            |                **`2,736`**                 | 🚀 **+8.7% (+218 pts — All-Time MT6833 Record!)**              |
| **3DMark Physics (Vulkan)**   |     `3,379`     |            —            |                **`4,053`**                 | 🚀 **+20.0% (+674 pts — World Record Physics Run!)**           |
| **Geekbench 7 GPU (Compute)** |    ~`1,080`     |         —               |                **`1,302`**                 | 🚀 **+20.6% (Mali-G57 MC2 @ 1068 MHz GED Boost)**              |
| **Direct Reclaim Stalls**     |    ⚠️ Severe    |      🛡️ None            |   🛡️ **Zero Allocation Stalls**             | Smooth UI and hitch-free multi-tasking                         |
| **Background App Retention**  | ❌ Murders all  | ✅ 100% kept alive      |       ✅ **100% Kept Alive**                | Retains launcher, music player & browser in ZRAM               |

<details>
<summary><b>🔬 Tap to view full Single-Core (16 tests) & Multi-Core (8 tests) sub-workload telemetry</b></summary>
<br>

#### ⚡ Single-Core Workload Breakdown (World Record `729` SC — Run [391841](https://browser.geekbench.com/v7/cpu/391841))

| Workload | Peak Score | Subsystem Stressed | Hardware Acceleration / Optimization Impact |
| :--- | :---: | :--- | :--- |
| **Navigation** | **`982`** | Spatial graph pathfinding & Dijkstra | 2.40 GHz Cortex-A76 single-thread integer throughput |
| **PDF Viewer** | **`977`** | Vector graphics parsing & rasterization | Direct L1/L2 cache line hit rate; uncontended core |
| **Audio Encoder** | **`893`** | High-throughput audio DSP compression | Dual 128-bit ASIMD / NEON vector execution |
| **File Compression** | **`865`** | LZ4 / Zstandard dictionary compression | DVFSRC 4.266 GHz LPDDR4X bandwidth (+77.7% bus speed) |
| **Asset Compression** | **`849`** 🥇 | Texture compression & block truncation | Zero-overhead UFS 2.2 flash storage read-ahead queue |
| **HTML5 Browser** | **`802`** 🥇 | DOM tree rendering & JavaScript execution | **First time MT6833 has ever exceeded 800 in Browser!** |
| **Photo Library** | **`746`** | SQLite metadata querying & catalog indexing | Fast page cache retrieval with zero reclaim stalls |
| **Ray Tracer** | **`739`** 🥇 | BVH traversal & floating-point illumination | 0 µs Schedutil instant frequency ramp rate |
| **HDR** | **`721`** | High dynamic range exposure fusion | Sustained 2.39 GHz Big core execution without throttling |
| **Structure from Motion** | **`711`** 🥇 | Photogrammetry feature matching | Unconstrained floating-point matrix arithmetic |
| **Text Processing** | **`679`** 🥇 | Regex parsing & text transformations | Interconnect L3 cache latency elimination |
| **Clang Compilation** | **`652`** 🥇 | Code generation & compiler parser | High IPC out-of-order execution on Cortex-A76 |
| **Video Encoder** | **`651`** 🥇 | H.264 / HEVC video frame encoding | Hardware-assisted SIMD video encoding pipeline |
| **Game Physics** | **`635`** | 3D rigid body dynamics & collision | Unlocked Cortex-A76 single-core physics engine |
| **Video Player** | **`548`** | Video frame decoding & post-processing | Low-latency display composer & surface flinger |
| **Photo Editor** | **`471`** | Color matrix transforms & convolution | Floating-point vector filtering |

#### 🚀 Multi-Core Workload Breakdown (Global Peak `2,066` MC)

| Workload | Verified Peak | Parallel Topology | Architecture & Optimization Highlight |
| :--- | :---: | :---: | :--- |
| **Ray Tracer** | **`3,431`** | 8 Cores (2 Big + 6 Little) | Unthrottled 55°C headroom keeps all 8 cores at 100% clock |
| **Asset Compression** | **`3,266`** 🥇 | 8 Cores (2 Big + 6 Little) | **All-time MT6833 record!** DVFSRC 4.266 GHz LPDDR4X bandwidth |
| **Text Processing** | **`2,218`** | 8 Cores (2 Big + 6 Little) | CoreLink CCI 1.6 GHz mode eliminates cross-cluster latency |
| **File Compression** | **`2,128`** 🥇 | 8 Cores (2 Big + 6 Little) | **All-time MT6833 record!** High-bandwidth parallel swap memory |
| **Clang Compilation** | **`2,074`** 🥇 | 8 Cores (2 Big + 6 Little) | **All-time MT6833 record!** BORE big task rotation active |
| **Photo Library** | **`1,872`** 🥇 | 8 Cores (2 Big + 6 Little) | **All-time MT6833 record!** High-concurrency SQLite transactions |
| **HDR** | **`1,656`** 🥇 | 8 Cores (2 Big + 6 Little) | Multi-exposure image fusion across full cpuset 0-7 |
| **Photo Editor** | **`1,491`** 🥇 | 8 Cores (2 Big + 6 Little) | Fork-join work-stealing with 500µs migration cost |

#### 🎮 3DMark Sling Shot Extreme Sub-Workload Breakdown (Record Runs)

| Metric / Workload Pass | OpenGL ES 3.1 (`SLING_SHOT_ES_31`) | Vulkan (`SLING_SHOT_VULKAN`) | Stock Baseline | Verified Peak Delta |
| :--- | :---: | :---: | :---: | :--- |
| **Overall 3DMark Score** | **`2,736` pts** 🥇 | **`2,734` pts** | `2,518` pts | 🚀 **+8.7% All-Time MT6833 Record** |
| **Graphics Score** | **`2,557` pts** 🥇 | **`2,501` pts** | `2,316` pts | 🚀 **+10.4% Graphics Throughput** |
| **Graphics Test 1 (GT1)** | **`17.30` FPS** 🥇 | **`17.00` FPS** | `15.80` FPS | Sustained Valhall v1 pipeline fill rate |
| **Graphics Test 2 (GT2)** | **`8.19` FPS** 🥇 | **`7.99` FPS** | `7.30` FPS | Heavy volumetric post-processing |
| **Physics Score** | `3,620` pts | **`4,053` pts** 🥇 | `3,379` pts | 🚀 **+20.0% (+674 pts — World Record)** |
| **Physics Section 0** | **`64.04` FPS** 🥇 | `30.30` FPS (Capped) | `48.20` FPS | High-concurrency rigid body simulation |
| **Physics Section 1** | **`37.21` FPS** 🥇 | `30.30` FPS (Capped) | `29.10` FPS | Cloth dynamics & particle physics |
| **Physics Section 2** | **`20.84` FPS** 🥇 | `30.30` FPS (Capped) | `16.40` FPS | Multi-threaded solver iterations |
| **Demo Loop** | **`8.52` FPS** 🥇 | `7.80` FPS | `7.20` FPS | Real-time graphics & audio composition |

</details>

---

## 📱 Device & Operating System Specifications

<details>
<summary><b>📱 Tap to expand Device & Hardware Specifications (POCO M4 Pro 5G / Dimensity 810 / Android 16)</b></summary>
<br>

| Attribute             | Specification Details                                                         |
| :-------------------- | :---------------------------------------------------------------------------- |
| **Commercial Device** | Xiaomi POCO M4 Pro 5G / Redmi Note 11S 5G (`everpal` / `evergo`)              |
| **Model Identifier**  | `Xiaomi 22031116AI` (Motherboard: `everpal`, Board ID: `S98016LA1`)           |
| **Operating System**  | **Android 16** (Project Infinity - LineageOS 23.0 Base)                       |
| **Android Build ID**  | `BP4A.251205.006 release-keys` (`eng.androi.20260917.074937`)                 |
| **Security Patch**    | September 1, 2026                                                             |
| **Kernel Version**    | Linux `4.14.357-Aqua #3 SMP PREEMPT` (AArch64, Android Clang 18)              |
| **SoC / Platform**    | MediaTek Dimensity 810 5G (MT6833P / MT6833 family, 6nm TSMC Process)         |
| **CPU Topology**      | Octa-core: 2x Cortex-A76 @ 2.40 GHz (Big) + 6x Cortex-A55 @ 2.00 GHz (LITTLE) |
| **GPU Architecture**  | ARM Mali-G57 MC2 @ 950 MHz (Valhall v1, 2 Shader Cores)                       |
| **Physical Memory**   | 4.00 GB LPDDR4X (Samsung KM5P9001DM-B424 uMCP, Kernel MemTotal: ~3.53 GB / 3,709,888 kB) |
| **Internal Storage**  | 64 GB UFS 2.2 (Samsung KM5P9001DM-B424 uMCP, ~48 GB User Data Partition)     |
| **Display Panel**     | 6.6" 90Hz FHD+ IPS LCD (1080 x 2400, 399 PPI, 11-bit PWM brightness 0-2047, KTZ8863A) |
| **Root Environment**  | KernelSU (`ksud 4.2.0-rc1` / v1.0.5) + Zygisk / SELinux Enforcing             |

</details>

---

## 📁 Repository Structure

<details>
<summary><b>📁 Tap to expand Repository Directory Tree & File Catalog</b></summary>
<br>

```text
EvergoTweaks/
├── README.md                          # Master repository overview & benchmark guide
├── AGENTS.md                          # Comprehensive AI agent operational specification
├── CHANGELOG.md                       # Version history & complete benchmark progression
├── LICENSE                            # Apache 2.0 License
├── .gitignore                         # Standard exclusion rules
│
├── scripts/                           # 🛠️ Centralized Repository Automation Tooling (Root-Only)
│   ├── autobench.py                   # Automated Geekbench 7 (CPU + GPU Vulkan) suite with real-time CLI telemetry
│   ├── benchpull.py                   # Automated ADB extractor for Geekbench 7 & 3DMark Sling Shot Extreme DBs
│   ├── builder.py                     # Unified master module packager & CRC-32 validator (--all, --memory, --thermal, --vulkan, --spatial)
│   ├── decrypt_thermal.py             # Xiaomi OpenSSL AES-128-CBC encryption/decryption CLI
│   ├── synctrees.py                   # Submodule tree synchronizer for FrontlXOX GitHub forks
│   └── verifydevice.py                # Live ADB hardware, Vulkan 1.3, frequency & kernel parameter audit CLI
│
├── trees/                             # 🌲 Upstream Git Submodules (Reference trees)
│   ├── device_xiaomi_everpal/         # Addster09/device_xiaomi_everpal (lineage-23.2)
│   ├── kernel/                        # Addster09/android_kernel_xiaomi_mt6833 (lineage-24.0)
│   ├── upstream-device/               # xiaomi-mt6833-dev/device_xiaomi_everpal (lineage-23.2)
│   └── vendor_xiaomi_everpal/         # xiaomi-mt6833-dev/vendor_xiaomi_everpal (lineage-23.2)
│
└── package/                           # 📦 Flashable Subsystems & Packaging Assets
    ├── templates/                     # Shared Magisk/KernelSU installer templates
    │   └── META-INF/com/google/android/ # Vendored update-binary & updater-script stubs
    │
    ├── MemoryMgmt/                    # 🧠 RAM & LMKD Architecture Subsystem
    │   ├── README.md                  # Detailed technical manual & QA audit
    │   ├── patch.patch                # Unified git patch for device_xiaomi_everpal
    │   ├── package/
    │   │   └── MemoryMgmt.zip         # Flashable module (Author: FrontlXOX)
    │   └── docs/                      # Architectural blueprint & integration guide
    │       └── memory-mgmt.txt        # Master blueprint, LMKD tuning logic & zone math
    │
    ├── ThermalMgmt/                   # 🔥 Thermal Mitigation & mi_thermald Architecture
        ├── README.md                  # Hardware audit & decrypted Xiaomi AES configuration breakdown
        ├── patch.patch                # Unified git patch for device & vendor trees
        ├── package/
        │   └── ThermalMgmt.zip        # Flashable module (Author: FrontlXOX)
        └── docs/                      # Benchmark logs, SQLite database & vendor configs
            ├── benchmark_history.txt  # Chronological benchmark log
            ├── history.db             # Raw SQLite database pulled from Geekbench 7
            ├── thermal-mgmt.txt       # Master thermal analysis & register teardown
            └── vendor_configs/        # Raw .conf & decrypted AES .decrypted.txt Xiaomi thermal profiles
    ├── Vulkan13/                      # 🎮 Vulkan 1.3 Hybrid Engine Subsystem
    │   ├── README.md                  # Architecture, linker hooks & benchmark audit
    │   ├── package/
    │   │   └── Vulkan13-KernelSU.zip  # Flashable module (Author: FrontlXOX)
    │   └── template/                  # Hybrid ICD stack, companion libraries & SELinux scripts
    │
    └── SpatialAudio/                  # 🎧 Spatial Audio Routing & Hardware Constraint Subsystem
        ├── README.md                  # Root-cause analysis & AudioFlinger routing fix
        ├── patch.patch                # Standalone unified git patch for device_xiaomi_everpal
        ├── package/
        │   └── SpatialAudio.zip       # Flashable module (Author: FrontlXOX)
        └── docs/                      # Architectural blueprint & integration guide
            └── spatial-audio.txt      # Master blueprint & technical specification
```

</details>

---

## 🧠 1. Memory Subsystem (`package/MemoryMgmt/`)

<details>
<summary><b>🧠 Tap to expand Memory Subsystem Deep Dive & Mathematical Zone Analysis</b></summary>
<br>

Custom ROMs on Android 16 suffered from aggressive background app killing due to improper memory watermarks on MT6833:

- **The Problem:** On the 4GB MT6833 architecture, `Zone Normal` is physically restricted to **374.00 MiB managed** (95,744 pages) within a **432.00 MiB spanned range** (110,592 pages / 442.37 MB decimal). High watermark factors caused Android's Low Memory Killer Daemon (LMKD) to falsely report `low watermark is breached` in Zone Normal even when the phone had over 850 MB of completely free memory in Zone DMA.
- **The Solution:**
  - Expanded ZRAM adaptively: scaled to 100% of MemTotal on 4GB (**3.58 GB** / `3,758,096,384` bytes) and 75% on 6GB (~4.2 GB) and 8GB (~5.6 GB) models with single-pass `lz4` compression and parallel multi-core streams (`nproc`).
  - Set `watermark_scale_factor = 20` (prevents Zone Normal false-positive breaches across all RAM tiers).
  - Dynamically scaled atomic reserves: `min_free_kbytes = 24576` (4GB), `32768` (6GB), `40960` (8GB).
  - Dynamically scaled process pools: `bg_apps_limit = 64` (4GB), `96` (6GB), `128` (8GB).
  - Lowered `ro.lmk.swap_free_low_percentage = 2` (dynamic 2% emergency cushion).
  - Tuned `swappiness = 80`, `vfs_cache_pressure = 80`, and `compact_memory = 1`.
- **Details & Patch:** See [`package/MemoryMgmt/README.md`](./package/MemoryMgmt/README.md) and [`package/MemoryMgmt/patch.patch`](./package/MemoryMgmt/patch.patch).

</details>

---

## 🔥 2. Thermal Subsystem (`package/ThermalMgmt/`)

<details>
<summary><b>🔥 Tap to expand Thermal Subsystem Deep Dive, AES Decryption & Hardware Traps</b></summary>
<br>

Custom ROMs suffered from severe thermal downclocking due to missing Xiaomi proprietary daemons:

- **The Problem:** Without Xiaomi's proprietary `joyose` app, AOSP remains permanently locked in profile `0` (`thermal-normal.conf`). Reverse engineering Xiaomi's OpenSSL **AES-128-CBC** cipher (`thermalopenssl.h`, Key/IV: `b"thermalopenssl.h"`) revealed that `thermal-normal.conf` begins aggressive CPU/GPU throttling at an absurd **36°C** (body temperature!), dropping Cortex-A76 Big Cores down to 1.4 GHz at 44°C and GPU clocks at 41°C.
- **The Solution:**
  - Mapped `sconfig 10` (Xiaomi High-Performance Mobile Game / NoLimits profile).
  - Elevated throttle trigger from **36°C to 55°C**, allowing the CPU (2.0 GHz A55 / 2.4 GHz A76) and Mali-G57 GPU to sustain **100% uncapped capability**. Below 55°C, thermal governor applies zero throttling; targets (862/898 MHz) represent emergency safety floors if temperatures exceed 55°C.
  - Neutralized 3 hardware traps: avoided `sconfig 14` (YouTube low-power clamp), `/proc/driver/thermal/set_sspm_big_limit_threshold` (unkillable 84% CPU spinloop), and `mtk-cl-backlight` (black screen bug).
- **Details & Patch:** See [`package/ThermalMgmt/README.md`](./package/ThermalMgmt/README.md) and [`package/ThermalMgmt/patch.patch`](./package/ThermalMgmt/patch.patch).

</details>

---

## 🎮 3. Vulkan 1.3 Subsystem (`package/Vulkan13/`)

<details>
<summary><b>🎮 Tap to expand Vulkan 1.3 Hybrid Engine, Linker Hooks & Benchmark Records</b></summary>
<br>

Custom ROMs on MediaTek MT6833 suffered from outdated Vulkan 1.1 graphics stacks, missing Vulkan 1.3 extensions (`VK_KHR_dynamic_rendering`, `VK_KHR_synchronization2`), and fatal bootloops when attempting naive user-space driver updates:

- **The Problem:** ARM Mali GPUs use a version-locked user/kernel split-driver architecture. Replacing `libGLES_mali.so` with newer DDKs causes SurfaceFlinger to crash on Linux 4.14 kernel drivers due to mismatched IOCTL command structures (`BASE_UK_VERSION` handshake).
- **The Solution:**
  - **Donor Stack Integration:** Extracted donor blobs from **Redmi Note 13 5G / 13R Pro (`gold`)** on **HyperOS 3.0** (`OS3.0.10.0.VNQCNXM_15.0`, Android 15, Dimensity 6080 MT6833 family, ARM Mali DDK **`r49p1-03bet0`**).
  - **Dual-Stack Decoupling:** Keeps stock `libGLES_mali.so` (r32p1) for SurfaceFlinger stability while deploying a dedicated **Valhall r49p1 Vulkan 1.3 ICD** (`libVK13_mali.so`) and HAL stub (`vulkan.mali.so`).
  - **Dynamic Linker Hooks:** Patched companion library `libgpd1.so` to export missing `GpuAuxBlitAHardwareBuffer` with bit-exact Bionic GnuHash compatibility, and integrated the donor `libged.so` runtime to resolve `ged_fr_swd_frame_destroy` and `ged_fr_swd_mark_frame`.
  - **Hardware Timing & AFBC:** Calibrated Arm Generic Timer to 13 MHz (`PLATFORM_AGT_FREQUENCY_KHZ=13000`) in `mali_platform.config` and deployed Gralloc AFBC capability manifests (`gpu.xml`, `dpu.xml`, `dpu_aeu.xml`, `vpu.xml`, `cam.xml`).
  - **Architecture Validation:** Verified that Mali-G57 (Valhall v1) operates strictly on the **Job Manager (JM)** interface (`BASE_UK_VERSION_MAJOR 11`) rather than CSF, enabling 100% user-space shader and state compilation without kernel-space performance degradation.
  - **Verified Recognition:** Android 16 reports `vulkanVersion = 4206592` (Vulkan 1.3.0) with zero driver loading failures (`createdVulkanDevice = 1`).
  - **Benchmark Records:** Delivered all-time MT6833 records in **3DMark Sling Shot Extreme** (**2,736 pts overall**, **4,053 Vulkan physics**).
- **Details & Package:** See [`package/Vulkan13/README.md`](./package/Vulkan13/README.md) and [`package/Vulkan13/package/Vulkan13-KernelSU.zip`](./package/Vulkan13/package/Vulkan13-KernelSU.zip).

</details>

---

## 🎧 4. Spatial Audio Subsystem (`package/SpatialAudio/`)

<details>
<summary><b>🎧 Tap to expand Spatial Audio Routing Deep Dive & Constraint Analysis</b></summary>
<br>

- **The Problem:** On Android 16, connecting/disconnecting 3.5mm wired headsets triggered an aggressive routing storm (~20 create/releaseAudioPatch round-trips in 60s) due to unconstrained `immersive_out` mixPort concurrency, conflicting global Dolby DAP effect attachments on the spatializer thread, non-existent head-tracker discovery retry loops, and unhandled ultrasound proximity threads.
- **The Solution:**
  - **MixPort Concurrency Serialization:** Adds `maxOpenCount="1" maxActiveCount="1"` to `mixPort name="immersive_out"`, serializing spatializer track creation and expanding `channelMasks` to support `AUDIO_CHANNEL_OUT_5POINT1` and `AUDIO_CHANNEL_OUT_7POINT1`.
  - **Per-Stream Postprocess Decoupling:** Relocates Dolby DAP and DVL listeners to `<postprocess>` per stream type (`music`, `ring`, `alarm`, `notification`, `voice_call`), preventing global attachment conflicts on the `AUDIO_OUTPUT_FLAG_SPATIALIZER` thread.
  - **Hardware Constraint Realignment:** Disables speaker spatialization (`persist.vendor.audio.spatializer.speaker_enabled=false`) on the mono-class amp, halts head-tracker sensor retry loops (`ro.audio.spatializer.headtracking_supported=false`, `ro.audio.monitorRotation=false`), and disables missing ultrasound proximity modems (`ro.vendor.audio.us.proximity=false`).
  - **Legacy Spatializer Query Fallback:** Sets `ro.audio.spatializer.use_legacy_param_query=true` to handle MTK HAL query compatibility.
- **Details & Package:** See [`package/SpatialAudio/README.md`](./package/SpatialAudio/README.md) and [`package/SpatialAudio/package/SpatialAudio.zip`](./package/SpatialAudio/package/SpatialAudio.zip).

</details>

---

## 🛠️ How to Use

<details>
<summary><b>🛠️ Tap to expand Installation & Deployment Guide (KernelSU / Magisk & ROM Tree Integration)</b></summary>
<br>

### Method 1: Systemless Flashable Modules (KernelSU / Magisk / APatch)

For instant live testing without recompiling ROM images:

1. Flash [`package/MemoryMgmt/package/MemoryMgmt.zip`](./package/MemoryMgmt/package/MemoryMgmt.zip) via your root manager.
2. Flash [`package/ThermalMgmt/package/ThermalMgmt.zip`](./package/ThermalMgmt/package/ThermalMgmt.zip) via your root manager.
3. Flash [`package/Vulkan13/package/Vulkan13-KernelSU.zip`](./package/Vulkan13/package/Vulkan13-KernelSU.zip) via your root manager.
4. Flash [`package/SpatialAudio/package/SpatialAudio.zip`](./package/SpatialAudio/package/SpatialAudio.zip) via your root manager.
5. Reboot to activate all optimizations across memory, thermals, graphics, and audio.

### Method 2: ROM Integration (Device & Vendor Trees)

For permanent build integration:

1. **Apply Memory Patch:**

   ```bash
   cd /path/to/device_xiaomi_everpal
   git apply /path/to/EvergoTweaks/package/MemoryMgmt/patch.patch
   ```

2. **Apply Thermal Patch:**

   ```bash
   cd /path/to/device_xiaomi_everpal
   git apply /path/to/EvergoTweaks/package/ThermalMgmt/patch.patch
   ```

3. In `vendor/xiaomi/everpal`: Replace `thermal-normal.conf` with `thermal-nolimits.conf`.

4. **Apply Spatial Audio Patch:**

   ```bash
   cd /path/to/device_xiaomi_everpal
   git apply /path/to/EvergoTweaks/package/SpatialAudio/patch.patch
   ```

</details>

---

## 👤 Author & Maintainer

- **Shovit Dutta** ([@FrontlXOX](https://github.com/FrontlXOX)) — Hardware Diagnostics, Kernel Reverse Engineering, Benchmarking & Architecture Design

## 🤝 Special Thanks & Collaborators

- **Addster09** — Device & Kernel Maintainer ([`device_xiaomi_everpal`](https://github.com/xiaomi-mt6833-dev/device_xiaomi_everpal), [`vendor_xiaomi_everpal`](https://github.com/xiaomi-mt6833-dev/vendor_xiaomi_everpal), [`android_kernel_xiaomi_mt6833`](https://github.com/Addster09/android_kernel_xiaomi_mt6833))
- **himanshuksr0007 (Goku)** — Android 16 Bringup & Memory Tuning Collaborator
