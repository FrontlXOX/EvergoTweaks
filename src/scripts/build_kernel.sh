#!/bin/bash
# EverpalTweaks — Aqua Kernel + Vulkan 1.3 Integrated Builder
# Target : Xiaomi Everpal (MT6833P / Dimensity 810)
# OS     : ZorinOS / Ubuntu 22.04+
# Clang  : ZyC Clang 22.0.0 (auto-downloaded to ~/toolchains/)
# Usage  :
#   ./src/scripts/build_kernel.sh              → kernel only  (AquaKernel-<date>.zip)
#   ./src/scripts/build_kernel.sh --vulkan     → kernel + Vulkan 1.3 overlay  (Vulkan13-KernelSU.zip)
#   ./src/scripts/build_kernel.sh --clean      → wipe out/ before building
#   ./src/scripts/build_kernel.sh --with-ksu   → apply ReSukiSU/SUSFS patches before building
#   Flags can be combined: ./src/scripts/build_kernel.sh --vulkan --clean --with-ksu

set -euo pipefail

# ── Paths ────────────────────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
if [ -d "$REPO_ROOT/src/trees/kernel/xiaomi/mt6833" ]; then
    KERNEL_DIR="$REPO_ROOT/src/trees/kernel/xiaomi/mt6833"
else
    KERNEL_DIR="$REPO_ROOT/src/trees/kernel"
fi
OUT_DIR="$KERNEL_DIR/out"
BOOT_DIR="$OUT_DIR/arch/arm64/boot"

# ── Toolchain ─────────────────────────────────────────────────────────────────
TC_DIR="$HOME/toolchains/ZyC-clang-22.0.0"
TC_URL="https://github.com/ZyCromerZ/Clang/releases/download/22.0.0git-20250928-release/Clang-22.0.0git-20250928.tar.gz"

# ── Build config ──────────────────────────────────────────────────────────────
DEVICE="everpal"
DEFCONFIG="${DEVICE}_defconfig"
DATE=$(date '+%Y%m%d-%H%M')
KERNEL_ZIP="AquaKernel-${DATE}.zip"

# ── Flags ─────────────────────────────────────────────────────────────────────
BUILD_VULKAN=false
CLEAN_BUILD=false
INCLUDE_KSU=false

for arg in "$@"; do
    case $arg in
        --vulkan)    BUILD_VULKAN=true  ;;
        --clean)     CLEAN_BUILD=true   ;;
        --with-ksu)  INCLUDE_KSU=true   ;;
    esac
done

# ── Toolchain bootstrap ───────────────────────────────────────────────────────
if [ ! -d "$TC_DIR" ]; then
    echo "[*] Downloading ZyC Clang 22.0.0 to $TC_DIR ..."
    mkdir -p "$TC_DIR"
    wget -q --show-progress "$TC_URL" -O /tmp/zyc-clang.tar.gz
    tar xf /tmp/zyc-clang.tar.gz -C "$TC_DIR"
    rm -f /tmp/zyc-clang.tar.gz
    echo "[+] Toolchain ready."
fi

export PATH="$TC_DIR/bin:$PATH"
export CC=clang
export LD=ld.lld

echo
echo "Compiler: $(clang --version | head -1)"
echo

# ── Pre-build cleanup ─────────────────────────────────────────────────────────
cd "$KERNEL_DIR"

if [ "$CLEAN_BUILD" = true ]; then
    echo "[*] Cleaning out/ ..."
    rm -rf "$OUT_DIR"
fi

rm -rf .config .config.old .tmp_versions
rm -rf include/generated include/config arch/arm64/include/generated
rm -rf vmlinux* System.map modules.builtin* Module.symvers modules.order
rm -rf scripts/kconfig/.tmp*

# ── KernelSU / SUSFS integration ──────────────────────────────────────────────
KSU_FLAG_FILE="$OUT_DIR/.ksu_applied"

[ -f "$KSU_FLAG_FILE" ] && echo "[*] KernelSU already applied — skipping patching."

