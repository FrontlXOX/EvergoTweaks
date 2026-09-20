#!/usr/bin/env python3
import os
import sys
import zipfile
import argparse
from payload_dumper.dumper import Dumper

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8") # type: ignore
        sys.stderr.reconfigure(encoding="utf-8") # type: ignore
    except Exception:
        pass


def dump_boot(zip_path: str, out_dir: str = ".") -> str:
    if not os.path.isfile(zip_path):
        raise FileNotFoundError(f"Archive not found: {zip_path}")
    os.makedirs(out_dir, exist_ok=True)
    with zipfile.ZipFile(zip_path, "r") as z:
        namelist = z.namelist()

        if "boot.img" in namelist:
            print(
                f"[+] Found boot.img directly in '{os.path.basename(zip_path)}'. Extracting..."
            )
            target_path = os.path.join(out_dir, "boot.img")
            with z.open("boot.img") as src, open(target_path, "wb") as dst:
                dst.write(src.read())
            size_mb = os.path.getsize(target_path) / (1024 * 1024)
            print(f"[OK] Extracted: {target_path} ({size_mb:.2f} MB)")
            return target_path

        if "payload.bin" not in namelist:
            raise RuntimeError(
                f"Neither 'payload.bin' nor 'boot.img' was found inside '{zip_path}'."
            )

        print(f"[+] Found 'payload.bin' in '{os.path.basename(zip_path)}'.")
        print("[+] Streaming payload and dumping 'boot.img' partition...")

        with z.open("payload.bin") as payload_file:
            dumper = Dumper(
                payloadfile=payload_file,
                out=out_dir,
                images="boot",
            )
            dumper.run()

    out_file = os.path.join(out_dir, "boot.img")
    if os.path.isfile(out_file):
        size_mb = os.path.getsize(out_file) / (1024 * 1024)
        print(f"[OK] Successfully dumped: {out_file} ({size_mb:.2f} MB)")
        return out_file
    else:
        raise RuntimeError(
            "Failed to dump boot.img (partition may not exist in payload)."
        )


def main():
    parser = argparse.ArgumentParser(
        description="Dump boot.img directly from an Android ROM zip file."
    )
    parser.add_argument("zip_path", help="Path to the Android ROM / OTA zip file")
    parser.add_argument(
        "-o", "--out", default=".", help="Output directory (default: current directory)"
    )

    args = parser.parse_args()

    try:
        dump_boot(args.zip_path, args.out)
    except Exception as e:
        print(f"[-] Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
