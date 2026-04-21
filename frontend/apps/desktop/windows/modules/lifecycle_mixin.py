class LifecycleMixin:
    def showEvent(self, event):
        if not getattr(self, "_shortcuts_initialized", False) and hasattr(self, "setup_keyboard_shortcuts"):
            self.setup_keyboard_shortcuts()
            self._shortcuts_initialized = True

        if not hasattr(self, "timer") or self.timer is None:
            from PyQt5.QtCore import QTimer

            self.timer = QTimer(self)
            self.timer.timeout.connect(self.update_ui)

        if self.timer is not None and not self.timer.isActive():
            self.timer.start(100)
        self._ui_timer_started = True

        if not getattr(self, "_network_monitor_initialized", False) and hasattr(self, "init_network_monitor"):
            self.init_network_monitor()
            self._network_monitor_initialized = True

        super().showEvent(event)

    def update_ui(self):
        # 低频检测输出设备变化，解决播放中插拔耳机导致无声的问题。
        self._ui_tick += 1
        if self._ui_tick % 10 == 0:
            self.audio_player.recover_on_device_change()

        if (
            getattr(self.audio_player, "is_playing", False)
            and not getattr(self.audio_player, "is_paused", False)
            and hasattr(self, "schedule_save_app_settings")
        ):
            interval = max(1, int(getattr(self, "_progress_persist_interval_seconds", 5) or 5))
            current_position = max(0.0, float(self.audio_player.get_position()))
            current_bucket = int(current_position // interval)
            if current_bucket > int(getattr(self, "_last_progress_save_bucket", -1)):
                self._last_progress_save_bucket = current_bucket
                self.schedule_save_app_settings()

    def closeEvent(self, event):
        if hasattr(self, "should_hide_to_tray_on_close") and self.should_hide_to_tray_on_close():
            event.ignore()
            self.hide_to_tray()
            return

        self._is_closing = True
        if hasattr(self, "_cancel_duration_probe"):
            self._cancel_duration_probe()
        if getattr(self, "current_song", None):
            self._pending_resume_song_id = str(self.current_song.get("id", "") or "")
            if getattr(self.audio_player, "is_playing", False):
                self._pending_resume_position_seconds = max(0.0, float(self.audio_player.get_position()))
        if hasattr(self, "timer") and self.timer is not None and self.timer.isActive():
            self.timer.stop()
        if getattr(self, "progress_timer", None) is not None and self.progress_timer.isActive():
            self.progress_timer.stop()
        network_timer = getattr(self, "_network_check_timer", None)
        if network_timer is not None and network_timer.isActive():
            network_timer.stop()
        if self.scan_worker and self.scan_worker.isRunning():
            self.scan_worker.requestInterruption()
            self.scan_worker.quit()
            self.scan_worker.wait(2000)
        if hasattr(self, "_cancel_decode_worker"):
            self._cancel_decode_worker()
        settings_timer = getattr(self, "_settings_save_timer", None)
        if settings_timer is not None and settings_timer.isActive():
            settings_timer.stop()
        self.cleanup_lyrics()
        self.save_playlists()
        self.save_app_settings()
        try:
            self.audio_player.stop()
        except Exception:
            # 关闭阶段优先保证进程可退出，底层音频 stop 异常不应触发崩溃。
            pass
        if hasattr(self, "teardown_system_tray"):
            self.teardown_system_tray()
        event.accept()

