# pylint: skip-file
# type: ignore
# flake8: noqa

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path


def _find_kernel_in_zip(z: zipfile.ZipFile) -> str:
    # 1. Match common kernel filenames first
    candidates = ['image.gz', 'image', 'image.lz4', 'zimage', 'kernel']
    for name in z.namelist():
        if os.path.basename(name).lower() in candidates:
            return name

    # 2. Inspect file magic bytes dynamically (gzip, lz4, or ARM64 Linux Image magic)
    for name in z.namelist():
        if name.endswith('/') or name.startswith('META-INF/') or name.startswith('tools/'):
            continue
        try:
            head = z.read(name)[:64]
            if head.startswith(b'\x1f\x8b') or head.startswith(b'\x04\x22\x4d\x18'):
                return name
            if len(head) >= 60 and head[56:60] == b'ARM\x64':
                return name
        except Exception:
            continue

    raise FileNotFoundError("Could not find a valid kernel binary inside the zip archive.")


def _is_anykernel_zip(p: Path) -> bool:
    try:
        with zipfile.ZipFile(p, 'r') as z:
            names = [n.lower() for n in z.namelist()]
            return any('anykernel' in n or 'image' in n or 'kernel' in n for n in names)
    except Exception:
        return False


def _list_kernelzips(directory: Path):
    zips = [p for p in directory.glob("*.zip") if p.is_file()]
    if not zips:
        raise FileNotFoundError(f"No .zip files found in {directory}")

    # Natural version sorting (e.g. V3.4 before V3.3)
    def version_key(p: Path):
        return [int(c) if c.isdigit() else c.lower() for c in re.split(r'(\d+)', p.name)]

    kernel_zips = [p for p in zips if _is_anykernel_zip(p)]
    candidates = kernel_zips if kernel_zips else zips
    candidates.sort(key=version_key, reverse=True)
    return candidates


def _auto_detect_kernelzip(directory: Path) -> Path:
    candidates = _list_kernelzips(directory)
    chosen = candidates[0]
    print(f"[+] Auto-detected kernel zip: {chosen.name}")
    return chosen


def _auto_detect_bootimg(directory: Path) -> Path:
    # Find all .img files in the directory, ignoring script output files starting with 'boot_'
    base_imgs = [p for p in directory.glob("*.img") if p.is_file() and not p.name.startswith("boot_")]
    candidates = base_imgs if base_imgs else [p for p in directory.glob("*.img") if p.is_file()]
    if not candidates:
        raise FileNotFoundError(f"No .img files found in {directory}")

    # Sort by latest modification time
    candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    chosen = candidates[0]
    print(f"[+] Auto-detected base boot image: {chosen.name}")
    return chosen


def _parse_unpack_output(text: str):
    params = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or ':' not in line:
            continue
        key, val = line.split(':', 1)
        params[key.strip()] = val.strip()
    return params


def _parse_avb_info(text: str):
    avb_info = {
        'has_avb': False,
        'partition_size': None,
        'partition_name': 'boot',
        'algorithm': 'SHA256_RSA2048',
        'salt': None,
        'props': []
    }
    if 'Footer version:' in text or 'VBMeta offset:' in text:
        avb_info['has_avb'] = True

    for line in text.splitlines():
        line = line.strip()
        if line.startswith('Image size:'):
            match = re.search(r'(\d+)\s+bytes', line)
            if match:
                avb_info['partition_size'] = match.group(1)
        elif line.startswith('Partition Name:'):
            avb_info['partition_name'] = line.split(':', 1)[1].strip()
        elif line.startswith('Algorithm:'):
            avb_info['algorithm'] = line.split(':', 1)[1].strip()
        elif line.startswith('Salt:'):
            avb_info['salt'] = line.split(':', 1)[1].strip()
        elif line.startswith('Prop:'):
            prop_part = line.split('Prop:', 1)[1].strip()
            if '->' in prop_part:
                k, v = prop_part.split('->', 1)
                avb_info['props'].append(f"{k.strip()}:{v.strip().strip('\'\"')}")

    return avb_info


def main(kernelzip: str = "", bootimg: str = "", output: str = ""):
    """
    No kernelzip given -> build one image per kernel zip found in the folder.
    Explicit kernelzip given -> build just that one (previous behavior).
    """
    if not kernelzip:
        script_dir = Path(__file__).resolve().parent
        targets = _list_kernelzips(script_dir)
        print(f"[*] Building {len(targets)} image(s) - one per kernel zip")
        results = []
        for t in targets:
            print(f"--- {t.name} ---")
            results.append(_build_single(kernelzip=str(t), bootimg=bootimg, output=""))
        print(f"[SUCCESS] Built {len(results)} image(s)")
        return results
    return _build_single(kernelzip=kernelzip, bootimg=bootimg, output=output)


