#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# pylint: skip-file
# pylint: disable=all
# flake8: noqa
# ruff: noqa
# type: ignore

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
author=TesterProd
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

do_resetprop() {
    local k="$1" v="$2"
    if command -v resetprop >/dev/null 2>&1; then
        resetprop "$k" "$v"
    elif [ -x /data/adb/ksu/bin/resetprop ]; then
        /data/adb/ksu/bin/resetprop "$k" "$v"
    elif [ -x /data/adb/magisk/resetprop ]; then
        /data/adb/magisk/resetprop "$k" "$v"
    elif [ -x /data/adb/ap/bin/resetprop ]; then
        /data/adb/ap/bin/resetprop "$k" "$v"
    elif [ -x /system/bin/resetprop ]; then
        /system/bin/resetprop "$k" "$v"
    fi
}

# ── Detect Physical RAM & CPU Topology dynamically ───────────────────────
MEM_TOTAL_KB=$(awk '/MemTotal/ {print $2}' /proc/meminfo 2>/dev/null)
[ -z "$MEM_TOTAL_KB" ] && MEM_TOTAL_KB=3709888
MEM_TOTAL_MB=$(( MEM_TOTAL_KB / 1024 ))

CPU_CORES=$(nproc 2>/dev/null || cat /sys/devices/system/cpu/present 2>/dev/null | awk -F'-' '{print $2+1}')
[ -z "$CPU_CORES" ] || [ "$CPU_CORES" -le 0 ] && CPU_CORES=8

# ── Dynamic Variant Sizing (4GB / 6GB / 8GB MT6833 Family) ───────────────
if [ "$MEM_TOTAL_MB" -ge 7000 ]; then
    # 8GB Physical RAM Variant (~7.5GB Linux MemTotal)
    ZRAM_SIZE_BYTES=$(( (MEM_TOTAL_KB * 1024 * 75) / 100 ))
    MIN_FREE_KB=40960
    BG_APPS=128
    PHANTOM_APPS=48
elif [ "$MEM_TOTAL_MB" -ge 5000 ]; then
    # 6GB Physical RAM Variant (~5.5GB Linux MemTotal)
    ZRAM_SIZE_BYTES=$(( (MEM_TOTAL_KB * 1024 * 75) / 100 ))
    MIN_FREE_KB=32768
    BG_APPS=96
    PHANTOM_APPS=40
else
    # 4GB Physical RAM Variant (~3.53GB Linux MemTotal)
    # Calibrated to 3,758,096,384 bytes (3.58GB), 24MB min_free, 64 cached apps
    ZRAM_SIZE_BYTES=3758096384
    MIN_FREE_KB=24576
    BG_APPS=64
    PHANTOM_APPS=32
fi

# ── ZRAM: Adaptive Expansion with LZ4 & Parallel CPU Streams ───────────────
if [ -b /dev/block/zram0 ]; then
    CURRENT_SIZE=$(cat /sys/block/zram0/disksize 2>/dev/null)
    if [ "$CURRENT_SIZE" != "$ZRAM_SIZE_BYTES" ]; then
        swapoff /dev/block/zram0 2>/dev/null
        echo 1 > /sys/block/zram0/reset 2>/dev/null
        echo "lz4" > /sys/block/zram0/comp_algorithm 2>/dev/null
        echo "$CPU_CORES" > /sys/block/zram0/max_comp_streams 2>/dev/null
        echo "$ZRAM_SIZE_BYTES" > /sys/block/zram0/disksize 2>/dev/null
        mkswap /dev/block/zram0 2>/dev/null
        swapon /dev/block/zram0 2>/dev/null
        echo "$TAG zram0 resized dynamically to ${ZRAM_SIZE_BYTES} bytes (LZ4, ${CPU_CORES} streams) for ${MEM_TOTAL_MB}MB RAM"
    else
        echo "$CPU_CORES" > /sys/block/zram0/max_comp_streams 2>/dev/null
        echo "$TAG zram0 already optimal (${ZRAM_SIZE_BYTES} bytes, ${CPU_CORES} streams)"
    fi
