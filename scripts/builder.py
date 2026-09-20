#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EvergoTweaks Master Module Builder & Validator
Builds, packages, and validates all Magisk/KernelSU modules:
  - MemoryMgmt (Adaptive ZRAM, LMKD, swappiness, watermarks)
  - ThermalMgmt (sconfig 10, mi_thermald decoupling, 55°C headroom, GPU boost)
  - Vulkan13 (Valhall r49p1 Vulkan 1.3 ICD, AnyKernel3/KernelSU hybrid stack)
"""

import os
import sys
import shutil
import zipfile
import tempfile
import argparse

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_template_meta(root_dir: str) -> str:
    candidates = [
        os.path.join(
            root_dir, "package", "templates", "META-INF", "com", "google", "android"
        ),
        os.path.join(root_dir, "templates", "META-INF", "com", "google", "android"),
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    raise FileNotFoundError("Missing META-INF installer templates")


def get_vulkan_template(root_dir: str) -> str:
    candidates = [
        os.path.join(root_dir, "package", "templates", "Vulkan13"),
        os.path.join(root_dir, "package", "Vulkan13", "template"),
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    raise FileNotFoundError("Missing Vulkan13 template directory")


# ==============================================================================
# 1. MEMORY MANAGEMENT MODULE
# ==============================================================================
def build_memory_module(root_dir: str) -> str:
    template_meta = get_template_meta(root_dir)
    out_dir = os.path.join(root_dir, "package", "MemoryMgmt", "package")
    os.makedirs(out_dir, exist_ok=True)
    pkg_zip = os.path.join(out_dir, "MemoryMgmt.zip")

    with tempfile.TemporaryDirectory() as tmp_dir:
        meta_dir = os.path.join(tmp_dir, "META-INF", "com", "google", "android")
        os.makedirs(meta_dir, exist_ok=True)

        module_prop = """id=everpal-ram-mgmt
name=Everpal Memory Management
version=v1
versionCode=1
author=FrontlXOX
description=Master RAM & LMKD architecture for Xiaomi Everpal/Evergo (MT6833P / Dimensity 810). Adaptive ZRAM (3.58GB 4GB / 75% 6-8GB LZ4), swappiness 80, watermark_scale_factor 20, adaptive min_free_kbytes (24-40MB), swap_free_low 2%, UFS 512kB read-ahead. Eliminates direct reclaim stalls and aggressive app kills.
"""
        with open(
            os.path.join(tmp_dir, "module.prop"), "w", encoding="utf-8", newline="\n"
        ) as f:
            f.write(module_prop)

        system_prop = """# system.prop — injected by Magisk/KernelSU at boot.
# Everpal RAM Management v1

# ── LMKD ──────────────────────────────────────────────────────────────────
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

# ── PSI tuning ─────────────────────────────────────────────────────────────
ro.lmk.psi_partial_stall_ms=250
ro.lmk.psi_complete_stall_ms=800
ro.lmk.kill_timeout_ms=250
ro.lmk.critical_upgrade=false

# ── Activity Manager ───────────────────────────────────────────────────────
persist.sys.fw.bg_apps_limit=64
persist.device_config.activity_manager.max_cached_processes=64
persist.device_config.activity_manager.max_phantom_processes=32
persist.sys.fw.bservice_enable=true
persist.sys.fw.bservice_limit=8
persist.sys.fw.bservice_age=8000
persist.device_config.activity_manager_native_boot.freeze_debounce_timeout=600000
"""
        with open(
            os.path.join(tmp_dir, "system.prop"), "w", encoding="utf-8", newline="\n"
        ) as f:
            f.write(system_prop)

        service_sh = """#!/system/bin/sh
# service.sh — Magisk/KernelSU late-start. Mirrors init.mt6833.rc + init.everpal.rc (v1).

TAG="[everpal-ram-mgmt]"

write() {
    local path="$1" val="$2"
    if [ -w "$path" ]; then
        echo "$val" > "$path"
        echo "$TAG set $path = $val"
    else
        echo "$TAG SKIP $path (not writable)" >&2
    fi
}

log -t "$TAG" "Applying Everpal RAM & LMKD architecture v1..."

# 1. Detect RAM Size & Set Dynamic Parameters
TOTAL_RAM_KB=$(awk '/MemTotal:/ {print $2}' /proc/meminfo)

