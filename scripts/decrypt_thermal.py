#!/usr/bin/env python3

import os
import sys
import argparse
import subprocess

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

KEY = b"thermalopenssl.h"
IV = b"thermalopenssl.h"


def pad_pkcs7(data: bytes, block_size: int = 16) -> bytes:
    pad_len = block_size - (len(data) % block_size)
    return data + bytes([pad_len] * pad_len)


def unpad_pkcs7(data: bytes) -> bytes:
    if not data:
        return b""
    pad_len = data[-1]
    if 1 <= pad_len <= 16 and data.endswith(bytes([pad_len] * pad_len)):
        return data[:-pad_len]
    return data


def decrypt_data(encrypted: bytes) -> bytes:
    try:
        from Crypto.Cipher import AES

        cipher = AES.new(KEY, AES.MODE_CBC, IV)
        return unpad_pkcs7(cipher.decrypt(encrypted))
    except ImportError:
        cmd = ["openssl", "enc", "-d", "-aes-128-cbc", "-K", KEY.hex(), "-iv", IV.hex()]
        res = subprocess.run(cmd, input=encrypted, capture_output=True)
        if res.returncode != 0:
            raise RuntimeError(
                f"OpenSSL decryption failed: {res.stderr.decode('utf-8', errors='replace')}"
            )
        return res.stdout


def encrypt_data(plain: bytes) -> bytes:
    padded = pad_pkcs7(plain)
    try:
        from Crypto.Cipher import AES

        cipher = AES.new(KEY, AES.MODE_CBC, IV)
        return cipher.encrypt(padded)
    except ImportError:
        cmd = ["openssl", "enc", "-e", "-aes-128-cbc", "-K", KEY.hex(), "-iv", IV.hex()]
        res = subprocess.run(cmd, input=plain, capture_output=True)
        if res.returncode != 0:
            raise RuntimeError(
                f"OpenSSL encryption failed: {res.stderr.decode('utf-8', errors='replace')}"
            )
        return res.stdout


def main():
    parser = argparse.ArgumentParser(
        description="Xiaomi MT6833 Thermal Config Cipher Tool"
    )
    parser.add_argument(
        "input_file", nargs="?", default=None, help="Path to input file"
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Path to output file (default: stdout for decrypt, input.conf for encrypt)",
    )
    parser.add_argument(
        "-e",
        "--encrypt",
        action="store_true",
        help="Encrypt plaintext to thermal config",
    )
    parser.add_argument(
        "-d",
        "--decrypt",
        action="store_true",
        help="Decrypt thermal config to plaintext (default)",
    )
    parser.add_argument("--batch", help="Batch decrypt all .conf files in directory")

    args = parser.parse_args()

    if args.batch:
        target_dir = args.batch
        count = 0
        for f in os.listdir(target_dir):
            if f.endswith(".conf") and not f.endswith(".decrypted.conf"):
                in_path = os.path.join(target_dir, f)
                out_path = os.path.join(
                    target_dir, f.replace(".conf", ".decrypted.txt")
                )
                with open(in_path, "rb") as rf:
                    dec = decrypt_data(rf.read())
                with open(out_path, "wb") as wf:
                    wf.write(dec)
                count += 1
                print(f"[✓] Decrypted: {f} -> {os.path.basename(out_path)}")
        print(f"\n[+] Successfully batch decrypted {count} configs in {target_dir}")
        return

    if not args.input_file:
        parser.print_help()
        sys.exit(1)

    with open(args.input_file, "rb") as f:
        in_bytes = f.read()

    if args.encrypt:
        out_bytes = encrypt_data(in_bytes)
        out_file = args.output or (args.input_file.rsplit(".", 1)[0] + ".conf")
        with open(out_file, "wb") as f:
            f.write(out_bytes)
        print(
            f"[+] Successfully encrypted {args.input_file} -> {out_file} ({len(out_bytes)} bytes)"
        )
    else:
        out_bytes = decrypt_data(in_bytes)
        if args.output:
            with open(args.output, "wb") as f:
                f.write(out_bytes)
            print(
                f"[+] Successfully decrypted {args.input_file} -> {args.output} ({len(out_bytes)} bytes)"
            )
        else:
            print(out_bytes.decode("utf-8", errors="replace"))


if __name__ == "__main__":
    main()