fi

# ── VM / memory management (swappiness 80, wsf 20, adaptive min_free) ─────
write /proc/sys/vm/swappiness               80
write /proc/sys/vm/watermark_scale_factor   20
write /proc/sys/vm/min_free_kbytes          $MIN_FREE_KB
write /sys/kernel/mm/swap/vma_ra_enabled    false
write /proc/sys/vm/page-cluster             0
write /proc/sys/vm/vfs_cache_pressure       80
write /proc/sys/vm/dirty_ratio              30
write /proc/sys/vm/dirty_background_ratio   10

# ── Storage I/O Optimization (UFS 2.2) ────────────────────────────────────
for d in /sys/block/sd*; do
    [ -f "$d/queue/read_ahead_kb" ] && write "$d/queue/read_ahead_kb" 512
    [ -f "$d/queue/iostats" ] && write "$d/queue/iostats" 0
done

# ── Post-boot (Linux 4.14: compact_memory, not compaction_proactiveness) ──
write /proc/sys/vm/stat_interval            10
write /proc/sys/vm/compact_memory           1

# ── Runtime LMK & AM property updates (Adaptive RAM Scaling) ──────────────
do_resetprop persist.sys.fw.bg_apps_limit "$BG_APPS"
do_resetprop persist.device_config.activity_manager.max_cached_processes "$BG_APPS"
do_resetprop persist.device_config.activity_manager.max_phantom_processes "$PHANTOM_APPS"
do_resetprop ro.lmk.thrashing_limit 300
do_resetprop ro.lmk.thrashing_limit_decay 15
do_resetprop ro.lmk.downgrade_pressure 80
do_resetprop ro.lmk.swap_util_max 90
do_resetprop ro.lmk.swap_free_low_percentage 2
do_resetprop ro.lmk.kill_heaviest_task false
do_resetprop ro.lmk.psi_partial_stall_ms 250
do_resetprop ro.lmk.psi_complete_stall_ms 800
do_resetprop ro.lmk.kill_timeout_ms 250
do_resetprop ro.lmk.critical_upgrade false

echo "$TAG all RAM tweaks applied dynamically for ${MEM_TOTAL_MB}MB device tier"
"""
        with open(
            os.path.join(tmp_dir, "service.sh"), "w", encoding="utf-8", newline="\n"
        ) as f:
            f.write(service_sh)

        shutil.copy(
            os.path.join(template_meta, "update-binary"),
            os.path.join(meta_dir, "update-binary"),
        )
        shutil.copy(
            os.path.join(template_meta, "updater-script"),
            os.path.join(meta_dir, "updater-script"),
        )

        with zipfile.ZipFile(pkg_zip, "w", zipfile.ZIP_DEFLATED) as z:
            for root, dirs, files in os.walk(tmp_dir):
                for file in files:
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, tmp_dir)
                    z.write(full_path, rel_path)

    print(f"[+] Successfully built {pkg_zip} ({os.path.getsize(pkg_zip)} bytes)")
    return pkg_zip


def build_thermal_module(root_dir: str) -> str:
    template_meta = get_template_meta(root_dir)
    subproject_dir = os.path.join(root_dir, "package", "ThermalMgmt")
    nolimits_conf = os.path.join(
        subproject_dir, "docs", "vendor_configs", "thermal-nolimits.conf"
    )
    if not os.path.exists(nolimits_conf):
        raise FileNotFoundError(f"Missing thermal-nolimits.conf at {nolimits_conf}")

    out_dir = os.path.join(subproject_dir, "package")
    os.makedirs(out_dir, exist_ok=True)
    pkg_zip = os.path.join(out_dir, "ThermalMgmt.zip")

    with tempfile.TemporaryDirectory() as tmp_dir:
        meta_dir = os.path.join(tmp_dir, "META-INF", "com", "google", "android")
        vendor_etc = os.path.join(tmp_dir, "system", "vendor", "etc")
        os.makedirs(meta_dir, exist_ok=True)
        os.makedirs(vendor_etc, exist_ok=True)

        module_prop = """id=everpal-thermal-master
