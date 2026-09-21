#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# pylint: skip-file
# pylint: disable=all
# flake8: noqa
# ruff: noqa
# type: ignore

import os
import sys
import json
import sqlite3
import datetime
import subprocess

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
    if devices:
        CURRENT_DEVICE = target if (target and target in devices) else devices[0]
    return CURRENT_DEVICE


def run_adb(cmd_list):
    adb_cmd = [ADB]
    if CURRENT_DEVICE:
        adb_cmd.extend(["-s", CURRENT_DEVICE])
    adb_cmd.extend(cmd_list)
    res = subprocess.run(adb_cmd, capture_output=True, text=True, errors="replace")
    return res.stdout.strip()


def pull_geekbench_cpu():
    run_adb(
        [
            "shell",
            "su",
            "-c",
            "cp /data/data/com.primatelabs.parkdale/files/history.db /sdcard/history.db && chmod 666 /sdcard/history.db",
        ]
    )
    local_db = os.path.join(DOCS_DIR, "history.db")
    run_adb(["pull", "/sdcard/history.db", local_db])
    if not os.path.exists(local_db):
        return None

    try:
        con = sqlite3.connect(local_db)
        cur = con.cursor()
        row = cur.execute("""
            SELECT c.document_id, c.score, c.multicore_score, d.json
            FROM cpu_documents c
            JOIN documents d ON c.document_id = d.id
            ORDER BY c.rowid DESC LIMIT 1
        """).fetchone()
        if not row:
            return None
        doc_id, sc, mc, raw_json = row
        data = json.loads(raw_json)
        url = data.get("browser", {}).get("url", "")
        freqs = data.get("processor_frequency", {}).get("frequencies", [])
        return {
            "id": doc_id,
            "single_core": sc,
            "multi_core": mc,
            "url": url,
            "frequencies": freqs,
            "data": data,
        }
    except Exception as e:
        print(f"Error querying Geekbench history.db: {e}")
        return None


def pull_geekbench_gpu():
    local_db = os.path.join(DOCS_DIR, "history.db")
    if not os.path.exists(local_db):
        return None

    try:
        con = sqlite3.connect(local_db)
        cur = con.cursor()
        row = cur.execute("""
            SELECT g.document_id, g.score, g.api, d.json
            FROM gpu_documents g
            JOIN documents d ON g.document_id = d.id
            ORDER BY g.rowid DESC LIMIT 1
        """).fetchone()
        if not row:
            return None
        doc_id, score, api_type, raw_json = row
        data = json.loads(raw_json)
        url = data.get("browser", {}).get("url", "")
        return {
            "id": doc_id,
            "score": score,
            "api": api_type,
            "url": url,
            "data": data,
        }
    except Exception as e:
        print(f"Error querying Geekbench GPU in history.db: {e}")
        return None


def log_history(entry_line: str):
    history_file = os.path.join(DOCS_DIR, "benchmark_history.txt")
    with open(history_file, "a", encoding="utf-8") as f:
        f.write(entry_line + "\n")


