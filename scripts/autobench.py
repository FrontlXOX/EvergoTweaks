#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# pylint: skip-file
# pylint: disable=all
# flake8: noqa
# ruff: noqa
# type: ignore
"""
EvergoTweaks AutoBench — Unified Geekbench 7 Automated Benchmark Orchestrator
Target: Xiaomi POCO M4 Pro 5G / Redmi Note 11S 5G (everpal / evergo)
Platform: MediaTek Dimensity 810 (MT6833P / MT6833)
Capabilities:
  - System prep, background process purge & hardware performance locks assertion
  - Geekbench 7 CPU benchmark orchestration (Single-Core & Multi-Core)
  - Geekbench 7 GPU Compute benchmark orchestration (Vulkan default / OpenCL)
  - Real-time CLI live telemetry streaming (Workload name, CPU Big/Little clocks, GPU clock, battery thermals)
  - Automated SQLite extraction, JSON parsing, and history database sync
"""

import os
import sys
import time
import json
import sqlite3
import argparse
import datetime
import subprocess
import xml.etree.ElementTree as ET

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ADB = (
    r"D:\Software\Platform-Tools\adb.exe"
    if os.path.exists(r"D:\Software\Platform-Tools\adb.exe")
    else "adb"
)
CURRENT_DEVICE = None
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS_DIR = os.path.join(REPO_ROOT, "package", "ThermalMgmt", "docs")


def run_adb(cmd_list, timeout=30):
    adb_cmd = [ADB]
    if CURRENT_DEVICE:
        adb_cmd.extend(["-s", CURRENT_DEVICE])
    adb_cmd.extend(cmd_list)
    try:
        res = subprocess.run(
            adb_cmd, capture_output=True, text=True, errors="replace", timeout=timeout
        )
        return res.stdout.strip()
    except Exception:
        return ""


def run_adb_shell(cmd: str, timeout=30) -> str:
    return run_adb(["shell", cmd], timeout=timeout)


def run_adb_root(cmd: str, timeout=30) -> str:
    return run_adb(["shell", "su", "-c", cmd], timeout=timeout)


def ensure_device(target=None):
    global CURRENT_DEVICE
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
    devices = [
        line.split()[0]
        for line in lines[1:]
        if len(line.split()) >= 2 and line.split()[1] == "device"
    ]
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
            devices = [
                line.split()[0]
                for line in lines[1:]
                if len(line.split()) >= 2 and line.split()[1] == "device"
            ]
    if devices:
        CURRENT_DEVICE = target if (target and target in devices) else devices[0]
    return CURRENT_DEVICE


def get_hardware_telemetry():
    raw = run_adb_shell(
        "echo $(cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq 2>/dev/null) "
        "$(cat /sys/devices/system/cpu/cpu6/cpufreq/scaling_cur_freq 2>/dev/null) "
        "$(cat /sys/kernel/ged/hal/current_freqency 2>/dev/null) "
        "$(cat /sys/class/power_supply/battery/temp 2>/dev/null) "
        "$(cat /sys/class/power_supply/battery/capacity 2>/dev/null)"
    )
    parts = raw.split()
    little_ghz = 0.0
    big_ghz = 0.0
    gpu_mhz = 0
    temp_c = 0.0
    cap_pct = 0
    try:
        if len(parts) >= 6:
            little_ghz = float(parts[0]) / 1_000_000.0 if parts[0].isdigit() else 0.0
            big_ghz = float(parts[1]) / 1_000_000.0 if parts[1].isdigit() else 0.0
            gpu_mhz = int(parts[3]) // 1000 if parts[3].isdigit() else 0
            temp_c = float(parts[4]) / 10.0 if parts[4].isdigit() else 0.0
            cap_pct = int(parts[5]) if parts[5].isdigit() else 0
        elif len(parts) >= 4:
            little_ghz = float(parts[0]) / 1_000_000.0 if parts[0].isdigit() else 0.0
            big_ghz = float(parts[1]) / 1_000_000.0 if parts[1].isdigit() else 0.0
            temp_c = float(parts[-2]) / 10.0 if parts[-2].isdigit() else 0.0
            cap_pct = int(parts[-1]) if parts[-1].isdigit() else 0
    except Exception:
        pass
    return {
        "little_ghz": little_ghz,
        "big_ghz": big_ghz,
        "gpu_mhz": gpu_mhz,
        "temp_c": temp_c,
        "cap_pct": cap_pct,
    }