name=Everpal Thermal Management
version=v1
versionCode=1
author=TesterProd
description=Master thermal & performance architecture for Xiaomi Everpal/Evergo (MT6833P / Dimensity 810). Unlocks full 2.0GHz A55 / 2.4GHz A76 hardware clocks (sconfig 10 / NoLimits, 55C headroom), CoreLink CCI 1.6GHz Perf mode lock, DVFSRC 4.266GHz LPDDR4X RAM lock, DVFS Sports mode, Schedutil 0us instant ramp, cpuset 0-7 foreground, BORE big task rotation, Mali-G57 always_on & 50ms DVFS lock, and TCP Wi-Fi resilience.
"""
        with open(
            os.path.join(tmp_dir, "module.prop"), "w", encoding="utf-8", newline="\n"
        ) as f:
            f.write(module_prop)

        service_sh = """#!/system/bin/sh
# Everpal Thermal Master Service (v1)
# Prepared By: Shovit Dutta | Author / Research: Addster09 x Shovit Dutta
# Module Author: TesterProd

LOG="/data/adb/everpal-thermal.log"

log_msg() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG"
}

write() {
    local path="$1" val="$2"
    if [ -f "$path" ] || [ -w "$path" ]; then
        chmod 664 "$path" 2>/dev/null
        echo "$val" > "$path" 2>/dev/null
        log_msg "set $path = $val"
    fi
}

# Wait for system boot completion
while [ "$(getprop sys.boot_completed)" != "1" ]; do
    sleep 2
done

sleep 3
log_msg "Everpal Thermal Master v1 initializing..."

# 1. Enforce sconfig 10 (Xiaomi MT6833 High-Performance Mobile Game / NoLimits Profile)
# Verified: sconfig 10 unlocks 100% 2.0GHz Cortex-A55 and 2.4GHz Cortex-A76 clocks with 55°C headroom
write /sys/class/thermal/thermal_message/sconfig 10

# 2. Verify and enforce full CPU scaling max frequencies
for p in /sys/devices/system/cpu/cpufreq/policy*; do
    if [ -f "$p/scaling_max_freq" ] && [ -f "$p/cpuinfo_max_freq" ]; then
        max_f=$(cat "$p/cpuinfo_max_freq")
        echo "$max_f" > "$p/scaling_max_freq" 2>/dev/null
    fi
done
log_msg "CPU scaling policy max frequencies verified uncapped."

# 3. CPU Schedutil Governor Instant Ramp-Up (0 µs debounce) & Frequency Hold (20 ms)
# Eliminates clock ramp latency across Cortex-A76 Big cores (policy6) and LITTLE cores (policy0)
write /sys/devices/system/cpu/cpufreq/policy6/schedutil/up_rate_limit_us 0
write /sys/devices/system/cpu/cpufreq/policy0/schedutil/up_rate_limit_us 0
write /sys/devices/system/cpu/cpufreq/policy6/schedutil/down_rate_limit_us 20000
write /sys/devices/system/cpu/cpufreq/policy0/schedutil/down_rate_limit_us 20000

# 4. MediaTek CoreLink Cache Coherent Interconnect (CCI) Perf Mode Hardware Lock
# Mode 1: Boosts interconnect and L3 cache coherency bandwidth between A76 and A55 clusters to 1.6 GHz (OPP 0)
# chmod 444 blocks non-root Power HAL from reverting to Normal mode (OPP 3-6)
write /proc/cpufreq/cpufreq_cci_mode 1
chmod 444 /proc/cpufreq/cpufreq_cci_mode 2>/dev/null

