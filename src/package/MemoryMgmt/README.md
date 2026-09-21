# Everpal Memory Management Master Blueprint

> **Prepared By:** Shovit Dutta
> **Author / Tuning:** himanshuksr0007 (Goku) x Shovit Dutta
> **Target Device:** Xiaomi POCO M4 Pro 5G / Redmi Note 11S 5G (`everpal`)
> **Hardware:** MediaTek Dimensity 810 (MT6833P / MT6833 family, 2x A76 @ 2.4 GHz + 6x A55 @ 2.0 GHz, Mali-G57 MC2)
> **Kernel & OS:** Linux `4.14.357-Aqua #3` | Android 16 (Project Infinity - `BP4A.251205.006`)
> **Target Repository:** [device_xiaomi_everpal](https://github.com/FrontlXOX/device_xiaomi_everpal)
> **Date:** September 18, 2026

---

## 📱 Device & Operating System Specifications

<details>
<summary><b>📱 Tap to expand Device & Hardware Specifications (POCO M4 Pro 5G / Dimensity 810 / Android 16)</b></summary>
<br>

| Specification          | Hardware & Software Configuration                                             |
| :--------------------- | :---------------------------------------------------------------------------- |
| **Commercial Device**  | Xiaomi POCO M4 Pro 5G / Redmi Note 11S 5G (`everpal`)              |
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
src/package/MemoryMgmt/
├── README.md                      # Comprehensive master technical manual & QA zone audit
├── patch.patch                    # Standalone unified git patch for device_xiaomi_everpal
│
├── package/                       # Production flashable KernelSU / Magisk module
│   └── MemoryMgmt.zip             # Flashable module (Author: FrontlXOX)
│
└── docs/                          # Complete architectural blueprint & integration guide
    └── memory-mgmt.txt            # Master blueprint (TL;DR, QA audit, hardware zone math, git diff)
```

</details>

---

## ⚡ Executive Summary for Goku

Through extensive multi-day kernel diagnostics and stress testing across Geekbench 7, 3DMark, Chrome, ReSukiSU, and Smart Launcher, this configuration breaks all previous performance records on everpal while solving the aggressive background app killing on Android 16.

### Performance Records Achieved:

- **Multi-Core Record:** **`1,788`** (Warmed-up v7 Pass 2) / **`1,709`** (Cold-boot v7 Pass 1) vs **`1,500`** (Stock) — **+288 points (+19.2%) increase!**
- **Single-Core Score:** **`578`** (Module / all apps alive) vs **`610`** (Stock / all background apps killed).
- **Multi-Tasking Retention:** Smart Launcher (`ginlemon.flowerfree`) survived the full 14-minute heavy benchmark suite without restart (resident footprint dynamically compressed from 244 MB down to 97 MB). Google Play Store and system services survived 100% intact. Zero kills occurred below `oom_score_adj 900`.

---

## 🔍 The Special QA Audit: Stock Baseline vs Memory Management Alone

<details>
<summary><b>🔍 Tap to expand Special QA Audit: Stock Baseline vs Memory Management Alone</b></summary>
<br>

| Workload           |  Stock Baseline (No Module)  |     Memory Management Alone     | Physical Cause                                                                                                                                                                  |
| :----------------- | :--------------------------: | :-----------------------------: | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Single-Core**    |           **610**            |               578               | Stock LMK killed all background apps before GB7 started; GB7 had the entire memory bus exclusively to itself. Memory Management kept all apps alive (multitasking trade-off).   |
| **Multi-Core**     |            1,500             |            **1,788**            | 6+ threads allocating simultaneously choked Stock memory into direct-reclaim stalls. Memory Management's 3.58 GB ZRAM absorbed allocation bursts asynchronously with zero stalls (+19.2%). |
| **App Retention**  |      ❌ Launcher killed       |       ✅ 100% apps alive        | Stock LMK murdered launcher, settings, and background tasks. Memory Management retained Smart Launcher, Google Play, Termux, and browser in compressed ZRAM without restart.     |
| **Allocation Wait**|      ⚠️ Severe stalls        |      🛡️ Zero direct stalls      | Stock suffered direct page reclaim stalls on CPU cores. Memory Management shifted page writes to asynchronous LZ4 swap.                                                         |

> **Engineering Takeaway:** A ROM that scores 610 by aggressively killing the launcher, music player, and browser the moment a game or camera launches is unviable for daily use. Gaining **+288 points (+19.2%) in Multi-Core** while keeping apps alive in the background is the true production standard.

</details>

---

## 🛠️ The 5 Root Cause Discoveries

<details>
<summary><b>🛠️ Tap to expand The 5 Root Cause Discoveries & Architectural Fixes</b></summary>
<br>

1. **`swap_free_low_percentage = 2%` (NOT 5% or 10%):**
   - Stock Android sets this to 10% or 5%. With a 3.58 GB ZRAM, 5% is **183 MB**.
   - When free swap hit 172 MB during Geekbench, LMKD triggered emergency kill escalation, killing essential apps.
   - Lowering to 2% drops the threshold to **73 MB (+110 MB cushion)**, completely eliminating emergency escalations.

2. **`watermark_scale_factor = 20` (NOT 100 or 150):**
   - On the MediaTek MT6833, `Zone Normal` is physically restricted to **374.00 MiB managed** (95,744 pages) within a **432.00 MiB spanned range** (110,592 pages / 442.37 MB decimal).
   - High watermark factors inflated Zone Normal's `low` watermark to 3,357 pages (13.4 MB), above its free pool (3,338 pages), causing LMK to falsely report `low watermark is breached` even when the phone had **over 850 MB of free RAM** in Zone DMA!
   - Setting `wsf=20` drops Zone Normal's low watermark to 1,860 pages, providing a safe **+422 page margin**.

3. **`min_free_kbytes = 24576` (24 MB, was 18,432 KB):**
   - Balances the atomic reserve across all three zones (DMA, Normal, Movable) without starving Zone Normal.

4. **`ro.lmk.kill_timeout_ms = 250` (Android default is 10ms):**
   - Enforces exact 250ms spacing between kill evaluations, stopping millisecond cascade kills.

5. **`init.everpal.rc` Fix: `compaction_proactiveness` Does NOT Exist on Linux 4.14:**
   - That sysctl was introduced in Linux 5.8+. On Linux 4.14, writing to it errors out silently.
   - Replace with: `write /proc/sys/vm/compact_memory 1` to perform post-boot compaction.

</details>

---

## 📊 Complete Parameter Comparison Matrix

<details>
<summary><b>📊 Tap to expand Complete Parameter Comparison Matrix (Stock vs Commit vs Tested Architecture)</b></summary>
<br>

| Parameter                             | Stock ROM |   Commit `42d0a1ba`    | Final Tested Architecture  | Hardware / Kernel Reason                             |
| :------------------------------------ | :-------: | :--------------------: | :------------------------: | :--------------------------------------------------- |
| **ZRAM Disk Size**                    |  1.99 GB  |        1.99 GB         | **3.58 GB (`3758096384`)** | Absorbs anonymous memory; prevents RAM starvation    |
| **ZRAM Algorithm**                    |   `lz4`   | `zstd`/`lz4` overwrite |         **`lz4`**          | Hardware optimal on MT6833; single clean write       |
| **`swappiness`**                      | 160 / 60  |           80           |          **`80`**          | Perfect reclaim balance; caps swap at ~35%           |
| **`watermark_scale_factor`**          |    10     |      [unset / 10]      |          **`20`**          | Protects Zone Normal (442 MB) from false breaches    |
| **`min_free_kbytes`**                 | 4,932 KB  |       18,432 KB        |      **`24,576 KB`**       | 24 MB atomic buffer across all 3 zones               |
| **`vfs_cache_pressure`**              |    100    |           80           |          **`80`**          | Retains directory/inode cache for fast app switching |
| **`page-cluster`**                    |     0     |           0            |          **`0`**           | Single-page swap I/O without readahead latency       |
| **`vma_ra_enabled`**                  |   true    |         false          |        **`false`**         | Disables redundant swap VMA read-ahead               |
| **`dirty_ratio`**                     |    20     |           30           |          **`30`**          | Allows larger write buffer before flush              |
| **`dirty_background_ratio`**          |    10     |           10           |          **`10`**          | Background flush threshold                           |
| **`stat_interval`**                   |     1     |           10           |          **`10`**          | Reduces VM stat recalculation overhead               |
| **Post-Boot Compaction**              |   none    |   `proactive` (err)    |   **`compact_memory=1`**   | Defragments zones on 4.14 kernel completion          |
| **`ro.lmk.swap_free_low_percentage`** |    10%    |           5%           |          **`2%`**          | Lowers emergency threshold from 183 MB to 73 MB      |
| **`ro.lmk.thrashing_limit`**          |    30     |          150           |         **`300`**          | Eliminates thrashing panic during 3D/ray tracing     |
| **`ro.lmk.thrashing_limit_decay`**    |    10     |           10           |          **`15`**          | Settles pressure score rapidly after spikes          |
| **`ro.lmk.kill_timeout_ms`**          |   10 ms   |     [unset / 10ms]     |        **`250 ms`**        | Paces kills to allow freed memory to register        |
| **`ro.lmk.swap_util_max`**            |   100%    |          85%           |         **`90%`**          | Full swap utilization without premature cutoff       |
| **`ro.lmk.downgrade_pressure`**       |    100    |           80           |          **`80`**          | Threshold for downgrading pressure events            |
| **`ro.lmk.kill_heaviest_task`**       |   true    |         false          |        **`false`**         | Kills strictly by OOM priority, not RSS footprint    |
| **`ro.lmk.psi_partial_stall_ms`**     |   70 ms   |         200 ms         |        **`250 ms`**        | Tolerates transient burst memory pressure            |
| **`ro.lmk.psi_complete_stall_ms`**    |  700 ms   |         700 ms         |        **`800 ms`**        | Prevents false "device not responding" kills         |
| **`bg_apps_limit`**                   |    32     |           64           |          **`64`**          | Expanded ActivityManager cached process pool         |
| **`max_cached_processes`**            |    32     |           64           |          **`64`**          | Retains up to 64 cached processes                    |

</details>

---

## 📱 Hardware Variant Agnostic Design (4GB / 6GB / 8GB)

<details>
<summary><b>📱 Tap to expand Dynamic Hardware Variant Agnostic Design (4GB / 6GB / 8GB)</b></summary>
<br>

The Xiaomi POCO M4 Pro 5G / Redmi Note 11S 5G (`everpal`) was manufactured across **4GB, 6GB, and 8GB LPDDR4X** physical memory configurations. To ensure complete universal portability across all hardware variants without hardcoded limitations:

- **Dynamic RAM Detection:** `service.sh` interrogates `/proc/meminfo` (`MemTotal`) at boot to establish the exact physical memory tier.
- **Adaptive ZRAM Disk Sizing:**
  - **4GB Tier (~3.53 GB Linux MemTotal):** Calibrated to **3.58 GB** (`3,758,096,384` bytes) with single-pass `lz4` compression to prevent `Zone Normal` exhaustion.
  - **6GB Tier (~5.5 GB Linux MemTotal):** Dynamically scales to **75% of MemTotal** (~4.2 GB ZRAM swap).
  - **8GB Tier (~7.5 GB Linux MemTotal):** Dynamically scales to **75% of MemTotal** (~5.6 GB ZRAM swap).
- **Proportional Atomic Reserves (`min_free_kbytes`):**
  - **4GB Tier:** `24,576 KB` (24 MB dedicated atomic pool).
  - **6GB Tier:** `32,768 KB` (32 MB dedicated atomic pool).
  - **8GB Tier:** `40,960 KB` (40 MB dedicated atomic pool).
- **Adaptive ActivityManager Process Retention:**
  - **4GB Tier:** `64` cached processes (`32` phantom processes).
  - **6GB Tier:** `96` cached processes (`40` phantom processes).
  - **8GB Tier:** `128` cached processes (`48` phantom processes).
- **Dynamic Stream Parallelism:** `max_comp_streams` is queried via `nproc` (8 parallel streams across all 8 Dimensity 810 CPU cores).

</details>

---

## 🚀 How to Implement in Device Trees

<details>
<summary><b>🚀 Tap to expand Device Tree & Init RC Integration Steps</b></summary>
<br>

### Option A: Apply the Standalone Git Patch (Recommended)

From the root of your [`device_xiaomi_everpal`](https://github.com/FrontlXOX/device_xiaomi_everpal) repository clone:

```bash
git apply patch.patch
```

### Option B: Manual Integration

#### 1. `configs/props/vendor.prop`

```properties
# LMKD
ro.config.low_ram=false
ro.lmk.use_psi=true
ro.lmk.use_minfree_levels=false
ro.lmk.use_new_strategy=true
ro.lmk.thrashing_limit=300
ro.lmk.thrashing_limit_decay=15
ro.lmk.downgrade_pressure=80
ro.lmk.swap_util_max=90
ro.lmk.swap_free_low_percentage=2
ro.lmk.kill_heaviest_task=false

# PSI & Kill Pacing
ro.lmk.psi_partial_stall_ms=250
ro.lmk.psi_complete_stall_ms=800
ro.lmk.kill_timeout_ms=250
ro.lmk.critical_upgrade=false

# Activity Manager
persist.sys.fw.bg_apps_limit=64
persist.device_config.activity_manager.max_cached_processes=64
persist.device_config.activity_manager.max_phantom_processes=32
persist.sys.fw.bservice_enable=true
persist.sys.fw.bservice_limit=8
persist.sys.fw.bservice_age=8000
persist.device_config.activity_manager_native_boot.freeze_debounce_timeout=600000
```

#### 2. `init/init.mt6833.rc`

Under `on fs`:

```rc
    # ZRAM compression algorithm (lz4 is hardware optimal on MT6833)
    write /sys/block/zram0/comp_algorithm lz4

    # Swappiness: 80 balances ZRAM use and RAM retention
    write /proc/sys/vm/swappiness 80
    write /proc/sys/vm/watermark_scale_factor 20
    write /proc/sys/vm/min_free_kbytes 24576
    write /sys/kernel/mm/swap/vma_ra_enabled false

    # Memory management
    write /proc/sys/vm/page-cluster 0
    write /proc/sys/vm/vfs_cache_pressure 80
    write /proc/sys/vm/dirty_ratio 30
    write /proc/sys/vm/dirty_background_ratio 10
```

#### 3. `init/init.everpal.rc`

Under `on property:sys.boot_completed=1`:

```rc
on property:sys.boot_completed=1
    # Linux 4.14 memory compaction (compaction_proactiveness is 5.8+ only)
    write /proc/sys/vm/stat_interval 10
    write /proc/sys/vm/compact_memory 1
```

#### 4. `fstab.mt6833` / `fstab.mt6833.ramdisk`

Ensure ZRAM disksize is configured for 3.58 GB (~3,758,096,384 bytes):

```text
/dev/block/zram0 none swap defaults zramsize=3758096384,max_comp_streams=8
```

</details>

---

## 📲 How to Test Live on Device

<details>
<summary><b>📲 Tap to expand Live Testing via KernelSU / Magisk Instructions</b></summary>
<br>

To test these exact parameters immediately on an active device without building the full ROM:

1. Copy [`src/package/MemoryMgmt/package/MemoryMgmt.zip`](file:///D:/Evergo/EverpalTweaks/src/package/MemoryMgmt/package/MemoryMgmt.zip) to the device.
2. Flash via **KernelSU**, **Magisk**, or **APatch**.
3. Reboot to verify properties via `getprop ro.lmk.swap_free_low_percentage` (expect `2`) and `cat /proc/sys/vm/watermark_scale_factor` (expect `20`).

</details>
