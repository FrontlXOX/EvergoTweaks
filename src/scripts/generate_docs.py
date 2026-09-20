import json
import gzip
import os
import shutil

CONVERSATION_ID = "55d888ff-3b0a-40a5-8174-8d80f8256ee5"
BASE_LOGS = rf"C:\Users\psycosis\.gemini\antigravity-cli\brain\{CONVERSATION_ID}\.system_generated\logs"
FULL_LOG = os.path.join(BASE_LOGS, "transcript_full.jsonl")
COMPACT_LOG = os.path.join(BASE_LOGS, "transcript.jsonl")
DOCS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs")

os.makedirs(DOCS_DIR, exist_ok=True)
ARCHIVE_GZ = os.path.join(DOCS_DIR, "transcript_archive.jsonl.gz")
TRANSCRIPT_MD = os.path.join(DOCS_DIR, "SESSION_TRANSCRIPT.md")

log_path = FULL_LOG if os.path.exists(FULL_LOG) else COMPACT_LOG
print(f"Reading log from: {log_path}")

# 1. Compress raw jsonl to docs/transcript_archive.jsonl.gz
with open(log_path, "rb") as f_in:
    with gzip.open(ARCHIVE_GZ, "wb") as f_out:
        shutil.copyfileobj(f_in, f_out)
print(f"[+] Gzipped raw transcript to: {ARCHIVE_GZ} ({os.path.getsize(ARCHIVE_GZ):,} bytes)")

# 2. Parse and generate SESSION_TRANSCRIPT.md
md_lines = [
    "# EverpalTweaks Master Engineering Session Transcript\n",
    f"> **Conversation ID:** {CONVERSATION_ID}  ",
    "> **Device:** Xiaomi POCO M4 Pro 5G / Redmi Note 11S 5G (everpal)  ",
    "> **Platform:** MediaTek Dimensity 810 (MT6833P / MT6833)  ",
    "> **OS:** Android 16 (Project Infinity - LineageOS 23.0 Base)  ",
    "> **Kernel:** Linux 4.14.357-Aqua SMP PREEMPT  ",
    "> **Archival Format:** Comprehensive dialogue history + raw gzip backup (`src/docs/transcript_archive.jsonl.gz`)  \n",
    "---\n"
]

with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
        except Exception:
            continue

        source = entry.get("source", "")
        step_type = entry.get("type", "")
        created_at = entry.get("created_at", "")
        content = entry.get("content", "")
        calls = entry.get("tool_calls", [])

        if step_type == "USER_INPUT" or source == "USER_EXPLICIT":
            md_lines.append(f"\n## 👤 USER ({created_at})\n\n")
            md_lines.append(f"{content}\n\n---\n")
        elif step_type == "PLANNER_RESPONSE" or source == "MODEL":
            md_lines.append(f"\n## 🤖 ANTIGRAVITY ({created_at})\n\n")
            if content:
                md_lines.append(f"{content}\n\n")
            if calls:
                md_lines.append("### 🛠️ Tool Executions\n\n")
                for call in calls:
                    call_name = call.get("name", "")
                    args = call.get("args", {})
                    summary = args.get("toolSummary", "")
                    action = args.get("toolAction", "")
                    cmd = args.get("CommandLine", "")
                    target = args.get("TargetFile", "")
                    
                    md_lines.append(f"- **`{call_name}`**")
                    if summary:
                        md_lines.append(f": {summary}")
                    elif action:
                        md_lines.append(f": {action}")
                    if cmd:
                        md_lines.append(f"\n  ```powershell\n  {cmd}\n  ```\n")
                    elif target:
                        md_lines.append(f" (`{target}`)\n")
                    else:
                        md_lines.append("\n")
            md_lines.append("---\n")

with open(TRANSCRIPT_MD, "w", encoding="utf-8") as f_out:
    f_out.writelines(md_lines)

print(f"[+] Generated SESSION_TRANSCRIPT.md ({os.path.getsize(TRANSCRIPT_MD):,} bytes, {len(md_lines):,} sections)")
