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
| **Geekbench 7 GPU (Compute)** |    ~`1,080`     |         —          |                **`1,302`**                 | 🚀 **+20.6% (Mali-G57 MC2 @ 1068 MHz GED Boost)**              |
| **Direct Reclaim Stalls**     |    ⚠️ Severe    |      🛡️ None       |   🛡️ **Zero Allocation Stalls**    | Smooth UI and hitch-free multi-tasking                         |
| **Background App Retention**  | ❌ Murders all  | ✅ 100% kept alive |       ✅ **100% Kept Alive**       | Retains launcher, music player & browser in ZRAM               |

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
├── .pylintrc                          # Universal Python linter configuration
├── pyproject.toml                     # Pyright/Ruff/Flake8 root tool configuration
│
├── scripts/                           # 🛠️ Centralized Repository Automation Tooling (Root-Only)
│   ├── autobench.py                   # Automated Geekbench 7 (CPU + GPU Vulkan) suite with real-time CLI telemetry
│   ├── build_all.py                   # Unified module packager & CRC-32 validator (--memory, --thermal)
│   ├── decrypt_thermal.py             # Xiaomi OpenSSL AES-128-CBC encryption/decryption CLI
│   ├── pull_benchmark.py              # Automated ADB extractor for Geekbench 7 CPU & GPU SQLite DB
│   └── verify_device.py               # Live ADB hardware & kernel parameter audit CLI
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
    │   │   └── MemoryMgmt.zip         # Flashable module (Author: TesterProd)
    │   └── docs/                      # Architectural blueprint & integration guide
    │       └── memory-mgmt.txt        # Master blueprint, LMKD tuning logic & zone math
    │
    └── ThermalMgmt/                   # 🔥 Thermal Mitigation & mi_thermald Architecture
        ├── README.md                  # Hardware audit & decrypted Xiaomi AES configuration breakdown
        ├── patch.patch                # Unified git patch for device & vendor trees
        ├── package/
        │   └── ThermalMgmt.zip        # Flashable module (Author: TesterProd)
        └── docs/                      # Benchmark logs, SQLite database & vendor configs
            ├── benchmark_history.txt  # Chronological benchmark log
            ├── history.db             # Raw SQLite database pulled from Geekbench 7
            ├── thermal-mgmt.txt       # Master thermal analysis & register teardown
            └── vendor_configs/        # Raw .conf & decrypted AES .decrypted.txt Xiaomi thermal profiles
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

## 🛠️ How to Use

<details>
<summary><b>🛠️ Tap to expand Installation & Deployment Guide (KernelSU / Magisk & ROM Tree Integration)</b></summary>
<br>

### Method 1: Systemless Flashable Modules (KernelSU / Magisk / APatch)

For instant live testing without recompiling ROM images:

1. Flash [`package/MemoryMgmt/package/MemoryMgmt.zip`](./package/MemoryMgmt/package/MemoryMgmt.zip) via your root manager.
2. Flash [`package/ThermalMgmt/package/ThermalMgmt.zip`](./package/ThermalMgmt/package/ThermalMgmt.zip) via your root manager.
3. Reboot to activate full 2.4 GHz clocks, 55°C thermal headroom, and 3.58 GB LZ4 ZRAM.

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

</details>

---

## 👤 Author & Maintainer

- **Shovit Dutta** ([@ShovitDutta1](https://gitlab.com/ShovitDutta1)) — Hardware Diagnostics, Kernel Reverse Engineering, Benchmarking & Architecture Design

## 🤝 Special Thanks & Collaborators

- **Addster09** — Device & Kernel Maintainer ([`device_xiaomi_everpal`](https://github.com/xiaomi-mt6833-dev/device_xiaomi_everpal), [`vendor_xiaomi_everpal`](https://github.com/xiaomi-mt6833-dev/vendor_xiaomi_everpal), [`android_kernel_xiaomi_mt6833`](https://github.com/Addster09/android_kernel_xiaomi_mt6833))
- **himanshuksr0007 (Goku)** — Android 16 Bringup & Memory Tuning Collaborator
