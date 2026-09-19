# Vulkan 1.3 Hybrid Engine — EvergoTweaks Subsystem

> **Architecture, Implementation & Verification Specification for ARM Mali-G57 (Valhall v1) on MediaTek MT6833 / MT6833P**  
> Target Device: **Xiaomi POCO M4 Pro 5G / Redmi Note 11S 5G (`everpal` / `evergo`)**  
> Target Platform: **MediaTek Dimensity 810 5G (MT6833P, Mali-G57 MC2 @ 1068 MHz GED Boost)**  
> Target OS: **Android 16 (Project Infinity / LineageOS 23.0 Base, Build BP4A.251205.006)**  
> Target Kernel: **Linux 4.14.357-Aqua #3 SMP PREEMPT**  
> Primary Remote: `https://gitlab.com/ShovitDutta1/EvergoTweaks`  
> Author & Maintainer: **Shovit Dutta**  
> Special Thanks & Collaborators: **Addster09 x himanshuksr0007 (Goku)**  

---

## 1. Architectural Problem & The IOCTL Synchronization Trap

ARM Mali GPUs utilize a strict **split-driver architecture** where the user-space driver (ICD / HAL) and kernel-space device driver (`mali_kbase` at `/dev/mali0`) are version-locked via kernel ioctl ABIs:

```text
┌────────────────────────────────────────────────────────────────────────┐
│               Android Application / Game / 3D Engine                   │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│       Android Vulkan Loader (/system/lib64/libvulkan.so)               │
│               [Native Android 16 Vulkan 1.3/1.4 Loader]                │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│     User-Space ICD Blob (/vendor/lib64/hw/vulkan.mali.so)              │
│       Stock: r32p1-01eac0 (Vulkan 1.1) ──► Target: r49p1 (Vulkan 1.3) │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
                    IOCTL Interface (ABI Version Locked)
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│       Kernel Device Driver (/dev/mali0 — mali_kbase)                   │
│       Linux 4.14.357: mali-r32p1                                       │
└────────────────────────────────────────────────────────────────────────┘
```

### Why Direct User-Space Blob Replacement Bootloops
Replacing the entire vendor OpenGL ES and Vulkan driver stack (`libGLES_mali.so`, `vulkan.mali.so`) with newer `r44p0` or `r49p1` binaries on a device running an `r32p1` kernel causes an instant bootloop:
1. Android's **SurfaceFlinger** boots using OpenGL ES (`RenderEngine-GLES`).
2. `libGLES_mali.so` attempts to initialize `/dev/mali0` using the newer ioctl ABI structures.
3. The `r32p1` kernel driver rejects the unknown command codes with `EINVAL` (`Inappropriate ioctl for device`).
4. SurfaceFlinger crashes with `SIGSEGV`, causing an immediate system crash and persistent bootloop.

---

## 2. The Hybrid Decoupled Vulkan 1.3 Engine

To achieve **full Vulkan 1.3 capability** without destabilizing SurfaceFlinger:

1. **Dual-Stack Decoupling:**
   - **OpenGL ES:** Retains the stock, hardware-proven `/vendor/lib64/egl/libGLES_mali.so` (r32p1), ensuring SurfaceFlinger, system UI composition, and legacy GLES apps interact flawlessly with the Linux 4.14 `mali_kbase` kernel driver.
   - **Vulkan 1.3 ICD:** Deploys a dedicated, standalone **Valhall r49p1 Vulkan 1.3 ICD** (`libVK13_mali.so`) paired with a compliant HAL stub (`vulkan.mali.so`).
2. **Android 16 Feature Manifest Overlay:**
   Systemlessly injects certified Vulkan 1.3 feature declarations into `/vendor/etc/permissions/`:
   - `android.hardware.vulkan.version.xml` (`version = 4206592` = `0x00403000` = Vulkan 1.3.0)
   - `android.hardware.vulkan.level.xml` (`level = 1`)
   - `android.hardware.vulkan.compute.xml` (`version = 0`)
   - `android.software.vulkan.deqp.level.xml` (`date = 2023-03-01`)