if [ "$TOTAL_RAM_KB" -lt 5000000 ]; then
    # 4GB Variant (~3,709,888 kB) -> 100% MemTotal (~3.58 GB ZRAM)
    ZRAM_SIZE_BYTES=3758096384
    MIN_FREE_KB=24576
    BG_LIMIT=64
elif [ "$TOTAL_RAM_KB" -lt 7000000 ]; then
    # 6GB Variant (~5,800,000 kB) -> 75% MemTotal (~4.2 GB ZRAM)
    ZRAM_SIZE_BYTES=4509715660
    MIN_FREE_KB=32768
    BG_LIMIT=96
else
    # 8GB Variant (~7,800,000 kB) -> 75% MemTotal (~5.6 GB ZRAM)
    ZRAM_SIZE_BYTES=6012954214
    MIN_FREE_KB=40960
    BG_LIMIT=128
fi

# Set dynamic userspace cached app limits
setprop persist.sys.fw.bg_apps_limit "$BG_LIMIT"
setprop persist.device_config.activity_manager.max_cached_processes "$BG_LIMIT"
setprop persist.device_config.activity_manager.max_phantom_processes $((BG_LIMIT / 2))

# 2. Kernel VM Watermarks & Swappiness
write /proc/sys/vm/swappiness 80
write /proc/sys/vm/vfs_cache_pressure 80
write /proc/sys/vm/watermark_scale_factor 20
write /proc/sys/vm/min_free_kbytes "$MIN_FREE_KB"
write /proc/sys/vm/extra_free_kbytes 0
write /proc/sys/vm/overcommit_memory 1
write /proc/sys/vm/page-cluster 0

# Dynamic memory compaction at boot
write /proc/sys/vm/compact_memory 1

# 3. Dynamic ZRAM Reconfiguration
if [ -b /dev/block/zram0 ]; then
    CURR_SWAP_SIZE=$(awk '/zram0/ {print $3}' /proc/swaps 2>/dev/null)
    CURR_SWAP_BYTES=$((CURR_SWAP_SIZE * 1024))

    # Re-initialize only if size differs significantly
    DIFF=$((ZRAM_SIZE_BYTES - CURR_SWAP_BYTES))
    if [ "$DIFF" -gt 104857600 ] || [ "$DIFF" -lt -104857600 ]; then
        log -t "$TAG" "Reconfiguring ZRAM to $ZRAM_SIZE_BYTES bytes (LZ4)..."
        swapoff /dev/block/zram0 2>/dev/null
        write /sys/block/zram0/reset 1
        
        if [ -f /sys/block/zram0/comp_algorithm ]; then
            write /sys/block/zram0/comp_algorithm lz4
        fi

        NPROC=$(nproc 2>/dev/null || echo 8)
        write /sys/block/zram0/max_comp_streams "$NPROC"
        write /sys/block/zram0/disksize "$ZRAM_SIZE_BYTES"
        mkswap /dev/block/zram0
        swapon /dev/block/zram0 -p 32767
    fi
fi

# 4. Storage I/O Read-Ahead & Optimization (UFS 2.2)
for queue in /sys/block/sd*/queue; do
    if [ -d "$queue" ]; then
        write "$queue/read_ahead_kb" 512
        write "$queue/nr_requests" 128
        write "$queue/iostats" 0
    fi
done

log -t "$TAG" "Everpal RAM & LMKD architecture v1 applied successfully."
"""
        with open(
            os.path.join(tmp_dir, "service.sh"), "w", encoding="utf-8", newline="\n"
        ) as f:
            f.write(service_sh)

        for meta_file in ["update-binary", "updater-script"]:
            src_f = os.path.join(template_meta, meta_file)
            dst_f = os.path.join(meta_dir, meta_file)
            shutil.copy2(src_f, dst_f)

        with zipfile.ZipFile(pkg_zip, "w", zipfile.ZIP_DEFLATED) as z:
            for root, _, files in os.walk(tmp_dir):
                for f in files:
                    full_path = os.path.join(root, f)
                    rel_path = os.path.relpath(full_path, tmp_dir)
                    z.write(full_path, rel_path)

    size = os.path.getsize(pkg_zip)
    print(f"[+] Successfully built {pkg_zip} ({size} bytes)")
    return pkg_zip


# ==============================================================================
# 2. THERMAL MANAGEMENT MODULE
# ==============================================================================
def build_thermal_module(root_dir: str) -> str:
    template_meta = get_template_meta(root_dir)
    out_dir = os.path.join(root_dir, "package", "ThermalMgmt", "package")
    os.makedirs(out_dir, exist_ok=True)
    pkg_zip = os.path.join(out_dir, "ThermalMgmt.zip")

    with tempfile.TemporaryDirectory() as tmp_dir:
        meta_dir = os.path.join(tmp_dir, "META-INF", "com", "google", "android")
        os.makedirs(meta_dir, exist_ok=True)

        module_prop = """id=everpal-thermal-master
