# AGENTS.md — EvergoTweaks Optimization Suite

> **AI Agent Context & Master Operational Specification for EvergoTweaks**
> Target Device: **Xiaomi POCO M4 Pro 5G / Redmi Note 11S 5G (`everpal` / `evergo`)**
> Target SoC: **MediaTek Dimensity 810 5G (MT6833P / MT6833 family)**
> Target OS: **Android 16** (Project Infinity / LineageOS 23.0 base)
> Target Kernel: **Linux 4.14.357-Aqua #3 SMP PREEMPT**
> Primary Remote: `https://gitlab.com/ShovitDutta1/EvergoTweaks`

---

## 1. Project Purpose & System Identity

**EvergoTweaks** is an empirically audited, hardware-verified optimization suite developed to resolve custom ROM performance degradation, thermal throttling, and aggressive background process termination on the Xiaomi POCO M4 Pro 5G / Redmi Note 11S 5G (`everpal` / `evergo`).

This repository maintains two production-grade subsystems:

1. **`MemoryMgmt/`** — Resolves MT6833 `Zone Normal` memory exhaustion, tunes Android 16 LMKD watermarks, and scales ZRAM to 3.58 GB LZ4 for zero direct reclaim stalls and 100% background app retention.
2. **`ThermalMgmt/`** — Decrypts Xiaomi OpenSSL AES-128-CBC thermal profiles, decouples thermal regulation from missing proprietary `joyose`, maps `sconfig 10` (NoLimits profile with 55°C headroom), and uncaps Cortex-A76 Big cores (2.4 GHz) and Mali-G57 GPU clocks.

### Authorship & Collaborator Attribution

