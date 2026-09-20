#!/system/bin/sh
MODDIR=${0%/*}

# Detect source directory: either $MODDIR/vendor or $MODDIR/system/vendor
if [ -d "$MODDIR/vendor" ]; then
    SRC_DIR="$MODDIR/vendor"
elif [ -d "$MODDIR/system/vendor" ]; then
    SRC_DIR="$MODDIR/system/vendor"
elif [ -d "/data/adb/modules/everpal-vulkan13/vendor" ]; then
    SRC_DIR="/data/adb/modules/everpal-vulkan13/vendor"
elif [ -d "/data/adb/modules/everpal-vulkan13/system/vendor" ]; then
    SRC_DIR="/data/adb/modules/everpal-vulkan13/system/vendor"
else
    SRC_DIR=""
fi

if [ -n "$SRC_DIR" ]; then
    # Ensure placeholder files exist on /vendor (read-write remount if needed)
    NEED_RW=0
    for target in \
        /vendor/lib64/egl/libVK13_mali.so \
        /vendor/lib64/libge2.so \
        /vendor/lib64/libgpd1.so \
        /vendor/lib/egl/libVK13_mali.so \
        /vendor/lib/hw/vulkan.mali.so \
        /vendor/lib/hw/vulkan.mt6833.so \
        /vendor/lib/libge2.so \
        /vendor/lib/libgpd1.so \
        /vendor/etc/mali_platform.config; do
        if [ ! -e "$target" ]; then
            NEED_RW=1
            break
        fi
    done

    if [ "$NEED_RW" -eq 1 ]; then
        mount -o remount,rw /vendor 2>/dev/null
        mkdir -p /vendor/lib/hw 2>/dev/null
        mkdir -p /vendor/lib/egl 2>/dev/null
        touch /vendor/lib64/egl/libVK13_mali.so 2>/dev/null
        touch /vendor/lib64/libge2.so 2>/dev/null
        touch /vendor/lib64/libgpd1.so 2>/dev/null
        touch /vendor/lib/egl/libVK13_mali.so 2>/dev/null
        touch /vendor/lib/hw/vulkan.mali.so 2>/dev/null
        touch /vendor/lib/hw/vulkan.mt6833.so 2>/dev/null
        touch /vendor/lib/libge2.so 2>/dev/null
        touch /vendor/lib/libgpd1.so 2>/dev/null
        touch /vendor/etc/mali_platform.config 2>/dev/null
        mount -o remount,ro /vendor 2>/dev/null
    fi

    # Bind-mount 64-bit binaries
    [ -f "$SRC_DIR/lib64/hw/vulkan.mali.so" ] && [ -e /vendor/lib64/hw/vulkan.mali.so ] && mount -o bind "$SRC_DIR/lib64/hw/vulkan.mali.so" /vendor/lib64/hw/vulkan.mali.so
    [ -f "$SRC_DIR/lib64/hw/vulkan.mt6833.so" ] && [ -e /vendor/lib64/hw/vulkan.mt6833.so ] && mount -o bind "$SRC_DIR/lib64/hw/vulkan.mt6833.so" /vendor/lib64/hw/vulkan.mt6833.so
    [ -f "$SRC_DIR/lib64/egl/libVK13_mali.so" ] && [ -e /vendor/lib64/egl/libVK13_mali.so ] && mount -o bind "$SRC_DIR/lib64/egl/libVK13_mali.so" /vendor/lib64/egl/libVK13_mali.so
    [ -f "$SRC_DIR/lib64/libge2.so" ] && [ -e /vendor/lib64/libge2.so ] && mount -o bind "$SRC_DIR/lib64/libge2.so" /vendor/lib64/libge2.so
    [ -f "$SRC_DIR/lib64/libgpd1.so" ] && [ -e /vendor/lib64/libgpd1.so ] && mount -o bind "$SRC_DIR/lib64/libgpd1.so" /vendor/lib64/libgpd1.so

    # Bind-mount 32-bit binaries
    [ -f "$SRC_DIR/lib/hw/vulkan.mali.so" ] && [ -e /vendor/lib/hw/vulkan.mali.so ] && mount -o bind "$SRC_DIR/lib/hw/vulkan.mali.so" /vendor/lib/hw/vulkan.mali.so
    [ -f "$SRC_DIR/lib/hw/vulkan.mt6833.so" ] && [ -e /vendor/lib/hw/vulkan.mt6833.so ] && mount -o bind "$SRC_DIR/lib/hw/vulkan.mt6833.so" /vendor/lib/hw/vulkan.mt6833.so
    [ -f "$SRC_DIR/lib/libge2.so" ] && [ -e /vendor/lib/libge2.so ] && mount -o bind "$SRC_DIR/lib/libge2.so" /vendor/lib/libge2.so
    [ -f "$SRC_DIR/lib/libgpd1.so" ] && [ -e /vendor/lib/libgpd1.so ] && mount -o bind "$SRC_DIR/lib/libgpd1.so" /vendor/lib/libgpd1.so

    # Bind-mount configs and permission feature XMLs
    [ -f "$SRC_DIR/etc/mali_platform.config" ] && [ -e /vendor/etc/mali_platform.config ] && mount -o bind "$SRC_DIR/etc/mali_platform.config" /vendor/etc/mali_platform.config
    [ -f "$SRC_DIR/etc/permissions/android.hardware.vulkan.version.xml" ] && [ -e /vendor/etc/permissions/android.hardware.vulkan.version.xml ] && mount -o bind "$SRC_DIR/etc/permissions/android.hardware.vulkan.version.xml" /vendor/etc/permissions/android.hardware.vulkan.version.xml
    [ -f "$SRC_DIR/etc/permissions/android.software.vulkan.deqp.level.xml" ] && [ -e /vendor/etc/permissions/android.software.vulkan.deqp.level.xml ] && mount -o bind "$SRC_DIR/etc/permissions/android.software.vulkan.deqp.level.xml" /vendor/etc/permissions/android.software.vulkan.deqp.level.xml
fi

# Set SELinux contexts on mounted endpoints
chcon -h u:object_r:same_process_hal_file:s0 /vendor/lib64/hw/vulkan*.so 2>/dev/null
chcon -h u:object_r:same_process_hal_file:s0 /vendor/lib64/egl/libVK13_mali.so 2>/dev/null
chcon -h u:object_r:same_process_hal_file:s0 /vendor/lib64/libge2.so 2>/dev/null
chcon -h u:object_r:same_process_hal_file:s0 /vendor/lib64/libgpd1.so 2>/dev/null
chcon -h u:object_r:same_process_hal_file:s0 /vendor/lib/hw/vulkan*.so 2>/dev/null
chcon -h u:object_r:same_process_hal_file:s0 /vendor/lib/libge2.so 2>/dev/null
chcon -h u:object_r:same_process_hal_file:s0 /vendor/lib/libgpd1.so 2>/dev/null
chcon -h u:object_r:same_process_hal_file:s0 /vendor/etc/mali_platform.config 2>/dev/null
chcon -h u:object_r:vendor_configs_file:s0 /vendor/etc/permissions/android.hardware.vulkan*.xml 2>/dev/null
chcon -h u:object_r:vendor_configs_file:s0 /vendor/etc/permissions/android.software.vulkan*.xml 2>/dev/null
