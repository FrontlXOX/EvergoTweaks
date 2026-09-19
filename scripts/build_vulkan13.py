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


def build_vulkan13_package(
    root_dir: str,
    kernel_image: str = None,
    dtbo_image: str = None,
    blobs_dir: str = None,
) -> str:
    subsystem_dir = os.path.join(root_dir, "package", "Vulkan13")
    template_dir = os.path.join(subsystem_dir, "template")
    out_dir = os.path.join(subsystem_dir, "package")
    os.makedirs(out_dir, exist_ok=True)
    pkg_zip = os.path.join(out_dir, "Vulkan13-KernelSU.zip")

    if not os.path.exists(template_dir):
        raise FileNotFoundError(f"Missing Vulkan13 template directory at {template_dir}")

    with tempfile.TemporaryDirectory() as tmp_dir:
        # 1. Copy base template structure
        for item in os.listdir(template_dir):
            src_path = os.path.join(template_dir, item)
            dst_path = os.path.join(tmp_dir, item)
            if os.path.isdir(src_path):
                shutil.copytree(src_path, dst_path)
            else:
                shutil.copy2(src_path, dst_path)

        # 2. Inject kernel image if provided
        if kernel_image and os.path.isfile(kernel_image):
            print(f"[+] Injecting kernel binary: {kernel_image}")
            shutil.copy2(kernel_image, os.path.join(tmp_dir, "Image.gz"))

        if dtbo_image and os.path.isfile(dtbo_image):
            print(f"[+] Injecting DTBO image: {dtbo_image}")
            shutil.copy2(dtbo_image, os.path.join(tmp_dir, "dtbo.img"))

        # 3. Inject vendor blobs if directory provided
        if blobs_dir and os.path.isdir(blobs_dir):
            print(f"[+] Injecting vendor blobs from: {blobs_dir}")
            for root, _, files in os.walk(blobs_dir):
                for f in files:
                    if f in ("vulkan.mali.so", "libGLES_mali.so", "libGLES_meow.so"):
                        rel_path = os.path.relpath(os.path.join(root, f), blobs_dir)
                        target_loc = os.path.join(
                            tmp_dir, "system", "vendor", rel_path
                        )
                        os.makedirs(os.path.dirname(target_loc), exist_ok=True)
                        shutil.copy2(os.path.join(root, f), target_loc)
                        print(f"    -> Mapped {f} to system/vendor/{rel_path}")

        # 4. Create flashable zip archive
        with zipfile.ZipFile(pkg_zip, "w", zipfile.ZIP_DEFLATED) as z:
            for root, dirs, files in os.walk(tmp_dir):
                for file in files:
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, tmp_dir)
                    z.write(full_path, rel_path)

    size_bytes = os.path.getsize(pkg_zip)
    print(f"[+] Successfully built {pkg_zip} ({size_bytes} bytes / {size_bytes / 1024:.1f} KB)")
    return pkg_zip


def verify_package(zip_path: str) -> bool:
    if not os.path.exists(zip_path):
        print(f"[-] ERROR: {zip_path} does not exist!")
        return False

    required_entries = [
        "anykernel.sh",
        "module.prop",
        "system.prop",
        "META-INF/com/google/android/update-binary",
        "META-INF/com/google/android/updater-script",
        "tools/ak3-core.sh",
        "tools/busybox",
        "tools/magiskboot",
        "system/vendor/etc/permissions/android.hardware.vulkan.version.xml",
        "system/vendor/etc/permissions/android.hardware.vulkan.level.xml",
    ]

    with zipfile.ZipFile(zip_path, "r") as z:
        names = z.namelist()
        missing = [e for e in required_entries if e not in names]
        if missing:
            print(f"[-] ERROR: Missing critical entries in package: {missing}")
            return False

        bad_file = z.testzip()
        if bad_file:
            print(f"[-] ERROR: Corrupt entry in {zip_path}: {bad_file}")
            return False

    print(f"[✓] Package verified: {len(names)} entries, CRC-32 valid ({os.path.getsize(zip_path)} bytes)")
    return True


def main():
    parser = argparse.ArgumentParser(
        description="EvergoTweaks Vulkan 1.3 Hybrid KernelSU/AnyKernel3 Packager"
    )
    parser.add_argument(
        "--kernel", "-k", default=None, help="Path to compiled Image.gz"
    )
    parser.add_argument(
        "--dtbo", "-d", default=None, help="Path to compiled dtbo.img"
    )
    parser.add_argument(
        "--blobs", "-b", default=None, help="Path to donor vendor blobs directory"
    )
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Verify existing package without rebuilding",
    )
    args = parser.parse_args()

    print("=" * 65)
    print(" EvergoTweaks Vulkan 1.3 Hybrid Module Builder & Validator")
    print("=" * 65)

    pkg_zip = os.path.join(
        REPO_ROOT, "package", "Vulkan13", "package", "Vulkan13-KernelSU.zip"
    )

    if not args.verify_only:
        build_vulkan13_package(
            REPO_ROOT,
            kernel_image=args.kernel,
            dtbo_image=args.dtbo,
            blobs_dir=args.blobs,
        )

    print("\n" + "=" * 65)
    print(" Verifying Package Integrity")
    print("=" * 65)

    if not verify_package(pkg_zip):
        sys.exit(1)

    print("\n[+] Hybrid Vulkan 1.3 KernelSU package ready for deployment!")


if __name__ == "__main__":
    main()