def get_active_workload_name():
    xml_data = run_adb_shell(
        "uiautomator dump /sdcard/gb_wl.xml >/dev/null 2>&1 && cat /sdcard/gb_wl.xml 2>/dev/null"
    )
    if not xml_data or "<hierarchy" not in xml_data:
        return None
    try:
        root = ET.fromstring(xml_data)
        for node in root.iter("node"):
            if "progressStatus" in node.attrib.get("resource-id", ""):
                txt = node.attrib.get("text", "").strip()
                if txt:
                    return txt
    except Exception:
        pass
    return None


def prepare_system():
    print("[*] Preparing system environment...")
    run_adb_shell("svc power stayon true")
    run_adb_shell("input keyevent KEYCODE_WAKEUP")
    run_adb_shell("wm dismiss-keyguard")
    run_adb_shell("settings put system accelerometer_rotation 0")
    run_adb_shell("settings put system user_rotation 0")
    run_adb_shell("input keyevent KEYCODE_HOME")
    time.sleep(1)

    third_party = run_adb_shell("pm list packages -3").splitlines()
    whitelist = [
        "com.primatelabs.parkdale",
        "ginlemon.flowerfree",
        "me.bmax.apatch",
        "io.github.a13e300.ksu",
        "com.topjohnwu.magisk",
    ]
    killed = 0
    for line in third_party:
        pkg = line.replace("package:", "").strip()
        if pkg and pkg not in whitelist:
            run_adb_shell(f"am force-stop {pkg}")
            killed += 1
    run_adb_shell("am kill-all")
    print(f"    Cleaned up {killed} background user packages.")

    perf_cmds = [
        "echo 10 > /sys/class/thermal/thermal_message/sconfig",
        "chmod 664 /proc/cpufreq/cpufreq_cci_mode 2>/dev/null",
        "echo 1 > /proc/cpufreq/cpufreq_cci_mode 2>/dev/null",
        "chmod 444 /proc/cpufreq/cpufreq_cci_mode 2>/dev/null",
        "echo 0 > /sys/devices/platform/10012000.dvfsrc/helio-dvfsrc/dvfsrc_req_ddr_opp 2>/dev/null",
        "echo 0 > /sys/devices/platform/10012000.dvfsrc/helio-dvfsrc/dvfsrc_req_vcore_opp 2>/dev/null",
        "echo 0 > /proc/perfmgr/boost_ctrl/dram_ctrl/ddr 2>/dev/null",
        "echo 3 0 > /proc/ppm/policy_status 2>/dev/null",
        "echo 5 1 > /proc/ppm/policy_status 2>/dev/null",
        "echo 3 > /proc/cpufreq/cpufreq_power_mode 2>/dev/null",
        "echo 0-7 > /dev/cpuset/foreground/cpus 2>/dev/null",
        "echo 0-7 > /dev/cpuset/top-app/cpus 2>/dev/null",
        "echo 24000000 > /proc/sys/kernel/sched_latency_ns 2>/dev/null",
        "echo 3000000 > /proc/sys/kernel/sched_min_granularity_ns 2>/dev/null",
        "echo 4000000 > /proc/sys/kernel/sched_wakeup_granularity_ns 2>/dev/null",
        "echo 10240 > /dev/cpuctl/top-app/cpu.shares 2>/dev/null",
        "echo 250000 > /proc/sys/kernel/sched_migration_cost_ns 2>/dev/null",
        "echo 250000 > /proc/perfmgr/boost_ctrl/eas_ctrl/m_sched_migrate_cost_n 2>/dev/null",
        "echo 128 > /proc/sys/kernel/sched_nr_migrate 2>/dev/null",
        "echo 40 > /proc/sys/kernel/sched_walt_init_task_load_pct 2>/dev/null",
        "echo 1 > /proc/sys/kernel/sched_big_task_rotation 2>/dev/null",
        "echo 1 > /proc/perfmgr/boost_ctrl/eas_ctrl/sched_big_task_rotation 2>/dev/null",
        "echo 1 > /proc/sys/kernel/sched_child_runs_first 2>/dev/null",
        "echo 25 > /dev/stune/top-app/schedtune.boost 2>/dev/null",
        "echo 1 > /dev/stune/top-app/schedtune.prefer_idle 2>/dev/null",
        "echo 25 > /proc/perfmgr/boost_ctrl/eas_ctrl/perfserv_ta_boost 2>/dev/null",
        "echo '3 1' > /proc/perfmgr/boost_ctrl/eas_ctrl/perfserv_prefer_idle 2>/dev/null",
        "echo always_on > /sys/devices/platform/13000000.mali/power_policy 2>/dev/null",
        "chmod 664 /sys/devices/platform/13000000.mali/dvfs_period 2>/dev/null",
        "echo 50 > /sys/devices/platform/13000000.mali/dvfs_period 2>/dev/null",
        "chmod 444 /sys/devices/platform/13000000.mali/dvfs_period 2>/dev/null",
        "echo 1 > /sys/module/ged/parameters/boost_gpu_enable 2>/dev/null",
        "echo 1 > /sys/module/ged/parameters/enable_gpu_boost 2>/dev/null",
        "echo 1 > /sys/module/ged/parameters/ged_boost_enable 2>/dev/null",
        "echo 1 > /sys/module/ged/parameters/ged_smart_boost 2>/dev/null",
        "echo 1 > /sys/module/ged/parameters/gx_game_mode 2>/dev/null",
        "echo 1 > /sys/module/ged/parameters/gx_force_cpu_boost 2>/dev/null",
        "echo 1 > /sys/module/ged/parameters/gx_boost_on 2>/dev/null",
        "chmod 664 /sys/module/ged/parameters/gpu_bottom_freq 2>/dev/null",
        "echo 955000 > /sys/module/ged/parameters/gpu_bottom_freq 2>/dev/null",
        "echo 1068000 > /sys/module/ged/parameters/gpu_cust_boost_freq 2>/dev/null",
        "echo 1068000 > /sys/module/ged/parameters/gpu_cust_upbound_freq 2>/dev/null",
    ]
    for c in perf_cmds:
        run_adb_root(c)
    print(
        "    Hardware compute locks asserted (sconfig 10, CCI 1.6GHz, DDR 4.266GHz, Mali DVFS 50ms, GED 1.068GHz)."
    )


