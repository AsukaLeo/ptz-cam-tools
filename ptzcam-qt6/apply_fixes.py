#!/usr/bin/env python3
"""Apply critical fixes to USBTab and dshow_capture."""

import re

# Fix 1: Update usb_tab.py to prevent signal loop
uv_file = 'app/tabs/usb_tab.py'
with open(uv_file, 'r', encoding='utf-8') as f:
    content = f.read()

# Fix _on_capture_state_changed to not call _stop_playback
old_state_handler = '''    def _on_capture_state_changed(self, state: str) -> None:
        """Handle capture state change.
        
        Args:
            state: New state ('playing', 'stopped').
        """
        self._logger.debug(f"Capture state: {state}")
        if state == 'stopped':
            self._stop_playback()'''

new_state_handler = '''    def _on_capture_state_changed(self, state: str) -> None:
        """Handle capture state change.
        
        Args:
            state: New state ('playing', 'stopped').
        """
        self._logger.debug(f"Capture state: {state}")
        # Only update UI if state changed externally
        if state == 'stopped' and self.play_btn.text() == "停止":
            # Playback stopped externally, update UI only
            self._update_ui_stopped()'''

content = content.replace(old_state_handler, new_state_handler)

# Fix _stop_playback to prevent multiple calls
old_stop = '''    def _stop_playback(self) -> None:
        """Stop video playback."""
        self._logger.info("Stopping playback")
        self._notify_status("视频已停止")
        
        # Stop capture
        self._dshow_capture.stop_capture()
        
        # Show placeholder
        if hasattr(self.preview_widget, 'show_placeholder'):
            self.preview_widget.show_placeholder()
        
        # Update UI
        self.play_btn.setText("播放")
        self.device_combo.setEnabled(True)
        self.refresh_btn.setEnabled(True)
        self.res_combo.setEnabled(True)
        self.fmt_combo.setEnabled(True)
        self.fps_combo.setEnabled(True)'''

new_stop = '''    def _stop_playback(self) -> None:
        """Stop video playback."""
        # Prevent multiple calls
        if self.play_btn.text() == "播放":
            return
        
        self._logger.info("Stopping playback")
        self._notify_status("视频已停止")
        
        # Only stop if running
        if self._dshow_capture.is_running():
            self._dshow_capture.stop_capture()
        
        self._update_ui_stopped()
    
    def _update_ui_stopped(self) -> None:
        """Update UI to stopped state (without calling stop_capture)."""
        # Show placeholder
        if hasattr(self.preview_widget, 'show_placeholder'):
            self.preview_widget.show_placeholder()
        
        # Update UI
        self.play_btn.setText("播放")
        self.device_combo.setEnabled(True)
        self.refresh_btn.setEnabled(True)
        self.res_combo.setEnabled(True)
        self.fmt_combo.setEnabled(True)
        self.fps_combo.setEnabled(True)'''

content = content.replace(old_stop, new_stop)

with open(uv_file, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"Fixed {uv_file}")

# Fix 2: Create a simpler device enumerator using Qt (gets real names)
ds_show_file = 'app/utils/dshow_capture.py'
with open(ds_show_file, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace enumerate_devices with one that uses Qt for names
old_enum = '''    @staticmethod
    def enumerate_devices() -> List[DShowDevice]:
        """Enumerate DirectShow video capture devices.
        
        Returns:
            List of available capture devices with formats.
        """
        if not _HAS_CV2 or cv2 is None:
            print("OpenCV not available")
            return []
        
        devices = []
        index = 0
        
        while True:
            cap = None
            try:
                cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
                if not cap.isOpened():
                    break
                
                # Get device name using Windows API
                name = get_device_friendly_name(index)
                
                # Enumerate supported formats
                formats = DirectShowCapture._enumerate_formats(cap)
                
                device = DShowDevice(
                    index=index,
                    name=name,
                    device_path=f"video={index}",
                    formats=formats
                )
                devices.append(device)
                
            except Exception as e:
                print(f"Error enumerating device {index}: {e}")
                break
            finally:
                if cap:
                    cap.release()
            
            index += 1
            
            # Safety limit
            if index > 10:
                break
        
        return devices'''

new_enum = '''    @staticmethod
    def enumerate_devices(qt_device_names: dict = None) -> List[DShowDevice]:
        """Enumerate DirectShow video capture devices.
        
        Args:
            qt_device_names: Optional dict mapping index to device name from Qt.
        
        Returns:
            List of available capture devices with formats.
        """
        if not _HAS_CV2 or cv2 is None:
            print("OpenCV not available")
            return []
        
        devices = []
        index = 0
        
        while True:
            cap = None
            try:
                cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
                if not cap.isOpened():
                    break
                
                # Get device name - prefer Qt name, fallback to Windows API
                if qt_device_names and index in qt_device_names:
                    name = qt_device_names[index]
                else:
                    name = get_device_friendly_name(index)
                
                # Enumerate supported formats
                formats = DirectShowCapture._enumerate_formats(cap)
                
                device = DShowDevice(
                    index=index,
                    name=name,
                    device_path=f"video={index}",
                    formats=formats
                )
                devices.append(device)
                
            except Exception as e:
                print(f"Error enumerating device {index}: {e}")
                break
            finally:
                if cap:
                    cap.release()
            
            index += 1
            
            # Safety limit
            if index > 10:
                break
        
        return devices'''

content = content.replace(old_enum, new_enum)

with open(ds_show_file, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"Fixed {ds_show_file}")

print("\nFixes applied successfully!")
print("Now run: python main.py")
