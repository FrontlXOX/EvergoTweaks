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

log -t "$TAG" "System boot completed. Verifying Vulkan 1.3 driver binding..."

# 1. Audit Driver Inode & Availability
NEED_HEAL=0
if [ ! -f /vendor/lib64/hw/vulkan.mali.so ] || [ ! -f /vendor/lib64/egl/libVK13_mali.so ]; then
    NEED_HEAL=1
fi

# Verify driver version via dumpsys gpu
VK_VER="$(dumpsys gpu 2>/dev/null | grep -E 'vulkanVersion.*=.*' | head -n1 | cut -d= -f2 | tr -d ' ')"
if [ "$VK_VER" != "4206592" ]; then
    log -t "$TAG" "Detected Vulkan version code: '$VK_VER' (Expected: 4206592 / 1.3.0). Self-healing triggered."
    NEED_HEAL=1
else
    log -t "$TAG" "Vulkan 1.3.0 (0x00403000) verified active in SurfaceFlinger."
fi

# 2. Self-Healing Execution if Mounts were dropped or missing
if [ "$NEED_HEAL" -eq 1 ]; then
    log -t "$TAG" "Executing emergency self-healing remount..."
    MODDIR=${0%/*}
    if [ -x "$MODDIR/post-fs-data.sh" ]; then
        sh "$MODDIR/post-fs-data.sh"
    elif [ -x /data/adb/post-fs-data.d/everpal-vulkan13.sh ]; then
        sh /data/adb/post-fs-data.d/everpal-vulkan13.sh
    fi

    # Soft-reload SurfaceFlinger to rebind graphics HAL without rebooting
    log -t "$TAG" "Signaling SurfaceFlinger to re-enumerate Vulkan ICD..."
    killall -9 surfaceflinger 2>/dev/null || (stop surfaceflinger && start surfaceflinger)
fi

# 3. Final SELinux Audit
chcon -h u:object_r:same_process_hal_file:s0 /vendor/lib64/hw/vulkan*.so 2>/dev/null
chcon -h u:object_r:same_process_hal_file:s0 /vendor/lib64/egl/lib* 2>/dev/null
chcon -h u:object_r:same_process_hal_file:s0 /vendor/lib64/libge2.so 2>/dev/null
chcon -h u:object_r:same_process_hal_file:s0 /vendor/lib64/libgpd1.so 2>/dev/null
chcon -h u:object_r:vendor_configs_file:s0 /vendor/etc/permissions/android.*vulkan*.xml 2>/dev/null

log -t "$TAG" "Vulkan 1.3 watchdog finished. Log preserved at $LOG_FILE."