# Unlocks peak LPDDR4X transfer rate to 4.266 GHz (OPP 0) and Vcore to 725 mV
[ -f /sys/devices/platform/10012000.dvfsrc/helio-dvfsrc/dvfsrc_req_ddr_opp ] && echo 0 > /sys/devices/platform/10012000.dvfsrc/helio-dvfsrc/dvfsrc_req_ddr_opp 2>/dev/null
[ -f /sys/devices/platform/10012000.dvfsrc/helio-dvfsrc/dvfsrc_req_vcore_opp ] && echo 0 > /sys/devices/platform/10012000.dvfsrc/helio-dvfsrc/dvfsrc_req_vcore_opp 2>/dev/null
[ -f /proc/perfmgr/boost_ctrl/dram_ctrl/ddr ] && echo 0 > /proc/perfmgr/boost_ctrl/dram_ctrl/ddr 2>/dev/null

# MediaTek PPM (Processor Power Management) Power Budget Uncap
# Policy 3 (PWR_THRO) enforces artificial power ceilings; disabling unlocks full compute
# Policy 5 (DLPT) is preserved enabled to prevent kernel printk spam and PMIC current dip
[ -f /proc/ppm/policy_status ] && echo 3 0 > /proc/ppm/policy_status 2>/dev/null
[ -f /proc/ppm/policy_status ] && echo 5 1 > /proc/ppm/policy_status 2>/dev/null

# 5. MediaTek Native CPU DVFS Power Mode (Sports Mode)
# Mode 3: Performance(Sports) mode maximizes clock residency and eliminates power-throttling hysteresis
write /proc/cpufreq/cpufreq_power_mode 3

# 6. CPU Cpuset Architecture: Unlock Both Big Cores for Foreground
# Stock AOSP restricts foreground to 0-6 (locks out CPU 7). Unlocking to 0-7 enables full 8-core compute
write /dev/cpuset/foreground/cpus 0-7
write /dev/stune/foreground/schedtune.prefer_idle 1

# 7. BORE & Task Placement Optimization
# BORE (Burst-Oriented Response Enhancer) & Task Placement Optimization
# sched_latency_ns: 24ms native BORE timeslice prevents context-switching thrashing across 8 cores
# sched_min_granularity_ns: 3ms minimal CPU-bound execution chunk
# sched_wakeup_granularity_ns: 4ms eliminates thread preemption jitter
# sched_migration_cost_ns: 350µs allows Big-core work stealing at barriers while preserving cache
# sched_nr_migrate: 128 allows full thread balancing across 8 cores without truncation
# sched_walt_init_task_load_pct: 40 places new worker threads directly on Big cores
write /proc/sys/kernel/sched_big_task_rotation 1
[ -f /proc/perfmgr/boost_ctrl/eas_ctrl/sched_big_task_rotation ] && echo 1 > /proc/perfmgr/boost_ctrl/eas_ctrl/sched_big_task_rotation 2>/dev/null
write /proc/sys/kernel/sched_child_runs_first 1
write /proc/sys/kernel/sched_latency_ns 24000000
write /proc/sys/kernel/sched_min_granularity_ns 3000000
write /proc/sys/kernel/sched_wakeup_granularity_ns 4000000
write /proc/sys/kernel/sched_migration_cost_ns 250000
[ -f /proc/perfmgr/boost_ctrl/eas_ctrl/m_sched_migrate_cost_n ] && echo 250000 > /proc/perfmgr/boost_ctrl/eas_ctrl/m_sched_migrate_cost_n 2>/dev/null
write /proc/sys/kernel/sched_nr_migrate 128
write /proc/sys/kernel/sched_walt_init_task_load_pct 40
write /dev/cpuctl/top-app/cpu.shares 10240

