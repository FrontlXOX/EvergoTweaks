#!/system/bin/sh
# service.sh — Everpal Vulkan 1.3 Late-Start Watchdog & Self-Healing Service
TAG="[Everpal-Vulkan13-Watchdog]"
LOG_FILE="/dev/everpal_vulkan13.log"

exec > "$LOG_FILE" 2>&1
log -t "$TAG" "Starting Vulkan 1.3 boot completion watchdog..."

# Await boot completion (up to 60s)
TIMEOUT=60
COUNT=0
while [ "$COUNT" -lt "$TIMEOUT" ]; do
    if [ "$(getprop sys.boot_completed)" = "1" ]; then
        break
    fi
    sleep 1
    COUNT=$((COUNT + 1))
done

# Allow framework services 3 seconds to finalize graphics enumeration
sleep 3
log -t "$TAG" "System boot completed. Auditing Vulkan 1.3 driver binding..."

# 1. Audit Driver Inode & Availability
NEED_HEAL=0
if [ ! -f /vendor/lib64/hw/vulkan.mali.so ] || [ ! -f /vendor/lib64/egl/libVK13_mali.so ]; then
    log -t "$TAG" "Warning: Core Vulkan 1.3 library endpoints missing from /vendor."
    NEED_HEAL=1
fi

# Audit driver version via dumpsys gpu
VK_VER="$(dumpsys gpu 2>/dev/null | grep -E 'vulkanVersion.*=.*' | head -n1 | cut -d= -f2 | tr -d ' ')"
if [ "$VK_VER" = "4206592" ]; then
    log -t "$TAG" "Vulkan 1.3.0 (0x00403000) verified active in SurfaceFlinger."
else
    log -t "$TAG" "Notice: dumpsys gpu reported vulkanVersion='$VK_VER'. Checking mounts."
    if [ ! -f /vendor/lib64/egl/libVK13_mali.so ]; then
        NEED_HEAL=1
    fi
fi

# 2. Safe Self-Healing Execution (Preserves SurfaceFlinger stability, zero RescueParty risk)
if [ "$NEED_HEAL" -eq 1 ]; then
    log -t "$TAG" "Re-executing mount engine in global mount namespace..."
    MODDIR=${0%/*}
    SCRIPT=""
    if [ -x "$MODDIR/post-fs-data.sh" ]; then
        SCRIPT="$MODDIR/post-fs-data.sh"
    fi

    if [ -n "$SCRIPT" ]; then
        if [ -x /system/bin/nsenter ] && [ -e /proc/1/ns/mnt ]; then
            nsenter --mount=/proc/1/ns/mnt sh "$SCRIPT" 2>&1
        else
            sh "$SCRIPT" 2>&1
        fi
    fi
fi

# 3. Final SELinux Audit
chcon -h u:object_r:same_process_hal_file:s0 /vendor/lib64/hw/vulkan*.so 2>/dev/null
chcon -h u:object_r:same_process_hal_file:s0 /vendor/lib64/egl/lib* 2>/dev/null
chcon -h u:object_r:same_process_hal_file:s0 /vendor/lib64/libge2.so 2>/dev/null
chcon -h u:object_r:same_process_hal_file:s0 /vendor/lib64/libgpd1.so 2>/dev/null
chcon -h u:object_r:vendor_configs_file:s0 /vendor/etc/permissions/android.*vulkan*.xml 2>/dev/null

log -t "$TAG" "Vulkan 1.3 watchdog finished safely. Log preserved at $LOG_FILE."