def _build_single(kernelzip: str = "", bootimg: str = "", output: str = "") -> str:
    """
    Unpacks a base boot image, replaces its kernel with the one from an AnyKernel3 zip,
    repacks it with matching header/ramdisk/dtb, and re-applies AVB signing.

    Auto-finds the zip and boot.img dynamically with no hardcoded filenames.
    """
    script_dir = Path(__file__).resolve().parent
    python_dir = script_dir / "python"
    mkbootimg_script = python_dir / "mkbootimg.py"
    unpack_script = python_dir / "unpack_bootimg.py"
    avbtool_script = python_dir / "avbtool.py"
    testkey_path = python_dir / "testkey_rsa2048.pem"

    # Auto-detect kernel zip if not explicitly given
    if not kernelzip:
        kzip_path = _auto_detect_kernelzip(script_dir)
    else:
        kzip_path = Path(kernelzip).resolve()
        if not kzip_path.is_file() and (script_dir / kernelzip).is_file():
            kzip_path = (script_dir / kernelzip).resolve()
        if not kzip_path.is_file():
            raise FileNotFoundError(f"Kernel zip file not found: {kernelzip}")

    # Auto-detect boot image if not explicitly given.
    # Variant pairing: HyOS kernel zips need HyOSBOOT.img, everything else uses
    # AospBOOT.img. Falls back to generic auto-detect only if the paired file
    # is missing (with a loud warning - wrong base = no-boot risk).
    if not bootimg:
        paired = None
        if "hyos" in kzip_path.name.lower():
            cand = script_dir / "HyOSBOOT.img"
            if cand.is_file():
                paired = cand
            else:
                print("[!] WARNING: HyOS kernel zip but no HyOSBOOT.img in folder - "
                      "falling back to auto-detect (probably the wrong base!)")
        else:
            cand = script_dir / "AospBOOT.img"
            if cand.is_file():
                paired = cand
        if paired is not None:
            bimg_path = paired
            print(f"[+] Paired base boot image: {bimg_path.name}")
        else:
            bimg_path = _auto_detect_bootimg(script_dir)
    else:
        bimg_path = Path(bootimg).resolve()
        if not bimg_path.is_file() and (script_dir / bootimg).is_file():
            bimg_path = (script_dir / bootimg).resolve()
        if not bimg_path.is_file():
            raise FileNotFoundError(f"Base boot image file not found: {bootimg}")

    if not output:
        clean_zip_stem = kzip_path.stem.replace(" ", "_")
        prefix = "" if clean_zip_stem.lower().startswith("boot_") else "boot_"
        output_name = f"{prefix}{clean_zip_stem}.img"
        out_path = script_dir / output_name
    else:
        out_path = Path(output).resolve()

    print("\n--- Repack Configuration ---")
    print(f"[*] Base Boot Image : {bimg_path.name} ({bimg_path.stat().st_size:,} bytes)")
    print(f"[*] Kernel Zip      : {kzip_path.name}")
    print(f"[*] Output Target   : {out_path.name}")
    print("----------------------------\n")

    work_dir = Path(tempfile.mkdtemp(prefix="kernel_repack_"))

    try:
        # 1. Extract Kernel from zip
        with zipfile.ZipFile(kzip_path, 'r') as z:
            k_entry = _find_kernel_in_zip(z)
            print(f"[+] Found kernel binary inside zip: {k_entry}")
            extracted_kernel = work_dir / "kernel_new"
            with open(extracted_kernel, 'wb') as f:
                f.write(z.read(k_entry))

        # 2. Unpack base boot.img
        unpacked_dir = work_dir / "unpacked"
        unpacked_dir.mkdir()

        unpack_cmd = [
            sys.executable, str(unpack_script),
            "--boot_img", str(bimg_path),
            "--out", str(unpacked_dir)
        ]
        unpack_proc = subprocess.run(unpack_cmd, capture_output=True, text=True, check=True)
        params = _parse_unpack_output(unpack_proc.stdout)

        hdr_ver = params.get('boot image header version', '2')
        page_size = params.get('page size', '2048')
        cmdline = params.get('command line args', '')
        extra_cmdline = params.get('additional command line args', '')
        os_version = params.get('os version', '')
        os_patch_level = params.get('os patch level', '')
        kernel_addr_str = params.get('kernel load address', '0x40080000')
        ramdisk_addr_str = params.get('ramdisk load address', '0x51100000')
        tags_addr_str = params.get('kernel tags load address', '0x47c80000')
        dtb_addr_str = params.get('dtb address', '0x47c80000')

        kernel_addr = int(kernel_addr_str, 16)
        ramdisk_addr = int(ramdisk_addr_str, 16)
        tags_addr = int(tags_addr_str, 16)

        base = kernel_addr & ~0x00FFFFFF
        kernel_offset = kernel_addr - base
        ramdisk_offset = ramdisk_addr - base
        tags_offset = tags_addr - base

        ramdisk_file = unpacked_dir / "ramdisk"
        dtb_file = unpacked_dir / "dtb"

        # 3. Check AVB info
        avb_cmd = [sys.executable, str(avbtool_script), "info_image", "--image", str(bimg_path)]
        avb_proc = subprocess.run(avb_cmd, capture_output=True, text=True)
        avb_info = _parse_avb_info(avb_proc.stdout) if avb_proc.returncode == 0 else {'has_avb': False}

        # 4. Repack boot.img
        mkboot_cmd = [
            sys.executable, str(mkbootimg_script),
            "--kernel", str(extracted_kernel),
            "--ramdisk", str(ramdisk_file),
            "--base", hex(base),
            "--kernel_offset", hex(kernel_offset),
            "--ramdisk_offset", hex(ramdisk_offset),
            "--tags_offset", hex(tags_offset),
            "--pagesize", page_size,
            "--header_version", hdr_ver,
            "-o", str(out_path)
        ]

        if dtb_file.is_file() and int(params.get('dtb size', '0')) > 0:
            dtb_addr = int(dtb_addr_str, 16)
            dtb_offset = dtb_addr - base
            mkboot_cmd.extend(["--dtb", str(dtb_file), "--dtb_offset", hex(dtb_offset)])

        if cmdline:
            mkboot_cmd.extend(["--cmdline", cmdline])
        if extra_cmdline:
            mkboot_cmd.extend(["--extra_cmdline", extra_cmdline])
        if os_version:
            mkboot_cmd.extend(["--os_version", os_version])
        if os_patch_level:
            mkboot_cmd.extend(["--os_patch_level", os_patch_level])

        print("[+] Repacking boot image with mkbootimg...")
        subprocess.run(mkboot_cmd, capture_output=True, text=True, check=True)

        # 5. Sign with AVB if original had AVB footer
        if avb_info.get('has_avb'):
            print("[+] Original image has AVB footer. Adding signed AVB hash footer...")
            part_size = avb_info.get('partition_size') or str(bimg_path.stat().st_size)
            part_name = avb_info.get('partition_name') or 'boot'
            algo = avb_info.get('algorithm') or 'SHA256_RSA2048'
            salt = avb_info.get('salt') or 'ea8468a030d2b72074a1da8937fe69585e5eb96a445aabf43443e65125df5ecb'

            avb_sign_cmd = [
                sys.executable, str(avbtool_script), "add_hash_footer",
                "--image", str(out_path),
                "--partition_size", str(part_size),
                "--partition_name", part_name,
                "--algorithm", algo,
                "--key", str(testkey_path),
                "--salt", salt
            ]
            for prop in avb_info.get('props', []):
                avb_sign_cmd.extend(["--prop", prop])

            subprocess.run(avb_sign_cmd, capture_output=True, text=True, check=True)
            print("[+] AVB footer signed successfully.")

        final_size = out_path.stat().st_size
        print(f"\n[SUCCESS] Flashable image generated: {out_path.name}")
        print(f"          Path: {out_path}")
        print(f"          Size: {final_size:,} bytes ({final_size / (1024*1024):.2f} MB)")
        return str(out_path)

    finally:
        shutil.rmtree(work_dir, ignore_errors=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create flashable boot.img(s) from AnyKernel3 zip(s) and base boot.img. No kernel zip given = build one image per zip found.")
    parser.add_argument("kernelzip_pos", nargs="?", default="", help="Path to AnyKernel3 zip (optional)")
    parser.add_argument("bootimg_pos", nargs="?", default="", help="Path to base boot.img (optional)")
    parser.add_argument("-k", "--kernelzip", default="", help="Path to AnyKernel3 zip")
    parser.add_argument("-b", "--bootimg", default="", help="Path to base boot.img")
    parser.add_argument("-o", "--output", default="", help="Path for output .img file")

    args = parser.parse_args()
    kzip = args.kernelzip or args.kernelzip_pos
    bimg = args.bootimg or args.bootimg_pos

    try:
        main(kernelzip=kzip, bootimg=bimg, output=args.output)
    except Exception as err:
        print(f"\n[ERROR] {err}", file=sys.stderr)
        sys.exit(1)
