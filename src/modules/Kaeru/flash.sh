#!/usr/bin/env bash

set -e

echo "=== Flash LK + Enable BLDR Spoof ==="
fastboot wait-for-device
fastboot flash lk version-9.bin
echo "Rebooting to bootloader..."
fastboot reboot bootloader
echo "Waiting for bootloader..."
fastboot wait-for-device
fastboot oem bldr_spoof on
echo "Rebooting..."
fastboot reboot
echo "=== Done ==="