def wait_for_cooldown(target_temp_c=38.0, max_wait_sec=180):
    telem = get_hardware_telemetry()
    temp_c = telem["temp_c"]
    cap = telem["cap_pct"]
    if temp_c <= target_temp_c or temp_c == 0.0:
        print(
            f"[+] Device thermal state optimal: {temp_c:.1f}°C (Target <= {target_temp_c:.1f}°C, Battery: {cap}%)"
        )
        return True

    print(
        f"[*] Thermal cooldown active: Current={temp_c:.1f}°C, Cooling target <= {target_temp_c:.1f}°C..."
    )
    start_t = time.time()
    while time.time() - start_t < max_wait_sec:
        time.sleep(3)
        telem = get_hardware_telemetry()
        temp_c = telem["temp_c"]
        elapsed = int(time.time() - start_t)
        sys.stdout.write(
            f"\r    Waiting for thermal settle: {temp_c:.1f}°C / {target_temp_c:.1f}°C [{elapsed}s]   "
        )
        sys.stdout.flush()
        if temp_c <= target_temp_c:
            print(f"\n[+] Thermal cooldown achieved: {temp_c:.1f}°C")
            return True
    print(f"\n[!] Cooldown timeout reached ({temp_c:.1f}°C). Proceeding with test.")
    return False


