# Fix for USBTab - prevent signal loop and improve video display

# In _on_capture_state_changed, add a guard:
def _on_capture_state_changed(self, state: str) -> None:
    """Handle capture state change."""
    self._logger.debug(f"Capture state: {state}")
    # Only update UI, don't call _stop_playback again to avoid loop
    if state == 'stopped' and self.play_btn.text() == "停止":
        # Playback stopped externally, update UI only
        self.play_btn.setText("播放")
        self.device_combo.setEnabled(True)
        self.refresh_btn.setEnabled(True)
        self.res_combo.setEnabled(True)
        self.fmt_combo.setEnabled(True)
        self.fps_combo.setEnabled(True)
        # Show placeholder
        if hasattr(self.preview_widget, 'show_placeholder'):
            self.preview_widget.show_placeholder()

# In _stop_playback, prevent calling stop_capture if already stopped:
def _stop_playback(self) -> None:
    """Stop video playback."""
    self._logger.info("Stopping playback")
    self._notify_status("视频已停止")
    
    # Only stop if running
    if self._dshow_capture.is_running():
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
    self.fps_combo.setEnabled(True)
