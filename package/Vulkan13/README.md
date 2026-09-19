# Vulkan 1.3 Hybrid Engine — EvergoTweaks Subsystem

> **Architecture & Implementation Specification for ARM Mali-G57 (Valhall v1) on MediaTek MT6833 / MT6833P**  
> Target Device: **Xiaomi POCO M4 Pro 5G / Redmi Note 11S 5G (`everpal` / `evergo`)**  
> Target Platform: **MediaTek Dimensity 810 (MT6833P, Mali-G57 MC2)**  
> Target OS: **Android 16 (Project Infinity / LineageOS 23.0)**  
> Kernel: **Linux 4.14.357-Aqua #3 SMP PREEMPT**  

---

## 1. Architectural Problem & The IOCTL Trap

ARM Mali GPUs utilize a **split-driver architecture** where the user-space driver and kernel-space driver are strictly version-locked:

```text
┌────────────────────────────────────────────────────────────────────────┐
│               Android Application / Game / Benchmark                   │
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
│       Current: r32p1-01eac0 (Vulkan 1.1) ──► Target: r44p0 (Vulkan 1.3)│
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
                    IOCTL Interface (ABI Version Locked)
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│       Kernel Device Driver (/dev/mali0 — mali_kbase)                   │
│       Current: mali-r32p1                ──► Target: mali-r44p0         │
└────────────────────────────────────────────────────────────────────────┘
```

### Why Magisk/KernelSU Modules Alone Fail
If you replace only the user-space libraries (`libGLES_mali.so`, `vulkan.mali.so`) with newer `r44p0` binaries while keeping an `r32p1` kernel:
1. The new driver attempts to initialize `/dev/mali0` using the `r44p0` `ioctl` structure.
2. The `r32p1` kernel driver rejects the unknown command codes with `EINVAL` or `Inappropriate ioctl for device`.
3. SurfaceFlinger crashes with `SIGSEGV`, causing an immediate black screen or bootloop.

---

## 2. The Hybrid KernelSU + AnyKernel3 Solution

To resolve the synchronization trap without forcing users to re-flash their entire custom ROM, EvergoTweaks implements a **Hybrid KernelSU Engine**:

1. **At Flash Time (in KernelSU Manager / TWRP):**
   - The installer uses **AnyKernel3** (`split_boot`) to unpack the device's live `boot` partition, replace the kernel with the `mali-r44p0`-enabled `Image.gz`, and write it back to `/dev/block/by-name/boot`.
   - Simultaneously, it detects `/data/adb/modules/` and deploys the matching `r44p0` user-space libraries and Android Vulkan 1.3 feature XMLs systemlessly into `/data/adb/modules/everpal-vulkan13/`.
2. **At Boot Time:**
   - The device boots the new kernel with the matching `mali_kbase` driver.
   - KernelSU overlays `/vendor/lib64/hw/vulkan.mali.so`, `/vendor/lib64/egl/libGLES_mali.so`, and `/vendor/etc/permissions/android.hardware.vulkan.version.xml`.
   - Both layers initialize with matching DDK revisions.

---

## 3. Required Kernel & Vendor Upgrades

### Layer 1: Kernel Driver (`trees/kernel/`)
- Driver path: `drivers/misc/mediatek/gpu/gpu_mali/mali_valhall/`
- Target DDK revision: `mali-r44p0`
- Config switch in `arch/arm64/configs/everpal_defconfig`:
  ```makefile
  -CONFIG_MTK_GPU_VERSION="mali valhall r32p1"
  +CONFIG_MTK_GPU_VERSION="mali valhall r44p0"
  ```

### Layer 2: Donor Vendor Blobs (`trees/vendor_xiaomi_everpal/`)
Donor devices sharing identical MT6833 silicon and Mali-G57 MC2 running HyperOS / Android 14+:
- **Redmi Note 13 5G (`gold`)** — Dimensity 6080 (Overclocked MT6833)
- **POCO M6 Pro 5G / Redmi 12 5G**
- Required files:
  - `proprietary/vendor/lib64/egl/libGLES_mali.so`
  - `proprietary/vendor/lib64/hw/vulkan.mali.so`
  - `proprietary/vendor/lib/egl/libGLES_mali.so` (32-bit)
  - `proprietary/vendor/lib/hw/vulkan.mali.so` (32-bit)

### Layer 3: System Feature Declaration
In `/vendor/etc/permissions/android.hardware.vulkan.version.xml`:
```xml
<?xml version="1.0" encoding="utf-8"?>
<permissions>
    <feature name="android.hardware.vulkan.version" version="4206592" />
</permissions>
```
*(4206592 = `0x403000` = Vulkan 1.3.0)*

---

## 4. Building the Hybrid Package

To build the flashable hybrid module:

```bash
# Build complete package with bundled kernel and blobs:
python scripts/build_vulkan13.py --kernel out/arch/arm64/boot/Image.gz --blobs path/to/r44p0_blobs/

# Or package existing template for KernelSU overlay:
python scripts/build_vulkan13.py
```

Output:
`package/Vulkan13/package/Vulkan13-KernelSU.zip`

Flash directly inside **KernelSU Manager** and reboot.
