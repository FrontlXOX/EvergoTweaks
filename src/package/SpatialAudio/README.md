# Everpal Spatial Audio Routing Master Blueprint

> **Prepared By:** Shovit Dutta
> **Author / Tuning:** himanshuksr0007 (Goku) x Shovit Dutta
> **Target Device:** Xiaomi POCO M4 Pro 5G / Redmi Note 11S 5G (`everpal`)
> **Hardware:** MediaTek Dimensity 810 (MT6833P / MT6833 family, 2x A76 @ 2.4 GHz + 6x A55 @ 2.0 GHz, Mali-G57 MC2)
> **Kernel & OS:** Linux `4.14.357-Aqua #3` | Android 16 (Project Infinity - `BP4A.251205.006`)
> **Target Repository:** [device_xiaomi_everpal](https://github.com/himanshuksr0007/device_xiaomi_everpal)
> **Date:** September 20, 2026

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
| **GPU Architecture**   | ARM Mali-G57 MC2 @ 950 MHz - 1068 MHz (Valhall v1, 2 Shader Cores)           |
| **Physical Memory**    | 4.00 GB LPDDR4X (Samsung KM5P9001DM-B424 uMCP, Kernel MemTotal: ~3.53 GB)     |
| **Internal Storage**   | 64 GB UFS 2.2 (Samsung KM5P9001DM-B424 uMCP, ~48 GB User Data Partition)     |
| **Audio Hardware**     | MediaTek MT6359 Codec + Awinic AW87389 SmartPA (mono-class speaker amp)       |
| **Root & Environment** | KernelSU (`ksud 4.2.0-rc1` / v1.0.5) + Zygisk / SELinux Enforcing             |

</details>

---

## 📁 Repository & Directory Layout

<details>
<summary><b>📁 Tap to expand Directory Layout & File Catalog</b></summary>
<br>

```text
src/package/SpatialAudio/
├── README.md                      # Comprehensive master technical manual & architecture guide
├── patch.patch                    # Standalone unified git patch for device_xiaomi_everpal
│
├── package/                       # Production flashable KernelSU / Magisk module
│   └── SpatialAudio.zip           # Flashable module (Author: FrontlXOX)
│
└── docs/                          # Complete architectural blueprint & integration guide
    └── spatial-audio.txt          # Master blueprint (Root-cause teardown, HAL fixes, git diff)
```

</details>

---

## ⚡ Executive Summary for Goku & Maintainers

On Android 16 (Project Infinity / LineageOS 23.0), the Xiaomi POCO M4 Pro 5G / Redmi Note 11S 5G (`everpal`) encountered severe audio routing chatter, audio patch storms, and occasional audioserver restarts when connecting wired headsets and rotating the device.

This subsystem provides the complete fix packaged as both a **systemless KernelSU/Magisk flashable module (`SpatialAudio.zip`)** and a **clean device tree patch (`patch.patch`)**.

### The 4 Core Fixes:

1. **`immersive_out` Concurrency Limitation:**
   - Adds `maxOpenCount="1" maxActiveCount="1"` to `mixPort name="immersive_out"`. Prevents `accdet` hardware interrupt bounces from opening multiple concurrent spatializer HAL output streams and saturating ALSA ring buffers.
   - Adds `AUDIO_CHANNEL_OUT_5POINT1` and `AUDIO_CHANNEL_OUT_7POINT1` channel masks for surround spatialization.

2. **Dolby DAP Stream Decoupling:**
   - Declares Dolby Audio Processing (`dap`) and Volume Listeners (`dvl`) as named effects only in `audio_effects.xml`.
   - Attaches them strictly per-session in `<postprocess>` across individual stream types (`music`, `ring`, `alarm`, `notification`, `voice_call`), preventing them from binding globally to the `AUDIO_OUTPUT_FLAG_SPATIALIZER` thread where AudioFlinger rejects them.

3. **Hardware Constraint Realignment:**
   - `persist.vendor.audio.spatializer.speaker_enabled=false`: Everpal has a single mono-class speaker (AW87389 / sia81xx) without multi-channel HRTF geometry. Disabling speaker spatialization eliminates needless re-route cascades.
   - `ro.audio.spatializer.headtracking_supported=false`: Everpal lacks a dedicated head-tracking sensor HAL. Disabling this eliminates the 43-second sensor discovery retry loop on headphone connection.
   - `ro.audio.monitorRotation=false`: Prevents screen rotation sensor triggers from recalculating head-tracking orientation.
   - `ro.vendor.audio.us.proximity=false`: Disables ultrasound proximity audio modem threads, which are absent on everpal hardware.

4. **DecibelSpatializer HAL Fallback:**
   - `ro.audio.spatializer.use_legacy_param_query=true`: Bypasses missing MTK params 10/13 HAL callbacks, forcing AudioFlinger to query spatializer state through legacy interfaces.

---

## 🛠️ Standalone Flashable Module (`src/package/SpatialAudio/package/SpatialAudio.zip`)

The flashable module is built using `scripts/builder.py --spatial` (or `--all`) and can be flashed directly in **KernelSU Manager**, **Magisk**, or **APatch**:

- **Module ID:** `everpal-spatial-audio`
- **Module Name:** `Everpal Spatial Audio Routing Fix`
- **Author:** `FrontlXOX`
- **Version:** `v1 (1)`

### Flash via ADB:
```bash
adb push src/package/SpatialAudio/package/SpatialAudio.zip /sdcard/
adb shell "su -c 'ksud module install /sdcard/SpatialAudio.zip'"
```

---

## 🌲 ROM Source Integration (`patch.patch`)

To bake these fixes directly into `device_xiaomi_everpal`:

```bash
cd device/xiaomi/everpal
git apply /path/to/EverpalTweaks/src/package/SpatialAudio/patch.patch
```

Or cherry-pick the commits directly:
```bash
git remote add goku https://github.com/himanshuksr0007/device_xiaomi_everpal.git
git fetch goku
git cherry-pick 3181d48e68b345b48091c0b1590e13c2601510d9
git cherry-pick 9b44c3693d63eab24b5eb558fda72501bb5806a0
git cherry-pick de93de3af829f971c10132bd4278113dfc0fc561
git cherry-pick 68fb9b12bec280eaf65e04f44f4d44b27c4bfdcd
```
> **Notice:** Commit `fc70a36b97876fb676c19bad7fb6e50bbb3d5c53` (switch to uncompressed EROFS) is intentionally excluded until kernel EROFS support is verified.