3. **Hardware Driver Config:**
   Installs `/vendor/etc/mali_platform.config` to configure GPU memory limits, Mali shader cache pools, and pipeline caches.

---

## 3. Dynamic Linker Dependency Traps & Solutions

During live Bionic dynamic linker verification (`/system/bin/linker64 /vendor/lib64/hw/vulkan.mali.so`), two missing vendor extension symbols were uncovered that prevented the Vulkan 1.3 ICD from initializing:

### Blocker 1: Missing `GpuAuxBlitAHardwareBuffer`
- **Mechanism:** `libVK13_mali.so` references `GpuAuxBlitAHardwareBuffer`, a vendor extension symbol introduced in Dimensity 6080 HyperOS firmware for auxiliary GPU buffer blitting. Stock MT6833 `libgpu_aux.so` does not export this function.
- **Resolution:** Re-purposed an unused debug hook symbol in `libgpd1.so` (the companion debug library already declared as `DT_NEEDED` by `libVK13_mali.so`). Patched `.dynstr` and `.gnu.hash` in both 64-bit and 32-bit `libgpd1.so` to export `GpuAuxBlitAHardwareBuffer` with bit-exact Bionic `GnuHash::LookupByName` compatibility.

### Blocker 2: Missing `ged_fr_swd_frame_destroy` & `ged_fr_swd_mark_frame`
- **Mechanism:** `libVK13_mali.so` links to MediaTek's GPU Extension Device (`libged.so`) for frame rate watchdog telemetry (`ged_fr_swd_*`). The older stock MT6833 `libged.so` (58 KB) lacked these entry points.
- **Resolution:** Integrated the updated donor `libged.so` (101 KB) from HyperOS 2.0 (Dimensity 6080 `gold`). Symbol auditing proved the donor library is a **strict superset** of the stock binary (69 stock functions preserved + 23 new functions) with zero missing system dependencies.

---

## 4. Hardware Verification & Benchmark Records

Live hardware verification via `dumpsys gpu` confirmed:
- `vulkanVersion = 4206592` (0x00403000 = **Vulkan 1.3.0**)
- `glesVersion = 196610` (OpenGL ES 3.2)
- `createdVulkanDevice = 1`
- `vkDriverLoadingTime: 2493308 ns`
- `vkLoadingFailureCount = 0`

### Empirical Benchmark Achievements

| Benchmark / Workload | Stock AOSP Baseline | EvergoTweaks Peak | Record Status |
| :--- | :---: | :---: | :--- |
| **3DMark Sling Shot Extreme (Overall)** | `2,518` pts | **`2,736` pts** | 🚀 **+8.7% All-Time Global MT6833 Record** |
| **3DMark Sling Shot Extreme (Graphics)** | `2,316` pts | **`2,557` pts** | 🚀 **+10.4% (GT1: 17.30 FPS / GT2: 8.19 FPS)** |
| **3DMark Sling Shot Extreme (Physics / Vulkan)** | `3,379` pts | **`4,053` pts** | 🚀 **+20.0% (+674 pts — World Record Run)** |
| **Geekbench 7 GPU (Compute - OpenCL)** | ~`1,080` pts | **`1,302` pts** | 🚀 **+20.6% (Mali-G57 MC2 @ 1068 MHz GED Boost)** |
| **Geekbench 7 GPU (Compute - Vulkan)** | ❌ Unsupported | ✅ **Functional** | Full Vulkan 1.3 device creation & compute passes |

---

## 5. Building & Deploying the Module

All builds are centralized and validated via root Python automation:

```bash
# Build Vulkan 1.3 flashable KernelSU module:
python scripts/build_all.py --vulkan

# Build all modules (Memory, Thermal, Vulkan):
python scripts/build_all.py
```

### Flashable Output
- Path: `package/Vulkan13/package/Vulkan13-KernelSU.zip`
- Flash directly in **KernelSU Manager** and reboot.
