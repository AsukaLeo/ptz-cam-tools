#!/usr/bin/env python3
"""Device detection debug script."""

import sys
sys.path.insert(0, '.')

from PySide6.QtWidgets import QApplication
from PySide6.QtMultimedia import QMediaDevices, QCameraDevice

print("=" * 60)
print("Device Detection Debug Test")
print("=" * 60)

# Step 1: Check QApplication
print("\n[Step 1] Creating QApplication...")
app = QApplication.instance() or QApplication(sys.argv)
print(f"  QApplication created: {app}")

# Step 2: Check QMediaDevices
print("\n[Step 2] Creating QMediaDevices...")
try:
    md = QMediaDevices()
    print(f"  QMediaDevices created: {md}")
except Exception as e:
    print(f"  ERROR: {e}")
    sys.exit(1)

# Step 3: Get videoInputs
print("\n[Step 3] Getting video inputs...")
try:
    devices = md.videoInputs()
    print(f"  Found {len(devices)} device(s)")
except Exception as e:
    print(f"  ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Step 4: Inspect each device
print("\n[Step 4] Inspecting devices...")
for i, device in enumerate(devices):
    print(f"\n  Device {i+1}:")
    try:
        device_id = device.id()
        print(f"    ID type: {type(device_id)}")
        print(f"    ID: {device_id[:80] if len(str(device_id)) > 80 else device_id}...")
    except Exception as e:
        print(f"    ID ERROR: {e}")
    
    try:
        print(f"    Description: {device.description()}")
    except Exception as e:
        print(f"    Description ERROR: {e}")
    
    try:
        print(f"    IsDefault: {device.isDefault()}")
    except Exception as e:
        print(f"    IsDefault ERROR: {e}")
    
    try:
        print(f"    Position: {device.position()}")
    except Exception as e:
        print(f"    Position ERROR: {e}")
    
    # Check photo resolutions
    try:
        resolutions = device.photoResolutions()
        print(f"    Photo resolutions: {len(resolutions)} available")
        for j, res in enumerate(resolutions[:3]):  # Show first 3
            print(f"      - {res.width()}x{res.height()}")
    except Exception as e:
        print(f"    Photo resolutions ERROR: {e}")
    
    # Check video formats
    try:
        formats = device.videoFormats()
        print(f"    Video formats: {len(formats)} available")
        for j, fmt in enumerate(formats[:3]):  # Show first 3
            try:
                print(f"      - {fmt.resolution().width()}x{fmt.resolution().height()} "
                      f"@ {fmt.maxFrameRate()}fps")
            except Exception as e2:
                print(f"      - Format {j} ERROR: {e2}")
    except Exception as e:
        print(f"    Video formats ERROR: {e}")

# Step 5: Test DeviceManager
print("\n[Step 5] Testing DeviceManager...")
from app.utils.device_manager import DeviceManager, CameraDevice

try:
    dm = DeviceManager()
    print("  DeviceManager created")
    
    devices = dm.enumerate_devices()
    print(f"  DeviceManager found {len(devices)} device(s)")
    
    for device in devices:
        print(f"    - {device.name} (ID: {device.id[:50]}...)")
except Exception as e:
    print(f"  ERROR: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("Test Complete")
print("=" * 60)