def main():
    print("=" * 65)
    print(" Everpal Automated Benchmark Extractor (Geekbench 7)")
    print("=" * 65)

    target_arg = None
    if len(sys.argv) > 1:
        if sys.argv[1] in ("-s", "--target") and len(sys.argv) > 2:
            target_arg = sys.argv[2]
        elif not sys.argv[1].startswith("-"):
            target_arg = sys.argv[1]

    device = ensure_device(target_arg)
    if not device:
        print("[-] No active ADB devices found!")
        print(
            "    Ensure device is connected via USB (with USB debugging enabled), or provide wireless target:"
        )
        print("    Usage: python pull_benchmark.py [ip:port] or set ADB_TARGET=ip:port")
        sys.exit(1)

    print(f"[+] Connected Target: {device}")
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 1. Geekbench 7 CPU
    gb_cpu = pull_geekbench_cpu()
    if gb_cpu:
        print(f"[*] Geekbench 7 Single-Core : {gb_cpu['single_core']}")
        print(f"[*] Geekbench 7 Multi-Core  : {gb_cpu['multi_core']}")
        print(f"[*] CPU Online Result URL   : {gb_cpu['url']}")
        if gb_cpu["frequencies"]:
            print(f"[*] CPU Frequencies Sampled : {gb_cpu['frequencies'][:10]} ...")
        entry = f"[{now_str}] Geekbench 7 CPU: Single={gb_cpu['single_core']}, Multi={gb_cpu['multi_core']}, URL={gb_cpu['url']}"
        log_history(entry)
    else:
        print("[-] No Geekbench 7 CPU results found.")

    print("-" * 65)

    # 2. Geekbench 7 GPU
    gb_gpu = pull_geekbench_gpu()
    if gb_gpu:
        print(f"[*] Geekbench 7 GPU Score   : {gb_gpu['score']}")
        print(f"[*] GPU Compute API         : {gb_gpu['api']}")
        print(f"[*] GPU Online Result URL   : {gb_gpu['url']}")
        entry = f"[{now_str}] Geekbench 7 GPU: Score={gb_gpu['score']}, API={gb_gpu['api']}, URL={gb_gpu['url']}"
        log_history(entry)
    else:
        print("[-] No Geekbench 7 GPU results found in database yet.")

    print("-" * 65)

    # 3. 3DMark Sling Shot Extreme
    mark_runs = pull_3dmark()
    if mark_runs:
        for mark_res in mark_runs:
            print(f"[*] 3DMark Test API         : {mark_res['api']}")
            print(f"[*] 3DMark Overall Score    : {mark_res['overall']}")
            print(
                f"[*] 3DMark Graphics Score   : {mark_res['graphics']:.0f} (GT1: {mark_res['gt1']:.2f} FPS, GT2: {mark_res['gt2']:.2f} FPS)"
            )
            print(
                f"[*] 3DMark Physics Score    : {mark_res['physics']:.0f} (P1: {mark_res['p1']:.2f}, P2: {mark_res['p2']:.2f}, P3: {mark_res['p3']:.2f} FPS)"
            )
            scores_dump = json.dumps(
                {
                    "api": mark_res["api"],
                    "overallScore": mark_res["overall"],
                    "graphicsScore": mark_res["graphics"],
                    "physicsScore": mark_res["physics"],
                    "gt1": mark_res["gt1"],
                    "gt2": mark_res["gt2"],
                    "demo": mark_res["demo"],
                }
            )
            entry = f"[{now_str}] 3DMark: Test={mark_res['api']}, Scores={scores_dump}"
            log_history(entry)
            print("-" * 65)
    else:
        print("[-] No 3DMark results found in database yet.")

    print("=" * 65)


def pull_3dmark():
    run_adb(
        [
            "shell",
            "su",
            "-c",
            "cp /data/data/com.futuremark.dmandroid.application/databases/fm_local_results.db* /sdcard/ 2>/dev/null && chmod 666 /sdcard/fm_local_results.db*",
        ]
    )
    local_db = os.path.join(DOCS_DIR, "fm_local_results.db")
    run_adb(["pull", "/sdcard/fm_local_results.db", local_db])
    if not os.path.exists(local_db):
        return []

    results = []
    try:
        con = sqlite3.connect(local_db)
        cur = con.cursor()
        rows = cur.execute("""
            SELECT id, scores, result_path, date
            FROM results
            ORDER BY id ASC
        """).fetchall()
        con.close()
        for row in rows:
            res_id, raw_scores, result_path, date_val = row
            scores_data = json.loads(raw_scores)
            overall = scores_data.get("overallScore", 0)
            sub_map = {
                item["resultType"]: item["score"]
                for item in scores_data.get("subScores", [])
            }
            results.append({
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
            })
        return results
    except Exception as e:
        print(f"Error querying 3DMark fm_local_results.db: {e}")
        return []


if __name__ == "__main__":
    main()
