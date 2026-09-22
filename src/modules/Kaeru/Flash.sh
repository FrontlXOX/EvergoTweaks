#!/usr/bin/env bash
set -e
echo "=== Flash LK + Enable BLDR Spoof ==="
fastboot flash lk version-9.bin
fastboot reboot bootloader
fastboot oem bldr_spoof on
fastboot reboot
echo "=== Done ==="
