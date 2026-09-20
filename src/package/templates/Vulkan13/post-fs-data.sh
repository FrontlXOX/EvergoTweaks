#!/system/bin/sh
MODDIR=${0%/*}
TAG="[Everpal-Vulkan13-PostFS]"
MIRROR_BASE="/dev/vulkan13_mirror"

log -t "$TAG" "Initializing Vulkan 1.3 mount engine..."

# Detect source directory
if [ -d "$MODDIR/system/vendor" ]; then
    SRC_DIR="$MODDIR/system/vendor"
elif [ -d "$MODDIR/vendor" ]; then
    SRC_DIR="$MODDIR/vendor"
elif [ -d "/data/adb/modules/everpal-vulkan13/system/vendor" ]; then
    SRC_DIR="/data/adb/modules/everpal-vulkan13/system/vendor"
elif [ -d "/data/adb/modules/everpal-vulkan13/vendor" ]; then
    SRC_DIR="/data/adb/modules/everpal-vulkan13/vendor"
else
    SRC_DIR=""
fi

if [ -z "$SRC_DIR" ]; then
    log -t "$TAG" "ERROR: Source vendor directory not found. Aborting."
    exit 1
fi

# Pre-mount SELinux context tagging on source backing files
# Prevents EROFS failures and ensures proper SP-HAL labeling before read-only bind mounts lock inodes
chcon -R u:object_r:same_process_hal_file:s0 "$SRC_DIR/lib"* 2>/dev/null
chcon -R u:object_r:same_process_hal_file:s0 "$SRC_DIR/etc/mali_platform.config" 2>/dev/null
chcon -R u:object_r:vendor_configs_file:s0 "$SRC_DIR/etc/permissions" 2>/dev/null
chcon -R u:object_r:vendor_configs_file:s0 "$SRC_DIR/etc/gralloc" 2>/dev/null

# 1. Early Property Enforcement via resetprop
for p in \
    "ro.hardware.vulkan=mali" \
    "ro.vendor.arm.egl.configs.r8_g8_b8_a8_32bit_fixed.hal_format=0x1" \
    "ro.vendor.arm.egl.configs.r8_g8_b8_a8_32bit_fixed.recordable=true" \
    "ro.vendor.arm.egl.configs.r8_g8_b8_a8_32bit_fixed.framebuffer_target=false" \
    "ro.vendor.arm.egl.configs.r8_g8_b8_a0_32bit_fixed.hal_format=0x2" \
    "ro.vendor.arm.egl.configs.r8_g8_b8_a0_32bit_fixed.recordable=false" \
    "ro.vendor.arm.egl.configs.r8_g8_b8_a0_32bit_fixed.framebuffer_target=false" \
    "ro.vendor.arm.egl.configs.r8_g8_b8_a0_24bit_fixed.hal_format=0x2" \
    "ro.vendor.arm.egl.configs.r8_g8_b8_a0_24bit_fixed.recordable=false" \
    "ro.vendor.arm.egl.configs.r8_g8_b8_a0_24bit_fixed.framebuffer_target=false" \
    "ro.vendor.arm.egl.configs.r5_g6_b5_a0_16bit_fixed.hal_format=0x4" \
    "ro.vendor.arm.egl.configs.r5_g6_b5_a0_16bit_fixed.recordable=false" \
    "ro.vendor.arm.egl.configs.r5_g6_b5_a0_16bit_fixed.framebuffer_target=false" \
    "ro.vendor.arm.egl.configs.r10_g10_b10_a2_32bit_fixed.hal_format=0x2b" \
    "ro.vendor.arm.egl.configs.r10_g10_b10_a2_32bit_fixed.recordable=false" \
    "ro.vendor.arm.egl.configs.r10_g10_b10_a2_32bit_fixed.framebuffer_target=false" \
    "ro.vendor.arm.egl.configs.r16_g16_b16_a16_64bit_float.hal_format=0x16" \
    "ro.vendor.arm.egl.configs.r16_g16_b16_a16_64bit_float.recordable=false" \
    "ro.vendor.arm.egl.configs.r16_g16_b16_a16_64bit_float.framebuffer_target=false" \
    "ro.vendor.arm.egl.configs.r8_g8_b8_a0_24bit_yuv_special.hal_format=0x23" \
    "ro.vendor.arm.egl.configs.r8_g8_b8_a0_24bit_yuv_special.framebuffer_target=false"; do
    key="${p%%=*}"
    val="${p#*=}"
    resetprop -n "$key" "$val" 2>/dev/null
done

# Helper: Atomic individual file bind mount
bind_file() {
    local src="$1" dst="$2"
    if [ -f "$src" ] && [ -e "$dst" ]; then
        mount -o bind "$src" "$dst" 2>/dev/null
        return $?
    fi
    return 1
}

# Helper: Bulletproof Directory Overlay / Tmpfs Mirror (Universal EROFS & ext4 solution)
overlay_or_mirror_dir() {
    local src_dir="$1" dst_dir="$2" scontext="$3" mirror_sub="$4"
    [ ! -d "$src_dir" ] && return 0
    [ ! -d "$dst_dir" ] && return 0

    # Strategy A: Kernel OverlayFS (atomic SELinux context on read-only lowerdirs)
    if mount -t overlay overlay -o lowerdir="$src_dir:$dst_dir",context="$scontext" "$dst_dir" 2>/dev/null; then
        log -t "$TAG" "OverlayFS mount successful on $dst_dir"
        return 0
    fi

    # Strategy B: Tmpfs Mirror Mount (Universal EROFS Fallback)
    local staging="$MIRROR_BASE/$mirror_sub"
    rm -rf "$staging" 2>/dev/null
    mkdir -p "$staging"
    cp -af "$dst_dir"/* "$staging"/ 2>/dev/null
    cp -af "$src_dir"/* "$staging"/ 2>/dev/null
    chown -R 0:0 "$staging" 2>/dev/null
    chmod 755 "$staging"
    chcon -R "$scontext" "$staging" 2>/dev/null

    if mount -o bind "$staging" "$dst_dir" 2>/dev/null; then
        mount -o bind,remount,ro "$dst_dir" 2>/dev/null
        chcon -h "$scontext" "$dst_dir" 2>/dev/null
        log -t "$TAG" "Tmpfs mirror mount successful on $dst_dir (read-only secured)"
        return 0
    fi

    log -t "$TAG" "WARNING: Failed to overlay/mirror $dst_dir"
    return 1
}

mkdir -p "$MIRROR_BASE" 2>/dev/null

# 2. 64-bit Core HAL Binaries (Direct Inode Bind-Mount for existing files)
bind_file "$SRC_DIR/lib64/hw/vulkan.mali.so" /vendor/lib64/hw/vulkan.mali.so
bind_file "$SRC_DIR/lib64/hw/vulkan.mt6833.so" /vendor/lib64/hw/vulkan.mt6833.so

# 3. 64-bit EGL & Decoupled Libraries via Directory Overlay/Mirror
# Also stage libge2.so & libgpd1.so into egl/ to satisfy SP-HAL linker search
mkdir -p "$SRC_DIR/lib64/egl" 2>/dev/null
[ -f "$SRC_DIR/lib64/libge2.so" ] && cp -af "$SRC_DIR/lib64/libge2.so" "$SRC_DIR/lib64/egl/" 2>/dev/null
[ -f "$SRC_DIR/lib64/libgpd1.so" ] && cp -af "$SRC_DIR/lib64/libgpd1.so" "$SRC_DIR/lib64/egl/" 2>/dev/null

overlay_or_mirror_dir "$SRC_DIR/lib64/egl" /vendor/lib64/egl "u:object_r:same_process_hal_file:s0" "lib64_egl"

# Bind libge2 / libgpd1 directly into /vendor/lib64 if target exists
bind_file "$SRC_DIR/lib64/libge2.so" /vendor/lib64/libge2.so
bind_file "$SRC_DIR/lib64/libgpd1.so" /vendor/lib64/libgpd1.so

# 4. 32-bit Compatibility Layer (Gracefully skipped on 64-bit-only ROMs)
if [ -d /vendor/lib ]; then
    bind_file "$SRC_DIR/lib/hw/vulkan.mali.so" /vendor/lib/hw/vulkan.mali.so
    bind_file "$SRC_DIR/lib/hw/vulkan.mt6833.so" /vendor/lib/hw/vulkan.mt6833.so
    bind_file "$SRC_DIR/lib/libge2.so" /vendor/lib/libge2.so
    bind_file "$SRC_DIR/lib/libgpd1.so" /vendor/lib/libgpd1.so

    if [ -d /vendor/lib/egl ]; then
        mkdir -p "$SRC_DIR/lib/egl" 2>/dev/null
        [ -f "$SRC_DIR/lib/libge2.so" ] && cp -af "$SRC_DIR/lib/libge2.so" "$SRC_DIR/lib/egl/" 2>/dev/null
        [ -f "$SRC_DIR/lib/libgpd1.so" ] && cp -af "$SRC_DIR/lib/libgpd1.so" "$SRC_DIR/lib/egl/" 2>/dev/null
        overlay_or_mirror_dir "$SRC_DIR/lib/egl" /vendor/lib/egl "u:object_r:same_process_hal_file:s0" "lib_egl"
    fi
fi

# 5. Configuration & Hardware Permissions (Overlay / Mirror)
bind_file "$SRC_DIR/etc/mali_platform.config" /vendor/etc/mali_platform.config
overlay_or_mirror_dir "$SRC_DIR/etc/permissions" /vendor/etc/permissions "u:object_r:vendor_configs_file:s0" "etc_permissions"
overlay_or_mirror_dir "$SRC_DIR/etc/gralloc" /vendor/etc/gralloc "u:object_r:vendor_configs_file:s0" "etc_gralloc"

# 6. Final SELinux Context Hardening
chcon -h u:object_r:same_process_hal_file:s0 /vendor/lib64/hw/vulkan*.so 2>/dev/null
chcon -h u:object_r:same_process_hal_file:s0 /vendor/lib64/egl/lib* 2>/dev/null
chcon -h u:object_r:same_process_hal_file:s0 /vendor/lib64/libge2.so 2>/dev/null
chcon -h u:object_r:same_process_hal_file:s0 /vendor/lib64/libgpd1.so 2>/dev/null
chcon -h u:object_r:same_process_hal_file:s0 /vendor/etc/mali_platform.config 2>/dev/null
chcon -h u:object_r:vendor_configs_file:s0 /vendor/etc/permissions/android.*vulkan*.xml 2>/dev/null
chcon -h u:object_r:vendor_configs_file:s0 /vendor/etc/gralloc/*.xml 2>/dev/null

log -t "$TAG" "Vulkan 1.3 mount engine execution completed."
