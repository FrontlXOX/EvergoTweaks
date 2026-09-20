#!/system/bin/sh
MODDIR=${0%/*}

# Set SELinux contexts on module files
chcon -R u:object_r:same_process_hal_file:s0 "$MODDIR/system/vendor/lib" 2>/dev/null
chcon -R u:object_r:same_process_hal_file:s0 "$MODDIR/system/vendor/lib64" 2>/dev/null
chcon -R u:object_r:same_process_hal_file:s0 "$MODDIR/system/vendor/etc/mali_platform.config" 2>/dev/null
chcon -R u:object_r:vendor_configs_file:s0 "$MODDIR/system/vendor/etc/permissions" 2>/dev/null
chcon -R u:object_r:vendor_configs_file:s0 "$MODDIR/system/vendor/etc/gralloc" 2>/dev/null

# Also enforce contexts on live /vendor mountpoints
chcon -h -R u:object_r:same_process_hal_file:s0 /vendor/lib64/egl 2>/dev/null
chcon -h -R u:object_r:same_process_hal_file:s0 /vendor/lib64/hw 2>/dev/null
chcon -h -R u:object_r:same_process_hal_file:s0 /vendor/lib64/*mali* 2>/dev/null
chcon -h -R u:object_r:same_process_hal_file:s0 /vendor/lib64/*gpu* 2>/dev/null
chcon -h -R u:object_r:same_process_hal_file:s0 /vendor/lib64/*ged* 2>/dev/null
chcon -h -R u:object_r:same_process_hal_file:s0 /vendor/lib64/*mms* 2>/dev/null
chcon -h -R u:object_r:same_process_hal_file:s0 /vendor/lib64/*gpd* 2>/dev/null

chcon -h -R u:object_r:same_process_hal_file:s0 /vendor/lib/egl 2>/dev/null
chcon -h -R u:object_r:same_process_hal_file:s0 /vendor/lib/hw 2>/dev/null
chcon -h -R u:object_r:same_process_hal_file:s0 /vendor/lib/*mali* 2>/dev/null
chcon -h -R u:object_r:same_process_hal_file:s0 /vendor/lib/*gpu* 2>/dev/null
chcon -h -R u:object_r:same_process_hal_file:s0 /vendor/lib/*ged* 2>/dev/null
chcon -h -R u:object_r:same_process_hal_file:s0 /vendor/lib/*mms* 2>/dev/null
chcon -h -R u:object_r:same_process_hal_file:s0 /vendor/lib/*gpd* 2>/dev/null

chcon -h -R u:object_r:same_process_hal_file:s0 /vendor/etc/mali_platform.config 2>/dev/null
chcon -h -R u:object_r:vendor_configs_file:s0 /vendor/etc/permissions/android.hardware.vulkan*.xml 2>/dev/null
chcon -h -R u:object_r:vendor_configs_file:s0 /vendor/etc/permissions/android.software.vulkan*.xml 2>/dev/null
chcon -h -R u:object_r:vendor_configs_file:s0 /vendor/etc/gralloc 2>/dev/null


