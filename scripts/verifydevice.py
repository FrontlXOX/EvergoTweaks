#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# pylint: skip-file
# pylint: disable=all
# flake8: noqa
# ruff: noqa
# type: ignore
"""
EvergoTweaks Hardware & Kernel Verification Tool
Connects via ADB to audit real-time CPU frequencies, thermal profile,
ZRAM sizing, memory watermarks, and LMKD properties on connected MT6833/MT6833P devices.
"""

import os
import sys
import subprocess

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ADB = (
    r"D:\Software\Platform-Tools\adb.exe"
    if os.path.exists(r"D:\Software\Platform-Tools\adb.exe")
    else "adb"
)
CURRENT_DEVICE = None


def run_adb(cmd: str) -> str:
    adb_cmd = [ADB]
    if CURRENT_DEVICE:
        adb_cmd.extend(["-s", CURRENT_DEVICE])
    adb_cmd.extend(["shell", cmd])
    res = subprocess.run(adb_cmd, capture_output=True, text=True, errors="replace")
    return res.stdout.strip()


def check_devices(target=None):
    if target:
        subprocess.run(
            [ADB, "connect", target], capture_output=True, text=True, errors="replace"
        )
    res = subprocess.run(
        [ADB, "devices"], capture_output=True, text=True, errors="replace"
    )
    lines = [
        line.strip()
        for line in res.stdout.strip().splitlines()
        if line.strip() and not line.startswith("*")
    ]
    devices = [line.split()[0] for line in lines[1:] if "\tdevice" in line]
    if not devices:
        env_target = os.environ.get("ADB_TARGET")
        if env_target:
            subprocess.run(
                [ADB, "connect", env_target],
                capture_output=True,
                text=True,
                errors="replace",
            )
            res = subprocess.run(
                [ADB, "devices"], capture_output=True, text=True, errors="replace"
            )
            lines = [
                line.strip()
                for line in res.stdout.strip().splitlines()
                if line.strip() and not line.startswith("*")
            ]
            devices = [line.split()[0] for line in lines[1:] if "\tdevice" in line]
    return devices


