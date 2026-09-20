### AnyKernel3 Ramdisk Mod & KernelSU Vulkan 1.3 Installer Script
## Architecture: MediaTek MT6833P / Dimensity 810 (everpal / evergo)
## Author: Shovit Dutta & Addster09
## Module Author: FrontlXOX

### AnyKernel setup
# global properties
properties() { '
kernel.string=Everpal: Aqua Kernel (Vulkan 1.3 Enhanced) by Addster09 x Shovit Dutta
do.devicecheck=1
do.modules=0
do.systemless=1
do.cleanup=1
do.cleanuponabort=1
device.name1=everpal
device.name2=evergo
device.name3=missi
device.name4=light
device.name5=camellia
supported.versions=11-16
'; } # end properties

# boot shell variables
block=boot;
is_slot_device=auto;
ramdisk_compression=auto;
patch_vbmeta_flag=auto;
no_block_display=1;

# import functions/variables and setup patching - see for reference (DO NOT REMOVE)
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

# 2. KernelSU / Magisk Systemless Vendor Overlay Injection
ui_print " ";
ui_print "── Installing Vulkan 1.3 HAL & Vendor Overlay ──";
if [ -d /data/adb/modules ]; then
    MODDIR=/data/adb/modules/everpal-vulkan13
    rm -rf $MODDIR
    mkdir -p $MODDIR
    cp -af $home/module.prop $MODDIR/
    cp -af $home/system.prop $MODDIR/
    if [ -d $home/system ]; then
        cp -af $home/system $MODDIR/
    fi
    touch $MODDIR/auto_mount
    set_perm_recursive $MODDIR 0 0 755 644
    ui_print "- KernelSU vendor overlay active at $MODDIR";
    ui_print "- Vulkan 1.3 ICD, EGL, and permissions XML armed.";
else
    ui_print "- /data/adb/modules not found (flashing from pure recovery without root).";
    ui_print "- Please install module via KernelSU Manager after booting.";
fi;

ui_print " ";
ui_print "── Everpal Vulkan 1.3 Installation Complete! Reboot to activate. ──";
## end boot install