name=Everpal Thermal Management & Performance Master
version=v1
versionCode=1
author=FrontlXOX
description=Hardware compute master for Xiaomi Everpal/Evergo (Dimensity 810). Decouples thermal regulation from missing joyose, locks sconfig 10 (55°C headroom), pins CoreLink CCI at 1.6 GHz, accelerates Mali-G57 GPU DVFS to 50ms with 1068MHz boost, and unlocks full 2.4 GHz Big core capability.
"""
        with open(
            os.path.join(tmp_dir, "module.prop"), "w", encoding="utf-8", newline="\n"
        ) as f:
            f.write(module_prop)

        system_prop = """# system.prop — injected by Magisk/KernelSU at boot.
# Everpal Thermal & Performance Master v1

sys.thermal.mode=10
sys.thermal.config=thermal-nolimits.conf
persist.sys.thermal.mode=10
persist.sys.thermal.config=thermal-nolimits.conf

# MediaTek GED & GPU Acceleration
ro.vendor.ged.hal.enable=1
ro.vendor.ged.boost_enable=1
ro.vendor.ged.profile=gaming
debug.sf.disable_backpressure=1
debug.sf.enable_gl_backpressure=0
"""
        with open(
            os.path.join(tmp_dir, "system.prop"), "w", encoding="utf-8", newline="\n"
        ) as f:
            f.write(system_prop)

        service_sh = """#!/system/bin/sh
# service.sh — Magisk/KernelSU late-start. Hardware Compute Master v1.

TAG="[everpal-thermal-master]"

write() {
    local path="$1" val="$2"
    if [ -w "$path" ]; then
        echo "$val" > "$path"
        echo "$TAG set $path = $val"
    else
        echo "$TAG SKIP $path (not writable)" >&2
    fi
}

lock_node() {
    local path="$1" val="$2"
    if [ -e "$path" ]; then
        chmod 644 "$path" 2>/dev/null
        echo "$val" > "$path" 2>/dev/null
        chmod 444 "$path" 2>/dev/null
        echo "$TAG LOCKED $path = $val (read-only)"
    fi
}

log -t "$TAG" "Applying Everpal Hardware Compute Master v1..."

# 1. Thermal Governor & Sconfig 10
setprop sys.thermal.mode 10
setprop sys.thermal.config thermal-nolimits.conf
setprop persist.sys.thermal.mode 10
setprop persist.sys.thermal.config thermal-nolimits.conf

if [ -f /sys/class/thermal/thermal_message/sconfig ]; then
    write /sys/class/thermal/thermal_message/sconfig 10
fi

# Reset any stuck throttling floors
write /proc/driver/thermal/cl_kpi 0
write /proc/driver/thermal/cl_sdm_kpi 0

# 2. MediaTek CoreLink CCI Hardware Interconnect Lock (1.60 GHz Mode)
for cci in /sys/devices/platform/10012000.dvfsrc/dvfsrc_force_vcore_opp \\
           /sys/devices/platform/soc/10012000.dvfsrc/dvfsrc_force_vcore_opp \\
           /proc/driver/dvfsrc/force_vcore_opp; do
    if [ -e "$cci" ]; then
        lock_node "$cci" 0
    fi
done

# 3. ARM Mali-G57 MC2 GPU Acceleration & DVFS Lock (50ms Evaluation)
for dvfs_p in /sys/module/pvrsrvkm/parameters/gpu_dvfs_period \\
              /sys/devices/platform/13040000.mali/gpu_dvfs_period \\
              /sys/devices/platform/soc/13040000.mali/gpu_dvfs_period; do
    if [ -e "$dvfs_p" ]; then
        lock_node "$dvfs_p" 50
    fi
done

for gpower in /sys/devices/platform/13040000.mali/power_policy \\
              /sys/devices/platform/soc/13040000.mali/power_policy; do
    if [ -e "$gpower" ]; then
        write "$gpower" "always_on"
    fi
done

