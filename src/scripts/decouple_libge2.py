import os

# 1. Patch 64-bit libVK13_mali.so
p_vk64 = 'package/templates/Vulkan13/system/vendor/lib64/egl/libVK13_mali.so'
with open(p_vk64, 'rb') as f:
    d = bytearray(f.read())
if b'libged.so\x00' in d:
    d = d.replace(b'libged.so\x00', b'libge2.so\x00')
    with open(p_vk64, 'wb') as f:
        f.write(d)
    print('[+] Patched 64-bit libVK13_mali.so DT_NEEDED -> libge2.so')
else:
    print('[-] 64-bit libVK13_mali.so already patched or libged.so not found')

# 2. Patch 32-bit libVK13_mali.so
p_vk32 = 'package/templates/Vulkan13/system/vendor/lib/egl/libVK13_mali.so'
with open(p_vk32, 'rb') as f:
    d = bytearray(f.read())
if b'libged.so\x00' in d:
    d = d.replace(b'libged.so\x00', b'libge2.so\x00')
    with open(p_vk32, 'wb') as f:
        f.write(d)
    print('[+] Patched 32-bit libVK13_mali.so DT_NEEDED -> libge2.so')
else:
    print('[-] 32-bit libVK13_mali.so already patched or libged.so not found')

# 3. Patch and rename 64-bit libged.so -> libge2.so
p_ged64 = 'package/templates/Vulkan13/system/vendor/lib64/libged.so'
p_ge2_64 = 'package/templates/Vulkan13/system/vendor/lib64/libge2.so'
if os.path.exists(p_ged64):
    with open(p_ged64, 'rb') as f:
        d = bytearray(f.read())
    d = d.replace(b'libged.so\x00', b'libge2.so\x00')
    with open(p_ge2_64, 'wb') as f:
        f.write(d)
    os.remove(p_ged64)
    print('[+] Created 64-bit libge2.so and removed libged.so')

# 4. Patch and rename 32-bit libged.so -> libge2.so
p_ged32 = 'package/templates/Vulkan13/system/vendor/lib/libged.so'
p_ge2_32 = 'package/templates/Vulkan13/system/vendor/lib/libge2.so'
if os.path.exists(p_ged32):
    with open(p_ged32, 'rb') as f:
        d = bytearray(f.read())
    d = d.replace(b'libged.so\x00', b'libge2.so\x00')
    with open(p_ge2_32, 'wb') as f:
        f.write(d)
    os.remove(p_ged32)
    print('[+] Created 32-bit libge2.so and removed libged.so')