def get_latest_geekbench_cpu_doc():
    run_adb_root(
        "cp /data/data/com.primatelabs.parkdale/files/history.db /sdcard/history.db 2>/dev/null && chmod 666 /sdcard/history.db"
    )
    local_db = os.path.join(DOCS_DIR, "history.db")
    run_adb(["pull", "/sdcard/history.db", local_db])
    if not os.path.exists(local_db):
        return None, 0

    try:
        con = sqlite3.connect(local_db)
        cur = con.cursor()
        row = cur.execute("""
            SELECT c.document_id, c.score, c.multicore_score, d.json
            FROM cpu_documents c
            JOIN documents d ON c.document_id = d.id
            ORDER BY c.rowid DESC LIMIT 1
        """).fetchone()
        con.close()
        if not row:
            return None, 0
        doc_id, sc, mc, raw_json = row
        data = json.loads(raw_json)
        return {
            "id": doc_id,
            "single_core": sc,
            "multi_core": mc,
            "url": data.get("browser", {}).get("url", ""),
            "frequencies": data.get("processor_frequency", {}).get("frequencies", []),
            "data": data,
        }, doc_id
    except Exception:
        return None, 0


def get_latest_geekbench_gpu_doc():
    run_adb_root(
        "cp /data/data/com.primatelabs.parkdale/files/history.db /sdcard/history.db 2>/dev/null && chmod 666 /sdcard/history.db"
    )
    local_db = os.path.join(DOCS_DIR, "history.db")
    run_adb(["pull", "/sdcard/history.db", local_db])
    if not os.path.exists(local_db):
        return None, 0

    try:
        con = sqlite3.connect(local_db)
        cur = con.cursor()
        row = cur.execute("""
            SELECT g.document_id, g.score, g.api, d.json
            FROM gpu_documents g
            JOIN documents d ON g.document_id = d.id
            ORDER BY g.rowid DESC LIMIT 1
        """).fetchone()
        con.close()
        if not row:
            return None, 0
        doc_id, score, api_type, raw_json = row
        data = json.loads(raw_json)
        return {
            "id": doc_id,
            "score": score,
            "api": api_type,
            "url": data.get("browser", {}).get("url", ""),
            "data": data,
        }, doc_id
    except Exception:
        return None, 0


def run_geekbench_cpu_test():
    print("\n" + "=" * 65)
    print(" 🚀 Executing Geekbench 7 CPU Benchmark")
    print("=" * 65)

    initial_doc, initial_id = get_latest_geekbench_cpu_doc()
    print(f"[*] Baseline Geekbench CPU Document ID: {initial_id}")

    run_adb_shell("am force-stop com.primatelabs.parkdale")
    time.sleep(1)
    run_adb_shell(
        "am start -n com.primatelabs.parkdale/com.primatelabs.geekbench.HomeActivity"
    )
    time.sleep(3)

    run_adb_shell("input tap 99 341")
    time.sleep(1)

    print("[*] Triggering 'Run CPU Benchmark' [779, 1455]...")
    run_adb_shell("input tap 779 1455")
    start_time = time.time()

    print("[*] Monitoring live Geekbench 7 CPU execution...")
    last_workload = "Initializing CPU Test"
    last_wl_check = 0

    while True:
        time.sleep(1.5)
        elapsed = int(time.time() - start_time)
        telem = get_hardware_telemetry()

        # Check workload name periodically
        if time.time() - last_wl_check >= 6.0:
            last_wl_check = time.time()
            active_wl = get_active_workload_name()
            if active_wl and active_wl != last_workload:
                last_workload = active_wl
                print(f"\n    [+] Phase -> {last_workload} ({elapsed}s)")

        sys.stdout.write(
            f"\r    [GB7-CPU] {elapsed:>3}s | {last_workload:<24} | CPU: {telem['big_ghz']:.2f}G / {telem['little_ghz']:.2f}G | GPU: {telem['gpu_mhz']:>4}M | {telem['temp_c']:.1f}°C ({telem['cap_pct']}%)   "
        )
        sys.stdout.flush()

        # Check database for completion every 3 iterations
        if elapsed % 4 == 0:
            latest_doc, latest_id = get_latest_geekbench_cpu_doc()
            if latest_id > initial_id:
                print(f"\n[✓] Geekbench 7 CPU completed successfully in {elapsed}s!")
                return latest_doc

        if elapsed > 480:
            print("\n[!] Timeout: Geekbench 7 CPU exceeded 8 minutes.")
            return None