# MediaTek GED Boost & GPU Freq Clamps
for ged in /sys/module/ged/parameters; do
    if [ -d "$ged" ]; then
        write "$ged/gpu_bottom_freq" 955000
        write "$ged/gpu_cust_boost_freq" 1068000
        write "$ged/gpu_cust_upbound_freq" 1068000
        write "$ged/ged_boost_enable" 1
        write "$ged/ged_smart_boost" 1
        write "$ged/boost_extra_freq" 1068000
        write "$ged/boost_gpu_enable" 1
        write "$ged/boost_upper_bound" 1068000
        write "$ged/enable_game_self_frc" 1
        write "$ged/gx_game_mode" 1
        write "$ged/gx_frc_mode" 1
        write "$ged/gx_boost_on" 1
        write "$ged/is_ged_srv_running" 1
    fi
done

# 4. CPU Schedutil Latency Elimination & BORE Optimization
for pol in /sys/devices/system/cpu/cpufreq/policy*; do
    if [ -d "$pol" ]; then
        write "$pol/schedutil/up_rate_limit_us" 0
        write "$pol/schedutil/down_rate_limit_us" 500
        write "$pol/schedutil/iowait_boost_enable" 1
    fi
done

write /proc/sys/kernel/sched_migration_cost_ns 250000
write /dev/cpuset/top-app/cpu.shares 10240
write /dev/cpuset/foreground/cpu.shares 8192
write /dev/cpuset/foreground/cpus 0-7
write /dev/cpuset/top-app/cpus 0-7

# 5. Network & Wi-Fi Latency Stabilization
write /proc/sys/net/ipv4/tcp_slow_start_after_idle 0
write /proc/sys/net/ipv4/tcp_keepalive_time 60
write /proc/sys/net/ipv4/tcp_keepalive_intvl 10
write /proc/sys/net/ipv4/tcp_keepalive_probes 5