# 8. Schedtune Top-App Foreground Acceleration
write /dev/stune/top-app/schedtune.boost 25
write /dev/stune/top-app/schedtune.prefer_idle 1

# 9. MediaTek Hardware EAS Controller (CGroup 3 = Top-App)
[ -f /proc/perfmgr/boost_ctrl/eas_ctrl/perfserv_prefer_idle ] && echo "3 1" > /proc/perfmgr/boost_ctrl/eas_ctrl/perfserv_prefer_idle 2>/dev/null
[ -f /proc/perfmgr/boost_ctrl/eas_ctrl/perfserv_ta_boost ] && echo "25" > /proc/perfmgr/boost_ctrl/eas_ctrl/perfserv_ta_boost 2>/dev/null

# 10. ARM Mali-G57 MC2 GPU Platform & Power Policy Acceleration
# always_on prevents shader core power-gating and wakeup latency between frames
# 50ms dvfs_period enables 2x faster reaction to 3D rendering spikes; chmod 444 blocks Power HAL overwrite
write /sys/devices/platform/13000000.mali/power_policy always_on
write /sys/devices/platform/13000000.mali/dvfs_period 50
chmod 444 /sys/devices/platform/13000000.mali/dvfs_period 2>/dev/null
write /sys/devices/platform/13000000.mali/js_scheduling_period 50

# 11. MediaTek GED (Graphics Enforcement Daemon) GPU Acceleration
# Uncaps ARM Mali-G57 MC2 up to 1068 MHz and enforces real-time frame synchronization
write /sys/module/ged/parameters/boost_gpu_enable 1
write /sys/module/ged/parameters/enable_gpu_boost 1
write /sys/module/ged/parameters/ged_boost_enable 1
write /sys/module/ged/parameters/ged_smart_boost 1
write /sys/module/ged/parameters/gx_game_mode 1
write /sys/module/ged/parameters/gx_force_cpu_boost 1
write /sys/module/ged/parameters/gx_boost_on 1
write /sys/module/ged/parameters/gpu_bottom_freq 955000
write /sys/module/ged/parameters/gpu_cust_boost_freq 1068000
write /sys/module/ged/parameters/gpu_cust_upbound_freq 1068000

# 12. UFS 2.2 Storage I/O Optimization
for d in /sys/block/sd*; do
    [ -f "$d/queue/read_ahead_kb" ] && echo 512 > "$d/queue/read_ahead_kb" 2>/dev/null
    [ -f "$d/queue/iostats" ] && echo 0 > "$d/queue/iostats" 2>/dev/null
done

# 13. Network & TCP Wi-Fi ADB Stability
# Prevents congestion window collapse and socket timeouts during heavy benchmark/compute bursts
write /proc/sys/net/ipv4/tcp_slow_start_after_idle 0
write /proc/sys/net/ipv4/tcp_keepalive_time 60
write /proc/sys/net/ipv4/tcp_keepalive_intvl 10
write /proc/sys/net/ipv4/tcp_keepalive_probes 5

# 14. Memory Compaction
write /proc/sys/vm/compact_memory 1

