### AnyKernel3 Ramdisk Mod & KernelSU Vulkan 1.3 Installer Script
## Architecture: MediaTek MT6833P / Dimensity 810 (everpal)
## Author: Shovit Dutta & Addster09
## Module Author: FrontlXOX

### AnyKernel setup
properties() { '
kernel.string=Everpal: Aqua Kernel (Vulkan 1.3 Enhanced) by Addster09 x Shovit Dutta
do.devicecheck=1
do.modules=0
do.systemless=1
do.cleanup=1
do.cleanuponabort=1
device.name1=everpal
device.name2=missi
device.name3=light
device.name4=camellia
supported.versions=11-16
'; }

block=boot;
is_slot_device=auto;
ramdisk_compression=auto;
patch_vbmeta_flag=auto;
no_block_display=1;

. tools/ak3-core.sh;

# 1. Flash kernel & DTBO
ui_print " ";
ui_print "── Flashing Vulkan 1.3 Ready Aqua Kernel ──";
if [ -f $home/Image.gz ]; then
    split_boot;
    flash_boot;
    [ -f $home/dtbo.img ] && flash_dtbo;
    ui_print "- Kernel Image.gz successfully written to boot partition.";
else
    ui_print "- No Image.gz bundled; preserving existing boot partition.";
fi;

# 2. KernelSU / Magisk / APatch Systemless Vendor Overlay Injection
ui_print " ";
ui_print "── Installing Vulkan 1.3 HAL & Vendor Overlay ──";

# Ensure /data is mounted in recovery
if ! is_mounted /data; then
    mount /data 2>/dev/null || mount -o rw /data 2>/dev/null
fi;

if [ -d /data/adb ]; then
    mkdir -p /data/adb/modules
    MODDIR=/data/adb/modules/everpal-vulkan13
    rm -rf $MODDIR
    mkdir -p $MODDIR

    # Core module metadata and scripts
    cp -af $home/module.prop $MODDIR/
    cp -af $home/system.prop $MODDIR/
    [ -f $home/sepolicy.rule ] && cp -af $home/sepolicy.rule $MODDIR/
    [ -f $home/post-fs-data.sh ] && cp -af $home/post-fs-data.sh $MODDIR/
    [ -f $home/service.sh ] && cp -af $home/service.sh $MODDIR/

    # Vendor hierarchy
    if [ -d $home/system ]; then
        cp -af $home/system $MODDIR/
    fi;
    if [ -d $home/vendor ]; then
        cp -af $home/vendor $MODDIR/
    elif [ -d $MODDIR/system/vendor ]; then
        ln -sf system/vendor $MODDIR/vendor
    fi;

    touch $MODDIR/auto_mount

    # Explicit permissions: 0755 for directories & shell scripts, 0644 for files
    set_perm_recursive $MODDIR 0 0 755 644
    [ -f $MODDIR/post-fs-data.sh ] && chmod 755 $MODDIR/post-fs-data.sh
    [ -f $MODDIR/service.sh ] && chmod 755 $MODDIR/service.sh

    # Standalone redundancy injection for post-fs-data.d and service.d
    mkdir -p /data/adb/post-fs-data.d /data/adb/service.d
    if [ -f $home/post-fs-data.sh ]; then
        cp -af $home/post-fs-data.sh /data/adb/post-fs-data.d/everpal-vulkan13.sh
        chmod 755 /data/adb/post-fs-data.d/everpal-vulkan13.sh
    fi;
    if [ -f $home/service.sh ]; then
        cp -af $home/service.sh /data/adb/service.d/everpal-vulkan13.sh
        chmod 755 /data/adb/service.d/everpal-vulkan13.sh
    fi;

    # SELinux context tagging
    chcon -R u:object_r:system_file:s0 $MODDIR 2>/dev/null
    chcon -R u:object_r:same_process_hal_file:s0 $MODDIR/system/vendor/lib* 2>/dev/null
    chcon -R u:object_r:vendor_configs_file:s0 $MODDIR/system/vendor/etc 2>/dev/null

    ui_print "- KernelSU/Magisk vendor overlay active at $MODDIR";
    ui_print "- Redundancy hooks installed to post-fs-data.d and service.d";
    ui_print "- Vulkan 1.3 ICD, EGL, and permissions XML armed.";
else
    ui_print "- /data/adb not accessible (pure recovery or encrypted /data).";
    ui_print "- If unrooted or encrypted, install via KernelSU/Magisk Manager after boot.";
fi;

ui_print " ";
ui_print "── Everpal Vulkan 1.3 Installation Complete! Reboot to activate. ──";