def run_geekbench_gpu_test(api="vulkan"):
    print("\n" + "=" * 65)
    print(f" 🎮 Executing Geekbench 7 GPU Compute Benchmark ({api.upper()})")
    print("=" * 65)

    initial_doc, initial_id = get_latest_geekbench_gpu_doc()
    print(f"[*] Baseline Geekbench GPU Document ID: {initial_id}")

    run_adb_shell("am force-stop com.primatelabs.parkdale")
    time.sleep(1)
    run_adb_shell(
        "am start -n com.primatelabs.parkdale/com.primatelabs.geekbench.HomeActivity"
    )
    time.sleep(3)

    print("[*] Navigating to GPU compute tab...")
    run_adb_shell("input tap 297 341")
    time.sleep(2)

    if api.lower() == "vulkan":
        print("[*] Selecting Vulkan compute backend...")
        run_adb_shell("input tap 800 1600")
        time.sleep(1)
        run_adb_shell("input tap 794 1696")
        time.sleep(1)
    elif api.lower() == "opencl":
        print("[*] Selecting OpenCL compute backend...")
        run_adb_shell("input tap 800 1600")
        time.sleep(1)
        run_adb_shell("input tap 794 1600")
        time.sleep(1)

    print("[*] Triggering 'Run GPU Benchmark' [779, 1761]...")
    run_adb_shell("input tap 779 1761")
    start_time = time.time()

    print(f"[*] Monitoring live Geekbench 7 GPU ({api.upper()}) execution...")
    last_workload = f"Initializing GPU ({api.upper()})"
    last_wl_check = 0

    while True:
        time.sleep(1.5)
        elapsed = int(time.time() - start_time)
        telem = get_hardware_telemetry()

        # Check workload name periodically
        if time.time() - last_wl_check >= 6.0:
            last_wl_check = time.time()
            active_wl = get_active_workload_name()
            if active_wl and active_wl != last_workload:
                last_workload = active_wl
                print(f"\n    [+] Phase -> {last_workload} ({elapsed}s)")

        sys.stdout.write(
            f"\r    [GB7-GPU] {elapsed:>3}s | {last_workload:<24} | CPU: {telem['big_ghz']:.2f}G / {telem['little_ghz']:.2f}G | GPU: {telem['gpu_mhz']:>4}M | {telem['temp_c']:.1f}°C ({telem['cap_pct']}%)   "
        )
        sys.stdout.flush()

        # Check database for completion every 3 iterations
        if elapsed % 4 == 0:
            latest_doc, latest_id = get_latest_geekbench_gpu_doc()
            if latest_id > initial_id:
                print(
                    f"\n[✓] Geekbench 7 GPU ({api.upper()}) completed successfully in {elapsed}s!"
                )
                return latest_doc

        if elapsed > 480:
            print(f"\n[!] Timeout: Geekbench 7 GPU exceeded 8 minutes.")
            return None