if [ "$INCLUDE_KSU" = true ] && [ ! -f "$KSU_FLAG_FILE" ]; then
    echo "[*] Applying ReSukiSU + SUSFS patches ..."
    curl -LSs "https://raw.githubusercontent.com/ReSukiSU/ReSukiSU/main/kernel/setup.sh" | bash
    git clone https://github.com/JackA1ltman/NonGKI_Kernel_Build_2nd.git --depth=1 SU_patch
    for patch in SU_patch/Patches/*sh; do
        bash "$patch"
    done
    patch -p1 < SU_patch/Patches/Patch/susfs_patch_to_4.14.patch
    wget -q https://raw.githubusercontent.com/Addster09/EverpalPatches/main/KSUPatches/defconfig-Enable-KSU-and-SUSFS.patch
    wget -q https://raw.githubusercontent.com/Addster09/EverpalPatches/main/KSUPatches/susfs_patch_taskmmu.patch
    patch -p1 < defconfig-Enable-KSU-and-SUSFS.patch
    patch -p1 < susfs_patch_taskmmu.patch
    rm -rf defconfig-Enable-KSU-and-SUSFS.patch susfs_patch_taskmmu.patch SU_patch
    mkdir -p "$OUT_DIR"
    touch "$KSU_FLAG_FILE"
    echo "[+] KernelSU + SUSFS applied."
fi

# ── Build ─────────────────────────────────────────────────────────────────────
mkdir -p "$OUT_DIR"
echo "[*] Generating defconfig: $DEFCONFIG"
make O=out ARCH=arm64 "$DEFCONFIG"

echo
echo "[*] Starting kernel compilation ($(nproc) threads) ..."
SECONDS=0

make -j"$(nproc)" O=out \
    ARCH=arm64 \
    CC="ccache clang" \
    LLVM=1 \
    LLVM_IAS=1 \
    CROSS_COMPILE=aarch64-linux-gnu- \
    CROSS_COMPILE_ARM32=arm-linux-gnueabi- \
    KCFLAGS="-Wno-error=default-const-init-var-unsafe" \
    Image.gz dtbs

ELAPSED=$SECONDS
echo
echo "[+] Kernel compiled in $((ELAPSED / 60))m $((ELAPSED % 60))s"

# Locate outputs
KERNEL_IMAGE="$BOOT_DIR/Image.gz"
DTBO_IMAGE="$BOOT_DIR/dtbo.img"

if [ ! -f "$KERNEL_IMAGE" ]; then
    echo "[!] Image.gz not found at $KERNEL_IMAGE — build may have failed."
    exit 1
fi

# ── Package ───────────────────────────────────────────────────────────────────
if [ "$BUILD_VULKAN" = true ]; then
    echo
    echo "[*] Building combined Vulkan 1.3 + Kernel zip via builder.py ..."

    DTBO_ARG=""
    [ -f "$DTBO_IMAGE" ] && DTBO_ARG="--dtbo $DTBO_IMAGE"

    python3 "$SCRIPT_DIR/builder.py" --vulkan \
        --kernel "$KERNEL_IMAGE" \
        $DTBO_ARG

    VULKAN_ZIP="$REPO_ROOT/src/package/Vulkan13/package/Vulkan13-KernelSU.zip"
    echo
    echo "[+] Done! Combined zip: $VULKAN_ZIP"
    echo "    Flash via KernelSU Manager or recovery (AnyKernel3 compatible)."
else
    echo
    echo "[*] Packaging kernel-only zip ..."
    git clone -q --depth=1 https://github.com/Addster09/AnyKernel3 AnyKernel3
    cp "$KERNEL_IMAGE" AnyKernel3/
    [ -f "$DTBO_IMAGE" ] && cp "$DTBO_IMAGE" AnyKernel3/
    (cd AnyKernel3 && zip -r9 "../$KERNEL_ZIP" . -x '*.git*' README.md '*placeholder')
    rm -rf AnyKernel3

    echo
    echo "[+] Done! Kernel zip: $KERNEL_DIR/$KERNEL_ZIP"
    echo "    Flash via TWRP / OrangeFox recovery."
fi