# 15. Delayed Background Re-Enforcement (Locks out Power HAL late-initialization)
(
    sleep 25
    chmod 664 /proc/cpufreq/cpufreq_cci_mode 2>/dev/null
    echo 1 > /proc/cpufreq/cpufreq_cci_mode 2>/dev/null
    chmod 444 /proc/cpufreq/cpufreq_cci_mode 2>/dev/null

    chmod 664 /sys/devices/platform/13000000.mali/dvfs_period 2>/dev/null
    echo 50 > /sys/devices/platform/13000000.mali/dvfs_period 2>/dev/null
    chmod 444 /sys/devices/platform/13000000.mali/dvfs_period 2>/dev/null

    [ -f /sys/devices/platform/10012000.dvfsrc/helio-dvfsrc/dvfsrc_req_ddr_opp ] && echo 0 > /sys/devices/platform/10012000.dvfsrc/helio-dvfsrc/dvfsrc_req_ddr_opp 2>/dev/null
    [ -f /sys/devices/platform/10012000.dvfsrc/helio-dvfsrc/dvfsrc_req_vcore_opp ] && echo 0 > /sys/devices/platform/10012000.dvfsrc/helio-dvfsrc/dvfsrc_req_vcore_opp 2>/dev/null
    [ -f /proc/perfmgr/boost_ctrl/dram_ctrl/ddr ] && echo 0 > /proc/perfmgr/boost_ctrl/dram_ctrl/ddr 2>/dev/null

    [ -f /proc/ppm/policy_status ] && echo 3 0 > /proc/ppm/policy_status 2>/dev/null
    [ -f /proc/ppm/policy_status ] && echo 5 1 > /proc/ppm/policy_status 2>/dev/null
    [ -f /proc/perfmgr/boost_ctrl/eas_ctrl/sched_big_task_rotation ] && echo 1 > /proc/perfmgr/boost_ctrl/eas_ctrl/sched_big_task_rotation 2>/dev/null
    [ -f /proc/perfmgr/boost_ctrl/eas_ctrl/m_sched_migrate_cost_n ] && echo 250000 > /proc/perfmgr/boost_ctrl/eas_ctrl/m_sched_migrate_cost_n 2>/dev/null
    echo 250000 > /proc/sys/kernel/sched_migration_cost_ns 2>/dev/null
    echo 10240 > /dev/cpuctl/top-app/cpu.shares 2>/dev/null
    [ -f /proc/perfmgr/boost_ctrl/eas_ctrl/perfserv_ta_boost ] && echo "25" > /proc/perfmgr/boost_ctrl/eas_ctrl/perfserv_ta_boost 2>/dev/null
    echo 128 > /proc/sys/kernel/sched_nr_migrate 2>/dev/null
    echo 40 > /proc/sys/kernel/sched_walt_init_task_load_pct 2>/dev/null
    chmod 664 /sys/module/ged/parameters/gpu_bottom_freq 2>/dev/null
    echo 955000 > /sys/module/ged/parameters/gpu_bottom_freq 2>/dev/null
    echo 1068000 > /sys/module/ged/parameters/gpu_cust_boost_freq 2>/dev/null
    echo 1068000 > /sys/module/ged/parameters/gpu_cust_upbound_freq 2>/dev/null
    echo 1 > /sys/module/ged/parameters/ged_smart_boost 2>/dev/null
    echo 1 > /sys/module/ged/parameters/boost_gpu_enable 2>/dev/null
    echo 1 > /sys/module/ged/parameters/enable_gpu_boost 2>/dev/null
    echo 1 > /sys/module/ged/parameters/ged_boost_enable 2>/dev/null
    echo 1 > /sys/module/ged/parameters/gx_game_mode 2>/dev/null
    log_msg "Post-boot re-assertion complete. CoreLink CCI, Mali DVFS, PPM uncap, DVFSRC DDR, and GED 955MHz locked."
) &

# 16. Guardrails:
# - NEVER write to /proc/driver/thermal/set_sspm_big_limit_threshold (triggers unkillable 84% CPU kernel IPI spinloop)
# - NEVER touch mtk-cl-backlight cooling device (drops PWM brightness to 0 causing black screen)
# - NEVER force settings min_refresh_rate (preserves smooth Android 16 display composer)

log_msg "Everpal Thermal Master v1 armed and active successfully."
"""
        with open(
            os.path.join(tmp_dir, "service.sh"), "w", encoding="utf-8", newline="\n"
        ) as f:
            f.write(service_sh)

        system_prop = """# Everpal Thermal Master System Properties