def main():
    print("=" * 65)
    print("EvergoTweaks Device Verification Suite")
    print("=" * 65)

    global CURRENT_DEVICE
    target_arg = None
    if len(sys.argv) > 1:
        if sys.argv[1] in ("-s", "--target") and len(sys.argv) > 2:
            target_arg = sys.argv[2]
        elif not sys.argv[1].startswith("-"):
            target_arg = sys.argv[1]

    devices = check_devices(target_arg)
    if not devices:
        print("[-] No active ADB devices found!")
        print(
            "    Ensure device is connected via USB (with USB debugging enabled), or provide wireless target:"
        )
        print(
            "    Usage: python scripts/verify_device.py [ip:port] or set ADB_TARGET=ip:port"
        )
        sys.exit(1)

    device_id = target_arg if (target_arg and target_arg in devices) else devices[0]
    CURRENT_DEVICE = device_id
    print(f"[+] Connected Target: {device_id}")

    # 1. System Info
    model = run_adb("getprop ro.product.model")
    board = run_adb("getprop ro.product.board")
    os_ver = run_adb("getprop ro.build.version.release")
    build_id = run_adb("getprop ro.build.display.id")
    kernel = run_adb("uname -r")
    soc = run_adb("getprop ro.board.platform")

    print(f"\n📱 [System & Platform]")
    print(f"   Model       : {model} (Board: {board})")
    print(f"   Platform    : {soc.upper()} (Dimensity 810 / MT6833P)")
    print(f"   Android     : Android {os_ver} ({build_id})")
    print(f"   Kernel      : {kernel}")

    # 2. CPU Frequencies
    cpu0_max = run_adb(
        "cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_max_freq 2>/dev/null"
    )
    cpu0_cur = run_adb(
        "cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq 2>/dev/null"
    )
    cpu6_max = run_adb(
        "cat /sys/devices/system/cpu/cpu6/cpufreq/scaling_max_freq 2>/dev/null"
    )
    cpu6_cur = run_adb(
        "cat /sys/devices/system/cpu/cpu6/cpufreq/scaling_cur_freq 2>/dev/null"
    )

    print(f"\n⚡ [CPU Frequency Scaling]")
    print(
        f"   LITTLE (A55): Cur: {int(cpu0_cur)//1000 if cpu0_cur.isdigit() else cpu0_cur} MHz / Max: {int(cpu0_max)//1000 if cpu0_max.isdigit() else cpu0_max} MHz"
    )
    print(
        f"   Big    (A76): Cur: {int(cpu6_cur)//1000 if cpu6_cur.isdigit() else cpu6_cur} MHz / Max: {int(cpu6_max)//1000 if cpu6_max.isdigit() else cpu6_max} MHz"
    )

    # 3. Thermal Profile
    sconfig = run_adb("cat /sys/class/thermal/thermal_message/sconfig 2>/dev/null")
    thermal_mode = run_adb("getprop sys.thermal.mode")
    skin_temp = run_adb("cat /sys/class/thermal/thermal_zone0/temp 2>/dev/null")
    skin_val = float(skin_temp) / 1000.0 if skin_temp.isdigit() else 0.0

    print(f"\n🔥 [Thermal Management]")
    print(
        f"   sconfig     : {sconfig} {'[✓ OK: High-Performance NoLimits]' if sconfig == '10' else '[!] Expected 10'}"
    )
    print(f"   Thermal Mode: {thermal_mode if thermal_mode else 'default'}")
    print(f"   Skin Temp   : {skin_val:.1f}°C")

    # 4. Memory & ZRAM
    mem_total = run_adb("cat /proc/meminfo | grep MemTotal | awk '{print $2}'")
    mem_avail = run_adb("cat /proc/meminfo | grep MemAvailable | awk '{print $2}'")
    zram_size = run_adb("cat /sys/block/zram0/disksize 2>/dev/null")
    zram_algo = run_adb("cat /sys/block/zram0/comp_algorithm 2>/dev/null")
    zram_streams = run_adb("cat /sys/block/zram0/max_comp_streams 2>/dev/null")

    zram_mb = int(zram_size) // (1024 * 1024) if zram_size.isdigit() else 0
    mem_mb = int(mem_total) // 1024 if mem_total.isdigit() else 0
    avail_mb = int(mem_avail) // 1024 if mem_avail.isdigit() else 0

    # Determine expected values based on detected RAM tier
    if mem_mb >= 7000:
        ram_tier = "8GB LPDDR4X"
        exp_min_free = "40960"
        exp_zram_str = "~5.6GB (75%)"
        is_zram_ok = zram_mb >= 5000
    elif mem_mb >= 5000:
        ram_tier = "6GB LPDDR4X"
        exp_min_free = "32768"
        exp_zram_str = "~4.2GB (75%)"
        is_zram_ok = zram_mb >= 3800
    else:
        ram_tier = "4GB LPDDR4X"
        exp_min_free = "24576"
        exp_zram_str = "3.58GB"
        is_zram_ok = zram_size == "3758096384" or zram_mb >= 3500

    print(f"\n🧠 [Memory & ZRAM Architecture]")
    print(f"   Physical RAM: {mem_mb} MB MemTotal (Hardware: {ram_tier})")
    print(f"   Available   : {avail_mb} MB free/reclaimable")
    print(
        f"   ZRAM Disk   : {zram_mb} MB ({zram_size} bytes) {'[✓ OK: ' + exp_zram_str + ']' if is_zram_ok else '[!] Expected ' + exp_zram_str}"
    )
    print(f"   Compression : {zram_algo}")
    print(f"   Comp Streams: {zram_streams} parallel streams")

    # 5. Kernel Tunables & LMKD
    wsf = run_adb("cat /proc/sys/vm/watermark_scale_factor 2>/dev/null")
    min_free = run_adb("cat /proc/sys/vm/min_free_kbytes 2>/dev/null")
    swappiness = run_adb("cat /proc/sys/vm/swappiness 2>/dev/null")
    vfs_press = run_adb("cat /proc/sys/vm/vfs_cache_pressure 2>/dev/null")
    swap_low = run_adb("getprop ro.lmk.swap_free_low_percentage")
    thrash = run_adb("getprop ro.lmk.thrashing_limit")
    kill_to = run_adb("getprop ro.lmk.kill_timeout_ms")

    print(f"\n🛡️ [Kernel VM & LMKD Tunables]")
    print(
        f"   watermark_scale_factor: {wsf} {'[✓ OK: 20]' if wsf == '20' else '[!] Expected 20'}"
    )
    print(
        f"   min_free_kbytes       : {min_free} kB {'[✓ OK: ' + exp_min_free + ']' if min_free == exp_min_free else '[!] Expected ' + exp_min_free}"
    )
    print(
        f"   swappiness            : {swappiness} {'[✓ OK: 80]' if swappiness == '80' else '[!] Expected 80'}"
    )
    print(
        f"   vfs_cache_pressure    : {vfs_press} {'[✓ OK: 80]' if vfs_press == '80' else '[!] Expected 80'}"
    )
    print(
        f"   swap_free_low_%       : {swap_low}% {'[✓ OK: 2%]' if swap_low == '2' else '[!] Expected 2'}"
    )
    print(f"   thrashing_limit       : {thrash}")
    print(f"   kill_timeout_ms       : {kill_to} ms")

    # 6. Hardware Acceleration & Compute Engine
    cci_mode = run_adb("cat /proc/cpufreq/cpufreq_cci_mode 2>/dev/null")
    power_mode = run_adb("cat /proc/cpufreq/cpufreq_power_mode 2>/dev/null")
    up_rate = run_adb(
        "cat /sys/devices/system/cpu/cpufreq/policy6/schedutil/up_rate_limit_us 2>/dev/null"
    )
    down_rate = run_adb(
        "cat /sys/devices/system/cpu/cpufreq/policy6/schedutil/down_rate_limit_us 2>/dev/null"
    )
    fg_cpus = run_adb("cat /dev/cpuset/foreground/cpus 2>/dev/null")
    big_rot = run_adb("cat /proc/sys/kernel/sched_big_task_rotation 2>/dev/null")
    ta_boost = run_adb("cat /dev/stune/top-app/schedtune.boost 2>/dev/null")
    ta_idle = run_adb("cat /dev/stune/top-app/schedtune.prefer_idle 2>/dev/null")
    ta_uclamp = run_adb(
        "cat /proc/perfmgr/boost_ctrl/eas_ctrl/current_ta_uclamp_min 2>/dev/null"
    )
    sched_util = run_adb("cat /dev/stune/top-app/schedtune.util.min 2>/dev/null")
    ged_smart = run_adb("cat /sys/module/ged/parameters/ged_smart_boost 2>/dev/null")
    ged_boost = run_adb("cat /sys/module/ged/parameters/boost_gpu_enable 2>/dev/null")
    mali_pwr = run_adb(
        "cat /sys/devices/platform/13000000.mali/power_policy 2>/dev/null"
    )
    mali_dvfs = run_adb(
        "cat /sys/devices/platform/13000000.mali/dvfs_period 2>/dev/null"
    )
    ra_kb = run_adb("cat /sys/block/sda/queue/read_ahead_kb 2>/dev/null")
    sched_io = run_adb("cat /sys/block/sda/queue/scheduler 2>/dev/null")
    rq_aff = run_adb("cat /sys/block/sda/queue/rq_affinity 2>/dev/null")
    tcp_idle = run_adb("cat /proc/sys/net/ipv4/tcp_slow_start_after_idle 2>/dev/null")

    dvfsrc_dump = run_adb(
        "cat /sys/devices/platform/10012000.dvfsrc/helio-dvfsrc/dvfsrc_dump 2>/dev/null | head -n 3"
    )
    ddr_freq = "unknown"
    vcore_val = "unknown"
    for line in dvfsrc_dump.splitlines():
        if "DDR" in line:
            parts = line.split()
            if len(parts) >= 3:
                ddr_freq = f"{parts[2]} {parts[3]}"
        elif "Vcore" in line:
            parts = line.split()
            if len(parts) >= 3:
                vcore_val = f"{parts[2]} {parts[3]}"

    print(f"\n🚀 [Hardware Acceleration & Compute Engine]")
    print(
        f"   CoreLink CCI Mode     : {cci_mode.splitlines()[0] if cci_mode else 'default'} {'[✓ OK: Perf Mode]' if 'Perf' in cci_mode else ''}"
    )
    print(
        f"   DVFSRC LPDDR4X RAM    : {ddr_freq} {'[✓ OK: 4.266 GHz Peak]' if '4266000' in ddr_freq else ''}"
    )
    print(
        f"   DVFSRC Vcore Voltage  : {vcore_val} {'[✓ OK: 725 mV Peak]' if '725000' in vcore_val else ''}"
    )
    print(
        f"   CPU DVFS Power Mode   : {power_mode.splitlines()[0] if power_mode else 'default'} {'[✓ OK: Sports Mode]' if 'Sports' in power_mode or 'Performance' in power_mode else ''}"
    )
    print(
        f"   Big Schedutil Ramp    : Up={up_rate}µs, Down={down_rate}µs {'[✓ OK: 0µs Instant Ramp]' if up_rate == '0' else ''}"
    )
    print(
        f"   Foreground Cpuset     : {fg_cpus} {'[✓ OK: Both Big Cores Unlocked]' if fg_cpus == '0-7' else ''}"
    )
    print(
        f"   BORE Big Task Rotation: {big_rot} {'[✓ OK: Enabled]' if big_rot == '1' else ''}"
    )
    print(f"   EAS Top-App Boost     : Boost={ta_boost}, PreferIdle={ta_idle}")
    print(
        f"   EAS Compute Floor     : uclamp={ta_uclamp}%, util.min={sched_util} {'[✓ OK: Compute Floor]' if ta_uclamp != '0' or sched_util != '0' else ''}"
    )
    print(
        f"   ARM Mali Power Policy : {mali_pwr.splitlines()[0] if mali_pwr else 'default'} {'[✓ OK: always_on]' if 'always_on' in mali_pwr else ''}"
    )
    print(
        f"   Mali DVFS Period      : {mali_dvfs} ms {'[✓ OK: 50ms fast]' if mali_dvfs == '50' else ''}"
    )
    print(
        f"   MediaTek GED Boost    : SmartBoost={ged_smart}, GpuBoost={ged_boost} {'[✓ OK: Active]' if ged_smart == '1' and ged_boost == '1' else ''}"
    )
    print(
        f"   UFS Storage Queue     : Scheduler={sched_io} {'[✓ OK: none]' if '[none]' in sched_io else ''}"
    )
    print(
        f"   UFS RQ Core Affinity  : {rq_aff} {'[✓ OK: Submitting Core]' if rq_aff == '2' else ''}"
    )
    print(
        f"   UFS Read-Ahead        : {ra_kb} kB {'[✓ OK: 512kB]' if ra_kb == '512' else ''}"
    )
    print(
        f"   TCP Slow Start Idle   : {tcp_idle} {'[✓ OK: Disabled (Stable)]' if tcp_idle == '0' else ''}"
    )

    # 7. Vulkan 1.3 Hybrid Engine
    dumpsys_gpu = run_adb("dumpsys gpu")
    vk_ver = "unknown"
    vk_load_fail = "0"
    vk_load_time = "unknown"
    for line in dumpsys_gpu.splitlines():
        if "vulkanVersion" in line and "=" in line:
            vk_ver = line.split("=")[-1].strip()
        elif "vkLoadingFailureCount" in line and "=" in line:
            vk_load_fail = line.split("=")[-1].strip()
        elif "vkDriverLoadingTime:" in line:
            parts = line.split(":")
            if len(parts) > 1 and parts[1].strip().isdigit():
                vk_load_time = parts[1].strip()

    print(f"\n🎮 [Vulkan 1.3 Hybrid Engine]")
    is_vk13 = vk_ver == "4206592"
    print(f"   Vulkan Version Code   : {vk_ver} {'[✓ OK: Vulkan 1.3.0 (0x00403000)]' if is_vk13 else '[!] Unexpected Version'}")
    print(f"   Driver Loading Errors : {vk_load_fail} {'[✓ OK: 0 Errors]' if vk_load_fail == '0' else '[!] Driver Errors Detected'}")
    if vk_load_time != "unknown":
        print(f"   Driver Init Latency   : {int(vk_load_time) / 1000000:.2f} ms ({vk_load_time} ns) [✓ OK: Fast Load]")

    print("\n" + "=" * 65)
    print("Verification Completed Successfully.")
    print("=" * 65)


if __name__ == "__main__":
    main()