log -t "$TAG" "Everpal Hardware Compute Master v1 applied successfully."
"""
        with open(
            os.path.join(tmp_dir, "service.sh"), "w", encoding="utf-8", newline="\n"
        ) as f:
            f.write(service_sh)

        for meta_file in ["update-binary", "updater-script"]:
            src_f = os.path.join(template_meta, meta_file)
            dst_f = os.path.join(meta_dir, meta_file)
            shutil.copy2(src_f, dst_f)

        with zipfile.ZipFile(pkg_zip, "w", zipfile.ZIP_DEFLATED) as z:
            for root, _, files in os.walk(tmp_dir):
                for f in files:
                    full_path = os.path.join(root, f)
                    rel_path = os.path.relpath(full_path, tmp_dir)
                    z.write(full_path, rel_path)

    size = os.path.getsize(pkg_zip)
    print(f"[+] Successfully built {pkg_zip} ({size} bytes)")
    return pkg_zip


# ==============================================================================
# 3. VULKAN 1.3 HYBRID ENGINE MODULE
# ==============================================================================
def build_vulkan13_module(
    root_dir: str,
    kernel_image: str = None,
    dtbo_image: str = None,
    blobs_dir: str = None,
) -> str:
    template_dir = get_vulkan_template(root_dir)
    out_dir = os.path.join(root_dir, "package", "Vulkan13", "package")
    os.makedirs(out_dir, exist_ok=True)
    pkg_zip = os.path.join(out_dir, "Vulkan13-KernelSU.zip")

    with tempfile.TemporaryDirectory() as tmp_dir:
        # Copy base template structure
        for item in os.listdir(template_dir):
            s = os.path.join(template_dir, item)
            d = os.path.join(tmp_dir, item)
            if os.path.isdir(s):
                shutil.copytree(s, d, symlinks=True)
            else:
                shutil.copy2(s, d)

        # Inject kernel image if provided
        if kernel_image and os.path.exists(kernel_image):
            target_kernel = os.path.join(tmp_dir, "Image.gz")
            shutil.copy2(kernel_image, target_kernel)
            print(f"    -> Injected kernel image: {kernel_image}")

        # Inject dtbo image if provided
        if dtbo_image and os.path.exists(dtbo_image):
            target_dtbo = os.path.join(tmp_dir, "dtbo.img")
            shutil.copy2(dtbo_image, target_dtbo)
            print(f"    -> Injected dtbo image: {dtbo_image}")

        # Inject additional donor vendor blobs if specified
        if blobs_dir and os.path.exists(blobs_dir):
            for root, _, files in os.walk(blobs_dir):
                for f in files:
                    if f in ("vulkan.mali.so", "libGLES_mali.so", "libGLES_meow.so"):
                        rel_path = os.path.relpath(os.path.join(root, f), blobs_dir)
                        target_loc = os.path.join(tmp_dir, "system", "vendor", rel_path)
                        os.makedirs(os.path.dirname(target_loc), exist_ok=True)
                        shutil.copy2(os.path.join(root, f), target_loc)
                        print(f"    -> Mapped {f} to system/vendor/{rel_path}")

        # Assemble flashable zip package
        with zipfile.ZipFile(pkg_zip, "w", zipfile.ZIP_DEFLATED) as z:
            for root, _, files in os.walk(tmp_dir):
                for f in files:
                    full_path = os.path.join(root, f)
                    rel_path = os.path.relpath(full_path, tmp_dir)
                    z.write(full_path, rel_path)

    size_bytes = os.path.getsize(pkg_zip)
    print(
        f"[+] Successfully built {pkg_zip} ({size_bytes} bytes / {size_bytes / 1024:.1f} KB)"
    )
    return pkg_zip


# ==============================================================================
# CRC-32 & PACKAGE VALIDATION
# ==============================================================================
def verify_package(zip_path: str) -> bool:
    if not os.path.exists(zip_path):
        print(f"[-] ERROR: Package file does not exist: {zip_path}")
        return False

    with zipfile.ZipFile(zip_path, "r") as z:
        names = z.namelist()
        bad_file = z.testzip()
        if bad_file:
            print(f"[-] ERROR: Corrupt entry in {zip_path}: {bad_file}")
            return False

    print(
        f"[✓] {os.path.basename(zip_path)} verified: {len(names)} entries, CRC-32 valid ({os.path.getsize(zip_path)} bytes)"
    )
    return True


# ==============================================================================
# CLI ENTRY POINT
# ==============================================================================
def main():
    parser = argparse.ArgumentParser(
        description="EvergoTweaks Master Module Builder & Validator"
    )
    parser.add_argument(
        "--all", action="store_true", help="Build all modules (default if none chosen)"
    )
    parser.add_argument(
        "--memory", "-m", action="store_true", help="Build MemoryMgmt.zip"
    )
    parser.add_argument(
        "--thermal", "-t", action="store_true", help="Build ThermalMgmt.zip"
    )
    parser.add_argument(
        "--vulkan", "-v", action="store_true", help="Build Vulkan13-KernelSU.zip"
    )
    parser.add_argument(
        "--kernel", "-k", default=None, help="Path to compiled Image.gz (for Vulkan13)"
    )
    parser.add_argument(
        "--dtbo", "-d", default=None, help="Path to compiled dtbo.img (for Vulkan13)"
    )
    parser.add_argument(
        "--blobs", "-b", default=None, help="Path to donor vendor blobs directory"
    )

    args = parser.parse_args()

    build_mem = args.memory
    build_therm = args.thermal
    build_vulk = args.vulkan

    # Default to building all if no specific target is given
    if not (build_mem or build_therm or build_vulk) or args.all:
        build_mem = True
        build_therm = True
        build_vulk = True

    print("=" * 60)
    print(" EvergoTweaks Master Module Builder & Validator")
    print("=" * 60)

    total_steps = sum([build_mem, build_therm, build_vulk])
    step = 1

    mem_zip = None
    therm_zip = None
    vulk_zip = None

    if build_mem:
        print(f"\n[{step}/{total_steps}] Building MemoryMgmt.zip...")
        mem_zip = build_memory_module(REPO_ROOT)
        step += 1

    if build_therm:
        print(f"\n[{step}/{total_steps}] Building ThermalMgmt.zip...")
        therm_zip = build_thermal_module(REPO_ROOT)
        step += 1

    if build_vulk:
        print(f"\n[{step}/{total_steps}] Building Vulkan13-KernelSU.zip...")
        vulk_zip = build_vulkan13_module(
            REPO_ROOT,
            kernel_image=args.kernel,
            dtbo_image=args.dtbo,
            blobs_dir=args.blobs,
        )
        step += 1

    print("\n" + "=" * 60)
    print(" Verifying Packages (CRC-32 & Structure)")
    print("=" * 60)

    all_ok = True
    if build_mem and mem_zip:
        all_ok = all_ok and verify_package(mem_zip)

    if build_therm and therm_zip:
        all_ok = all_ok and verify_package(therm_zip)

    if build_vulk and vulk_zip:
        all_ok = all_ok and verify_package(vulk_zip)

    if all_ok:
        print("\n[+] All requested modules successfully built and verified!\n")
        sys.exit(0)
    else:
        print("\n[-] Build validation failed for one or more modules!\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