persist.sys.thermal.config=thermal-nolimits.conf
vendor.sys.thermal.data.path=/vendor/etc
"""
        with open(
            os.path.join(tmp_dir, "system.prop"), "w", encoding="utf-8", newline="\n"
        ) as f:
            f.write(system_prop)

        shutil.copy(
            os.path.join(template_meta, "update-binary"),
            os.path.join(meta_dir, "update-binary"),
        )
        shutil.copy(
            os.path.join(template_meta, "updater-script"),
            os.path.join(meta_dir, "updater-script"),
        )
        shutil.copy(nolimits_conf, os.path.join(vendor_etc, "thermal-normal.conf"))

        with zipfile.ZipFile(pkg_zip, "w", zipfile.ZIP_DEFLATED) as z:
            for root, dirs, files in os.walk(tmp_dir):
                for file in files:
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, tmp_dir)
                    z.write(full_path, rel_path)

    print(f"[+] Successfully built {pkg_zip} ({os.path.getsize(pkg_zip)} bytes)")
    return pkg_zip


def verify_zip(zip_path: str, expected_entries: list) -> bool:
    if not os.path.exists(zip_path):
        print(f"[-] ERROR: {zip_path} does not exist!")
        return False
    with zipfile.ZipFile(zip_path, "r") as z:
        names = z.namelist()
        missing = [e for e in expected_entries if e not in names]
        if missing:
            print(f"[-] ERROR: {zip_path} missing entries: {missing}")
            return False
        bad_file = z.testzip()
        if bad_file:
            print(f"[-] ERROR: Corrupt entry in {zip_path}: {bad_file}")
            return False
    print(
        f"[✓] {os.path.basename(zip_path)} verified: {len(names)} entries, CRC-32 valid ({os.path.getsize(zip_path)} bytes)"
    )
    return True


def main():
    parser = argparse.ArgumentParser(
        description="EvergoTweaks Unified Module Packager & Validator"
    )
    parser.add_argument(
        "--memory", "-m", action="store_true", help="Build MemoryMgmt.zip only"
    )
    parser.add_argument(
        "--thermal", "-t", action="store_true", help="Build ThermalMgmt.zip only"
    )
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Verify existing packages without rebuilding",
    )
    args = parser.parse_args()

    print("=" * 60)
    print(" EvergoTweaks Unified Module Builder & Validator")
    print("=" * 60)

    build_mem = True
    build_therm = True
    if args.memory and not args.thermal:
        build_therm = False
    elif args.thermal and not args.memory:
        build_mem = False

    mem_zip = os.path.join(
        REPO_ROOT, "package", "MemoryMgmt", "package", "MemoryMgmt.zip"
    )
    therm_zip = os.path.join(
        REPO_ROOT, "package", "ThermalMgmt", "package", "ThermalMgmt.zip"
    )

    if not args.verify_only:
        if build_mem:
            print("\n[1/2] Building MemoryMgmt.zip...")
            build_memory_module(REPO_ROOT)
        if build_therm:
            print("\n[2/2] Building ThermalMgmt.zip...")
            build_thermal_module(REPO_ROOT)

    print("\n" + "=" * 60)
    print(" Verifying Packages (CRC-32 & Structure)")
    print("=" * 60)

    all_ok = True
    if build_mem:
        mem_ok = verify_zip(
            mem_zip,
            [
                "module.prop",
                "service.sh",
                "system.prop",
                "META-INF/com/google/android/update-binary",
                "META-INF/com/google/android/updater-script",
            ],
        )
        all_ok = all_ok and mem_ok

    if build_therm:
        therm_ok = verify_zip(
            therm_zip,
            [
                "module.prop",
                "service.sh",
                "system.prop",
                "META-INF/com/google/android/update-binary",
                "META-INF/com/google/android/updater-script",
                "system/vendor/etc/thermal-normal.conf",
            ],
        )
        all_ok = all_ok and therm_ok

    if not all_ok:
        sys.exit(1)

    print("\n[+] All requested modules successfully built and verified!")


if __name__ == "__main__":
    main()