def get_latest_3dmark_doc():
    run_adb_root(
        "cp /data/data/com.futuremark.dmandroid.application/databases/fm_local_results.db* /sdcard/ 2>/dev/null && chmod 666 /sdcard/fm_local_results.db*"
    )
    local_db = os.path.join(DOCS_DIR, "fm_local_results.db")
    run_adb(["pull", "/sdcard/fm_local_results.db", local_db])
    if not os.path.exists(local_db):
        return None, 0

    try:
        con = sqlite3.connect(local_db)
        cur = con.cursor()
        row = cur.execute("""
            SELECT id, scores, result_path, date
            FROM results
            ORDER BY id DESC LIMIT 1
        """).fetchone()
        con.close()
        if not row:
            return None, 0
        res_id, raw_scores, result_path, date_val = row
        scores_data = json.loads(raw_scores)
        overall = scores_data.get("overallScore", 0)
        sub_map = {
            item["resultType"]: item["score"]
            for item in scores_data.get("subScores", [])
        }
        return {
            "id": res_id,
            "overall": overall,
            "graphics": sub_map.get(
                "SLING_SHOT_GRAPHICS_SCORE_N",
                sub_map.get("SLING_SHOT_GRAPHICS_SCORE_B", 0),
            ),
            "physics": sub_map.get(
                "SLING_SHOT_PHYSICS_SCORE_N",
                sub_map.get("SLING_SHOT_PHYSICS_SCORE_B", 0),
            ),
            "gt1": sub_map.get(
                "SLING_SHOT_GT1_N", sub_map.get("SLING_SHOT_GT1_B", 0.0)
            ),
            "gt2": sub_map.get(
                "SLING_SHOT_GT2_N", sub_map.get("SLING_SHOT_GT2_B", 0.0)
            ),
            "demo": sub_map.get(
                "SLING_SHOT_DEMO_N", sub_map.get("SLING_SHOT_DEMO_B", 0.0)
            ),
            "p1": sub_map.get(
                "SLING_SHOT_PHYSICS_SECTION0_N",
                sub_map.get("SLING_SHOT_PHYSICS_SECTION0_B", 0.0),
            ),
            "p2": sub_map.get(
                "SLING_SHOT_PHYSICS_SECTION1_N",
                sub_map.get("SLING_SHOT_PHYSICS_SECTION1_B", 0.0),
            ),
            "p3": sub_map.get(
                "SLING_SHOT_PHYSICS_SECTION2_N",
                sub_map.get("SLING_SHOT_PHYSICS_SECTION2_B", 0.0),
            ),
            "result_path": result_path,
            "date": date_val,
            "api": "Vulkan" if "SLING_SHOT_VULKAN" in raw_scores else "OpenGL ES 3.1",
        }, res_id
    except Exception:
        return None, 0


def run_3dmark_test(vulkan: bool = False):
    api_name = "Vulkan" if vulkan else "OpenGL ES 3.1"
    print("\n" + "=" * 65)
    print(f" 🎮 Executing 3DMark Sling Shot Extreme ({api_name}) Benchmark")
    print("=" * 65)

    initial_doc, initial_id = get_latest_3dmark_doc()
    print(f"[*] Baseline 3DMark Results ID: {initial_id}")

    run_adb_shell("am force-stop com.futuremark.dmandroid.application")
    time.sleep(1)
    run_adb_shell(
        "am start -n com.futuremark.dmandroid.application/com.futuremark.flamenco.ui.splash.SplashPageActivity"
    )
    time.sleep(4)

    # Tap Sling Shot Extreme tab header (x=540, y=319)
    run_adb_shell("input tap 540 319")
    time.sleep(1)

    # Re-assert GPU 955MHz floor and DDR 4.266GHz OPP 0 for 3DMark foreground window
    run_adb_root(
        "chmod 664 /sys/module/ged/parameters/gpu_bottom_freq 2>/dev/null && echo 955000 > /sys/module/ged/parameters/gpu_bottom_freq 2>/dev/null"
    )
    run_adb_root("echo 0 > /proc/perfmgr/boost_ctrl/dram_ctrl/ddr 2>/dev/null")
    run_adb_root(
        "echo 0 > /sys/devices/platform/10012000.dvfsrc/helio-dvfsrc/dvfsrc_req_ddr_opp 2>/dev/null"
    )
    run_adb_root(
        "echo 0 > /sys/devices/platform/10012000.dvfsrc/helio-dvfsrc/dvfsrc_req_vcore_opp 2>/dev/null"
    )

    if vulkan:
        print("[*] Opening 3DMark test selector [143, 1128]...")
        run_adb_shell("input tap 143 1128")
        time.sleep(1)
        print("[*] Selecting 'Sling Shot Extreme - Vulkan' [540, 1382]...")
        run_adb_shell("input tap 540 1382")
        time.sleep(1)
        print("[*] Triggering Vulkan test RUN [888, 1533]...")
        run_adb_shell("input tap 888 1533")
    else:
        # Tap Floating Action Button (FAB) to start test (x=959, y=1128)
        print("[*] Triggering 3DMark Sling Shot Extreme FAB [959, 1128]...")
        run_adb_shell("input tap 959 1128")
    start_time = time.time()

    print("[*] Monitoring live 3DMark rendering execution...")
    while True:
        time.sleep(2)
        elapsed = int(time.time() - start_time)
        telem = get_hardware_telemetry()
        sys.stdout.write(
            f"\r    [3DMark] {elapsed:>3}s elapsed | CPU: {telem['big_ghz']:.2f}G / {telem['little_ghz']:.2f}G | GPU: {telem['gpu_mhz']:>4}M | {telem['temp_c']:.1f}°C ({telem['cap_pct']}%)   "
        )
        sys.stdout.flush()

        if elapsed % 4 == 0:
            latest_doc, latest_id = get_latest_3dmark_doc()
            if latest_id > initial_id:
                print(
                    f"\n[✓] 3DMark Sling Shot Extreme completed successfully in {elapsed}s!"
                )
                return latest_doc

        if elapsed > 480:  # 8 minutes timeout
            print("\n[!] Timeout: 3DMark exceeded 8 minutes.")
            return None


