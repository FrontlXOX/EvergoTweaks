# ===================================================|| XOX ||===================================================
# ===================================================|| XOX ||===================================================
#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
TREES_DIR="$SCRIPT_DIR"

info() { printf '\033[1;34m==>\033[0m %s\n' "$*"; }
ok()   { printf '\033[1;32m  ✓\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m  !\033[0m %s\n' "$*"; }

clone() {
    local url="$1" dest="$2" branch="${3:-}"
    local target_dir="$TREES_DIR/$dest"
    if [ -d "$target_dir/.git" ] || [ -f "$target_dir/.git" ]; then
        info "Skipping $dest (already exists)"
        return 0
    fi
    mkdir -p "$(dirname "$target_dir")"
    if [ -n "$branch" ]; then
        info "Cloning $url ($branch) -> src/trees/$dest"
        git clone "$url" "$target_dir" -b "$branch" --depth=1
    else
        info "Cloning $url -> src/trees/$dest"
        git clone "$url" "$target_dir" --depth=1
    fi
    ok "src/trees/$dest done"
}

TREES=(
    "src/trees/device/xiaomi/everpal|https://github.com/himanshuksr0007/device_xiaomi_everpal.git|src/trees/device/xiaomi/everpal|lineage-23.2"
    "src/trees/vendor/xiaomi/everpal|https://github.com/himanshuksr0007/vendor_xiaomi_everpal.git|src/trees/vendor/xiaomi/everpal|lineage-23.2"
    "src/trees/vendor/xiaomi/camera|https://github.com/himanshuksr0007/vendor_xiaomi_camera-everpal.git|src/trees/vendor/xiaomi/camera|lineage-23.2"
    "src/trees/kernel/xiaomi/mt6833|https://github.com/himanshuksr0007/android_kernel_xiaomi_mt6833.git|src/trees/kernel/xiaomi/mt6833|lineage-24.0"
    "src/trees/device/mediatek/sepolicy_vndr|https://github.com/FrontlXOX/android_device_mediatek_sepolicy_vndr.git|src/trees/device/mediatek/sepolicy_vndr|lineage-23.0"
    "src/trees/hardware/mediatek|https://github.com/FrontlXOX/android_hardware_mediatek.git|src/trees/hardware/mediatek|lineage-23.0"
    "src/trees/hardware/xiaomi|https://github.com/FrontlXOX/android_hardware_xiaomi.git|src/trees/hardware/xiaomi|lineage-23.0"
    "src/trees/vendor/mediatek/ims|https://github.com/FrontlXOX/android_vendor_mediatek_ims.git|src/trees/vendor/mediatek/ims|android-16-qpr2"
)

clone "https://github.com/himanshuksr0007/device_xiaomi_everpal.git"        "device/xiaomi/everpal"            "lineage-23.2"
clone "https://github.com/himanshuksr0007/vendor_xiaomi_everpal.git"        "vendor/xiaomi/everpal"            "lineage-23.2"
clone "https://github.com/himanshuksr0007/vendor_xiaomi_camera-everpal.git" "vendor/xiaomi/camera"            "lineage-23.2"
clone "https://github.com/himanshuksr0007/android_kernel_xiaomi_mt6833.git" "kernel/xiaomi/mt6833"             "lineage-24.0"
clone "https://github.com/FrontlXOX/android_device_mediatek_sepolicy_vndr.git" "device/mediatek/sepolicy_vndr" "lineage-23.0"
clone "https://github.com/FrontlXOX/android_hardware_mediatek.git"          "hardware/mediatek"              "lineage-23.0"
clone "https://github.com/FrontlXOX/android_hardware_xiaomi.git"            "hardware/xiaomi"                "lineage-23.0"
clone "https://github.com/FrontlXOX/android_vendor_mediatek_ims.git"        "vendor/mediatek/ims"              "android-16-qpr2"

ok "All everpal trees cloned."

MAKE_SUBMODULES="n"
if [ -t 0 ]; then
    read -rp "Make all trees git submodules of this repo? [y/N]: " MAKE_SUBMODULES || true
else
    info "Non-interactive shell, skipping submodule stage."
fi

MAKE_SUBMODULES="${MAKE_SUBMODULES:-n}"
if [[ "$MAKE_SUBMODULES" =~ ^[Yy]$ ]]; then
    if ! git -C "$REPO_ROOT" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
        warn "Not inside a git repo, cannot register submodules. Skipping."
    else
        register() {
            local name="$1" url="$2" relpath="$3" branch="${4:-}"
            local abs_path="$REPO_ROOT/$relpath"
            if git -C "$REPO_ROOT" config -f .gitmodules --get "submodule.${name}.url" >/dev/null 2>&1; then
                info "Submodule '$name' already registered, skipping"
                return 0
            fi
            if [ ! -e "$abs_path/.git" ]; then
                warn "No git repo at $abs_path, skipping"
                return 0
            fi
            info "Registering submodule '$name' -> $relpath"
            git -C "$REPO_ROOT" config -f .gitmodules "submodule.${name}.path" "$relpath"
            git -C "$REPO_ROOT" config -f .gitmodules "submodule.${name}.url" "$url"
            [ -n "$branch" ] && git -C "$REPO_ROOT" config -f .gitmodules "submodule.${name}.branch" "$branch"
            git -C "$REPO_ROOT" config -f .gitmodules "submodule.${name}.ignore" "dirty"
            git -C "$REPO_ROOT" add "$relpath" 2>/dev/null || true
            git -C "$REPO_ROOT" config "submodule.${name}.url" "$url"
            git -C "$REPO_ROOT" config "submodule.${name}.active" "true"
            git -C "$REPO_ROOT" submodule absorbgitdirs -- "$relpath" 2>/dev/null || true
            ok "'$name' registered"
        }
        for entry in "${TREES[@]}"; do
            IFS='|' read -r name url path branch <<< "$entry"
            register "$name" "$url" "$path" "$branch"
        done
        ok "Submodule stage done. Check with: git submodule status"
    fi
else
    info "Keeping trees as plain clones."
fi
# ===================================================|| XOX ||===================================================
# ===================================================|| XOX ||===================================================
