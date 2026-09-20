#!/usr/bin/env python3
"""EvergoTweaks Submodule Upstream Synchronizer.

Synchronizes all local source and vendor trees from upstream GitHub repositories
directly into FrontlXOX GitHub forks (remote 'origin').
"""

import os
import subprocess
import sys
from pathlib import Path

# Force UTF-8 on Windows consoles
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

# ANSI Color formatting
GREEN = "\033[92m"
CYAN = "\033[96m"
YELLOW = "\033[93m"
RED = "\033[91m"
BOLD = "\033[1m"
RESET = "\033[0m"


def run_git(cwd: Path, *args: str) -> tuple[int, str, str]:
    """Execute a git command in a specific working directory."""
    try:
        proc = subprocess.run(
            ["git", "-C", str(cwd)] + list(args),
            capture_output=True,
            text=True,
            check=False,
        )
        return proc.returncode, proc.stdout.strip(), proc.stderr.strip()
    except Exception as exc:
        return -1, "", str(exc)


def sync_tree(tree_dir: Path) -> bool:
    """Sync a single tree directory to GitHub fork (remote 'origin')."""
    name = tree_dir.name
    print(f"\n{BOLD}[*] Synchronizing: {CYAN}{name}{RESET}")

    # Check git remotes
    code, remotes, _ = run_git(tree_dir, "remote")
    remote_list = remotes.split()
    if "origin" not in remote_list:
        print(f"    {YELLOW}[!] Skipping: 'origin' remote not found{RESET}")
        return False

    # Skip read-only upstream reference mirrors
    if name in ("upstream-device", "kernel-5.10"):
        print(f"    {CYAN}[*] Reference tree: Skipping push to upstream mirror{RESET}")
        return True

    # Get current branch
    code, branch, _ = run_git(tree_dir, "rev-parse", "--abbrev-ref", "HEAD")
    if code != 0 or not branch:
        branch = "main"

    print(f"    {CYAN}--> Active branch: {BOLD}{branch}{RESET}")

    # Push to origin (GitHub)
    print(f"    {CYAN}--> Pushing to GitHub (origin)...{RESET}")
    code, out, err = run_git(tree_dir, "push", "origin", f"{branch}:{branch}")
    if code == 0:
        msg = out or err or "Up to date"
        print(f"    {GREEN}[✓] Successfully synced to GitHub ({msg.splitlines()[-1] if msg.splitlines() else 'OK'}){RESET}")
        return True
    else:
        print(f"    {RED}[X] Push to GitHub failed: {err}{RESET}")
        return False


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    trees_dir = repo_root / "trees"

    if not trees_dir.is_dir():
        print(f"{RED}[X] Trees directory not found: {trees_dir}{RESET}")
        return 1

    print("=" * 60)
    print(f"{BOLD} EvergoTweaks Submodule Tree Synchronizer (FrontlXOX GitHub){RESET}")
    print("=" * 60)

    subtrees = [d for d in trees_dir.iterdir() if d.is_dir() and (d / ".git").exists()]
    if not subtrees:
        print(f"{YELLOW}[!] No git repositories found inside {trees_dir}{RESET}")
        return 1

    success_count = 0
    for tree in subtrees:
        if sync_tree(tree):
            success_count += 1

    print("\n" + "=" * 60)
    print(f"{BOLD}[+] Synchronization complete: {GREEN}{success_count}/{len(subtrees)} trees updated!{RESET}")
    print("=" * 60)
    return 0 if success_count == len(subtrees) else 1


if __name__ == "__main__":
    sys.exit(main())
