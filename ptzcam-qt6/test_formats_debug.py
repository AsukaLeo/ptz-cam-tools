#!/usr/bin/env python3
"""Debug pixel formats from cameras."""

import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtMultimedia import QMediaDevices, QCameraFormat

app = QApplication.instance() or QApplication(sys.argv)

md = QMediaDevices()
devices = md.videoInputs()

print("=" * 60)
print("Pixel Format Debug")
print("=" * 60)

# List all available pixel format enums
print("\n[QVideoFrameFormat.PixelFormat enum values]:")
from PySide6.QtMultimedia import QVideoFrameFormat
for attr_name in dir(QVideoFrameFormat.PixelFormat):
    if not attr_name.startswith('_'):
        try:
            value = getattr(QVideoFrameFormat.PixelFormat, attr_name)
            if isinstance(value, QVideoFrameFormat.PixelFormat):
                print(f"  {attr_name} = {int(value)}")
        except:
            pass

print("\n[Device formats]:")
for i, device in enumerate(devices):
    print(f"\nDevice {i+1}: {device.description()}")
    formats = device.videoFormats()
    print(f"  Total formats: {len(formats)}")
    
    # Show unique formats
    unique_formats = {}
    for fmt in formats[:20]:  # Check first 20
        try:
            pf = fmt.pixelFormat()
            pf_name = str(pf)
            pf_value = pf.value if hasattr(pf, 'value') else str(pf)
            
            key = pf_name
            if key not in unique_formats:
                unique_formats[key] = {
                    'value': pf_value,
                    'res': (fmt.resolution().width(), fmt.resolution().height()),
                    'fps': fmt.maxFrameRate()
                }
        except Exception as e:
            print(f"    Error reading format: {e}")
    
    for pf_name, info in sorted(unique_formats.items()):
        print(f"  {pf_name} (value={info['value']})")
        print(f"    Example: {info['res'][0]}x{info['res'][1]} @ {info['fps']}fps")

print("\n" + "=" * 60)