def log_results(gb_cpu, mark_res, gb_gpu=None):
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    history_file = os.path.join(DOCS_DIR, "benchmark_history.txt")
    os.makedirs(DOCS_DIR, exist_ok=True)

    with open(history_file, "a", encoding="utf-8") as f:
        if gb_cpu:
            f.write(
                f"[{now_str}] Geekbench 7 CPU: Single={gb_cpu['single_core']}, Multi={gb_cpu['multi_core']}, URL={gb_cpu['url']}\n"
            )
        if mark_res:
            scores_dump = json.dumps(
                {
                    "overallScore": mark_res["overall"],
                    "graphicsScore": mark_res["graphics"],
                    "physicsScore": mark_res["physics"],
                    "gt1": mark_res["gt1"],
                    "gt2": mark_res["gt2"],
                }
            )
            f.write(
                f"[{now_str}] 3DMark: Test=SLING_SHOT_ES_31, Scores={scores_dump}\n"
            )
        if gb_gpu:
            f.write(
                f"[{now_str}] Geekbench 7 GPU ({gb_gpu.get('api')}): Score={gb_gpu['score']}, URL={gb_gpu['url']}\n"
            )
    print(f"\n[+] Results recorded to {history_file}")


def print_summary_report(gb_cpu, mark_res, gb_gpu=None):
    print("\n" + "=" * 75)
    print(" 🏆 AUTOBENCH MASTER PERFORMANCE REPORT")
    print("=" * 75)

    if gb_cpu:
        print("⚡ [Geekbench 7 CPU Results]")
        print(
            f"   Single-Core Score  : {gb_cpu['single_core']} pts (World Record Baseline: 729)"
        )
        print(f"   Multi-Core Score   : {gb_cpu['multi_core']} pts (Target: 2066+)")
        print(f"   Official URL       : {gb_cpu['url']}")

        sections = gb_cpu.get("data", {}).get("sections", [])
        if len(sections) > 1:
            print("\n   📊 Multi-Core Sub-Workload Analysis:")
            sec1 = sections[1]
            for w in sec1.get("workloads", []):
                print(
                    f"      • {w.get('name'):<22} : {w.get('score'):>5} pts ({w.get('runtime'):.2f}s)"
                )

    if mark_res:
        print("\n🎯 [3DMark Sling Shot Extreme Results]")
        print(
            f"   Overall Score      : {mark_res['overall']} pts (Global Record: 2698)"
        )
        print(f"   Graphics Score     : {mark_res['graphics']:.0f} pts (Record: 2542)")
        print(f"     • Graphics Test 1: {mark_res['gt1']:.2f} FPS")
        print(f"     • Graphics Test 2: {mark_res['gt2']:.2f} FPS")
        print(f"   Physics Score      : {mark_res['physics']:.0f} pts (Record: 3561)")
        print(f"     • Part 1 (8 Thr) : {mark_res['p1']:.2f} FPS")
        print(f"     • Part 2 (24 Thr): {mark_res['p2']:.2f} FPS")
        print(f"     • Part 3 (48 Thr): {mark_res['p3']:.2f} FPS")

    if gb_gpu:
        print(f"\n🎮 [Geekbench 7 GPU Compute Results ({gb_gpu.get('api', 'Vulkan')})]")
        print(f"   Compute Score      : {gb_gpu['score']} pts")
        print(f"   Official URL       : {gb_gpu['url']}")

        sections = gb_gpu.get("data", {}).get("sections", [])
        if sections:
            print("\n   📊 GPU Compute Sub-Workload Analysis:")
            for s in sections:
                for w in s.get("workloads", []):
                    print(
                        f"      • {w.get('name'):<22} : {w.get('score'):>5} pts ({w.get('runtime'):.2f}s)"
                    )

    print("=" * 75)