- **Author & Maintainer:** Shovit Dutta
- **Special Thanks & Collaborators:**
  - **Device & Kernel Maintainer:** Addster09 ([`device_xiaomi_everpal`](https://github.com/xiaomi-mt6833-dev/device_xiaomi_everpal), [`vendor_xiaomi_everpal`](https://github.com/xiaomi-mt6833-dev/vendor_xiaomi_everpal), [`android_kernel_xiaomi_mt6833`](https://github.com/Addster09/android_kernel_xiaomi_mt6833))
  - **Android 16 Bringup & Memory Tuning:** himanshuksr0007 (Goku / Sudoku)
- **Flashable Module Author (`module.prop` metadata only):** `TesterProd`

---

## 2. Hardware & Operating System Specifications

| Component             | Technical Specification                                                       |
| :-------------------- | :---------------------------------------------------------------------------- |
| **Commercial Device** | Xiaomi POCO M4 Pro 5G / Redmi Note 11S 5G                                     |
| **Model Number**      | `Xiaomi 22031116AI` (Board: `everpal`, Board ID: `S98016LA1`, SKU: `India`)   |
| **Platform / SoC**    | MediaTek Dimensity 810 5G (MT6833P / MT6833 family, TSMC 6nm process)         |
| **CPU Topology**      | Octa-core: 2x Cortex-A76 @ 2.40 GHz (Big) + 6x Cortex-A55 @ 2.00 GHz (LITTLE) |
| **GPU Architecture**  | ARM Mali-G57 MC2 @ 950 MHz - 1068 MHz (Valhall v1, 2 Shader Cores)            |
| **Physical Memory**   | 4.00 GB LPDDR4X (Samsung KM5P9001DM-B424 uMCP, Kernel MemTotal: ~3.53 GB / 3,709,888 kB) |
| **Internal Storage**  | 64 GB UFS 2.2 (Samsung KM5P9001DM-B424 uMCP, ~48 GB User Data Partition)     |
| **Display Panel**     | 6.6" 90Hz FHD+ IPS LCD (1080 x 2400, 399 PPI, 11-bit PWM brightness 0-2047, KTZ8863A) |
| **Operating System**  | Android 16 (Project Infinity - LineageOS 23.0 Base)                           |
| **Android Build ID**  | `BP4A.251205.006 release-keys` (`eng.androi.20260917.074937`)                 |
| **Security Patch**    | September 1, 2026                                                             |
| **Kernel Version**    | Linux `4.14.357-Aqua #3 SMP PREEMPT` (AArch64, Android Clang 18)              |
| **Root Environment**  | KernelSU (`ksud 4.2.0-rc1` / v1.0.5) + Zygisk / SELinux Enforcing             |

---

## 3. Core Subsystems & Technical Deep Dives

### A. Memory Subsystem (`MemoryMgmt/`)

##### The MT6833 Memory Zone Bottleneck

On the 4GB MT6833/MT6833P architecture, physical RAM is segmented into three kernel memory zones:

1. `Zone DMA`: ~2,670 MB managed (683,696 pages, general DMA & bulk user memory)
2. `Zone Normal`: **~374.00 MiB managed** (95,744 pages) | **432.00 MiB spanned** (110,592 pages / 442.37 MB decimal)
3. `Zone Movable` (CMA): ~578 MB managed (148,032 pages reserved for camera/multimedia allocations)
*Total managed: 927,472 pages (3,709,888 kB / ~3.53 GB Linux MemTotal from 4GB physical LPDDR4X).*

> **Mathematical Distinction:**  
> - **Spanned Range:** `110,592 pages` = `442,368 KB` = **`432.00 MiB`** (binary) / **`442.37 MB`** (decimal).  
> - **Managed Pages:** `95,744 pages` = `382,976 KB` = **`374.00 MiB`** (binary) / **`382.98 MB`** (decimal).  
> Previous diagnostic references cited either the total physical spanned space (~442MB) or post-reservation managed pages (~374MB).

**The Failure Mechanism:** Default AOSP configurations utilize high watermark multipliers (`watermark_scale_factor = 100` to `200`). Because `Zone Normal` is physically restricted to only ~374 MiB managed, inflated watermarks force `Zone Normal` into persistent `low watermark is breached` states under moderate app loading—even when `Zone DMA` has over 850 MB of completely free, unfragmented physical RAM. This triggers Android 16's Low Memory Killer Daemon (`lmkd`) to aggressively kill background launchers, media players, and browser processes.

#### Production Solution & Tunables

Applied via `package/MemoryMgmt/patch.patch` (`device_xiaomi_everpal`) and `package/MemoryMgmt/package/MemoryMgmt.zip`:

- **Adaptive ZRAM Scaling:** Scaled dynamically to 100% of MemTotal on 4GB variants (**3.58 GB** / `3,758,096,384` bytes) and 75% of MemTotal on 6GB (~4.2 GB) and 8GB (~5.6 GB) variants using single-pass `lz4` compression with dynamic `max_comp_streams = $(nproc)` (8 parallel streams).
- **Watermark Factor:** Scaled down to `vm.watermark_scale_factor = 20` (prevents false-positive direct reclaim storms across all zones).
- **Proportional Atomic Headroom:** `vm.min_free_kbytes` dynamically calibrated by RAM tier: `24,576 KB` (4GB), `32,768 KB` (6GB), or `40,960 KB` (8GB).
- **Adaptive Process Pools:** `bg_apps_limit` scales dynamically: 64 cached (4GB), 96 cached (6GB), 128 cached (8GB).
- **Memory Compaction:** `vm.compact_memory = 1` armed at boot.
- **Kernel VM Swappiness:** `vm.swappiness = 80`, `vm.vfs_cache_pressure = 80`.
- **LMKD Threshold:** `ro.lmk.swap_free_low_percentage = 2` (dynamic 2% emergency reserve floor, preventing premature app murders when swap space is abundant).

---

### B. Thermal Subsystem (`package/ThermalMgmt/`)

#### The Xiaomi Joyose Dependency & AES-128-CBC Cipher

Xiaomi MT6833 stock firmware relies on `mi_thermald` interacting with a proprietary MIUI/HyperOS daemon: `com.xiaomi.joyose`. In pure AOSP and custom ROMs, `joyose` is absent. Consequently:

- `mi_thermald` defaults permanently to profile `0` (`thermal-normal.conf`).
- All vendor thermal configurations located in `/vendor/etc/` are encrypted using OpenSSL **AES-128-CBC** with static key and IV defined in `thermalopenssl.h`: **`b"thermalopenssl.h"`** (16 bytes ASCII).
- Reverse engineering of decrypted `thermal-normal.conf` revealed that Xiaomi begins aggressive CPU and GPU throttling at an absurd **36°C** (normal human skin temperature). Cortex-A76 Big cores drop to 1.4 GHz at 44°C, and GPU clocks throttle at 41°C.

#### Production Solution (`sconfig 10` & Hardware Compute Master v2.4)

Applied via `package/ThermalMgmt/patch.patch` and `package/ThermalMgmt/package/ThermalMgmt.zip`:

- Enforces `sconfig 10` (`thermal-mgame.conf` / `thermal-nolimits.conf`), shifting the thermal throttling ceiling from **36°C to 55°C**.
- Below 55°C, thermal governor applies zero throttling, allowing Cortex-A76 Big Cores to pin at sustained **2.40 GHz** and Cortex-A55 to pin at **2.00 GHz**. The `862000` / `898000` kHz targets in `thermal-nolimits.conf` represent the safety floor *only if* temperatures breach 55°C.
- Enforces and hardware-locks CoreLink CCI Perf mode at **1.60 GHz** (OPP 0) via `chmod 444`, preventing non-root Android Power HAL (`android.hardware.power-service.mediatek`) from downgrading interconnect and L3 cache bandwidth.
- Hardware-locks ARM Mali-G57 MC2 DVFS evaluation period to **50ms** (via `chmod 444`) with `always_on` power policy and MediaTek GED GPU acceleration up to 1.068 GHz.
- Eliminates CPU Schedutil ramp latency (`up_rate_limit_us = 0`), unlocks both Big cores for foreground (`cpuset 0-7`), configures BORE big task rotation, and preserves natural 8-core DynamIQ task distribution across all 6 Little cores and 2 Big cores.
- Optimizes UFS 2.2 flash storage dispatch via 512 kB read-ahead and zero I/O accounting CPU overhead (`iostats = 0`).
- Hardens network and Wi-Fi ADB connection stability by disabling TCP slow start after idle (`tcp_slow_start_after_idle = 0`) and calibrating 60-second keepalives.

#### Critical Hardware Traps Discovered & Neutralized

1. 🛑 **TRAP 1 (`sconfig 14`):** Profile 14 is the hardcoded YouTube low-power profile. Enforcing profile 14 clamps Big CPU cores to 1.2 GHz and locks refresh rate to 60Hz. Never map profile 14.
2. 🛑 **TRAP 2 (`set_sspm_big_limit_threshold`):** Writing temperature thresholds directly to `/proc/driver/thermal/set_sspm_big_limit_threshold` triggers an unkillable 84% CPU kernel IPI spinloop. Never write to this sysfs node.
3. 🛑 **TRAP 3 (`mtk-cl-backlight`):** Altering or overriding the `mtk-cl-backlight` cooling device in thermal configs forces the display PWM controller to 0, resulting in a black screen upon locking/unlocking the device. Backlight cooling limits MUST remain at state `0` (unrestricted).

---

### C. Graphics & Vulkan Subsystem (`package/Vulkan13/`)

#### The Split-Driver Synchronization Problem
ARM Mali GPUs require strict synchronization between the user-space driver (`vulkan.mali.so`, `libGLES_mali.so`) and the kernel device driver (`/dev/mali0` — `mali_kbase`). Directly replacing stock `libGLES_mali.so` with newer DDK binaries crashes SurfaceFlinger due to mismatched IOCTL command structures.

#### Production Solution: Hybrid Decoupling
- **Dual-Stack Decoupling:** Stock `libGLES_mali.so` (r32p1) handles SurfaceFlinger and system GLES rendering, while a standalone **Valhall r49p1 Vulkan 1.3 ICD** (`libVK13_mali.so`) extracted from **Redmi Note 13 5G (`gold`)** on **HyperOS 3.0** (`OS3.0.10.0.VNQCNXM_15.0`) serves Vulkan 1.3 workloads.
- **Linker Hooks & AFBC:** Companion library `libgpd1.so` patched to export missing `GpuAuxBlitAHardwareBuffer` via bit-exact Bionic GnuHash; donor `libged.so` integrated; Arm Generic Timer calibrated to 13 MHz (`PLATFORM_AGT_FREQUENCY_KHZ=13000`); Gralloc AFBC manifests deployed.
- **Mali-G57 Architecture Truth:** Mali-G57 (Valhall v1) uses the **Job Manager (JM)** interface (`BASE_UK_VERSION_MAJOR 11`), **NOT** CSF. Shader and pipeline compilation runs 100% in user-space, delivering full performance on Linux 4.14 without kernel bottlenecks.
- **Kernel Compilation Shims for 4.14:** When backporting 5.10 `mali_kbase`, porters must shim `access_ok(VERIFY_READ, addr, size)` (3 args vs 2 args in 5.0+), retain legacy ION buffer allocator (`mali_kbase_mem_linux.c`), guard modern `dma_fence_set_deadline()`, and port `platform/mt6833/` glue from `mali-r32p1`.

---

## 4. Empirical Benchmark Records & Baselines

These verified numbers represent the ground truth performance achievable with this repository:

| Benchmark                     |   Pure Stock AOSP   | Memory Management Alone | EvergoTweaks (Thermal + Memory Management) | Verified Deltas                                    |
| :---------------------------- | :-----------------: | :---------------------: | :----------------------------------------: | :------------------------------------------------- |
| **Geekbench 7 Multi-Core**    |       `1,500`       |         `1,788`         |                **`2,133`**                 | 🚀 **+42.2% (+633 pts — Global MT6833 Record)**    |
| **Geekbench 7 Single-Core**   |        `610`        |          `578`          |                 **`729`**                  | 🚀 **+19.5% (+119 pts — Global MT6833 Record)**   |
| **3DMark Sling Shot Extreme** |       `2,518`       |         —               |                **`2,736`**                 | 🚀 **+8.7% All-Time Global MT6833 Record**         |
| **3DMark Physics (Vulkan)**   |       `3,379`       |         —               |                **`4,053`**                 | 🚀 **+20.0% (+674 pts — World Record Physics)**    |
| **Geekbench 7 GPU (Compute)** |       ~`1,080`      |         —               |                **`1,302`**                 | 🚀 **+20.6% (Mali-G57 MC2 @ 1068 MHz GED Boost)**  |
| **Direct Reclaim Stalls**     |      ⚠️ Severe      |      🛡️ None       |   🛡️ **Zero Allocation Stalls**    | `direct_reclaim = 0`                               |
| **App Retention**             | ❌ Aggressive Kills | ✅ 100% Kept Alive |       ✅ **100% Kept Alive**       | Retains Chrome tabs, music, launcher in ZRAM       |

- **Official Geekbench 7 Verification (Side-by-Side vs Stock Baseline):** [https://browser.geekbench.com/v7/cpu/compare/400164?baseline=380539](https://browser.geekbench.com/v7/cpu/compare/400164?baseline=380539) | **GPU Compute Compare:** [https://browser.geekbench.com/v7/gpu/compare/183548?baseline=183548](https://browser.geekbench.com/v7/gpu/compare/183548?baseline=183548) (All-Time Record Runs: [400164 — 2133 MC](https://browser.geekbench.com/v7/cpu/400164) / [392815 — 2108 MC](https://browser.geekbench.com/v7/cpu/392815) / [391841 — 729 SC](https://browser.geekbench.com/v7/cpu/391841) / [389858 — 728 SC](https://browser.geekbench.com/v7/cpu/389858) / [385213 — 2066 MC](https://browser.geekbench.com/v7/cpu/385213) | GPU OpenCL Record: [183548 — 1302 pts](https://browser.geekbench.com/v7/gpu/183548))
- **3DMark Sling Shot Extreme Official Runs:** OpenGL ES 3.1: **`2,736 pts`** (Graphics: **`2,557 pts`**, GT1: 17.30 FPS, GT2: 8.19 FPS) | Vulkan: **`2,734 pts`** (Physics: **`4,053 pts`** World Record, GT1: 17.00 FPS, GT2: 7.99 FPS).
- **Sustained Cortex-A76 Big Clocks:** `2,393 MHz` (~2.39 GHz pinned throughout compute runs).
- **Sub-Workload Highlights (Single-Core — Peak 729 SC World Record Run 391841):**
  - HTML5 Browser: **802** | Navigation: **972** | PDF Viewer: **970** | Audio Encoder: **891** | File Compression: **863** | Asset Compression: **849** | Ray Tracer: **735**
- **Sub-Workload Highlights (Multi-Core — Peak 2108 MC World Record Run 392815):**
  - Ray Tracer: **3,403** | Asset Compression: **3,246** | Text Processing: **2,159** | File Compression: **2,015** | Clang: **1,943** | Photo Library: **1,872**
- **Sub-Workload Highlights (GPU Compute — Peak 1302 pts Run 183548):**
  - Horizon Detection: **2,466** | Fluid Simulation: **1,687** | Photo Filter: **1,644** | Particle Physics: **1,528** | Video Filter: **1,454** | RAW: **1,444**

---

## 5. Repository Layout & File Catalog

All required automation and operational Python scripts reside **exclusively** in the root `scripts/` directory:

```text
EvergoTweaks/
├── AGENTS.md                          # Master context & AI operational instructions (This file)
├── README.md                          # Public repository overview & quickstart guide
├── CHANGELOG.md                       # Comprehensive version history & benchmark progression
├── LICENSE                            # Apache 2.0 License
├── .gitignore                         # Build outputs, temporary files, and platform artifacts
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
    │   ├── README.md                  # Comprehensive technical manual & QA zone math audit
    │   ├── patch.patch                # Unified diff for device_xiaomi_everpal
    │   ├── package/
    │   │   └── MemoryMgmt.zip         # Flashable module (Author: TesterProd)
    │   └── docs/                      # Architectural blueprint & integration guide
    │       └── memory-mgmt.txt        # Master blueprint, LMKD tuning logic & git diffs
    │
    ├── ThermalMgmt/                   # 🔥 Thermal Mitigation & mi_thermald Subsystem
        ├── README.md                  # Hardware audit, decrypted Xiaomi profiles & profile tables
        ├── patch.patch                # Unified diff for device and vendor trees
        ├── package/
        │   └── ThermalMgmt.zip        # Flashable module (Author: TesterProd)
        └── docs/                      # Benchmark logs, databases & vendor configs
            ├── benchmark_history.txt     # Chronological benchmark log
            ├── history.db                # Raw SQLite database pulled from Geekbench 7
            ├── thermal-mgmt.txt          # Master thermal analysis & register teardown
            └── vendor_configs/           # Raw .conf & decrypted AES .decrypted.txt Xiaomi thermal profiles
    │
    └── Vulkan13/                      # 🎮 Vulkan 1.3 Hybrid Engine Subsystem
        ├── README.md                  # Hardware audit, linker hooks & benchmark records
        ├── package/
        │   └── Vulkan13-KernelSU.zip  # Flashable module (Author: TesterProd)
        └── template/                  # Hybrid ICD stack, companion libraries & SELinux scripts
```

---

## 6. Essential Commands & Operational Workflows

### Building Flashable Modules (Unified & Reproducible)

To rebuild all KernelSU/Magisk modules and verify their zip integrity:

```bash
python scripts/build_all.py
```

Or rebuild individual modules:

```bash
python scripts/build_all.py --memory
python scripts/build_all.py --thermal
python scripts/build_all.py --vulkan
```

*Note: Flashable zips are always written exclusively to `package/<Module>/package/`.*

### Auditing Connected Device via ADB

Run a full hardware, frequency, thermal, and kernel tunable audit:

```bash
python scripts/verify_device.py
```

### Automated Benchmark Execution with Live Telemetry

Run the automated Geekbench 7 benchmark suite with real-time CLI clock & workload streaming:

```bash
# Run both CPU and GPU (Vulkan) benchmarks
python scripts/autobench.py

# Run CPU benchmark only
python scripts/autobench.py --cpu-only

# Run GPU Vulkan benchmark only
python scripts/autobench.py --gpu-only
```

### Decrypting / Inspecting Xiaomi Thermal Profiles

Decrypt a single thermal configuration:

```bash
python scripts/decrypt_thermal.py package/ThermalMgmt/docs/vendor_configs/thermal-normal.conf
```

Batch decrypt all vendor profiles:

```bash
python scripts/decrypt_thermal.py --batch package/ThermalMgmt/docs/vendor_configs/
```

### Pulling Live Benchmark Results via ADB

Extract Geekbench 7 CPU & GPU compute scores directly from on-device SQLite database:

```bash
python scripts/pull_benchmark.py
```

### Validating Device State via ADB

Run these non-destructive inspection commands on connected devices:

```bash
# Check current thermal profile and sconfig mode
adb shell "getprop sys.thermal.mode; cat /sys/class/thermal/thermal_message/sconfig"

# Check CPU scaling frequencies
adb shell "cat /sys/devices/system/cpu/cpu*/cpufreq/scaling_cur_freq"

# Inspect memory zones and watermarks
adb shell "cat /proc/zoneinfo | grep -E 'Node|min|low|high'"

# Inspect ZRAM and swap allocation
adb shell "cat /proc/swaps; cat /proc/meminfo | grep -E 'MemTotal|MemFree|MemAvailable|SwapTotal|SwapFree'"

# Inspect LMKD kill logs
adb logcat -d -s lmkd
```

### Git & GitLab Workflow

Commit message convention: `<emoji> [<TYPE>]: <description>`

```bash
# Commit format examples:
git commit -m "🦋 [FEAT]: add dynamic memory compaction trigger"
git commit -m "🐛 [FIX]: resolve thermal zone trip point mismatch"
git commit -m "♻️ [REFACTOR]: update vendor thermal conf parsing script"

# Push and release:
git push origin main
glab release create v1.0.0 "package/MemoryMgmt/package/MemoryMgmt.zip#MemoryMgmt.zip" "package/ThermalMgmt/package/ThermalMgmt.zip#ThermalMgmt.zip" --name "v1.0.0 - Release"
```

---

## 7. Inviolable Guardrails & Operational Constraints

All agents working within this codebase must strictly observe these rules:

1. 🛑 **Zero Unprompted Reboots:** NEVER execute `adb reboot` or issue reboot commands without explicit, written user permission.
2. 🛑 **No Kernel Spinloops:** NEVER write to `/proc/driver/thermal/set_sspm_big_limit_threshold`. It causes an unkillable 84% CPU kernel IPI spinloop.
3. 🛑 **No Backlight Tampering:** NEVER alter `mtk-cl-backlight` cooling levels in thermal configs. Doing so forces PWM brightness to 0, causing permanent black screens on lock/unlock.
4. 🛑 **Zip Placement Boundary:** Pre-compiled flashable `.zip` archives must reside **exclusively** inside their respective `package/` directories (`package/MemoryMgmt/package/` and `package/ThermalMgmt/package/`). Never place `.zip` files in the repository root or script directories.
5. 🛑 **Scripts Centralization Boundary:** All required Python automation, build, extraction, and verification scripts must reside **exclusively** in the root `scripts/` folder. Do not create or reintroduce scripts inside `package/*/scripts/`.
6. 🛑 **No Secrets or Bloat:** Never commit `.env` files, API tokens, local OS metadata (`.DS_Store`, `Thumbs.db`), Python caches (`__pycache__`), or SQLite WAL journal files.
7. 🛑 **Attribution Integrity:**
   - Magisk / KernelSU modules must maintain `author=TesterProd` strictly inside `module.prop`.
   - General project authorship and maintainership belongs to `Author & Maintainer: Shovit Dutta`.
   - Architectural and research credits honor: `Special Thanks & Collaborators: Addster09 x himanshuksr0007 (Goku)`.
   - Under NO circumstances should `TesterProd` be listed under Authors & Credits in documentation.
8. 🔄 **Benchmark URL Maintenance:** Whenever a new peak record run is achieved, always update the official side-by-side comparison URL (`https://browser.geekbench.com/v7/cpu/compare/<NEW_RECORD_ID>?baseline=380539`) across all documentation markdown files (`README.md`, `AGENTS.md`, `package/ThermalMgmt/README.md`).
9. 💬 **Collaborator Communications Protocol (`convo.txt`):** Whenever preparing technical information, updates, advice, or roadmaps to inform or reply to collaborators **Goku (`himanshuksr0007`)** or **Addster09**, ALWAYS create/write to a dedicated file named `convo.txt` in the repository root (`D:\Evergo\EvergoTweaks\convo.txt`). Ensure the message uses an engaging, sharp blend of in-depth technical accuracy and casual developer Telegram/chat style (e.g., emojis, code snippets, direct and punchy tone) ready for the user to copy-paste directly to them.
10. 🦊 **GitLab Primacy:** Always maintain **GitLab** (`https://gitlab.com/ShovitDutta1/`) as the primary hosting and collaboration forge for EvergoTweaks and its associated trees (`device_xiaomi_everpal`, `vendor_xiaomi_everpal`, `android_kernel_xiaomi_mt6833`). All forks, branches, releases, and collaborator links must prioritize GitLab.
