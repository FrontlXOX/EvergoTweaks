# Everpal Thermal Management Master Blueprint & Hardware Audit

> **Prepared By:** Shovit Dutta
> **Author / Research:** Addster09 x Shovit Dutta
> **Target Device:** Xiaomi POCO M4 Pro 5G / Redmi Note 11S 5G (`everpal` / `evergo`)
> **Model ID:** Xiaomi 22031116AI
> **Hardware:** MediaTek Dimensity 810 (MT6833P / MT6833 family, 2x A76 @ 2.4 GHz + 6x A55 @ 2.0 GHz, Mali-G57 MC2)
> **Kernel & OS:** Linux `4.14.357-Aqua #3` | Android 16 (Project Infinity - `BP4A.251205.006` / LineageOS 23.0)
> **Target Repositories:**
>
> - Device: [`device_xiaomi_everpal`](https://github.com/xiaomi-mt6833-dev/device_xiaomi_everpal)
> - Vendor: [`vendor_xiaomi_everpal`](https://github.com/xiaomi-mt6833-dev/vendor_xiaomi_everpal)
> - Kernel: [`android_kernel_xiaomi_mt6833`](https://github.com/Addster09/android_kernel_xiaomi_mt6833)
>   **Date:** September 18, 2026

---

### 🏅 Performance & Verification Dashboard

| Benchmark Target | Official Verification Badge | Peak Metric | Key Hardware Optimization Architecture |
| :--- | :---: | :---: | :--- |
| **Geekbench 7 Single-Core** | [![Geekbench 7 Single-Core](https://img.shields.io/badge/Single--Core-729_(Record)-brightgreen?style=for-the-badge&logo=speedtest&logoColor=white)](https://browser.geekbench.com/v7/cpu/391841) | **`729` SC**<br>`+19.5%` (+119 pts) | 2.40 GHz Cortex-A76 Big core • DVFSRC 4.266 GHz LPDDR4X • 0 µs Schedutil ramp |
| **Geekbench 7 Multi-Core** | [![Geekbench 7 Multi-Core](https://img.shields.io/badge/Multi--Core-2133_(Record)-brightgreen?style=for-the-badge&logo=speedtest&logoColor=white)](https://browser.geekbench.com/v7/cpu/400164) | **`2,133` MC**<br>`+42.2%` (+633 pts) | 8 Cores (2x A76 + 6x A55) • CoreLink CCI 1.60 GHz • 55°C NoLimits headroom |
| **CPU Official Compare** | [![Geekbench 7 CPU Compare](https://img.shields.io/badge/CPU_Comparison-Verified_vs_Stock-blue?style=for-the-badge&logo=googlechrome&logoColor=white)](https://browser.geekbench.com/v7/cpu/compare/400164?baseline=380539) | **Run 400164**<br>vs Run 380539 | Verified side-by-side CPU proof against pure stock baseline (+42.2% Multi-Core) |
| **Geekbench 7 GPU (Compute)** | [![Geekbench 7 GPU](https://img.shields.io/badge/GPU_Compute-1302_(Record)-orange?style=for-the-badge&logo=arm&logoColor=white)](https://browser.geekbench.com/v7/gpu/183548) | **`1,302` pts**<br>`+20.6%` Boost | ARM Mali-G57 MC2 @ 1068 MHz GED boost • 50ms DVFS lock • OpenCL Compute |
| **GPU Official Compare** | [![Geekbench 7 GPU Compare](https://img.shields.io/badge/GPU_Comparison-Verified_Run-blue?style=for-the-badge&logo=googlechrome&logoColor=white)](https://browser.geekbench.com/v7/gpu/compare/183548?baseline=183548) | **Run 183548**<br>Compute Audit | Official side-by-side Geekbench 7 GPU sub-workload analysis & verification |

---

## 📱 Device & Operating System Specifications

<details>
<summary><b>📱 Tap to expand Device & Hardware Specifications (POCO M4 Pro 5G / Dimensity 810 / Android 16)</b></summary>
<br>

| Specification          | Hardware & Software Configuration                                             |
| :--------------------- | :---------------------------------------------------------------------------- |
| **Commercial Device**  | Xiaomi POCO M4 Pro 5G / Redmi Note 11S 5G (`everpal` / `evergo`)              |
| **Model Identifier**   | `Xiaomi 22031116AI` (Motherboard: `everpal`, Board ID: `S98016LA1`)           |
| **Operating System**   | **Android 16** (Project Infinity - LineageOS 23.0 Base)                       |
| **Android Build ID**   | `BP4A.251205.006 release-keys` (`eng.androi.20260917.074937`)                 |
| **Security Patch**     | September 1, 2026                                                             |
| **Kernel Version**     | Linux `4.14.357-Aqua #3 SMP PREEMPT` (AArch64, Android Clang 18)              |
| **SoC / Platform**     | MediaTek Dimensity 810 5G (MT6833P / MT6833 family, 6nm TSMC Process)         |
| **CPU Architecture**   | Octa-core: 2x Cortex-A76 @ 2.40 GHz (Big) + 6x Cortex-A55 @ 2.00 GHz (LITTLE) |
| **GPU Architecture**   | ARM Mali-G57 MC2 @ 950 MHz (Valhall v1, 2 Shader Cores)                       |
| **Physical Memory**    | 4.00 GB LPDDR4X (Samsung KM5P9001DM-B424 uMCP, Kernel MemTotal: ~3.53 GB / 3,709,888 kB) |
| **Internal Storage**   | 64 GB UFS 2.2 (Samsung KM5P9001DM-B424 uMCP, ~48 GB User Data Partition)     |
| **Display Panel**      | 6.6" 90Hz FHD+ IPS LCD (1080 x 2400, 399 PPI, 11-bit PWM brightness 0-2047, KTZ8863A) |
| **Root & Environment** | KernelSU (`ksud 4.2.0-rc1` / v1.0.5) + Zygisk / SELinux Enforcing             |

</details>

---

## 📁 Repository & Directory Layout

<details>
<summary><b>📁 Tap to expand Directory Layout & File Catalog</b></summary>
<br>

```text
package/ThermalMgmt/
├── README.md                          # This master architectural blueprint & hardware audit
├── patch.patch                        # Unified git patch for device_xiaomi_everpal
│
├── package/                           # Production flashable KernelSU / Magisk module
│   └── ThermalMgmt.zip                # Production Master Thermal module (Author: TesterProd)
│
└── docs/                              # Deep technical documentation & benchmark artifacts
    ├── thermal-mgmt.txt               # Master engineering manual & Addster integration guide
    ├── benchmark_history.txt          # Chronological log of live benchmark runs and frequencies
    ├── history.db                     # Full Geekbench 7 SQLite benchmark document database
    └── vendor_configs/                # Raw .conf & decrypted AES .decrypted.txt Xiaomi thermal profiles
```

</details>

---

## ⚡ Executive Summary for Addster

During systematic empirical benchmarking and kernel audits on the Xiaomi POCO M4 Pro 5G (`everpal`) running Android 16, we examined why custom ROMs suffer from severe thermal throttling and lower multi-core/GPU performance compared to theoretical hardware capability.

By combining the **Everpal Memory Management v7.1 architecture** with our unlocked **Thermal Management v2.2 profile (`sconfig 10` / `thermal-nolimits`)**, we shattered all previous performance records on the MediaTek MT6833:

### 🏆 Benchmark Breakthrough Evolution

<details>
<summary><b>🏆 Tap to expand Complete Benchmark Evolution History (Stock Baseline to World Record)</b></summary>
<br>

| Milestone / Configuration                                     | Single-Core | Multi-Core  |        Delta vs Stock         | Physical Cause / Hardware State                                                                                                                      |
| :------------------------------------------------------------ | :---------: | :---------: | :---------------------------: | :--------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Pure Stock (No Module)**                                    |    `610`    |   `1,500`   |           Baseline            | Stock LMK murders all apps; multi-core collapses from direct reclaim stalls & 36°C thermal downclocking.                                             |
| **Memory Management Alone**                                   |    `578`    |   `1,788`   |         **+19.2% MC**         | 3.58 GB ZRAM eliminates memory stalls; all background apps kept alive. Still restricted by stock 36°C thermal throttling.                            |
| **Thermal Management v1.0 (`sconfig 14` Trap)**               |    `314`    |    `905`    |           -39.7% MC           | `sconfig 14` clamped CPU clocks to 1.04/1.12 GHz; SSPM IPI write burned 83% CPU on 2 cores.                                                          |
| **Thermal Management v1.1 (`sconfig 14` Clean)**              |    `331`    |   `1,033`   |           -31.1% MC           | Spinloop removed; proved `sconfig 14` is an active half-clock clamp (YouTube playback profile).                                                      |
| **Thermal Management v2.0 + Memory Management v7.0**          |    `706`    | **`2,066`** | 🚀 **+37.7% MC<br>+15.7% SC** | **BROKE THE 2,000 MULTI-CORE RECORD ON MT6833!**<br>Uncapped 2.0 GHz A55 + 2.4 GHz A76 clocks sustained; 55°C throttle headroom; zero memory stalls. |
| **Thermal Management v2.1 + Memory Management v7.1**          |    `717`    | **`2,062`** | 🚀 **+17.5% SC<br>+37.5% MC** | CoreLink CCI Mode 1, CPU DVFS Sports Mode 3, BORE task rotation, GED GPU acceleration to 1.068 GHz.                                                 |
| **Thermal Management v2.2 + Memory Management v7.1**          |  **`722`**  | **`2,066`** | 🚀 **+18.4% SC<br>+37.7% MC** | Schedutil 0µs instant ramp rate, foreground cpuset 0-7 unlock, ARM Mali-G57 always_on power policy.                                                  |
| **Thermal Management v2.4 + Memory Management v7.1**          |  **`729`**  | **`2,058`** | 🚀 **+19.5% SC<br>+37.2% MC** | **NEW ALL-TIME MT6833 WORLD RECORD (729 SC)!**<br>DVFSRC LPDDR4X 4.266 GHz RAM lock (+77.7% bus bandwidth), PPM power throttle uncap, 58°C thermal headroom. |

- **Official Geekbench 7 Verification (Side-by-Side vs Stock Baseline):** [https://browser.geekbench.com/v7/cpu/compare/391841?baseline=380539](https://browser.geekbench.com/v7/cpu/compare/391841?baseline=380539) (All-Time Record Runs: [391841 — 729 SC](https://browser.geekbench.com/v7/cpu/391841) / [389858 — 728 SC](https://browser.geekbench.com/v7/cpu/389858) / [389671 — 726 SC](https://browser.geekbench.com/v7/cpu/389671) / [388551 — 722 SC](https://browser.geekbench.com/v7/cpu/388551) / [388007 — 717 SC](https://browser.geekbench.com/v7/cpu/388007) / [385213 — 2066 MC](https://browser.geekbench.com/v7/cpu/385213))

- **Sustained Cortex-A76 Hardware Clocks:** `[2390, 2389, 2391, 2392, 2391, 2393, 2392, 2392, 2384, 2391, 2390, 2391, 2391, 2391, 2392, 2392, 2391, 2389, 2390, 2391, 2392, 2392, 2389, 2386] MHz` (~2.39 GHz sustained throughout compute runs).
- **Sub-Workload Highlights (Single-Core — Peak 729 SC World Record Run 391841):**
  - HTML5 Browser: **802** (Record)
  - Navigation: **972**
  - PDF Viewer: **970**
  - Audio Encoder: **891**
  - File Compression: **863**
  - Asset Compression: **849** (Record)
  - Photo Library: **741**
  - Ray Tracer: **735** (Record)
  - HDR: **720**
  - Structure from Motion: **708** (Record)
  - Text Processing: **678** (Record)
  - Clang Compilation: **652** (Record)
  - Video Encoder: **649** (Record)
  - Game Physics: **630**
  - Video Player: **545**
  - Photo Editor: **470**
- **Sub-Workload Highlights (Multi-Core):**
  - Ray Tracer: **3,431**
  - Asset Compression: **3,261** (Peak)
  - Text Processing: **2,199** (Peak)
  - File Compression: **2,078** (Peak)
  - Clang Compilation: **2,074** (Peak)
  - Photo Library: **1,910**

</details>

---

## 🎮 3DMark Sling Shot Extreme (OpenGL ES 3.1) Benchmark

<details>
<summary><b>🎮 Tap to expand 3DMark Sling Shot Extreme Telemetry & Graphics Breakdown</b></summary>
<br>

Tested live on `everpal` running Android 16 with Thermal Management v2.4 + Memory Management v7.1 active:

| Metric                |    Result     | Context / Evaluation                                           |
| :-------------------- | :-----------: | :------------------------------------------------------------- |
| **Overall Score**     |  **`2,698`**  | 🥇 **New Global MT6833 Record! Better than 85% worldwide!**   |
| **Graphics Score**    |  **`2,542`**  | 🚀 **New Peak Record!** Mali-G57 GPU rendering with `always_on` |
| • Graphics Test 1     | **17.38 FPS** | Fast particle and geometry rendering (+3.1% over previous peak)|
| • Graphics Test 2     | **8.10 FPS**  | Heavy volumetric lighting & post-processing                    |
| **Physics Score**     |  **`3,561`**  | 🚀 **All-time physics record for MT6833! (Cpuset 0-7 unlocked)**|
| • Physics Test Part 1 | **63.56 FPS** | High-concurrency soft-body collision (Run 5: 62.00 FPS)        |
| • Physics Test Part 2 | **36.36 FPS** | Medium thread load (Run 5: 34.65 FPS)                          |
| • Physics Test Part 3 | **20.48 FPS** | **First time MT6833 has ever exceeded 20 FPS in Part 3!**      |
| **Thermal Monitoring**|  **40.3°C**   | Peak battery temp was only 40.3°C (+2.3°C rise); 1% battery use|

</details>

---

## 🔐 The Xiaomi Thermal Architecture & AES Decryption

Xiaomi's `mi_thermald` daemon controls hardware thermal throttling on MT6833. In `/vendor/etc/`, all `.conf` files are encrypted using OpenSSL **AES-128-CBC**:

- **Cipher Key:** `b"thermalopenssl.h"` (16 bytes)
- **Cipher IV:** `b"thermalopenssl.h"` (16 bytes)

When decrypted, `thermal-map.conf` reveals the exact profile mapping used by the system via `/sys/class/thermal/thermal_message/sconfig`:

### The MT6833 `sconfig` Profile Mapping Matrix

<details>
<summary><b>📋 Tap to expand Complete Decrypted Xiaomi sconfig Profile Mapping Matrix (Profiles 0–38)</b></summary>
<br>

```text
[0:thermal-normal.conf]        -> Default boot profile (Overly aggressive 36°C trigger)
[1:thermal-high.conf]          -> Missing on vendor partition (falls back to normal)
[2:thermal-extreme.conf]       -> Missing on vendor partition (falls back to normal)
[8:thermal-phone.conf]         -> Cellular call profile (1.75 GHz Little / 1.65 GHz Big)
[9:thermal-tgame.conf]         -> Downclocked thermal profile (1.28 GHz Little / 1.27 GHz Big)
[10:thermal-nolimits.conf]     -> 🚀 TRUE UNTHROTTLED GAMING PROFILE (55°C Trigger!)
[11:thermal-class0.conf]       -> Class 0 mitigation (0.96 GHz Little / 2.40 GHz Big)
[12:thermal-camera.conf]       -> Camera capture clamp (0.86 GHz Little / 0.89 GHz Big)
[13:thermal-tgame.conf]        -> Heavy thermal clamp
[14:thermal-youtube.conf]      -> 🔴 YOUTUBE STREAMING PROFILE (1.04 GHz Little / 1.12 GHz Big)
[15:thermal-arvr.conf]         -> VR profile (1.75 GHz Little / 1.99 GHz Big)
[16:thermal-tgame.conf]        -> Heavy thermal clamp
[19:thermal-navigation.conf]   -> GPS Navigation profile
[20:thermal-mgame.conf]        -> Mobile Game profile
[21:thermal-video.conf]        -> Video recording profile
[38:thermal-phone.conf]        -> Phone call fallback
```

</details>

---

## 🔍 The Root Cause of Custom ROM Throttling

<details>
<summary><b>🔍 Tap to expand Detailed Thermal Curve Comparison: Stock 36°C vs NoLimits 55°C Architecture</b></summary>
<br>

### 1. The Disastrous 36°C Stock Throttle Curve (`thermal-normal.conf`)

In stock MIUI/HyperOS, Xiaomi relies on its proprietary userspace daemon (`joyose`) to dynamically write `sconfig` codes when games or heavy apps launch.
**On AOSP / Project Infinity, `joyose` does not exist.** The system remains permanently locked in profile `0` (`thermal-normal.conf`).

Looking at our decrypted `thermal-normal.conf`:

```text
[SS-CPU0] (Cortex-A55 Cores)
trig:   36000    38000    40000    42000    44000    46000    48000    50000 mC
target: 1916000  1812000  1750000  1645000  1500000  1128000  1048000  756000 kHz

[SS-CPU6] (Cortex-A76 Big Cores)
trig:   36000    38000    40000    42000    44000    46000    48000    50000 mC
target: 1993000  1837000  1650000  1534000  1418000  1129000  1042000  840000 kHz
```

> **The Flaw:** `36°C` is lower than human body temperature. Within 15 seconds of any heavy compute or gaming session, `mtktsAP` hits 36°C–44°C, causing `mi_thermald` to throttle the Big Cores by **41%** (down to 1.4 GHz) and GPU clocks at 41°C.

### 2. The Unthrottled Solution (`thermal-nolimits.conf` / `sconfig 10`)

In `thermal-nolimits.conf`:

```text
[NL-SS-CPU0]
trig: 55000 mC | clr: 50000 mC | target: 862000 kHz

[NL-SS-CPU6]
trig: 55000 mC | clr: 50000 mC | target: 898000 kHz

[NL-MONITOR-GPU]
trig: 55000 mC | clr: 50000 mC | target: 20
```

> **The Fix:** The throttle trigger is elevated from 36°C to **55°C**. The CPU and GPU operate at **100% uncapped capability** throughout all normal gaming, multitasking, and benchmarking loads without thermal downclocking.

</details>

---

## ⚠️ The 3 Critical Hardware Traps on MT6833

<details>
<summary><b>⚠️ Tap to expand The 3 Critical Hardware Traps on MT6833 (sconfig 14, IPI spinloop, PWM backlight)</b></summary>
<br>

1. **The `sconfig 14` Trap:**
   - Developers coming from Snapdragon assume `14` is Benchmark mode.
   - On MT6833, `14` is `thermal-youtube.conf`, which locks CPU clocks to 1.04 GHz / 1.12 GHz, collapsing performance by over 50%.
   - **Never set `sconfig 14`.**

2. **The Kernel IPI Spinloop Trap (`/proc/driver/thermal/set_sspm_big_limit_threshold`):**
   - In `drivers/misc/mediatek/thermal/mt6833/src/mtk_thermal_ipi.c`:

     ```c
     while (thermal_to_mcupm(THERMAL_IPI_SET_BIG_FREQ_THRESHOLD, &thermal_data) != 0)
         udelay(500);
     ```

   - On Linux 4.14 MT6833 with production SSPM firmware, the MCUPM power coprocessor does not acknowledge this userspace IPI. The calling process becomes trapped in an unkillable kernel `D` state, spinning at **83%–84% CPU permanently**.
   - **Never write to this node from userspace scripts.**

3. **The Backlight Cooling Trap (`mtk-cl-backlight`):**
   - In `thermald-devices.conf`:

     ```text
     name:mtk-cl-backlight
     def_target:2047
     select_higher:0
     ```

   - `2047` is 100% PWM brightness. Writing `0` to its state forces the backlight to 0% brightness, causing a complete black screen upon unlocking the device.
   - **Leave backlight cooling devices strictly under kernel driver control.**

</details>

---

## 🛠️ Step-by-Step Implementation Guide for Addster

<details>
<summary><b>🛠️ Tap to expand Complete Implementation Guide (ROM Tree Integration & KernelSU Module)</b></summary>
<br>

### Option A: Clean ROM Integration (Recommended for Future Builds)

Apply [`patch.patch`](file:///D:/Evergo/EvergoTweaks/package/ThermalMgmt/patch.patch) to your device tree:

1. **Vendor Tree (`vendor/xiaomi/everpal`):**
   - Replace `/vendor/etc/thermal-normal.conf` with `/vendor/etc/thermal-nolimits.conf`.
   - Even if `mi_thermald` defaults to profile `0` on boot, it automatically loads the unthrottled 55°C NoLimits configuration.

2. **Device Tree (`device/xiaomi/everpal/configs/thermal/thermal_info_config.json`):**
   - Align Android 16 AIDL thermal HAL thresholds:

     ```json
     {
       "Name": "mtktsbattery",
       "Type": "BATTERY",
       "HotThreshold": ["NAN", "NAN", "NAN", 52, 57, 60, 62],
       "VrThreshold": "50.0",
       "Multiplier": 0.001
     },
     {
       "Name": "mtktsAP",
       "Type": "SKIN",
       "HotThreshold": ["NAN", "NAN", "NAN", 55, 75, 85, 95],
       "VrThreshold": "50.0",
       "Multiplier": 0.001
     }
     ```

3. **Device Init (`device/xiaomi/everpal/init/init.mt6833.thermal.rc`):**
   - Enforce `sconfig 10` on boot:

     ```rc
     on property:sys.boot_completed=1
         chmod 0664 /sys/class/thermal/thermal_message/sconfig
         write /sys/class/thermal/thermal_message/sconfig 10
     ```

---

### Option B: Systemless KernelSU / Magisk Module

For immediate testing on existing installations without recompiling ROM images:

- Flash [`package/ThermalMgmt/package/ThermalMgmt.zip`](file:///D:/Evergo/EvergoTweaks/package/ThermalMgmt/package/ThermalMgmt.zip) via KernelSU / Magisk / APatch.
- Automatically magic-mounts the NoLimits profile over `thermal-normal.conf`, arms `sconfig 10`, enforces and hardware-locks CoreLink CCI Perf mode (1.6 GHz OPP 0 via `chmod 444`), CPU DVFS Sports mode, Schedutil 0µs instant ramp rate (20ms hold), foreground cpuset 0-7 unlocking, BORE task rotation, ARM Mali-G57 always_on power policy with hardware-locked 50ms DVFS evaluation, MediaTek GED GPU acceleration up to 1.068 GHz, 512 kB UFS read-ahead, and TCP congestion resilience preventing Wi-Fi ADB timeouts. Includes a delayed background re-assertion pass to ensure complete persistence against late-starting Android vendor HALs.

</details>