def main():
    parser = argparse.ArgumentParser(
        description="AutoBench — Automated Benchmark Orchestration (Geekbench 7 CPU & 3DMark GPU)"
    )
    parser.add_argument(
        "target", nargs="?", default=None, help="ADB target [ip:port] or device serial"
    )
    parser.add_argument(
        "--cpu-only", action="store_true", help="Run Geekbench 7 CPU benchmark only"
    )
    parser.add_argument(
        "--gpu-only",
        action="store_true",
        help="Run 3DMark Sling Shot Extreme GPU benchmark only",
    )
    parser.add_argument(
        "--gb-gpu",
        action="store_true",
        help="Use Geekbench 7 GPU compute benchmark instead of 3DMark",
    )
    parser.add_argument(
        "--api",
        choices=["opencl", "vulkan"],
        default="opencl",
        help="Geekbench GPU compute API when --gb-gpu is used (default: opencl)",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Run CPU (Geekbench 7) and GPU (3DMark) benchmarks sequentially",
    )
    parser.add_argument(
        "--skip-cooldown",
        action="store_true",
        help="Skip thermal cooldown wait before tests",
    )
    parser.add_argument(
        "--cooldown-temp",
        type=float,
        default=38.0,
        help="Target cooldown battery temp in °C (default: 38.0)",
    )
    parser.add_argument(
        "--vulkan",
        action="store_true",
        help="Run 3DMark Sling Shot Extreme in Vulkan mode instead of OpenGL ES 3.1",
    )

    args = parser.parse_args()

    print("=" * 65)
    print(" EvergoTweaks AutoBench — CPU (Geekbench 7) & GPU (3DMark)")
    print("=" * 65)

    device = ensure_device(args.target)
    if not device:
        print("[-] Error: No ADB devices found or failed to connect.")
        sys.exit(1)
    print(f"[+] Connected Target: {device}")

    if args.cpu_only:
        do_cpu = True
        do_gpu = False
    elif args.gpu_only:
        do_cpu = False
        do_gpu = True
    else:
        do_cpu = True
        do_gpu = True

    prepare_system()

    gb_cpu = None
    mark_result = None
    gb_gpu = None

    try:
        if do_cpu:
            if not args.skip_cooldown:
                wait_for_cooldown(args.cooldown_temp)
            gb_cpu = run_geekbench_cpu_test()
            run_adb_shell("am force-stop com.primatelabs.parkdale")
            run_adb_shell("input keyevent KEYCODE_HOME")
            time.sleep(2)

        if do_gpu:
            if not args.skip_cooldown:
                wait_for_cooldown(args.cooldown_temp)
            if args.gb_gpu:
                gb_gpu = run_geekbench_gpu_test(api=args.api)
                run_adb_shell("am force-stop com.primatelabs.parkdale")
            else:
                mark_result = run_3dmark_test(vulkan=args.vulkan)
                # Keep 3DMark open on device so the user can inspect the native results screen
                time.sleep(2)

        log_results(gb_cpu, mark_result, gb_gpu)
        print_summary_report(gb_cpu, mark_result, gb_gpu)

    except KeyboardInterrupt:
        print("\n[!] AutoBench execution interrupted by user.")
        run_adb_shell("am force-stop com.primatelabs.parkdale")
        run_adb_shell("am force-stop com.futuremark.dmandroid.application")
        run_adb_shell("input keyevent KEYCODE_HOME")
    finally:
        run_adb_shell("svc power stayon false")


if __name__ == "__main__":
    main()
